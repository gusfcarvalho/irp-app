from decimal import Decimal

from app.models.schemas import MonthlyReport, Trade


def calculate_monthly_tax(month: str, trades: list[Trade]) -> MonthlyReport:
    # Skeleton only: rule engine not yet implemented.
    return MonthlyReport(
        month=month,
        swing_profit_loss=Decimal("0"),
        day_trade_profit_loss=Decimal("0"),
        fii_profit_loss=Decimal("0"),
        tax_due=Decimal("0"),
    )
