"""
Technical Indicator Calculator.

Computes standard and customized technical indicators on OHLCV DataFrames.
Strictly point-in-time calculation to eliminate look-ahead bias.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import ta.momentum
import ta.trend
import ta.volatility

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Computes technical features and indicators on historical OHLCV data.
    """

    def __init__(
        self,
        sma_periods: tuple[int, ...] = (20, 50, 200),
        ema_periods: tuple[int, ...] = (20, 50, 200),
        rsi_period: int = 14,
        atr_period: int = 14,
        adx_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        volume_sma_period: int = 20,
    ):
        self.sma_periods = sma_periods
        self.ema_periods = ema_periods
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.volume_sma_period = volume_sma_period

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators and return an enriched DataFrame.
        Does not mutate the original DataFrame.
        """
        if df.empty or len(df) < 20:
            logger.warning("DataFrame has fewer than 20 rows. Indicators may be NaN.")
            return df.copy()

        res = df.copy()

        # 1. Simple Moving Averages
        for period in self.sma_periods:
            res[f"sma{period}"] = res["close"].rolling(window=period, min_periods=period).mean()

        # 2. Exponential Moving Averages
        for period in self.ema_periods:
            res[f"ema{period}"] = res["close"].ewm(span=period, adjust=False).mean()

        # 3. RSI (Relative Strength Index)
        try:
            rsi_indicator = ta.momentum.RSIIndicator(
                close=res["close"], window=self.rsi_period, fillna=False
            )
            res[f"rsi{self.rsi_period}"] = rsi_indicator.rsi()
        except Exception as e:
            logger.error(f"Error computing RSI: {e}")
            res[f"rsi{self.rsi_period}"] = np.nan

        # 4. ATR (Average True Range)
        try:
            atr_indicator = ta.volatility.AverageTrueRange(
                high=res["high"],
                low=res["low"],
                close=res["close"],
                window=self.atr_period,
                fillna=False,
            )
            res[f"atr{self.atr_period}"] = atr_indicator.average_true_range()
        except Exception as e:
            logger.error(f"Error computing ATR: {e}")
            res[f"atr{self.atr_period}"] = np.nan

        # 5. ADX (Average Directional Index)
        try:
            adx_indicator = ta.trend.ADXIndicator(
                high=res["high"],
                low=res["low"],
                close=res["close"],
                window=self.adx_period,
                fillna=False,
            )
            res[f"adx{self.adx_period}"] = adx_indicator.adx()
            res["adx_pos"] = adx_indicator.adx_pos()
            res["adx_neg"] = adx_indicator.adx_neg()
        except Exception as e:
            logger.error(f"Error computing ADX: {e}")
            res[f"adx{self.adx_period}"] = np.nan
            res["adx_pos"] = np.nan
            res["adx_neg"] = np.nan

        # 6. MACD (Moving Average Convergence Divergence)
        try:
            macd_indicator = ta.trend.MACD(
                close=res["close"],
                window_slow=self.macd_slow,
                window_fast=self.macd_fast,
                window_sign=self.macd_signal,
                fillna=False,
            )
            res["macd"] = macd_indicator.macd()
            res["macd_signal"] = macd_indicator.macd_signal()
            res["macd_histogram"] = macd_indicator.macd_diff()
        except Exception as e:
            logger.error(f"Error computing MACD: {e}")
            res["macd"] = np.nan
            res["macd_signal"] = np.nan
            res["macd_histogram"] = np.nan

        # 7. Volume SMA & Relative Volume
        res[f"volume_sma{self.volume_sma_period}"] = (
            res["volume"].rolling(window=self.volume_sma_period, min_periods=self.volume_sma_period).mean()
        )
        # Relative volume = current volume / 20-day average volume
        # Handle zero division safely
        vol_sma = res[f"volume_sma{self.volume_sma_period}"]
        res["relative_volume"] = np.where(vol_sma > 0, res["volume"] / vol_sma, 1.0)

        # 8. Rate of Change (ROC - 20 bars)
        res["roc"] = res["close"].pct_change(periods=20) * 100.0

        # 9. Historical Volatility (Annualized standard deviation of daily log returns over 20 days)
        log_ret = np.log(res["close"] / res["close"].shift(1))
        res["volatility"] = log_ret.rolling(window=20).std() * np.sqrt(252) * 100.0

        # 10. Rolling Highs and Lows (20 and 50)
        # Note: shift(1) or current bar depends on context; high20 of previous 20 bars for breakout
        res["high20"] = res["high"].rolling(window=20).max()
        res["high50"] = res["high"].rolling(window=50).max()
        res["low20"] = res["low"].rolling(window=20).min()
        res["low50"] = res["low"].rolling(window=50).min()

        # Lookback highs of prior N bars (excluding today) for breakout detection:
        res["prior_high5"] = res["high"].shift(1).rolling(window=5).max()
        res["prior_high10"] = res["high"].shift(1).rolling(window=10).max()
        res["prior_low5"] = res["low"].shift(1).rolling(window=5).min()
        res["prior_low10"] = res["low"].shift(1).rolling(window=10).min()

        # 11. Slope of SMA200 (rising or falling over last 20 days)
        if "sma200" in res.columns:
            res["sma200_slope"] = (res["sma200"] - res["sma200"].shift(20)) / res["sma200"].shift(20)

        # 12. Recent Swing Low (over last 10 bars excluding current candle)
        # Defined as the lowest Low in the last 10 candles before the current one
        res["recent_swing_low"] = res["low"].shift(1).rolling(window=10, min_periods=3).min()
        res["recent_swing_high"] = res["high"].shift(1).rolling(window=10, min_periods=3).max()

        return res
