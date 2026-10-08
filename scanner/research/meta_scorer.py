"""
Adaptive Meta-Scoring & Trade Quality Filter.

Combines:
1. Base Strategy Score (Technical qualification)
2. Calibrated Machine Learning Probability P(+2R before -1R)
3. Historical Conditional Expectancy (EV in R)
4. Market Regime Alignment
5. Sector Momentum & Relative Strength vs NIFTY
6. Sample Size Verification

Classifies setups into statistically-backed quality tiers:
A+, A, B, C, REJECT.
Supports defensive 'NO TRADE' state when market lacks edge.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from scanner.research.expectancy import ConditionalExpectancyEngine, FeatureAnalysisResult
from scanner.research.ml_model import TradeQualityML
from scanner.research.observations import TradeObservation
from scanner.strategies.base import CandidateSetup


class SetupGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    REJECT = "REJECT"


@dataclass
class MetaScoringResult:
    symbol: str
    grade: SetupGrade
    meta_score: int  # 0 to 100
    base_score: int
    ml_probability: float  # Calibrated P(+2R before -1R)
    expected_value_r: float
    relative_strength: float
    sample_size_confidence: float
    is_tradable: bool
    components: dict[str, float]
    explanations: list[str]


class AdaptiveMetaScorer:
    """
    Ranks setups by combining technical criteria with learned empirical edge.
    """

    def __init__(
        self,
        ml_model: TradeQualityML | None = None,
        expectancy_engine: ConditionalExpectancyEngine | None = None,
    ):
        self.ml_model = ml_model or TradeQualityML()
        self.expectancy_engine = expectancy_engine or ConditionalExpectancyEngine()

    def evaluate_setup(
        self,
        setup: CandidateSetup,
        obs: TradeObservation,
        analysis_dict: dict[str, FeatureAnalysisResult] | None = None,
        rs_vs_nifty: float = 1.0,
        sector_outperforming: bool = False,
    ) -> MetaScoringResult:
        """
        Calculates meta-score and grade for a candidate setup.
        """
        explanations: list[str] = []

        # 1. Base Score (40% weight of meta-score)
        base_score = setup.score
        base_contrib = (base_score / 100.0) * 40.0

        # 2. ML Probability Component (25% weight)
        ml_prob = self.ml_model.predict_probability(obs)
        ml_contrib = (ml_prob / 0.70) * 25.0
        ml_contrib = min(25.0, max(5.0, ml_contrib))
        explanations.append(f"Model P(+2R before -1R): {int(ml_prob * 100)}%")

        # 3. Conditional Expectancy Component (20% weight)
        if analysis_dict:
            ev_r, conf, exp_notes = self.expectancy_engine.estimate_candidate_expectancy(obs, analysis_dict)
            explanations.extend(exp_notes)
        else:
            ev_r = 0.35
            conf = 0.50

        # Convert EV (-0.5R to +1.0R) to points
        ev_normalized = max(0.0, min(1.0, (ev_r + 0.2) / 1.0))
        ev_contrib = ev_normalized * 20.0 * conf
        explanations.append(f"Conditional Expectancy: {ev_r:+.2f}R (Confidence: {int(conf*100)}%)")

        # 4. Relative Strength & Sector Component (15% weight)
        rs_contrib = 0.0
        if rs_vs_nifty > 1.05:
            rs_contrib += 8.0
            explanations.append(f"Strong relative strength vs NIFTY ({rs_vs_nifty:.2f}x)")
        elif rs_vs_nifty >= 0.98:
            rs_contrib += 4.0

        if sector_outperforming:
            rs_contrib += 7.0
            explanations.append("Sector is actively outperforming the broad benchmark")
        else:
            rs_contrib += 2.0

        # Sum total meta-score (0-100)
        total_meta_score = round(base_contrib + ml_contrib + ev_contrib + rs_contrib)
        total_meta_score = max(0, min(100, total_meta_score))

        # Regime adjustment: reduce meta score if broad market is bearish
        regime_str = setup.market_regime.value if hasattr(setup.market_regime, "value") else str(setup.market_regime)
        if regime_str in ("BEARISH", "TRENDING_BEAR"):
            total_meta_score = int(total_meta_score * 0.75)
            explanations.append("Adverse market regime applied defensive haircut (-25%)")

        # Grade Assignment Logic (Section 29)
        if total_meta_score >= 82 and ev_r >= 0.30 and ml_prob >= 0.56 and rs_vs_nifty >= 1.02:
            grade = SetupGrade.A_PLUS
            is_tradable = True
        elif total_meta_score >= 74 and ev_r >= 0.15 and ml_prob >= 0.50:
            grade = SetupGrade.A
            is_tradable = True
        elif total_meta_score >= 66 and ev_r >= 0.0:
            grade = SetupGrade.B
            is_tradable = True
        elif total_meta_score >= 58:
            grade = SetupGrade.C
            is_tradable = False  # C setups are watched, not traded by default
        else:
            grade = SetupGrade.REJECT
            is_tradable = False

        components = {
            "base_score_contrib": round(base_contrib, 1),
            "ml_prob_contrib": round(ml_contrib, 1),
            "expectancy_contrib": round(ev_contrib, 1),
            "relative_strength_contrib": round(rs_contrib, 1),
        }

        return MetaScoringResult(
            symbol=setup.symbol,
            grade=grade,
            meta_score=total_meta_score,
            base_score=base_score,
            ml_probability=ml_prob,
            expected_value_r=round(ev_r, 2),
            relative_strength=rs_vs_nifty,
            sample_size_confidence=conf,
            is_tradable=is_tradable,
            components=components,
            explanations=explanations,
        )
