"""Unit tests for the position engine (fee distribution + custo médio)."""

from datetime import UTC, date, datetime
from decimal import Decimal

from app.services.position_engine import (
    CorporateAction,
    TxnWithFees,
    _adjusted_price,
    compute_positions,
    compute_positions_with_steps,
)


def _txn(ticker, side, qty, price, fees=Decimal(0), notional=None, date_=date(2026, 1, 1)):
    n = notional if notional is not None else Decimal(price) * qty
    return TxnWithFees(
        txn_id="x",
        upload_id="u",
        ticker=ticker,
        trade_date=date_,
        uploaded_at=datetime(2026, 1, 1, tzinfo=UTC),
        side=side,
        quantity=qty,
        raw_price=Decimal(price),
        total_nota_fees=fees,
        nota_notional=n,
    )


class TestFeeAdjustedPrice:
    def test_no_fees_unchanged(self):
        t = _txn("PETR4", "BUY", 100, "30.00", fees=Decimal(0))
        assert _adjusted_price(t) == Decimal("30.00")

    def test_buy_fee_increases_price(self):
        t = _txn("PETR4", "BUY", 100, "30.00", fees=Decimal("10.00"))
        adj = _adjusted_price(t)
        assert adj > Decimal("30.00")
        assert adj == Decimal("30.10")

    def test_sell_fee_decreases_price(self):
        t = _txn("PETR4", "SELL", 100, "30.00", fees=Decimal("10.00"))
        adj = _adjusted_price(t)
        assert adj < Decimal("30.00")
        assert adj == Decimal("29.90")

    def test_fee_distributed_proportionally(self):
        notional = Decimal("30.00") * 100 + Decimal("20.00") * 50  # 4000
        t1 = TxnWithFees("1", "u", "PETR4", date(2026,1,1), datetime(2026,1,1,tzinfo=UTC),
                          "BUY", 100, Decimal("30.00"), Decimal("40.00"), notional)
        t2 = TxnWithFees("2", "u", "VALE3", date(2026,1,1), datetime(2026,1,1,tzinfo=UTC),
                          "BUY", 50, Decimal("20.00"), Decimal("40.00"), notional)
        adj1 = _adjusted_price(t1)
        adj2 = _adjusted_price(t2)
        fee1 = (adj1 - Decimal("30.00")) * 100
        fee2 = (adj2 - Decimal("20.00")) * 50
        assert (fee1 + fee2).quantize(Decimal("0.01")) == Decimal("40.00")
        assert fee1 > fee2


