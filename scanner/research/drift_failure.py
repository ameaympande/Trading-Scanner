"""
Model Drift, Edge Decay Monitoring & Failure Analysis Engine.

Tracks:
1. Feature distribution drift (KS-test between baseline and live features)
2. Rolling-window Edge Decay (20, 50, 100 trade rolling expectancy)
3. Granular failure taxonomy (Loss reasons, average MAE, time to failure)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from scanner.research.observations import TradeObservation


@dataclass
class DriftReport:
    is_drift_detected: bool
    drifted_features: list[str]
    feature_p_values: dict[str, float]
    prediction_drift_score: float
    recommendation: str


@dataclass
class EdgeDecayReport:
    is_decay_detected: bool
    recent_20_expectancy_r: float
    recent_50_expectancy_r: float
    lifetime_expectancy_r: float
    recent_20_win_rate_pct: float
    lifetime_win_rate_pct: float
    warning_message: str | None


@dataclass
class FailureCategorySummary:
    label: str
    count: int
    pct_of_total_losses: float
    avg_mae_r: float
    avg_bars_to_failure: float
    description: str


class DriftAndFailureAnalyzer:
    """
    Monitors statistical stability of the models and analyzes root-cause failures.
    """

    def check_feature_drift(
        self,
        baseline_df: pd.DataFrame,
        recent_df: pd.DataFrame,
        features: list[str],
        p_threshold: float = 0.05,
    ) -> DriftReport:
        """
        Runs two-sample Kolmogorov-Smirnov test to detect feature distribution drift.
        """
        if baseline_df.empty or recent_df.empty or len(recent_df) < 15:
            return DriftReport(
                is_drift_detected=False,
                drifted_features=[],
                feature_p_values={},
                prediction_drift_score=0.0,
                recommendation="Insufficient recent data to assess feature drift.",
            )

        drifted = []
        p_vals = {}

        for f in features:
            if f in baseline_df.columns and f in recent_df.columns:
                b_vals = baseline_df[f].dropna().values
                r_vals = recent_df[f].dropna().values
                if len(b_vals) > 10 and len(r_vals) > 10:
                    _stat, p_val = stats.ks_2samp(b_vals, r_vals)
                    p_vals[f] = round(float(p_val), 4)
                    if p_val < p_threshold:
                        drifted.append(f)

        is_drift = len(drifted) >= 2
        rec = "Model inputs are stable."
        if is_drift:
            rec = f"WARNING: Feature drift detected in {drifted}. Reduce position confidence and inspect market regime."

        return DriftReport(
            is_drift_detected=is_drift,
            drifted_features=drifted,
            feature_p_values=p_vals,
            prediction_drift_score=len(drifted) / len(features) if features else 0.0,
            recommendation=rec,
        )

    def check_edge_decay(
        self,
        trades: list[TradeObservation],
    ) -> EdgeDecayReport:
        """
        Tracks rolling performance over 20 and 50 trade windows to detect edge decay.
        """
        completed = [t for t in trades if t.realized_r is not None]
        if len(completed) < 20:
            return EdgeDecayReport(
                is_decay_detected=False,
                recent_20_expectancy_r=0.0,
                recent_50_expectancy_r=0.0,
                lifetime_expectancy_r=0.0,
                recent_20_win_rate_pct=0.0,
                lifetime_win_rate_pct=0.0,
                warning_message="Insufficient completed trades to evaluate edge decay (<20 trades).",
            )

        r_all = [t.realized_r for t in completed if t.realized_r is not None]
        r_20 = r_all[-20:]
        r_50 = r_all[-50:] if len(r_all) >= 50 else r_all

        ev_all = float(np.mean(r_all))
        ev_20 = float(np.mean(r_20))
        ev_50 = float(np.mean(r_50))

        win_rate_all = float(np.mean([1 if r > 0 else 0 for r in r_all])) * 100.0
        win_rate_20 = float(np.mean([1 if r > 0 else 0 for r in r_20])) * 100.0

        # Decay triggers if recent 20 expectancy is negative or win rate drops significantly
        is_decay = (ev_20 < -0.15) or (win_rate_all - win_rate_20 > 25.0 and ev_20 < 0.05)
        warning = None
        if is_decay:
            warning = (
                f"EDGE DECAY DETECTED: Recent 20-trade expectancy is {ev_20:+.2f}R "
                f"(vs historical {ev_all:+.2f}R). Win rate dropped to {win_rate_20:.1f}%."
            )

        return EdgeDecayReport(
            is_decay_detected=is_decay,
            recent_20_expectancy_r=round(ev_20, 2),
            recent_50_expectancy_r=round(ev_50, 2),
            lifetime_expectancy_r=round(ev_all, 2),
            recent_20_win_rate_pct=round(win_rate_20, 1),
            lifetime_win_rate_pct=round(win_rate_all, 1),
            warning_message=warning,
        )

    def analyze_failures(
        self,
        trades: list[TradeObservation],
    ) -> list[FailureCategorySummary]:
        """
        Categorizes completed losing trades into actionable diagnostic categories.
        """
        losing_trades = [
            t for t in trades
            if t.realized_r is not None and t.realized_r <= 0
        ]
        if not losing_trades:
            return []

        total_losses = len(losing_trades)
        counts: dict[str, list[TradeObservation]] = {}

        for t in losing_trades:
            lbl = t.outcome_label.value if hasattr(t.outcome_label, "value") else str(t.outcome_label)
            if lbl not in counts:
                counts[lbl] = []
            counts[lbl].append(t)

        descriptions = {
            "EARLY_REVERSAL": "Stopped out within 1-2 bars of entry; immediate structural breakdown.",
            "LOW_VOLUME_FAILURE": "Lack of institutional volume follow-through caused price to roll over.",
            "MARKET_REGIME_FAILURE": "Setup failed due to severe broad market drag/correction.",
            "FAILED_BREAKOUT": "Attempted breakout was rejected at immediate resistance (bull trap).",
            "STOPPED": "Normal stop-loss execution after testing planned support.",
            "TIME_EXIT": "Trade ran out of time without reaching either target or stop.",
        }

        summaries: list[FailureCategorySummary] = []
        for label, group in counts.items():
            cnt = len(group)
            pct = round((cnt / total_losses) * 100.0, 1)
            maes = [g.mae_r for g in group if g.mae_r is not None]
            bars = [g.holding_period for g in group if g.holding_period is not None]

            avg_mae = float(np.mean(maes)) if maes else 1.0
            avg_bars = float(np.mean(bars)) if bars else 5.0

            summaries.append(
                FailureCategorySummary(
                    label=label,
                    count=cnt,
                    pct_of_total_losses=pct,
                    avg_mae_r=round(avg_mae, 2),
                    avg_bars_to_failure=round(avg_bars, 1),
                    description=descriptions.get(label, "Unclassified failure mechanism."),
                )
            )

        summaries.sort(key=lambda s: s.count, reverse=True)
        return summaries
