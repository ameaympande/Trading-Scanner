"""Tests for TREND_PULLBACK_V1 strategy."""

import pandas as pd

from scanner.config import MarketRegimeLabel
from scanner.indicators.calculator import IndicatorCalculator
from scanner.strategies.trend_pullback import TrendPullbackV1


def test_strategy_detects_uptrend_pullback(synthetic_uptrend_ohlcv: pd.DataFrame):
    calc = IndicatorCalculator()
    enriched = calc.calculate_all(synthetic_uptrend_ohlcv)

    strategy = TrendPullbackV1()
    setup = strategy.evaluate(
        symbol="SYNTH_BULL",
        company_name="Synthetic Bullish Corp",
        df=enriched,
        market_regime=MarketRegimeLabel.BULLISH,
        sector="Information Technology",
    )

    assert setup is not None, "Setup should be detected on synthetic uptrend pullback"
    assert setup.score >= 70, f"Expected score >= 70, got {setup.score}"
    assert setup.stop_loss < setup.entry_low, "Stop loss must be strictly below entry"
    assert setup.target1 > setup.entry_high, "Target must be strictly above entry"
    assert setup.risk_reward >= 2.0, f"Expected R:R >= 2.0, got {setup.risk_reward}"
    assert len(setup.reasons) > 0, "Setup must provide human-readable explainability reasons"
    assert "Daily close below" in setup.invalidation


def test_strategy_rejects_downtrend(synthetic_downtrend_ohlcv: pd.DataFrame):
    calc = IndicatorCalculator()
    enriched = calc.calculate_all(synthetic_downtrend_ohlcv)

    strategy = TrendPullbackV1()
    setup = strategy.evaluate(
        symbol="SYNTH_BEAR",
        company_name="Synthetic Bearish Corp",
        df=enriched,
        market_regime=MarketRegimeLabel.BEARISH,
        sector="Energy",
    )

    assert setup is None, "Setup must NOT trigger for a stock in clear downtrend"


def test_score_never_claims_profit_probability(synthetic_uptrend_ohlcv: pd.DataFrame):
    calc = IndicatorCalculator()
    enriched = calc.calculate_all(synthetic_uptrend_ohlcv)
    strategy = TrendPullbackV1()
    setup = strategy.evaluate(
        symbol="TEST",
        company_name="Test Corp",
        df=enriched,
        market_regime=MarketRegimeLabel.BULLISH,
    )
    if setup:
        # Score must be bounded in 0-100
        assert 0 <= setup.score <= 100
        # Check reasons do not contain false profit guarantees
        for r in setup.reasons:
            assert "guaranteed" not in r.lower()
            assert "sure shot" not in r.lower()
