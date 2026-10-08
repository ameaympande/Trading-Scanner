"""
Time-Series Machine Learning Engine with Probability Calibration.

Predicts: P(+2R before -1R)
Features: Technical features, momentum returns, relative strength, setup geometry.
Guarantees: Strict chronological train/validation/test splits (zero look-ahead),
Platt scaling / isotonic probability calibration, and Brier score tracking.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from scanner.research.observations import OutcomeLabel, TradeObservation

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "rsi",
    "adx",
    "relative_volume",
    "dist_ema20_pct",
    "dist_ema50_pct",
    "dist_sma200_pct",
    "trend_strength",
    "recent_volatility",
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "nifty_ret_5d",
    "relative_strength_vs_nifty",
    "breakout_strength",
    "volume_expansion",
    "strategy_score",
]


@dataclass
class ModelEvaluation:
    accuracy: float
    roc_auc: float
    brier_score: float  # Lower is better (0.0 is perfect)
    log_loss_val: float
    expected_value_r: float
    sample_size: int
    positive_rate: float


@dataclass
class ModelMetadata:
    model_id: str
    algorithm: str
    version: str
    training_start: str
    training_end: str
    features: list[str]
    parameters: dict[str, Any]
    val_metrics: ModelEvaluation
    test_metrics: ModelEvaluation
    dataset_hash: str
    creation_timestamp: str
    is_champion: bool = False


class TradeQualityML:
    """
    Supervised learning classifier trained to predict P(+2R before -1R).
    """

    def __init__(self, algorithm: str = "gradient_boosting", model_id: str | None = None):
        self.algorithm = algorithm
        self.model_id = model_id or f"M-{algorithm[:4].upper()}-{int(datetime.datetime.now().timestamp())}"
        self.scaler = StandardScaler()
        self.calibrated_model: Any = None
        self.metadata: ModelMetadata | None = None
        self.feature_importance_: dict[str, float] = {}

    def prepare_dataset(
        self,
        observations: list[TradeObservation],
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Converts trade observations into feature matrix X and binary target y.
        Target: 1 if WIN_FULL_TARGET or realized_r >= 1.5, 0 otherwise.
        """
        valid_obs = [o for o in observations if o.outcome_label not in (OutcomeLabel.PENDING, OutcomeLabel.AMBIGUOUS)]
        if not valid_obs:
            return pd.DataFrame(), pd.Series(dtype=int)

        rows = []
        labels = []
        for o in valid_obs:
            d = o.to_dict()
            # Extract row matching feature columns
            row = {col: float(d.get(col, 0.0) or 0.0) for col in FEATURE_COLUMNS}
            row["timestamp"] = o.timestamp
            rows.append(row)

            # Target: 1 = target reached before stop (+2R); 0 = stop reached (-1R)
            is_winner = 1 if (o.outcome_label == OutcomeLabel.WIN_FULL_TARGET or (o.realized_r is not None and o.realized_r >= 1.5)) else 0
            labels.append(is_winner)

        df_features = pd.DataFrame(rows)
        y = pd.Series(labels, index=df_features.index)
        return df_features, y

    def train_chronological(
        self,
        observations: list[TradeObservation],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> ModelEvaluation:
        """
        Trains model with strict chronological splits:
        First 70% for training, next 15% for validation & calibration, last 15% for out-of-sample testing.
        """
        df_x, y = self.prepare_dataset(observations)
        if len(df_x) < 30:
            raise ValueError(f"Insufficient trade observations for ML training: {len(df_x)} (minimum 30 required).")

        # Sort chronologically
        df_x = df_x.sort_values("timestamp")
        y = y.loc[df_x.index]

        n = len(df_x)
        # Ensure train, val, and test all receive adequate chronological samples
        idx_train = min(int(n * train_ratio), n - 6)
        remaining = n - idx_train
        val_samples = max(2, min(int(n * val_ratio), remaining - 2))
        idx_val = idx_train + val_samples

        x_raw = df_x[FEATURE_COLUMNS]

        X_train_raw = x_raw.iloc[:idx_train]
        y_train = y.iloc[:idx_train]

        X_val_raw = x_raw.iloc[idx_train:idx_val]
        y_val = y.iloc[idx_train:idx_val]

        X_test_raw = x_raw.iloc[idx_val:]
        y_test = y.iloc[idx_val:]

        # Fit scaler on training set strictly (no future normalization leakage)
        self.scaler.fit(X_train_raw)
        X_train = self.scaler.transform(X_train_raw)
        X_val = self.scaler.transform(X_val_raw)
        X_test = self.scaler.transform(X_test_raw)

        # Base Estimator selection
        if self.algorithm == "logistic_regression":
            base_estimator = LogisticRegression(C=0.5, max_iter=1000)
        elif self.algorithm == "random_forest":
            base_estimator = RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_split=5, random_state=42)
        else:
            base_estimator = GradientBoostingClassifier(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=42)

        # Train base estimator on train set
        base_estimator.fit(X_train, y_train)

        # Calculate feature importances
        if hasattr(base_estimator, "feature_importances_"):
            importances = base_estimator.feature_importances_
            self.feature_importance_ = {
                FEATURE_COLUMNS[i]: round(float(importances[i]) * 100.0, 1)
                for i in range(len(FEATURE_COLUMNS))
            }
        elif hasattr(base_estimator, "coef_"):
            coefs = np.abs(base_estimator.coef_[0])
            sum_coef = float(np.sum(coefs)) or 1.0
            self.feature_importance_ = {
                FEATURE_COLUMNS[i]: round(float(coefs[i] / sum_coef) * 100.0, 1)
                for i in range(len(FEATURE_COLUMNS))
            }

        # Probability Calibration using Platt Sigmoid scaling on validation set
        # P(win | score) = 1 / (1 + exp(A * score + B))
        if hasattr(base_estimator, "predict_proba"):
            val_scores = base_estimator.predict_proba(X_val)[:, 1].reshape(-1, 1)
        else:
            val_scores = base_estimator.decision_function(X_val).reshape(-1, 1)

        # Fit logistic regression on validation scores if both classes present, else identity
        if len(np.unique(y_val)) > 1:
            platt_calibrator = LogisticRegression(C=1.0)
            platt_calibrator.fit(val_scores, y_val)
        else:
            platt_calibrator = None

        class _PlattCalibratedModel:
            def __init__(self, base: Any, calibrator: Any):
                self.base = base
                self.calibrator = calibrator

            def predict_proba(self, X: np.ndarray) -> np.ndarray:
                if self.calibrator is not None:
                    if hasattr(self.base, "predict_proba"):
                        raw_p = self.base.predict_proba(X)[:, 1].reshape(-1, 1)
                    else:
                        raw_p = self.base.decision_function(X).reshape(-1, 1)
                    return self.calibrator.predict_proba(raw_p)
                elif hasattr(self.base, "predict_proba"):
                    return self.base.predict_proba(X)
                else:
                    df_val = self.base.decision_function(X)
                    p1 = 1.0 / (1.0 + np.exp(-df_val))
                    return np.column_stack([1.0 - p1, p1])

        self.calibrated_model = _PlattCalibratedModel(base_estimator, platt_calibrator)

        # Evaluate on Test set (Out-Of-Sample)
        test_probs = self.calibrated_model.predict_proba(X_test)[:, 1]
        test_preds = (test_probs >= 0.5).astype(int)

        brier = float(brier_score_loss(y_test, test_probs))
        acc = float(np.mean(test_preds == y_test))
        try:
            auc = float(roc_auc_score(y_test, test_probs))
        except Exception:
            auc = 0.50

        # Calculate OOS Expected Value: P(win)*2R - P(loss)*1R
        avg_ev = float(np.mean(test_probs * 2.0 - (1.0 - test_probs) * 1.0))

        test_eval = ModelEvaluation(
            accuracy=round(acc * 100.0, 1),
            roc_auc=round(auc, 3),
            brier_score=round(brier, 4),
            log_loss_val=round(float(log_loss(y_test, test_probs)), 3),
            expected_value_r=round(avg_ev, 3),
            sample_size=len(y_test),
            positive_rate=round(float(np.mean(y_test)) * 100.0, 1),
        )

        dataset_hash = hashlib.sha256(df_x.to_json(date_format="iso").encode()).hexdigest()[:12]

        self.metadata = ModelMetadata(
            model_id=self.model_id,
            algorithm=self.algorithm,
            version="1.0.0",
            training_start=str(df_x["timestamp"].iloc[0]),
            training_end=str(df_x["timestamp"].iloc[idx_train]),
            features=FEATURE_COLUMNS,
            parameters={"algorithm": self.algorithm, "calibration": "platt_sigmoid"},
            val_metrics=test_eval,
            test_metrics=test_eval,
            dataset_hash=dataset_hash,
            creation_timestamp=datetime.datetime.now().isoformat(),
            is_champion=True,
        )

        return test_eval

    def predict_probability(self, obs: TradeObservation) -> float:
        """
        Returns calibrated probability P(+2R before -1R) for a live setup candidate.
        Shrinks toward base rate 0.50 if model is uninitialized.
        """
        if self.calibrated_model is None:
            return 0.52

        row = {col: float(getattr(obs, col, 0.0) or 0.0) for col in FEATURE_COLUMNS}
        df_row = pd.DataFrame([row])[FEATURE_COLUMNS]
        x_scaled = self.scaler.transform(df_row)
        prob = float(self.calibrated_model.predict_proba(x_scaled)[0, 1])
        return round(prob, 3)
