"""Tests for Market Regime Engine."""

import pandas as pd

from scanner.config import MarketRegimeLabel
from scanner.regime.market_regime import MarketRegimeEngine


def test_market_regime_bullish(synthetic_uptrend_ohlcv: pd.DataFrame):
    engine = MarketRegimeEngine(benchmark_symbol="^NSEI")
    result = engine.evaluate_from_df(synthetic_uptrend_ohlcv)

    assert result.is_bullish
    assert result.regime == MarketRegimeLabel.BULLISH
    assert result.score > 0.35
    assert len(result.reasons) > 0


def test_market_regime_bearish(synthetic_downtrend_ohlcv: pd.DataFrame):
    engine = MarketRegimeEngine(benchmark_symbol="^NSEI")
    result = engine.evaluate_from_df(synthetic_downtrend_ohlcv)

    assert result.is_bearish
    assert result.regime == MarketRegimeLabel.BEARISH
    assert result.score < -0.35
    assert len(result.reasons) > 0
