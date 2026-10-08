"""
Pytest fixtures with synthetic and reproducible data.
Designed to test indicators, strategy logic, and look-ahead bias without network reliance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_uptrend_ohlcv() -> pd.DataFrame:
    """
    Generates 300 days of synthetic daily candles representing a healthy uptrend
    with a gentle pullback to EMA20/EMA50 followed by a breakout.
    """
    np.random.seed(42)
    n = 300
    dates = pd.date_range(end="2024-05-10", periods=n, freq="B", tz="UTC")

    # Base upward drift
    trend = np.linspace(100, 250, n)
    noise = np.random.normal(0, 1.5, n)
    close = trend + noise

    # Create a realistic pullback in the last 10 days
    # Days -10 to -3 pull back slightly
    close[-10:-2] = close[-10:-2] - np.linspace(1, 8, 8)
    # Day -1: bullish reversal / breakout candle
    close[-1] = close[-2] + 4.5

    open_price = close - np.random.uniform(-1.0, 1.0, n)
    # For the last bar, make it a solid bullish candle
    open_price[-1] = close[-1] - 3.0

    high = np.maximum(open_price, close) + np.random.uniform(0.5, 2.5, n)
    low = np.minimum(open_price, close) - np.random.uniform(0.5, 2.5, n)

    # Volume: standard volume, with spike on last candle
    volume = np.random.randint(150_000, 500_000, n).astype(float)
    volume[-1] = 900_000.0  # ~2x volume breakout

    df = pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "adjusted_close": close,
        },
        index=dates,
    )
    df.index.name = "timestamp"
    return df


@pytest.fixture
def synthetic_downtrend_ohlcv() -> pd.DataFrame:
    """
    Generates 300 days of synthetic downtrend candles (Price < 50 SMA < 200 SMA).
    """
    np.random.seed(99)
    n = 300
    dates = pd.date_range(end="2024-05-10", periods=n, freq="B", tz="UTC")

    trend = np.linspace(300, 150, n)
    noise = np.random.normal(0, 2.0, n)
    close = trend + noise

    open_price = close + np.random.uniform(-1.0, 1.0, n)
    high = np.maximum(open_price, close) + np.random.uniform(0.5, 2.0, n)
    low = np.minimum(open_price, close) - np.random.uniform(0.5, 2.0, n)
    volume = np.random.randint(50_000, 200_000, n).astype(float)

    df = pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "adjusted_close": close,
        },
        index=dates,
    )
    df.index.name = "timestamp"
    return df