class TestComputePositions:
    def test_simple_buy(self):
        txns = [_txn("PETR4", "BUY", 100, "30.00")]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 100
        assert result["PETR4"].mean_price == Decimal("30.00")

    def test_two_buys_weighted_mean(self):
        txns = [
            _txn("PETR4", "BUY", 100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY", 100, "40.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 200
        assert result["PETR4"].mean_price == Decimal("35.00")

    def test_sell_keeps_mean_reduces_qty(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL",  40, "35.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 60
        assert result["PETR4"].mean_price == Decimal("30.00")

    def test_full_sell_resets_position(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 0
        assert result["PETR4"].mean_price == Decimal("0")

    def test_buy_with_fees_adjusts_mean(self):
        txns = [_txn("PETR4", "BUY", 100, "30.00", fees=Decimal("10.00"))]
        result = compute_positions(txns)
        assert result["PETR4"].mean_price == Decimal("30.10")

    def test_chronological_ordering(self):
        txns = [
            _txn("PETR4", "BUY",  100, "40.00", date_=date(2026, 1, 2)),
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].mean_price == Decimal("35.00")

    def test_multiple_tickers_independent(self):
        txns = [
            _txn("PETR4", "BUY", 100, "30.00"),
            _txn("VALE3", "BUY",  50, "20.00"),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 100
        assert result["VALE3"].quantity == 50


def _ca(ticker, action_type, ratio_from, ratio_to, date_=date(2026, 1, 1)):
    """Helper to create corporate action."""
    return CorporateAction(
        txn_id="ca",
        ticker=ticker,
        trade_date=date_,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        action_type=action_type,
        ratio_from=ratio_from,
        ratio_to=ratio_to,
    )


class TestZeroQuantityTransactions:
    def test_zero_qty_buy_is_ignored(self):
        txns = [
            _txn("PETR4", "BUY", 0, "30.00"),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        result = compute_positions(txns)
        assert result.get("PETR4") is None or result["PETR4"].quantity == 0
        assert len(closed) == 0

    def test_zero_qty_mixed_with_valid_txn(self):
        txns = [
            _txn("PETR4", "BUY", 100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY",   0, "35.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 100
        assert result["PETR4"].mean_price == Decimal("30.00")


class TestShortPositions:
    def test_sell_more_than_owned_opens_short(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 150, "35.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == -50
        assert result["PETR4"].mean_price == Decimal("35.00")

    def test_sell_from_zero_opens_short(self):
        txns = [_txn("PETR4", "SELL", 100, "30.00")]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == -100
        assert result["PETR4"].mean_price == Decimal("30.00")

    def test_deepening_short_weighted_average(self):
        txns = [
            _txn("PETR4", "SELL", 100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL",  50, "20.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == -150
        # Weighted avg: (100 * 30 + 50 * 20) / 150 = 4000/150 ≈ 26.67
        expected_mean = (Decimal("100") * Decimal("30") + Decimal("50") * Decimal("20")) / 150
        assert abs(result["PETR4"].mean_price - expected_mean) < Decimal("0.01")

    def test_partial_cover_keeps_short_mean(self):
        txns = [
            _txn("PETR4", "SELL", 100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY",   40, "25.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == -60
        assert result["PETR4"].mean_price == Decimal("30.00")

    def test_full_cover_resets_position(self):
        txns = [
            _txn("PETR4", "SELL", 100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY",  100, "25.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 0
        assert result["PETR4"].mean_price == Decimal("0")

    def test_cover_short_and_go_long(self):
        txns = [
            _txn("PETR4", "SELL", 100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY",  150, "25.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 50
        assert result["PETR4"].mean_price == Decimal("25.00")


class TestBonusTransactions:
    def test_bonus_adds_shares_at_zero_cost(self):
        txns = [
            _txn("PETR4", "BUY", 100, "10.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BONUS", 10, "0.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 110
        # Mean diluted: (100 * 10 + 10 * 0) / 110 = 1000/110 ≈ 9.09
        expected_mean = (Decimal("10.00") * 100) / 110
        assert abs(result["PETR4"].mean_price - expected_mean) < Decimal("0.01")

    def test_bonus_fee_increases_cost_basis(self):
        t = _txn("PETR4", "BONUS", 100, "5.00", fees=Decimal("10.00"))
        adj = _adjusted_price(t)
        assert adj == Decimal("5.10")  # fee adds to cost basis, same as BUY

    def test_bonus_with_cost_basis(self):
        txns = [
            _txn("PETR4", "BUY", 100, "10.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BONUS", 10, "5.00", date_=date(2026, 1, 2)),
        ]
        result = compute_positions(txns)
        assert result["PETR4"].quantity == 110
        # Mean: (100 * 10 + 10 * 5) / 110 = 1050/110 ≈ 9.545
        expected_mean = (Decimal("10.00") * 100 + Decimal("5.00") * 10) / 110
        assert abs(result["PETR4"].mean_price - expected_mean) < Decimal("0.01")


class TestCorporateActions:
    def test_splitting_doubles_qty_halves_mean(self):
        """1:2 split: 100 shares at R$10 -> 200 shares at R$5"""
        txns = [_txn("PETR4", "BUY", 100, "10.00", date_=date(2026, 1, 1))]
        corp_actions = [_ca("PETR4", "SPLITTING", 1, 2, date_=date(2026, 1, 2))]
        result = compute_positions(txns, corp_actions)
        assert result["PETR4"].quantity == 200
        assert result["PETR4"].mean_price == Decimal("5.00")

    def test_grouping_halves_qty_doubles_mean(self):
        """2:1 grouping: 200 shares at R$5 -> 100 shares at R$10"""
        txns = [_txn("PETR4", "BUY", 200, "5.00", date_=date(2026, 1, 1))]
        corp_actions = [_ca("PETR4", "GROUPING", 2, 1, date_=date(2026, 1, 2))]
        result = compute_positions(txns, corp_actions)
        assert result["PETR4"].quantity == 100
        assert result["PETR4"].mean_price == Decimal("10.00")

    def test_split_preserves_total_cost_basis(self):
        """Total cost basis should be unchanged after split."""
        txns = [_txn("PETR4", "BUY", 100, "30.00", date_=date(2026, 1, 1))]
        corp_actions = [_ca("PETR4", "SPLITTING", 1, 3, date_=date(2026, 1, 2))]
        result = compute_positions(txns, corp_actions)

        original_cost = 100 * Decimal("30.00")  # 3000
        new_cost = result["PETR4"].quantity * result["PETR4"].mean_price

        assert result["PETR4"].quantity == 300
        assert abs(new_cost - original_cost) < Decimal("0.01")

    def test_grouping_preserves_total_cost_basis(self):
        """Total cost basis should be unchanged after grouping."""
        txns = [_txn("PETR4", "BUY", 300, "10.00", date_=date(2026, 1, 1))]
        corp_actions = [_ca("PETR4", "GROUPING", 3, 1, date_=date(2026, 1, 2))]
        result = compute_positions(txns, corp_actions)

        original_cost = 300 * Decimal("10.00")  # 3000
        new_cost = result["PETR4"].quantity * result["PETR4"].mean_price

        assert result["PETR4"].quantity == 100
        assert abs(new_cost - original_cost) < Decimal("0.01")

    def test_split_with_no_position_does_nothing(self):
        """Split on ticker with no position should not create position."""
        txns = []
        corp_actions = [_ca("PETR4", "SPLITTING", 1, 2, date_=date(2026, 1, 1))]
        result = compute_positions(txns, corp_actions)
        # Position exists but with qty=0
        assert result.get("PETR4") is None or result["PETR4"].quantity == 0

    def test_mixed_transactions_and_corporate_actions(self):
        """Test chronological processing of buys, sells, and corporate actions."""
        txns = [
            _txn("PETR4", "BUY", 100, "10.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY", 100, "12.00", date_=date(2026, 1, 3)),
        ]
        corp_actions = [
            _ca("PETR4", "SPLITTING", 1, 2, date_=date(2026, 1, 2)),  # After first buy
        ]
        result = compute_positions(txns, corp_actions)

        # After first buy: 100 @ 10
        # After split: 200 @ 5
        # After second buy: 200 + 100 = 300, mean = (200*5 + 100*12) / 300 = 2200/300 ≈ 7.33
        expected_mean = (Decimal("200") * Decimal("5") + Decimal("100") * Decimal("12")) / 300
        assert result["PETR4"].quantity == 300
        assert abs(result["PETR4"].mean_price - expected_mean) < Decimal("0.01")


class TestClosedPositions:
    def test_full_long_close_emits_event(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 1
        c = closed[0]
        assert c.ticker == "PETR4"
        assert c.direction == "LONG"
        assert c.quantity == 100
        assert c.open_mean_price == Decimal("30.00")
        assert c.close_price == Decimal("35.00")
        assert c.realized_pnl == Decimal("500.00000000")  # (35 - 30) * 100

    def test_partial_long_sell_no_close_event(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL",  40, "35.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 0

    def test_long_crossing_into_short_emits_close_for_long_portion(self):
        # Had +20, sold 100 → closes 20 long, opens -80 short
        txns = [
            _txn("PETR4", "BUY",  20, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 1
        c = closed[0]
        assert c.direction == "LONG"
        assert c.quantity == 20
        assert c.realized_pnl == Decimal("100.00000000")  # (35 - 30) * 20

    def test_long_cross_step_has_realized_pnl(self):
        txns = [
            _txn("PETR4", "BUY",  20, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 2)),
        ]
        _, steps, _ = compute_positions_with_steps(txns)
        sell_step = steps["PETR4"][1]
        assert sell_step.closes_quantity == 20
        assert sell_step.realized_pnl == Decimal("100.00000000")

    def test_full_short_cover_emits_event(self):
        txns = [
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 1
        c = closed[0]
        assert c.direction == "SHORT"
        assert c.quantity == 100
        assert c.realized_pnl == Decimal("500.00000000")  # (35 - 30) * 100 profit

    def test_short_crossing_into_long_emits_close_for_short_portion(self):
        # Short 100, buy 150 → closes 100 short, opens +50 long
        txns = [
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "BUY",  150, "30.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 1
        c = closed[0]
        assert c.direction == "SHORT"
        assert c.quantity == 100
        assert c.realized_pnl == Decimal("500.00000000")

    def test_open_date_set_on_open_cleared_on_close(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert closed[0].open_date == date(2026, 1, 1)
        assert closed[0].close_date == date(2026, 1, 2)

    def test_reopen_after_close_gets_new_open_date(self):
        txns = [
            _txn("PETR4", "BUY",  100, "30.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 100, "35.00", date_=date(2026, 1, 5)),
            _txn("PETR4", "BUY",  50,  "28.00", date_=date(2026, 1, 10)),
            _txn("PETR4", "SELL", 50,  "32.00", date_=date(2026, 1, 15)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 2
        assert closed[0].open_date == date(2026, 1, 1)
        assert closed[1].open_date == date(2026, 1, 10)

    def test_no_close_events_for_deepening_short(self):
        txns = [
            _txn("PETR4", "SELL", 50, "35.00", date_=date(2026, 1, 1)),
            _txn("PETR4", "SELL", 30, "33.00", date_=date(2026, 1, 2)),
        ]
        _, _, closed = compute_positions_with_steps(txns)
        assert len(closed) == 0
