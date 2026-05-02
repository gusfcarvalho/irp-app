"""Resolve B3 company descriptions (e.g. 'AMBEV S/A ON') to ticker codes (e.g. 'ABEV3').

Used when a brokerage note (e.g. Clear) supplies a full company name instead of
the ticker code.

Strategy
--------
1. Disk cache  — check `data/ticker_cache.json` first (persists across restarts).
2. Yahoo Finance search — free, no key required.  Filters to exchange=SAO (.SA suffix).
3. Share-type hint — uses the ON/PN/UNT suffix to pick the right class when a
   company has multiple share types.

Each new resolution is written to the cache immediately, so subsequent uploads
never hit the network for the same ticker.
"""

import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Valid B3 ticker: 4-5 uppercase letters followed by 1-2 digits (e.g. ABEV3, AAPL34)
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{2,4}\d{1,2}$")

# Noise tokens that appear in nota descriptions but are irrelevant for name matching
_NOISE = re.compile(
    r"\b(?:ON|PN|UNT|DRN|CI|ER|EJ|EX|NM|N1|N2|MA|MB|"
    r"S/?A|LTDA|CIA|COMPANHIA|HOLDING|PARTICIPACOES?|PARTICIPAÇÕES?)\b",
    re.IGNORECASE,
)
_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")

# Share-type → preferred ticker digit suffixes for disambiguation
_TYPE_DIGITS: dict[str, tuple[str, ...]] = {
    "ON":  ("3", "6"),
    "PN":  ("4", "5"),
    "UNT": ("11",),
    "DRN": ("34", "32", "33", "35", "36", "37", "38", "39"),
}

_YF_URL = "https://query2.finance.yahoo.com/v1/finance/search"
_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json",
}
_CACHE_PATH = Path(os.getenv("DATA_DIR", "./data")) / "ticker_cache.json"


# ── helpers ───────────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """Lowercase, punctuation-free, noise-token-stripped form for comparison."""
    name = _NOISE.sub(" ", name)
    name = _PUNCT.sub(" ", name)
    return _WS.sub(" ", name).strip().lower()


def _search_query(description: str) -> str:
    """Build a clean search string from a nota description."""
    q = _NOISE.sub(" ", description)
    q = _PUNCT.sub(" ", q)
    return _WS.sub(" ", q).strip()


def _share_type(description: str) -> Optional[str]:
    upper = description.upper()
    for t in ("UNT", "DRN", "PN", "ON"):   # longest first
        if re.search(rf"\b{t}\b", upper):
            return t
    return None


def _pick(candidates: list[str], stype: Optional[str]) -> Optional[str]:
    if not candidates:
        return None
    if len(candidates) == 1 or stype is None:
        return candidates[0]
    preferred_suffixes = _TYPE_DIGITS.get(stype, ())
    preferred = [t for t in candidates if any(t.endswith(s) for s in preferred_suffixes)]
    return (preferred or candidates)[0]


# ── resolver ─────────────────────────────────────────────────────────────────

class TickerResolver:
    """Yahoo Finance–backed resolver with persistent disk cache."""

    def __init__(self) -> None:
        self._cache: dict[str, Optional[str]] = {}   # norm_desc → ticker (or None)
        self._cache_loaded = False

    # ── public ───────────────────────────────────────────────────────────────

    def is_valid_ticker(self, s: str) -> bool:
        return bool(TICKER_RE.match(s.upper().strip()))

    def resolve(self, description: str) -> Optional[str]:
        """Return the B3 ticker that best matches *description*, or None."""
        if not self._cache_loaded:
            self._load_cache()

        stype = _share_type(description)
        key = _normalize(description)
        if not key:
            return None

        # 1. Disk cache hit
        if key in self._cache:
            cached = self._cache[key]
            logger.debug("Cache hit %r → %r", description, cached)
            return cached

        # 2. Yahoo Finance lookup
        result = self._yahoo_search(_search_query(description), stype)
        logger.info("Yahoo Finance %r → %r", description, result)

        # Persist even None so we don't retry failed lookups
        self._cache[key] = result
        self._save_cache()
        return result

    # ── internals ────────────────────────────────────────────────────────────

    def _load_cache(self) -> None:
        self._cache_loaded = True
        if _CACHE_PATH.exists():
            try:
                self._cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
                logger.debug("Ticker cache loaded (%d entries)", len(self._cache))
            except Exception as exc:
                logger.warning("Could not load ticker cache: %s", exc)
                self._cache = {}

    def _save_cache(self) -> None:
        try:
            _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            _CACHE_PATH.write_text(
                json.dumps(self._cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Could not save ticker cache: %s", exc)

    def _yahoo_search(self, query: str, stype: Optional[str]) -> Optional[str]:
        params = urllib.parse.urlencode({
            "q": query,
            "lang": "pt-BR",
            "region": "BR",
            "quotesCount": "10",
            "newsCount": "0",
            "listsCount": "0",
        })
        url = f"{_YF_URL}?{params}"
        try:
            req = urllib.request.Request(url, headers=_REQUEST_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            b3_tickers = [
                q["symbol"].removesuffix(".SA").upper()
                for q in data.get("quotes", [])
                if q.get("exchange") == "SAO"
                and str(q.get("symbol", "")).endswith(".SA")
            ]
            return _pick(b3_tickers, stype)

        except Exception as exc:
            logger.warning("Yahoo Finance search for %r failed: %s", query, exc)
            return None


# Module-level singleton
resolver = TickerResolver()
