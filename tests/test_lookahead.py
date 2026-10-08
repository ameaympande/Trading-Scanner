"""
Tests specifically designed to detect and catch look-ahead bias.
Ensures that indicators and setup evaluation at bar T strictly depend
only on information available up to bar T, and never on bar T+1 onwards.
"""

import numpy as np
import pandas as pd

from scanner.config import MarketRegimeLabel
from scanner.indicators.calculator import IndicatorCalculator
from scanner.strategies.trend_pullback import TrendPullbackV1


def test_indicator_point_in_time_integrity(synthetic_uptrend_ohlcv: pd.DataFrame):
    """
    Indicators calculated at index T must be identical whether calculated on
    the truncated series [0...T] or on the full series [0...T+N].
    """
    calc = IndicatorCalculator()
    full_enriched = calc.calculate_all(synthetic_uptrend_ohlcv)

    t_idx = 250  # Check at bar 250
    truncated_df = synthetic_uptrend_ohlcv.iloc[: t_idx + 1].copy()
    truncated_enriched = calc.calculate_all(truncated_df)

    cols_to_check = [
        "sma20", "sma50", "sma200",
        "rsi14", "atr14",
        "volume_sma20", "relative_volume",
        "recent_swing_low",
    ]

    for col in cols_to_check:
        val_full = full_enriched[col].iloc[t_idx]
        val_trunc = truncated_enriched[col].iloc[-1]
        assert np.isclose(val_full, val_trunc, rtol=1e-5, atol=1e-5), (
            f"Look-ahead detected in indicator {col}: full={val_full}, trunc={val_trunc}"
        )


def test_future_data_does_not_alter_past_signal(synthetic_uptrend_ohlcv: pd.DataFrame):
    """
    Altering future candles (T+1 to T+10) by 500% must have zero effect on
    the setup evaluated at candle T.
    """
    calc = IndicatorCalculator()
    strategy = TrendPullbackV1()

    t_idx = 280
    base_sub_df = synthetic_uptrend_ohlcv.iloc[: t_idx + 1].copy()
    enriched_base = calc.calculate_all(base_sub_df)
    setup_base = strategy.evaluate(
        symbol="TEST",
        company_name="Test Corp",
        df=enriched_base,
        market_regime=MarketRegimeLabel.BULLISH,
    )

    # Now take a dataset that includes future data up to 290, but corrupt future days
    corrupted_df = synthetic_uptrend_ohlcv.iloc[:295].copy()
    # Inject wild 500% spike in future days
    corrupted_df.iloc[t_idx + 1 :, corrupted_df.columns.get_loc("close")] *= 5.0
    corrupted_df.iloc[t_idx + 1 :, corrupted_df.columns.get_loc("volume")] *= 10.0

    # Evaluate at point T by slicing up to T
    corrupted_slice = corrupted_df.iloc[: t_idx + 1]
    enriched_corrupted = calc.calculate_all(corrupted_slice)
    setup_corrupted = strategy.evaluate(
        symbol="TEST",
        company_name="Test Corp",
        df=enriched_corrupted,
        market_regime=MarketRegimeLabel.BULLISH,
    )

    if setup_base is None:
        assert setup_corrupted is None
    else:
        assert setup_corrupted is not None
        assert setup_base.score == setup_corrupted.score
        assert setup_base.stop_loss == setup_corrupted.stop_loss
        assert setup_base.target1 == setup_corrupted.target1
        assert setup_base.risk_reward == setup_corrupted.risk_reward
