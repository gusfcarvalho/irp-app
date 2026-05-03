"""Parser for B3 Posicao (positions) XLSX report.

Handles sheets: Renda Fixa, Tesouro Direto, Acoes / BDR / ETF.
All transactions are flagged needs_review=True since closing prices
are used as a proxy for acquisition price.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import openpyxl

from app.services.parsers.b3_asset_type import infer_from_produto

logger = logging.getLogger(__name__)

_FIXED_INCOME_SHEET = "renda fixa"
_TESOURO_SHEETS = {"tesouro direto", "tesouro", "td"}
_EQUITY_SHEETS = {"ações", "acoes", "bdr", "etf", "ações bdr e etf", "acoes bdr e etf"}


@dataclass
class B3PosicaoTrade:
    ticker: str
    quantity: Decimal
    price: Decimal
    side: str = "BUY"
    needs_review: bool = True
    asset_type: str | None = None


@dataclass
class B3PosicaoResult:
    trades: list[B3PosicaoTrade] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _safe_decimal(val) -> Decimal | None:
    if val is None or val == "-" or val == "":
        return None
    s = str(val).strip().replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _find_col(headers: list, *candidates: str) -> int | None:
    """Return 0-based index of first matching header (case-insensitive)."""
    normalized = [str(h).strip().lower() if h else "" for h in headers]
    for candidate in candidates:
        c = candidate.lower()
        for i, h in enumerate(normalized):
            if h == c:
                return i
    return None


def _parse_renda_fixa(ws) -> list[B3PosicaoTrade]:
    trades = []
    headers = None
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = list(row)
            continue
        if not any(row):
            continue

        produto_idx = _find_col(headers, "produto")
        codigo_idx = _find_col(headers, "código", "codigo")
        qty_idx = _find_col(headers, "quantidade")
        curva_idx = _find_col(headers, "preço atualizado curva", "preco atualizado curva")
        fechamento_idx = _find_col(headers, "preço atualizado fechamento", "preco atualizado fechamento")
        mtm_idx = _find_col(headers, "preço atualizado mtm", "preco atualizado mtm")

        if qty_idx is None:
            logger.warning("Renda Fixa sheet missing quantidade column")
            break

        qty_raw = row[qty_idx]
        if not qty_raw:
            continue

        produto = str(row[produto_idx]).strip() if produto_idx is not None and row[produto_idx] else ""
        codigo = str(row[codigo_idx]).strip() if codigo_idx is not None and row[codigo_idx] else ""

        # Tesouro Direto rows appear in this sheet too; use Produto as the ticker
        # since they have no short Código. Also fall back to Produto when Código is absent.
        is_tesouro = produto.lower().startswith("tesouro")
        if is_tesouro:
            ticker = produto
        elif codigo:
            ticker = codigo
        else:
            ticker = produto

        if not ticker:
            continue

        ticker = str(ticker).strip()
        qty = _safe_decimal(qty_raw)
        if qty is None or qty <= 0:
            logger.warning("Renda Fixa: invalid quantity %r for ticker %s", qty_raw, ticker)
            continue

        # Try prices in order of preference: CURVA, FECHAMENTO, MTM
        price = None
        for idx in [curva_idx, fechamento_idx, mtm_idx]:
            if idx is not None:
                price = _safe_decimal(row[idx])
                if price is not None and price > 0:
                    break

        if price is None:
            logger.warning("Renda Fixa: no valid price for ticker %s", ticker)
            continue

        trades.append(B3PosicaoTrade(
            ticker=ticker,
            quantity=qty,
            price=price,
            asset_type=infer_from_produto(produto),
        ))

    return trades


def _parse_tesouro_direto(ws) -> list[B3PosicaoTrade]:
    """Parse Tesouro Direto sheet.

    TD quantities are fractional títulos (e.g. 0.68).  Since Transaction.quantity
    is an integer we store centésimos (× 100) and adjust the price proportionally
    so that qty_centesimos × price_per_centesimo == valor_aplicado exactly.
    """
    trades = []
    headers = None
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = list(row)
            continue
        if not any(row):
            continue

        produto_idx = _find_col(headers, "produto")
        qty_idx = _find_col(headers, "quantidade")
        valor_aplicado_idx = _find_col(headers, "valor aplicado")

        if produto_idx is None or qty_idx is None:
            logger.warning("Tesouro Direto sheet missing expected columns")
            break

        ticker = row[produto_idx]
        qty_raw = row[qty_idx]

        if not ticker or not qty_raw:
            continue

        ticker = str(ticker).strip()
        if not ticker:
            continue

        qty = _safe_decimal(qty_raw)
        if qty is None or qty <= 0:
            logger.warning("Tesouro Direto: invalid quantity %r for ticker %s", qty_raw, ticker)
            continue

        valor = _safe_decimal(row[valor_aplicado_idx]) if valor_aplicado_idx is not None else None
        if valor is None or valor <= 0:
            logger.warning("Tesouro Direto: no Valor Aplicado for ticker %s", ticker)
            continue

        # price = total_invested / quantity preserves cost basis exactly
        price = valor / qty

        trades.append(B3PosicaoTrade(ticker=ticker, quantity=qty, price=price, asset_type="TD"))

    return trades


def _parse_equity(ws) -> list[B3PosicaoTrade]:
    """Parse Ações / BDR / ETF sheets."""
    trades = []
    headers = None
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = list(row)
            continue
        if not any(row):
            continue

        ticker_idx = _find_col(headers, "código de negociação", "codigo de negociacao", "codigo negociacao")
        qty_idx = _find_col(headers, "qtd.", "qtd", "quantidade")
        price_idx = _find_col(headers, "preço de fechamento", "preco de fechamento", "preco fechamento")

        if ticker_idx is None or qty_idx is None:
            logger.warning("Equity sheet missing expected columns")
            break

        ticker = row[ticker_idx]
        qty_raw = row[qty_idx]

        if not ticker or not qty_raw:
            continue

        ticker = str(ticker).strip()
        if not ticker:
            continue

        qty = _safe_decimal(qty_raw)
        if qty is None or qty <= 0:
            logger.warning("Equity: invalid quantity %r for ticker %s", qty_raw, ticker)
            continue

        price = None
        if price_idx is not None:
            price = _safe_decimal(row[price_idx])
        if price is None or price <= 0:
            logger.warning("Equity: no valid price for ticker %s", ticker)
            continue

        trades.append(B3PosicaoTrade(ticker=ticker, quantity=qty, price=price, asset_type=None))

    return trades


def parse_posicao(filepath: str) -> B3PosicaoResult:
    result = B3PosicaoResult()
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
    except Exception as exc:
        result.errors.append(f"Failed to open XLSX: {exc}")
        return result

    for sheet_name in wb.sheetnames:
        normalized = sheet_name.strip().lower()
        ws = wb[sheet_name]
        try:
            if normalized == _FIXED_INCOME_SHEET:
                result.trades.extend(_parse_renda_fixa(ws))
            elif normalized in _TESOURO_SHEETS:
                result.trades.extend(_parse_tesouro_direto(ws))
            elif normalized in _EQUITY_SHEETS or any(eq in normalized for eq in _EQUITY_SHEETS):
                result.trades.extend(_parse_equity(ws))
            else:
                logger.info("Posicao: unrecognized sheet '%s', skipping", sheet_name)
        except Exception as exc:
            msg = f"Error parsing sheet '{sheet_name}': {exc}"
            logger.exception(msg)
            result.errors.append(msg)

    return result
