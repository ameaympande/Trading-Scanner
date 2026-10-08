"""
TREND_PULLBACK_V1 Strategy.

Identifies liquid NSE stocks in a healthy medium-term uptrend, looking for
controlled pullbacks to key moving averages followed by reversal/breakout confirmation.
"""

from __future__ import annotations

import logging

import pandas as pd

from scanner.config import MarketRegimeLabel, SignalDirection, get_settings
from scanner.strategies.base import CandidateSetup, Strategy

logger = logging.getLogger(__name__)


class TrendPullbackV1(Strategy):
    """
    Implementation of TREND_PULLBACK_V1.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.weights = self.settings.scoring_weights

    @property
    def name(self) -> str:
        return "TREND_PULLBACK_V1"

    def evaluate(
        self,
        symbol: str,
        company_name: str,
        df: pd.DataFrame,
        market_regime: MarketRegimeLabel,
        sector: str = "",
    ) -> CandidateSetup | None:
        """
        Evaluate stock at the latest candle for TREND_PULLBACK_V1 setup.
        """
        if df.empty or len(df) < self.settings.min_history_days:
            logger.debug(
                f"{symbol}: Insufficient history ({len(df)} < {self.settings.min_history_days})"
            )
            return None

        # Work on latest row
        curr = df.iloc[-1]

        close = float(curr["close"])
        open_price = float(curr["open"])
        high = float(curr["high"])
        low = float(curr["low"])
        volume = float(curr["volume"])

        # Technical values
        sma50 = float(curr["sma50"]) if pd.notna(curr.get("sma50")) else None
        sma200 = float(curr["sma200"]) if pd.notna(curr.get("sma200")) else None
        ema20 = float(curr["ema20"]) if pd.notna(curr.get("ema20")) else None
        ema50 = float(curr["ema50"]) if pd.notna(curr.get("ema50")) else None
        rsi14 = float(curr["rsi14"]) if pd.notna(curr.get("rsi14")) else None
        atr14 = float(curr["atr14"]) if pd.notna(curr.get("atr14")) else None
        vol_sma20 = float(curr["volume_sma20"]) if pd.notna(curr.get("volume_sma20")) else None
        rel_vol = float(curr["relative_volume"]) if pd.notna(curr.get("relative_volume")) else 1.0
        prior_high5 = float(curr["prior_high5"]) if pd.notna(curr.get("prior_high5")) else high
        swing_low = float(curr["recent_swing_low"]) if pd.notna(curr.get("recent_swing_low")) else low
        sma200_slope = float(curr["sma200_slope"]) if pd.notna(curr.get("sma200_slope")) else 0.0

        # Basic validations
        if sma50 is None or sma200 is None or ema20 is None or ema50 is None or atr14 is None or rsi14 is None:
            return None

        if atr14 <= 0 or close <= 0:
            return None

        avg_traded_val = (vol_sma20 or volume) * close

        # Hard filters (Reject immediately if failed)
        # 1. Liquidity filter
        if close < self.settings.min_price:
            return None
        if (vol_sma20 or volume) < self.settings.min_avg_volume:
            return None
        if avg_traded_val < self.settings.min_avg_traded_value:
            return None

        # 2. Hard Trend filter: close > SMA50 and SMA50 > SMA200
        if close < sma50 or sma50 < sma200:
            return None

        # 3. Hard Momentum filter: RSI between 45 and extreme limit (75)
        if rsi14 < self.settings.rsi_lower or rsi14 > self.settings.rsi_extreme_upper:
            return None

        # SCORING ENGINE (0 to 100)
        score_breakdown: dict[str, int] = {}
        reasons: list[str] = []

        # --- A. Trend Component (Max: weights.trend, e.g. 25) ---
        trend_score = 0
        trend_max = self.weights.trend
        trend_score += int(trend_max * 0.40)
        reasons.append(f"Price (₹{close:.2f}) > 50 SMA (₹{sma50:.2f})")

        trend_score += int(trend_max * 0.30)
        reasons.append(f"50 SMA > 200 SMA (₹{sma200:.2f}) - Strong medium-term uptrend")

        if sma200_slope > 0.005:
            trend_score += int(trend_max * 0.30)
            reasons.append(f"200 SMA slope is rising (+{sma200_slope*100:.2f}% over 20d)")
        elif sma200_slope >= 0:
            trend_score += int(trend_max * 0.15)
            reasons.append("200 SMA is flat-to-positive")
        trend_score = min(trend_max, trend_score)
        score_breakdown["trend"] = trend_score

        # --- B. Momentum Component (Max: weights.momentum, e.g. 15) ---
        momentum_score = 0
        momentum_max = self.weights.momentum
        if 50.0 <= rsi14 <= 65.0:
            momentum_score = momentum_max
            reasons.append(f"RSI 14 is in the optimal momentum zone ({rsi14:.1f})")
        elif 45.0 <= rsi14 < 50.0:
            momentum_score = int(momentum_max * 0.70)
            reasons.append(f"RSI 14 ({rsi14:.1f}) is recovering from pullback")
        elif 65.0 < rsi14 <= 70.0:
            momentum_score = int(momentum_max * 0.80)
            reasons.append(f"RSI 14 ({rsi14:.1f}) shows solid strength")
        else:
            momentum_score = int(momentum_max * 0.40)
            reasons.append(f"RSI 14 ({rsi14:.1f}) slightly elevated, caution on extension")
        score_breakdown["momentum"] = momentum_score

        # --- C. Pullback Quality (Max: weights.pullback_quality, e.g. 20) ---
        pullback_score = 0
        pullback_max = self.weights.pullback_quality
        dist_to_ema20 = abs(close - ema20) / atr14
        recent_low_5 = float(df["low"].iloc[-5:].min())

        pulled_to_ema20 = (recent_low_5 <= ema20 * 1.015) and (close >= ema20 * 0.98)
        pulled_to_ema50 = (recent_low_5 <= ema50 * 1.015) and (close >= ema50 * 0.98)

        if pulled_to_ema20:
            pullback_score += int(pullback_max * 0.60)
            reasons.append(f"Price tested/respected 20 EMA (₹{ema20:.2f})")
        elif pulled_to_ema50:
            pullback_score += int(pullback_max * 0.50)
            reasons.append(f"Price tested/respected 50 EMA (₹{ema50:.2f})")
        elif dist_to_ema20 <= 1.0:
            pullback_score += int(pullback_max * 0.40)
            reasons.append("Price is within 1 ATR of 20 EMA")

        norm_atr = (atr14 / close) * 100.0
        if norm_atr < 3.5:
            pullback_score += int(pullback_max * 0.40)
            reasons.append(f"Controlled volatility (ATR {norm_atr:.1f}% of price)")
        else:
            pullback_score += int(pullback_max * 0.20)

        pullback_score = min(pullback_max, pullback_score)
        score_breakdown["pullback_quality"] = pullback_score

        # --- D. Volume Confirmation (Max: weights.volume_confirmation, e.g. 15) ---
        volume_score = 0
        volume_max = self.weights.volume_confirmation
        if rel_vol >= 1.5:
            volume_score = volume_max
            reasons.append(f"High volume expansion ({rel_vol:.2f}x of 20d avg volume)")
        elif rel_vol >= 1.2:
            volume_score = int(volume_max * 0.80)
            reasons.append(f"Volume above average ({rel_vol:.2f}x of 20d avg volume)")
        elif rel_vol >= 1.0:
            volume_score = int(volume_max * 0.50)
            reasons.append(f"Normal volume ({rel_vol:.2f}x of 20d avg volume)")
        else:
            volume_score = int(volume_max * 0.20)
        score_breakdown["volume_confirmation"] = volume_score

        # --- E. Breakout / Reversal Confirmation (Max: weights.breakout_confirmation, e.g. 10) ---
        conf_score = 0
        conf_max = self.weights.breakout_confirmation
        candle_range = max(0.01, high - low)
        close_position = (close - low) / candle_range

        is_breakout = close > prior_high5
        is_bullish_candle = (close > open_price) and (close_position >= 0.65)

        if is_breakout and is_bullish_candle:
            conf_score = conf_max
            reasons.append(f"Breakout above 5-day prior high (₹{prior_high5:.2f}) with bullish candle")
        elif is_breakout:
            conf_score = int(conf_max * 0.80)
            reasons.append(f"Breakout above 5-day prior high (₹{prior_high5:.2f})")
        elif is_bullish_candle:
            conf_score = int(conf_max * 0.70)
            reasons.append(f"Bullish reversal candle (closed in top {int(close_position*100)}% of range)")
        else:
            conf_score = int(conf_max * 0.30)
        score_breakdown["breakout_confirmation"] = conf_score

        # --- F. Market Regime (Max: weights.market_regime, e.g. 10) ---
        regime_score = 0
        regime_max = self.weights.market_regime
        if market_regime == MarketRegimeLabel.BULLISH:
            regime_score = regime_max
            reasons.append("NIFTY 50 regime is BULLISH (favorable market tailwind)")
        elif market_regime == MarketRegimeLabel.NEUTRAL:
            regime_score = int(regime_max * 0.50)
            reasons.append("NIFTY 50 regime is NEUTRAL (reduced market influence)")
        else:
            regime_score = int(regime_max * 0.10)
            reasons.append("NIFTY 50 regime is BEARISH (adverse broad market, score reduced)")
        score_breakdown["market_regime"] = regime_score

        # --- G. Liquidity (Max: weights.liquidity, e.g. 5) ---
        liq_score = 0
        liq_max = self.weights.liquidity
        if avg_traded_val >= 50_000_000:
            liq_score = liq_max
        elif avg_traded_val >= 20_000_000:
            liq_score = int(liq_max * 0.80)
        else:
            liq_score = int(liq_max * 0.50)
        score_breakdown["liquidity"] = liq_score

        total_score = sum(score_breakdown.values())

        if total_score < self.settings.min_score:
            return None

        # --- ENTRY, STOP, TARGET CALCULATION (Structure + ATR) ---
        entry_low = round(close, 2)
        entry_high = round(max(close, high), 2)
        entry_mid = round((entry_low + entry_high) / 2.0, 2)

        atr_stop_dist = atr14 * self.settings.atr_stop_multiplier
        atr_stop = entry_mid - atr_stop_dist
        structural_stop = swing_low - (0.2 * atr14)
        stop_candidate = min(structural_stop, atr_stop)

        min_allowed_stop = entry_mid - (3.0 * atr14)
        max_allowed_stop = entry_mid - (0.8 * atr14)
        stop_loss = round(max(min_allowed_stop, min(stop_candidate, max_allowed_stop)), 2)

        risk_amount = round(entry_mid - stop_loss, 2)
        if risk_amount <= 0:
            return None

        min_reward = risk_amount * self.settings.min_rr
        target1 = round(entry_mid + min_reward, 2)
        target2 = round(entry_mid + (risk_amount * 3.5), 2)

        actual_rr = round((target1 - entry_mid) / risk_amount, 2)

        if actual_rr < self.settings.min_rr:
            return None

        invalidation = (
            f"Daily close below structural support at ₹{stop_loss:.2f} "
            f"or below 50 SMA (₹{sma50:.2f}) invalidates the setup."
        )

        return CandidateSetup(
            symbol=symbol,
            company_name=company_name,
            strategy_name=self.name,
            direction=SignalDirection.LONG,
            timestamp=df.index[-1],
            current_price=close,
            entry_low=entry_low,
            entry_high=entry_high,
            stop_loss=stop_loss,
            target1=target1,
            target2=target2,
            risk_reward=actual_rr,
            score=total_score,
            atr=round(atr14, 2),
            rsi=round(rsi14, 1),
            relative_volume=round(rel_vol, 2),
            market_regime=market_regime,
            expected_holding_period="5-15 trading days",
            reasons=reasons,
            invalidation=invalidation,
            score_breakdown=score_breakdown,
            sector=sector,
        )
