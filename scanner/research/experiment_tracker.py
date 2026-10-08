"""
Strategy Research Lab & Experiment Tracking Engine.

Records every research run with experiment_id, configuration parameters,
dataset hashes, and out-of-sample metrics.
Manages Champion / Challenger model promotions based on out-of-sample robustness.
"""

from __future__ import annotations

import datetime
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scanner.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ResearchExperiment:
    experiment_id: str
    strategy_name: str
    universe: str
    start_date: str
    end_date: str
    parameters: dict[str, Any]
    metrics: dict[str, Any]
    timestamp: str
    notes: str = ""


@dataclass
class ChampionChallengerStatus:
    champion_id: str
    champion_algorithm: str
    champion_oos_expectancy: float
    champion_brier_score: float
    challenger_id: str | None
    challenger_algorithm: str | None
    challenger_oos_expectancy: float | None
    challenger_brier_score: float | None
    is_promotion_eligible: bool
    evaluation_notes: list[str]


class ExperimentTracker:
    """
    Manages persistent storage and comparison of research experiments.
    """

    def __init__(self, storage_dir: Path | str | None = None):
        settings = get_settings()
        self.storage_dir = Path(storage_dir or (settings.data_cache_dir / "research"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_file = self.storage_dir / "experiments.json"
        self.models_file = self.storage_dir / "models_registry.json"

    def record_experiment(
        self,
        strategy_name: str,
        universe: str,
        parameters: dict[str, Any],
        metrics: dict[str, Any],
        start_date: str,
        end_date: str,
        notes: str = "",
    ) -> ResearchExperiment:
        """Saves a research run to experiments log."""
        exp_id = f"EXP-{strategy_name[:4]}-{int(datetime.datetime.now().timestamp())}"
        exp = ResearchExperiment(
            experiment_id=exp_id,
            strategy_name=strategy_name,
            universe=universe,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters,
            metrics=metrics,
            timestamp=datetime.datetime.now().isoformat(),
            notes=notes,
        )

        existing = self.list_experiments()
        existing.append(exp)

        with open(self.experiments_file, "w") as f:
            json.dump([asdict(e) for e in existing], f, indent=2)

        return exp

    def list_experiments(self) -> list[ResearchExperiment]:
        """Lists all recorded experiments."""
        if not self.experiments_file.exists():
            return []
        try:
            with open(self.experiments_file) as f:
                data = json.load(f)
            return [ResearchExperiment(**d) for d in data]
        except Exception as e:
            logger.error(f"Error reading experiments: {e}")
            return []

    def compare_experiments(self, exp_id_a: str, exp_id_b: str) -> dict[str, Any]:
        """Compares two experiments side-by-side."""
        exps = {e.experiment_id: e for e in self.list_experiments()}
        a = exps.get(exp_id_a)
        b = exps.get(exp_id_b)

        if not a or not b:
            raise ValueError("One or both experiment IDs not found.")

        return {
            "experiment_a": asdict(a),
            "experiment_b": asdict(b),
            "metric_delta": {
                k: round(float(b.metrics.get(k, 0)) - float(a.metrics.get(k, 0)), 3)
                for k in a.metrics
                if k in b.metrics and isinstance(a.metrics[k], (int, float))
            },
        }

    def evaluate_challenger(
        self,
        champion_metrics: dict[str, float],
        challenger_metrics: dict[str, float],
    ) -> tuple[bool, list[str]]:
        """
        Determines if a Challenger model satisfies criteria to displace the Champion.
        Criteria:
        1. OOS Expectancy must be higher
        2. Brier score (calibration error) must be lower
        3. Drawdown must not deteriorate by more than 15%
        """
        notes: list[str] = []
        eligible = True

        champ_ev = champion_metrics.get("expected_value_r", 0.30)
        chall_ev = challenger_metrics.get("expected_value_r", 0.0)

        champ_brier = champion_metrics.get("brier_score", 0.22)
        chall_brier = challenger_metrics.get("brier_score", 0.25)

        champ_dd = champion_metrics.get("max_drawdown_pct", 10.0)
        chall_dd = challenger_metrics.get("max_drawdown_pct", 12.0)

        if chall_ev >= champ_ev + 0.03:
            notes.append(f"✓ Challenger OOS Expectancy ({chall_ev:+.2f}R) outperforms Champion ({champ_ev:+.2f}R).")
        else:
            notes.append(f"✗ Challenger OOS Expectancy ({chall_ev:+.2f}R) does not meaningfully beat Champion ({champ_ev:+.2f}R).")
            eligible = False

        if chall_brier <= champ_brier:
            notes.append(f"✓ Challenger probability calibration Brier ({chall_brier:.4f}) is superior to Champion ({champ_brier:.4f}).")
        else:
            notes.append(f"✗ Challenger Brier score ({chall_brier:.4f}) is worse than Champion ({champ_brier:.4f}).")
            eligible = False

        if chall_dd <= champ_dd * 1.15:
            notes.append(f"✓ Challenger drawdown ({chall_dd:.1f}%) within acceptable boundaries of Champion ({champ_dd:.1f}%).")
        else:
            notes.append(f"✗ Challenger drawdown ({chall_dd:.1f}%) exceeds acceptable risk ceiling.")
            eligible = False

        return eligible, notes
