"""
Advanced Multi-State Market Regime & Sector Rotation Engine.

Classifies the market into granular regimes:
- TRENDING_BULL, TRENDING_BEAR, SIDEWAYS, HIGH_VOLATILITY, LOW_VOLATILITY, RECOVERY, BREAKOUT_REGIME
Calculates Market Breadth (% above SMA 20/50/200, Advance/Decline) and Sector Momentum.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np
import pandas as pd

from scanner.indicators.calculator import IndicatorCalculator


class DetailedRegime(StrEnum):
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    RECOVERY = "RECOVERY"
    BREAKOUT_REGIME = "BREAKOUT_REGIME"


@dataclass
class MarketBreadthSnapshot:
    pct_above_sma20: float
    pct_above_sma50: float
    pct_above_sma200: float
    advance_decline_ratio: float
    total_stocks_evaluated: int


@dataclass
class SectorPerformance:
    sector_name: str
    return_5d_pct: float
    return_20d_pct: float
    rs_vs_nifty_20d: float
    momentum_rank: int  # 1 is strongest
    is_outperforming: bool


@dataclass
class AdvancedRegimeAnalysis:
    timestamp: datetime.datetime | pd.Timestamp
    regime: DetailedRegime
    benchmark_close: float
    nifty_20d_return: float
    adx14: float
    rsi14: float
    breadth: MarketBreadthSnapshot | None
    sector_leaders: list[SectorPerformance] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    strategy_recommendation: str = "TREND_PULLBACK_V1 active"


class AdvancedRegimeEngine:
    """
    Evaluates multi-state market conditions, breadth, and sector rotation.
    """

    def __init__(self):
        self.calc = IndicatorCalculator()

    def classify_benchmark(self, nifty_df: pd.DataFrame) -> AdvancedRegimeAnalysis:
        """
        Classifies benchmark index into granular regime state.
        """
        if nifty_df.empty or len(nifty_df) < 50:
            return AdvancedRegimeAnalysis(
                timestamp=datetime.datetime.now(datetime.UTC),
                regime=DetailedRegime.SIDEWAYS,
                benchmark_close=0.0,
                nifty_20d_return=0.0,
                adx14=20.0,
                rsi14=50.0,
                breadth=None,
                reasons=["Insufficient benchmark data."],
            )

        enriched = self.calc.calculate_all(nifty_df)
        curr = enriched.iloc[-1]
        close = float(curr["close"])
        sma50 = float(curr["sma50"]) if pd.notna(curr.get("sma50")) else close
        sma200 = float(curr["sma200"]) if pd.notna(curr.get("sma200")) else close
        rsi14 = float(curr["rsi14"]) if pd.notna(curr.get("rsi14")) else 50.0
        adx14 = float(curr["adx14"]) if pd.notna(curr.get("adx14")) else 20.0
        atr14 = float(curr["atr14"]) if pd.notna(curr.get("atr14")) else close * 0.015
        prior_high20 = float(enriched["high"].iloc[-21:-1].max()) if len(enriched) > 21 else close

        ret_20d = float((close - enriched["close"].iloc[-20]) / enriched["close"].iloc[-20] * 100.0) if len(enriched) > 20 else 0.0
        volatility_norm = (atr14 / close) * 100.0

        reasons: list[str] = []
        regime = DetailedRegime.SIDEWAYS
        strategy_rec = "Caution advised; selective position sizing."

        # Classification decision hierarchy
        if volatility_norm > 2.2:
            regime = DetailedRegime.HIGH_VOLATILITY
            reasons.append(f"Elevated normalized volatility ({volatility_norm:.2f}% ATR/Price)")
            strategy_rec = "Defensive mode: Reduce position size, require wider stops."

        elif close > prior_high20 and rsi14 > 60:
            regime = DetailedRegime.BREAKOUT_REGIME
            reasons.append(f"NIFTY broke above 20-day high (₹{prior_high20:.1f})")
            strategy_rec = "Aggressive trend/breakout mode: high momentum."

        elif close > sma50 and sma50 > sma200 and rsi14 >= 52:
            regime = DetailedRegime.TRENDING_BULL
            reasons.append(f"Classic uptrend alignment: Price > 50 SMA > 200 SMA (RSI {rsi14:.1f})")
            strategy_rec = "TREND_PULLBACK optimal environment: positive edge expected."

        elif close < sma50 and sma50 < sma200 and rsi14 <= 45:
            regime = DetailedRegime.TRENDING_BEAR
            reasons.append(f"Downtrend alignment: Price < 50 SMA < 200 SMA (RSI {rsi14:.1f})")
            strategy_rec = "Defensive/Pause: Trend pullbacks face high failure rate."

        elif close > sma50 and sma50 < sma200 and rsi14 > 50:
            regime = DetailedRegime.RECOVERY
            reasons.append("Early stage recovery: Price crossing above 50 SMA against 200 SMA")
            strategy_rec = "Selective recovery trades: require volume confirmation."

        elif volatility_norm < 0.9:
            regime = DetailedRegime.LOW_VOLATILITY
            reasons.append(f"Low volatility compression ({volatility_norm:.2f}% ATR/Price)")
            strategy_rec = "Range-bound: prepare for pending volatility expansion."

        else:
            regime = DetailedRegime.SIDEWAYS
            reasons.append("Price consolidating between major moving averages.")
            strategy_rec = "Neutral stance: trade only A+ quality setups."

        return AdvancedRegimeAnalysis(
            timestamp=enriched.index[-1],
            regime=regime,
            benchmark_close=round(close, 2),
            nifty_20d_return=round(ret_20d, 2),
            adx14=round(adx14, 1),
            rsi14=round(rsi14, 1),
            breadth=None,
            reasons=reasons,
            strategy_recommendation=strategy_rec,
        )

    def calculate_sector_rankings(
        self,
        sector_stock_map: dict[str, list[pd.DataFrame]],
        nifty_20d_return: float,
    ) -> list[SectorPerformance]:
        """
        Calculates median return of stocks within each sector to rank sector strength.
        """
        perf_list: list[SectorPerformance] = []

        for sector, dfs in sector_stock_map.items():
            if not dfs:
                continue
            ret_5d_list = []
            ret_20d_list = []
            for df in dfs:
                if len(df) >= 21:
                    c = df["close"]
                    r5 = float((c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100.0)
                    r20 = float((c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100.0)
                    ret_5d_list.append(r5)
                    ret_20d_list.append(r20)

            if ret_20d_list:
                med_5d = float(np.median(ret_5d_list))
                med_20d = float(np.median(ret_20d_list))
                rs_vs_nifty = round((1.0 + med_20d / 100.0) / (1.0 + nifty_20d_return / 100.0), 3)

                perf_list.append(
                    SectorPerformance(
                        sector_name=sector,
                        return_5d_pct=round(med_5d, 2),
                        return_20d_pct=round(med_20d, 2),
                        rs_vs_nifty_20d=rs_vs_nifty,
                        momentum_rank=0,  # filled after sorting
                        is_outperforming=med_20d > nifty_20d_return,
                    )
                )

        perf_list.sort(key=lambda s: s.return_20d_pct, reverse=True)
        for rank, item in enumerate(perf_list, start=1):
            item.momentum_rank = rank

        return perf_list

    def calculate_relative_strength(
        self,
        stock_df: pd.DataFrame,
        nifty_df: pd.DataFrame,
    ) -> float:
        """
        Computes Relative Strength ratio of stock vs NIFTY over a 20-day window.
        Value > 1.0 indicates outperformance.
        """
        if len(stock_df) < 21 or len(nifty_df) < 21:
            return 1.0

        s_ret = (stock_df["close"].iloc[-1] - stock_df["close"].iloc[-20]) / stock_df["close"].iloc[-20]
        n_ret = (nifty_df["close"].iloc[-1] - nifty_df["close"].iloc[-20]) / nifty_df["close"].iloc[-20]

        rs = (1.0 + s_ret) / (1.0 + n_ret)
        return round(float(rs), 3)
