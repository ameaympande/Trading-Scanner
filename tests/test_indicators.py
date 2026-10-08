"""Tests for technical indicator calculations."""

import numpy as np
import pandas as pd

from scanner.indicators.calculator import IndicatorCalculator


def test_indicator_columns_present(synthetic_uptrend_ohlcv: pd.DataFrame):
    calc = IndicatorCalculator()
    enriched = calc.calculate_all(synthetic_uptrend_ohlcv)

    expected_cols = [
        "sma20", "sma50", "sma200",
        "ema20", "ema50", "ema200",
        "rsi14", "atr14", "adx14",
        "macd", "macd_signal", "macd_histogram",
        "volume_sma20", "relative_volume",
        "roc", "volatility",
        "high20", "low20",
        "recent_swing_low",
    ]
    for col in expected_cols:
        assert col in enriched.columns, f"Expected column {col} missing from enriched DataFrame"


def test_sma_calculation_accuracy():
    dates = pd.date_range("2024-01-01", periods=30, freq="D", tz="UTC")
    # Constant prices
    df = pd.DataFrame(
        {
            "open": [100.0] * 30,
            "high": [105.0] * 30,
            "low": [95.0] * 30,
            "close": [100.0] * 30,
            "volume": [1000] * 30,
        },
        index=dates,
    )
    calc = IndicatorCalculator(sma_periods=(20,))
    enriched = calc.calculate_all(df)
    assert np.isnan(enriched["sma20"].iloc[18])
    assert enriched["sma20"].iloc[19] == 100.0
    assert enriched["sma20"].iloc[-1] == 100.0


def test_rsi_bounds(synthetic_uptrend_ohlcv: pd.DataFrame):
    calc = IndicatorCalculator()
    enriched = calc.calculate_all(synthetic_uptrend_ohlcv)
    valid_rsi = enriched["rsi14"].dropna()
    assert (valid_rsi >= 0).all()
    assert (valid_rsi <= 100).all()


def test_relative_volume(synthetic_uptrend_ohlcv: pd.DataFrame):
    calc = IndicatorCalculator()
    enriched = calc.calculate_all(synthetic_uptrend_ohlcv)
    # The last bar volume was set to 900_000, higher than 20d average
    assert enriched["relative_volume"].iloc[-1] > 1.5
