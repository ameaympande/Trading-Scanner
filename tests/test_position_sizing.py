"""Tests for Position Sizing and Portfolio Risk engine."""

import pytest

from scanner.risk.position_sizing import PositionSizer


def test_position_sizing_exact_example():
    """
    Validates the exact example from the spec:
    Account size: ₹20,000
    Risk per trade: 0.75%
    Max risk: ₹150
    Entry: ₹500
    Stop: ₹485
    Risk/share: ₹15
    Quantity: floor(150 / 15) = 10 shares
    Position value: ₹5,000
    """
    sizer = PositionSizer()
    res = sizer.calculate_position(
        symbol="TEST",
        entry_price=500.0,
        stop_loss=485.0,
        account_size=20_000.0,
        risk_per_trade_pct=0.0075,
        max_single_pos_pct=0.25,
    )

    assert res.account_size == 20_000.0
    assert res.max_risk_amount == 150.0
    assert res.risk_per_share == 15.0
    assert res.quantity == 10
    assert res.position_value == 5_000.0
    assert res.position_pct_of_capital == 25.0


def test_position_sizing_respects_max_position_cap():
    """
    If risk/share is tiny, quantity might attempt to use 80% of account.
    The max single position cap (25%) must strictly constrain it.
    """
    sizer = PositionSizer()
    # Tiny stop loss of 0.5 on a 100 stock
    # Max risk is ₹1,000 on ₹100,000 account
    # 1000 / 0.5 = 2000 shares = ₹200,000 (200% of capital)
    # But max position cap of 25% limits capital to ₹25,000 -> 250 shares
    res = sizer.calculate_position(
        symbol="TIGHT_STOP",
        entry_price=100.0,
        stop_loss=99.5,
        account_size=100_000.0,
        risk_per_trade_pct=0.01,
        max_single_pos_pct=0.25,
    )

    assert res.is_constrained_by_max_position is True
    assert res.quantity == 250
    assert res.position_value == 25_000.0
    assert res.position_pct_of_capital == 25.0


def test_position_sizing_invalid_entry_stop():
    sizer = PositionSizer()
    with pytest.raises(ValueError):
        # Stop loss cannot be above entry for long setup
        sizer.calculate_position(
            symbol="INVALID",
            entry_price=100.0,
            stop_loss=110.0,
        )
