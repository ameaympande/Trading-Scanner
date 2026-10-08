"""Tests for Backtesting Engine, Indian Equity Costs, and Walk-Forward Validation."""

import pandas as pd

from scanner.backtest.costs import IndianEquityCostCalculator
from scanner.backtest.engine import BacktestEngine
from scanner.backtest.metrics import calculate_metrics
from scanner.backtest.walk_forward import WalkForwardEngine


def test_indian_equity_costs_calculation():
    """
    Test realistic fee calculation for a delivery round-trip trade:
    Buy 100 shares at ₹500 = ₹50,000 turnover
    Sell 100 shares at ₹550 = ₹55,000 turnover
    Total turnover = ₹105,000
    STT = 0.1% of 50,000 + 0.1% of 55,000 = ₹50 + ₹55 = ₹105
    DP Charge = ~₹15.93 flat
    Stamp Duty = 0.015% of 50,000 = ₹7.50
    Exchange charges + SEBI + GST + Slippage
    """
    calc = IndianEquityCostCalculator()
    friction = calc.calculate_costs(entry_price=500.0, exit_price=550.0, quantity=100)

    assert friction.buy_turnover == 50_000.0
    assert friction.sell_turnover == 55_000.0
    assert friction.stt == 105.0
    assert friction.dp_charges == 15.93
    assert friction.stamp_duty == 7.5
    assert friction.total_charges > 200.0  # Includes slippage, STT, DP, GST
    assert friction.total_cost_pct > 0.15


def test_backtest_engine_executes_on_synthetic_data(synthetic_uptrend_ohlcv: pd.DataFrame):
    """Verifies that the backtest engine executes cleanly without exceptions."""
    engine = BacktestEngine()
    result = engine.run_single_stock(
        symbol="TEST_STOCK",
        df=synthetic_uptrend_ohlcv,
        initial_capital=100_000.0,
    )

    assert result.strategy_name == "TREND_PULLBACK_V1"
    assert result.initial_capital == 100_000.0
    assert result.metrics is not None
    # Metrics fields must exist
    assert hasattr(result.metrics, "total_return_pct")
    assert hasattr(result.metrics, "max_drawdown_pct")
    assert hasattr(result.metrics, "win_rate_pct")


def test_metrics_empty_trades():
    metrics = calculate_metrics([])
    assert metrics.total_trades == 0
    assert metrics.win_rate_pct == 0.0
    assert metrics.total_return_pct == 0.0


def test_walk_forward_engine(synthetic_uptrend_ohlcv: pd.DataFrame):
    wf_engine = WalkForwardEngine()
    wf_res = wf_engine.run_split(
        symbol="WF_TEST",
        df=synthetic_uptrend_ohlcv,
    )

    assert wf_res.in_sample.name == "IN_SAMPLE"
    assert wf_res.out_of_sample.name == "OUT_OF_SAMPLE"
    assert "survivorship bias" in wf_res.warning.lower()
