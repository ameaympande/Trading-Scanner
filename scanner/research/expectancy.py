"""
Conditional Expectancy Engine & Feature-Outcome Analysis.

Evaluates historical setups to answer:
"Under what specific conditions (RSI buckets, regime, volume expansion) does this strategy actually deliver positive expectancy?"
Enforces sample-size shrinkage penalties to prevent noise from small sample sizes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from scanner.research.observations import TradeObservation


@dataclass
class BucketExpectancy:
    feature_name: str
    bucket_label: str
    sample_size: int
    win_rate_pct: float
    avg_win_r: float
    avg_loss_r: float
    raw_expectancy_r: float
    confidence_factor: float  # 0.0 to 1.0 (approaches 1.0 as N grows)
    shrunk_expectancy_r: float
    avg_mfe_r: float
    avg_mae_r: float


@dataclass
class FeatureAnalysisResult:
    feature_name: str
    base_expectancy_r: float
    total_samples: int
    buckets: list[BucketExpectancy]
    best_bucket: str
    worst_bucket: str


class ConditionalExpectancyEngine:
    """
    Computes statistical edge and conditional expected values across feature buckets.
    """

    def __init__(self, shrinkage_k: int = 20):
        # K governs the rate of Bayesian shrinkage toward the base rate
        self.shrinkage_k = shrinkage_k

    def analyze_observations(
        self,
        observations: list[TradeObservation],
    ) -> dict[str, FeatureAnalysisResult]:
        """
        Analyzes a list of historical completed observations across multiple dimensions.
        """
        completed = [o for o in observations if o.realized_r is not None]
        if not completed:
            return {}

        df = pd.DataFrame([o.to_dict() for o in completed])
        base_ev = float(df["realized_r"].mean())
        total_n = len(df)

        results: dict[str, FeatureAnalysisResult] = {}

        # 1. RSI Buckets
        if "rsi" in df.columns:
            rsi_bins = [0, 45, 50, 55, 60, 65, 70, 100]
            rsi_labels = ["<45", "45-50", "50-55", "55-60", "60-65", "65-70", ">70"]
            df["rsi_bucket"] = pd.cut(df["rsi"], bins=rsi_bins, labels=rsi_labels, include_lowest=True)
            results["rsi"] = self._evaluate_categorical_feature(df, "rsi_bucket", "rsi", base_ev, total_n)

        # 2. Relative Volume Buckets
        if "relative_volume" in df.columns:
            rvol_bins = [0, 0.8, 1.0, 1.3, 1.8, 3.0, 100.0]
            rvol_labels = ["<0.8x", "0.8-1.0x", "1.0-1.3x", "1.3-1.8x", "1.8-3.0x", ">3.0x"]
            df["rvol_bucket"] = pd.cut(df["relative_volume"], bins=rvol_bins, labels=rvol_labels, include_lowest=True)
            results["relative_volume"] = self._evaluate_categorical_feature(df, "rvol_bucket", "relative_volume", base_ev, total_n)

        # 3. Market Regime
        if "market_regime" in df.columns:
            results["market_regime"] = self._evaluate_categorical_feature(df, "market_regime", "market_regime", base_ev, total_n)

        # 4. Sector
        if "sector" in df.columns:
            results["sector"] = self._evaluate_categorical_feature(df, "sector", "sector", base_ev, total_n)

        # 5. ADX Trend Strength
        if "adx" in df.columns:
            adx_bins = [0, 20, 25, 35, 50, 100]
            adx_labels = ["<20 (Weak)", "20-25", "25-35 (Strong)", "35-50", ">50 (Exhaustion)"]
            df["adx_bucket"] = pd.cut(df["adx"], bins=adx_bins, labels=adx_labels, include_lowest=True)
            results["adx"] = self._evaluate_categorical_feature(df, "adx_bucket", "adx", base_ev, total_n)

        # 6. Distance from EMA20
        if "dist_ema20_pct" in df.columns:
            dist_bins = [-100.0, -2.0, 0.0, 2.0, 5.0, 100.0]
            dist_labels = ["Below EMA20 (>2%)", "Near EMA20 (-2% to 0)", "Above EMA20 (0-2%)", "Extended (2-5%)", "Overextended (>5%)"]
            df["ema20_bucket"] = pd.cut(df["dist_ema20_pct"], bins=dist_bins, labels=dist_labels, include_lowest=True)
            results["dist_ema20"] = self._evaluate_categorical_feature(df, "ema20_bucket", "dist_ema20_pct", base_ev, total_n)

        return results

    def _evaluate_categorical_feature(
        self,
        df: pd.DataFrame,
        group_col: str,
        feature_name: str,
        base_ev: float,
        total_n: int,
    ) -> FeatureAnalysisResult:
        buckets: list[BucketExpectancy] = []

        grouped = df.groupby(group_col, observed=False)
        for name, group in grouped:
            n = len(group)
            if n == 0:
                continue

            r_vals = group["realized_r"].values
            wins = r_vals[r_vals > 0]
            losses = r_vals[r_vals <= 0]

            win_rate = (len(wins) / n * 100.0) if n > 0 else 0.0
            avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
            avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0.0

            raw_ev = float(r_vals.mean())
            # Sample size shrinkage: confidence approaches 1.0 as N exceeds shrinkage_k (e.g. 20)
            conf_factor = round(n / (n + self.shrinkage_k), 3)
            shrunk_ev = round(conf_factor * raw_ev + (1.0 - conf_factor) * base_ev, 3)

            avg_mfe = float(group["mfe_r"].mean()) if "mfe_r" in group else 0.0
            avg_mae = float(group["mae_r"].mean()) if "mae_r" in group else 0.0

            buckets.append(
                BucketExpectancy(
                    feature_name=feature_name,
                    bucket_label=str(name),
                    sample_size=n,
                    win_rate_pct=round(win_rate, 1),
                    avg_win_r=round(avg_win, 2),
                    avg_loss_r=round(avg_loss, 2),
                    raw_expectancy_r=round(raw_ev, 3),
                    confidence_factor=conf_factor,
                    shrunk_expectancy_r=shrunk_ev,
                    avg_mfe_r=round(avg_mfe, 2),
                    avg_mae_r=round(avg_mae, 2),
                )
            )

        if not buckets:
            return FeatureAnalysisResult(
                feature_name=feature_name,
                base_expectancy_r=base_ev,
                total_samples=total_n,
                buckets=[],
                best_bucket="N/A",
                worst_bucket="N/A",
            )

        best_b = max(buckets, key=lambda b: b.shrunk_expectancy_r).bucket_label
        worst_b = min(buckets, key=lambda b: b.shrunk_expectancy_r).bucket_label

        return FeatureAnalysisResult(
            feature_name=feature_name,
            base_expectancy_r=round(base_ev, 3),
            total_samples=total_n,
            buckets=buckets,
            best_bucket=best_b,
            worst_bucket=worst_b,
        )

    def estimate_candidate_expectancy(
        self,
        candidate_obs: TradeObservation,
        analysis: dict[str, FeatureAnalysisResult],
    ) -> tuple[float, float, list[str]]:
        """
        Estimates the conditional expected R return of a live setup candidate
        based on historical feature buckets.
        Returns (estimated_ev_r, confidence_factor, explanation_notes).
        """
        if not analysis:
            return 0.20, 0.50, ["No historical observation database; defaulting to baseline prior."]

        notes: list[str] = []
        ev_adjustments: list[float] = []
        confidences: list[float] = []

        # Check regime
        if "market_regime" in analysis:
            b_match = next((b for b in analysis["market_regime"].buckets if b.bucket_label == candidate_obs.market_regime), None)
            if b_match and b_match.sample_size >= 5:
                ev_adjustments.append(b_match.shrunk_expectancy_r)
                confidences.append(b_match.confidence_factor)
                notes.append(f"Regime {candidate_obs.market_regime}: {b_match.shrunk_expectancy_r:+.2f}R (N={b_match.sample_size})")

        # Check relative volume
        if "relative_volume" in analysis:
            rvol = candidate_obs.relative_volume
            for b in analysis["relative_volume"].buckets:
                if (">3.0x" in b.bucket_label and rvol > 3.0) or ("1.8-3.0x" in b.bucket_label and 1.8 <= rvol <= 3.0) or ("1.3-1.8x" in b.bucket_label and 1.3 <= rvol < 1.8):
                    ev_adjustments.append(b.shrunk_expectancy_r)
                    confidences.append(b.confidence_factor)
                    notes.append(f"Volume {b.bucket_label}: {b.shrunk_expectancy_r:+.2f}R")
                    break

        # Check sector
        if "sector" in analysis:
            b_sector = next((b for b in analysis["sector"].buckets if b.bucket_label == candidate_obs.sector), None)
            if b_sector and b_sector.sample_size >= 4:
                ev_adjustments.append(b_sector.shrunk_expectancy_r)
                confidences.append(b_sector.confidence_factor)
                notes.append(f"Sector {candidate_obs.sector}: {b_sector.shrunk_expectancy_r:+.2f}R")

        if ev_adjustments:
            combined_ev = float(np.mean(ev_adjustments))
            avg_conf = float(np.mean(confidences))
        else:
            combined_ev = 0.25
            avg_conf = 0.50

        return round(combined_ev, 3), round(avg_conf, 2), notes
