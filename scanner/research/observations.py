"""
Trade Observation & Outcome Labeling Engine.

Captures structured feature snapshots for every trading setup candidate and calculates:
- Maximum Favorable Excursion (MFE in R)
- Maximum Adverse Excursion (MAE in R)
- Granular outcome classifications (WIN_FULL_TARGET, FAILED_BREAKOUT, etc.)
- Conservative resolution for ambiguous same-candle stop/target touches
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

import pandas as pd


class OutcomeLabel(StrEnum):
    WIN_FULL_TARGET = "WIN_FULL_TARGET"
    WIN_PARTIAL = "WIN_PARTIAL"
    STOPPED = "STOPPED"
    TIME_EXIT = "TIME_EXIT"
    FAILED_BREAKOUT = "FAILED_BREAKOUT"
    FAILED_PULLBACK = "FAILED_PULLBACK"
    EARLY_REVERSAL = "EARLY_REVERSAL"
    LATE_ENTRY = "LATE_ENTRY"
    LOW_VOLUME_FAILURE = "LOW_VOLUME_FAILURE"
    MARKET_REGIME_FAILURE = "MARKET_REGIME_FAILURE"
    AMBIGUOUS = "AMBIGUOUS"
    PENDING = "PENDING"


@dataclass
class OutcomeResult:
    label: OutcomeLabel
    exit_date: datetime.date | pd.Timestamp
    exit_price: float
    holding_period: int
    realized_r: float
    realized_pct: float
    mfe_r: float  # Maximum Favorable Excursion (in R)
    mae_r: float  # Maximum Adverse Excursion (in R)
    is_win: bool
    ambiguous_candle: bool = False
    details: str = ""


@dataclass
class TradeObservation:
    # 1. Identification
    symbol: str
    timestamp: datetime.datetime | pd.Timestamp
    market_regime: str
    sector: str
    industry: str
    price: float

    # 2. Technical Features
    atr: float
    rsi: float
    adx: float
    relative_volume: float
    dist_ema20_pct: float
    dist_ema50_pct: float
    dist_sma200_pct: float
    trend_strength: float
    recent_volatility: float

    # 3. Multi-Period Asset Returns
    ret_1d: float
    ret_3d: float
    ret_5d: float
    ret_10d: float
    ret_20d: float

    # 4. Benchmark & Relative Strength
    nifty_ret_1d: float
    nifty_ret_5d: float
    nifty_ret_20d: float
    relative_strength_vs_nifty: float
    sector_momentum_rank: float = 0.5
    stock_vs_sector_rs: float = 0.0

    # 5. Geometry & Setup Structure
    breakout_strength: float = 0.0
    pullback_depth_atr: float = 0.0
    volume_expansion: float = 1.0
    gap_pct: float = 0.0
    dist_to_resistance_pct: float = 5.0
    dist_to_support_pct: float = 3.0
    risk_reward: float = 2.0
    strategy_score: int = 75

    # 6. Trade Levels
    entry: float = 0.0
    stop: float = 0.0
    target: float = 0.0
    risk_per_share: float = 0.0

    # 7. Post-Trade Outcome & Excursions (filled after forward simulation)
    mfe_r: float | None = None
    mae_r: float | None = None
    realized_r: float | None = None
    realized_pct: float | None = None
    holding_period: int | None = None
    exit_reason: str | None = None
    outcome_label: OutcomeLabel = OutcomeLabel.PENDING

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if hasattr(self.timestamp, "isoformat"):
            d["timestamp"] = self.timestamp.isoformat()
        else:
            d["timestamp"] = str(self.timestamp)
        d["outcome_label"] = self.outcome_label.value
        return d


def calculate_mfe_mae(
    entry_price: float,
    stop_loss: float,
    candles: pd.DataFrame,
) -> tuple[float, float]:
    """
    Computes Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE)
    expressed in units of initial risk (R).
    """
    risk = max(0.01, entry_price - stop_loss)
    if candles.empty:
        return 0.0, 0.0

    max_high = float(candles["high"].max())
    min_low = float(candles["low"].min())

    mfe_r = round((max_high - entry_price) / risk, 2)
    mae_r = round((entry_price - min_low) / risk, 2)

    return max(0.0, mfe_r), max(0.0, mae_r)


def evaluate_trade_outcome(
    entry_date: pd.Timestamp | datetime.date,
    entry_price: float,
    stop_loss: float,
    target: float,
    forward_candles: pd.DataFrame,
    max_holding_bars: int = 20,
    regime_at_entry: str = "BULLISH",
    relative_volume_at_entry: float = 1.2,
) -> OutcomeResult:
    """
    Evaluates forward trade performance from forward daily candles.
    Strictly point-in-time from candle T+1 forward.
    Enforces conservative handling: if both Stop and Target are touched
    in the same candle, stop is assumed to have triggered first.
    """
    risk = max(0.01, entry_price - stop_loss)

    if forward_candles.empty:
        return OutcomeResult(
            label=OutcomeLabel.PENDING,
            exit_date=entry_date,
            exit_price=entry_price,
            holding_period=0,
            realized_r=0.0,
            realized_pct=0.0,
            mfe_r=0.0,
            mae_r=0.0,
            is_win=False,
            details="No forward data available.",
        )

    bars_checked = 0
    running_max_high = entry_price
    running_min_low = entry_price

    for i in range(min(len(forward_candles), max_holding_bars)):
        bar = forward_candles.iloc[i]
        bar_date = forward_candles.index[i]
        bars_checked += 1

        open_p = float(bar["open"])
        high_p = float(bar["high"])
        low_p = float(bar["low"])

        running_max_high = max(running_max_high, high_p)
        running_min_low = min(running_min_low, low_p)

        hit_stop = low_p <= stop_loss
        hit_target = high_p >= target

        # Conservative handling for ambiguous candles
        if hit_stop and hit_target:
            # Ambiguous single candle crossing both boundary levels
            # Conservative assumption: stopped out first to prevent optimistic bias
            exit_price = min(open_p, stop_loss)
            realized_r = round((exit_price - entry_price) / risk, 2)
            mfe_r = round((running_max_high - entry_price) / risk, 2)
            mae_r = round((entry_price - running_min_low) / risk, 2)
            return OutcomeResult(
                label=OutcomeLabel.STOPPED,
                exit_date=bar_date,
                exit_price=exit_price,
                holding_period=bars_checked,
                realized_r=realized_r,
                realized_pct=round((exit_price - entry_price) / entry_price * 100.0, 2),
                mfe_r=max(0.0, mfe_r),
                mae_r=max(0.0, mae_r),
                is_win=False,
                ambiguous_candle=True,
                details="Ambiguous candle touched both stop and target; conservative stop assumed.",
            )

        if hit_stop:
            exit_price = min(open_p, stop_loss)
            realized_r = round((exit_price - entry_price) / risk, 2)
            mfe_r = round((running_max_high - entry_price) / risk, 2)
            mae_r = round((entry_price - running_min_low) / risk, 2)

            # Rich failure classification
            if bars_checked <= 2:
                label = OutcomeLabel.EARLY_REVERSAL
            elif relative_volume_at_entry < 1.0:
                label = OutcomeLabel.LOW_VOLUME_FAILURE
            elif regime_at_entry in ("BEARISH", "TRENDING_BEAR"):
                label = OutcomeLabel.MARKET_REGIME_FAILURE
            elif mfe_r < 0.5:
                label = OutcomeLabel.FAILED_BREAKOUT
            else:
                label = OutcomeLabel.STOPPED

            return OutcomeResult(
                label=label,
                exit_date=bar_date,
                exit_price=exit_price,
                holding_period=bars_checked,
                realized_r=realized_r,
                realized_pct=round((exit_price - entry_price) / entry_price * 100.0, 2),
                mfe_r=max(0.0, mfe_r),
                mae_r=max(0.0, mae_r),
                is_win=False,
            )

        if hit_target:
            exit_price = max(open_p, target)
            realized_r = round((exit_price - entry_price) / risk, 2)
            mfe_r = round((running_max_high - entry_price) / risk, 2)
            mae_r = round((entry_price - running_min_low) / risk, 2)
            return OutcomeResult(
                label=OutcomeLabel.WIN_FULL_TARGET,
                exit_date=bar_date,
                exit_price=exit_price,
                holding_period=bars_checked,
                realized_r=realized_r,
                realized_pct=round((exit_price - entry_price) / entry_price * 100.0, 2),
                mfe_r=max(0.0, mfe_r),
                mae_r=max(0.0, mae_r),
                is_win=True,
            )

    # Time-based expiration after max_holding_bars
    last_bar = forward_candles.iloc[bars_checked - 1]
    exit_price = float(last_bar["close"])
    realized_r = round((exit_price - entry_price) / risk, 2)
    mfe_r = round((running_max_high - entry_price) / risk, 2)
    mae_r = round((entry_price - running_min_low) / risk, 2)

    label = OutcomeLabel.WIN_PARTIAL if realized_r > 0.5 else OutcomeLabel.TIME_EXIT

    return OutcomeResult(
        label=label,
        exit_date=forward_candles.index[bars_checked - 1],
        exit_price=exit_price,
        holding_period=bars_checked,
        realized_r=realized_r,
        realized_pct=round((exit_price - entry_price) / entry_price * 100.0, 2),
        mfe_r=max(0.0, mfe_r),
        mae_r=max(0.0, mae_r),
        is_win=realized_r > 0,
    )
