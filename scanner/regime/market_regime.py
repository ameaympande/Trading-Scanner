"""
Market Regime Classification Engine.

Evaluates benchmark index (NIFTY 50 / ^NSEI) to classify the broad market regime
as BULLISH, NEUTRAL, or BEARISH.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd

from scanner.config import MarketRegimeLabel, get_settings
from scanner.indicators.calculator import IndicatorCalculator

if TYPE_CHECKING:
    from scanner.data.loader import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class MarketRegimeResult:
    timestamp: datetime.datetime | pd.Timestamp
    benchmark_symbol: str
    regime: MarketRegimeLabel
    close_price: float
    sma50: float | None
    sma200: float | None
    rsi14: float | None
    adx14: float | None
    score: float  # -1.0 (strongly bearish) to +1.0 (strongly bullish)
    reasons: list[str]

    @property
    def is_bullish(self) -> bool:
        return self.regime == MarketRegimeLabel.BULLISH

    @property
    def is_bearish(self) -> bool:
        return self.regime == MarketRegimeLabel.BEARISH

    @property
    def is_neutral(self) -> bool:
        return self.regime == MarketRegimeLabel.NEUTRAL


class MarketRegimeEngine:
    """
    Evaluates market conditions using the benchmark index.
    """

    def __init__(
        self,
        benchmark_symbol: str = "^NSEI",
        data_loader: DataLoader | None = None,
        indicator_calculator: IndicatorCalculator | None = None,
    ):
        settings = get_settings()
        self.benchmark_symbol = benchmark_symbol or settings.regime_benchmark
        self.data_loader = data_loader
        self.calculator = indicator_calculator or IndicatorCalculator()

    def evaluate_from_df(self, df: pd.DataFrame) -> MarketRegimeResult:
        """
        Evaluate regime from an index OHLCV DataFrame (which has indicators calculated).
        """
        if df.empty or len(df) < 50:
            return MarketRegimeResult(
                timestamp=pd.Timestamp.now(tz="UTC"),
                benchmark_symbol=self.benchmark_symbol,
                regime=MarketRegimeLabel.NEUTRAL,
                close_price=0.0,
                sma50=None,
                sma200=None,
                rsi14=None,
                adx14=None,
                score=0.0,
                reasons=["Insufficient historical data for benchmark"],
            )

        # Enriched indicators if not already computed
        if "sma200" not in df.columns or "rsi14" not in df.columns:
            enriched = self.calculator.calculate_all(df)
        else:
            enriched = df

        latest = enriched.iloc[-1]
        close = float(latest["close"])
        sma50 = float(latest["sma50"]) if pd.notna(latest.get("sma50")) else None
        sma200 = float(latest["sma200"]) if pd.notna(latest.get("sma200")) else None
        rsi14 = float(latest["rsi14"]) if pd.notna(latest.get("rsi14")) else None
        adx14 = float(latest["adx14"]) if pd.notna(latest.get("adx14")) else None

        points = 0
        max_points = 5
        reasons: list[str] = []

        # 1. Price vs SMA200 (Major trend)
        if sma200 is not None:
            if close > sma200:
                points += 2
                reasons.append(f"Price ({close:.1f}) > 200 SMA ({sma200:.1f})")
            else:
                points -= 2
                reasons.append(f"Price ({close:.1f}) < 200 SMA ({sma200:.1f})")

        # 2. SMA50 vs SMA200 (Golden/Death cross)
        if sma50 is not None and sma200 is not None:
            if sma50 > sma200:
                points += 1.5
                reasons.append("50 SMA > 200 SMA (Golden cross alignment)")
            else:
                points -= 1.5
                reasons.append("50 SMA < 200 SMA (Death cross alignment)")

        # 3. Price vs SMA50 (Medium term trend)
        if sma50 is not None:
            if close > sma50:
                points += 1
                reasons.append(f"Price > 50 SMA ({sma50:.1f})")
            else:
                points -= 1
                reasons.append(f"Price < 50 SMA ({sma50:.1f})")

        # 4. RSI momentum
        if rsi14 is not None:
            if rsi14 >= 50:
                points += 0.5
                reasons.append(f"RSI ({rsi14:.1f}) in bullish momentum zone (>= 50)")
            else:
                points -= 0.5
                reasons.append(f"RSI ({rsi14:.1f}) in bearish momentum zone (< 50)")

        # Normalize score between -1.0 and +1.0
        normalized_score = max(-1.0, min(1.0, points / max_points))

        if normalized_score >= 0.35:
            regime = MarketRegimeLabel.BULLISH
        elif normalized_score <= -0.35:
            regime = MarketRegimeLabel.BEARISH
        else:
            regime = MarketRegimeLabel.NEUTRAL

        return MarketRegimeResult(
            timestamp=enriched.index[-1],
            benchmark_symbol=self.benchmark_symbol,
            regime=regime,
            close_price=close,
            sma50=sma50,
            sma200=sma200,
            rsi14=rsi14,
            adx14=adx14,
            score=normalized_score,
            reasons=reasons,
        )

    def evaluate(
        self,
        as_of_date: datetime.date | None = None,
        lookback_days: int = 400,
    ) -> MarketRegimeResult:
        """
        Fetch benchmark data up to as_of_date and evaluate regime.
        """
        if self.data_loader is None:
            from scanner.data.loader import DataLoader
            self.data_loader = DataLoader()

        end = as_of_date or datetime.date.today()
        start = end - datetime.timedelta(days=lookback_days)

        try:
            df, _ = self.data_loader.fetch_daily_ohlcv(
                symbol=self.benchmark_symbol,
                start_date=start,
                end_date=end,
                exchange="NSE",
            )
            if df.empty:
                logger.warning(f"No benchmark data found for {self.benchmark_symbol}")
                return MarketRegimeResult(
                    timestamp=pd.Timestamp.now(tz="UTC"),
                    benchmark_symbol=self.benchmark_symbol,
                    regime=MarketRegimeLabel.NEUTRAL,
                    close_price=0.0,
                    sma50=None,
                    sma200=None,
                    rsi14=None,
                    adx14=None,
                    score=0.0,
                    reasons=["Benchmark data unavailable - defaulting to NEUTRAL"],
                )
            return self.evaluate_from_df(df)
        except Exception as e:
            logger.error(f"Error evaluating market regime: {e}")
            return MarketRegimeResult(
                timestamp=pd.Timestamp.now(tz="UTC"),
                benchmark_symbol=self.benchmark_symbol,
                regime=MarketRegimeLabel.NEUTRAL,
                close_price=0.0,
                sma50=None,
                sma200=None,
                rsi14=None,
                adx14=None,
                score=0.0,
                reasons=[f"Error fetching benchmark: {e}"],
            )
