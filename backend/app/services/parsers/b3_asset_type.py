"""Infer AssetType from a B3 Produto string."""

_PREFIX_MAP: dict[str, str] = {
    "CDB":       "CDB",
    "LCI":       "LCI",
    "LCA":       "LCA",
    "LCF":       "LCF",
    "LIG":       "LIG",
    "CRI":       "CRI",
    "CRA":       "CRA",
    "DEB":       "DEB",
    "DEBENTURE": "DEB",
    "DEBÊNTURE": "DEB",
    "FI-INFRA":  "CRI",
    "FIDC":      "RF_POS",
    "FIC":       "RF_POS",
    # Tesouro Nacional codes that appear as prefixes
    "NTN-B":     "TD",
    "NTN-F":     "TD",
    "LFT":       "TD",
}


def infer_from_produto(produto: str) -> str | None:
    """Return the AssetType string inferred from a B3 Produto description, or None."""
    if not produto:
        return None
    if produto.strip().lower().startswith("tesouro"):
        return "TD"
    prefix = produto.split(" - ")[0].strip().upper()
    return _PREFIX_MAP.get(prefix)
