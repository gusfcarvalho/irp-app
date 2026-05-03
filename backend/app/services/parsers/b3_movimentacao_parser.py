"""Parser for B3 Movimentacoes (movements) XLSX report.

Only imports the allowed transaction types. Direction is inferred from
Entrada/Saída: Crédito → BUY, Débito → SELL.
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

import openpyxl

from app.services.parsers.b3_asset_type import infer_from_produto

logger = logging.getLogger(__name__)

# Product type prefixes that appear before the actual code in Produto
_PRODUCT_PREFIXES = {
    "CDB", "LCI", "LCA", "LCF", "LFT", "LIG",
    "NTN-B", "NTN-F", "CRI", "CRA",
    "DEB", "DEBENTURE", "DEBÊNTURE", "FI-INFRA",
    "FIDC", "FIC", "FII",
}

# Allowed movimentação types (normalized: upper, spaces around slash removed)
_ALLOWED_TYPES = {
    "RESGATE ANTECIPADO",
    "RESGATE",
    "VENCIMENTO/RESGATE SALDO EM CONTA",
    "APLICACAO",
    "APLICAÇÃO",
    "COMPRA/VENDA",
    "VENDA",
    "MDA COMPRA/VENDA DEFINITIVA MERCADO PRIMARIO",
    "COMPRA",
}


def _normalize_mov_type(t: str) -> str:
    t = t.strip().upper()
    t = re.sub(r'\s*/\s*', '/', t)
    t = t.rstrip('/').strip()
    return t


def _is_allowed(mov_type: str) -> bool:
    return _normalize_mov_type(mov_type) in _ALLOWED_TYPES


def _parse_ticker(produto: str) -> str:
    parts = [p.strip() for p in produto.split(" - ")]
    if len(parts) >= 2 and parts[0].upper() in _PRODUCT_PREFIXES:
        return parts[1].strip()
    return parts[0].strip()


def _parse_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    s = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return date.fromisoformat(s) if fmt == "%Y-%m-%d" else date(*reversed([int(x) for x in s.split("/")]))
        except (ValueError, AttributeError):
            continue
    return None


def _safe_decimal(val) -> Decimal | None:
    if val is None or val == "-" or val == "":
        return None
    s = str(val).strip().replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


@dataclass
class B3MovimentacaoTrade:
    ticker: str
    trade_date: date
    quantity: Decimal
    price: Decimal
    side: str              # BUY | SELL
    asset_type: str | None = None


@dataclass
class B3MovimentacaoResult:
    trades: list[B3MovimentacaoTrade] = field(default_factory=list)
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def parse_movimentacao(filepath: str) -> B3MovimentacaoResult:
    result = B3MovimentacaoResult()
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
    except Exception as exc:
        result.errors.append(f"Failed to open XLSX: {exc}")
        return result

    sheet = wb.active
    headers = None

    for row in sheet.iter_rows(values_only=True):
        if headers is None:
            headers = [str(h).strip() if h else "" for h in row]
            continue

        if not any(row):
            continue

        # Map columns by header
        h = {name.lower(): i for i, name in enumerate(headers)}

        entrada_saida = row[h.get("entrada/saída", h.get("entrada/saida", -1))]
        data_val = row[h.get("data", -1)]
        mov_type = row[h.get("movimentação", h.get("movimentacao", -1))]
        produto = row[h.get("produto", -1)]
        qty_raw = row[h.get("quantidade", -1)]
        price_raw = row[h.get("preço unitário", h.get("preco unitario", -1))]

        if not mov_type or not produto:
            continue

        if not _is_allowed(str(mov_type)):
            result.skipped += 1
            continue

        ticker = _parse_ticker(str(produto))
        if not ticker:
            result.errors.append(f"Cannot parse ticker from Produto: {produto}")
            continue

        trade_date = _parse_date(data_val)
        if trade_date is None:
            result.errors.append(f"Cannot parse date '{data_val}' for {ticker}")
            continue

        qty = _safe_decimal(qty_raw)
        if qty is None or qty <= 0:
            result.errors.append(f"Invalid quantity '{qty_raw}' for {ticker} on {trade_date}")
            continue

        price = _safe_decimal(price_raw)
        if price is None or price < 0:
            result.errors.append(f"Invalid price '{price_raw}' for {ticker} on {trade_date}")
            continue

        # Determine BUY/SELL from Entrada/Saída
        entrada = str(entrada_saida).strip().lower() if entrada_saida else ""
        if "credito" in entrada or "crédito" in entrada or entrada == "credito":
            side = "BUY"
        else:
            side = "SELL"

        result.trades.append(B3MovimentacaoTrade(
            ticker=ticker,
            trade_date=trade_date,
            quantity=qty,
            price=price,
            side=side,
            asset_type=infer_from_produto(str(produto)),
        ))

    return result
