"""
Dynamic Risk Management & Portfolio Correlation Engine.

Implements:
1. Drawdown Protection States (NORMAL, CAUTION, DEFENSIVE, PAUSED)
2. Trade Throttling based on Market Regime and Strategy Drift
3. Portfolio Correlation Filter (prevents clustering in identical bets)
4. Dynamic Grade-Based Position Sizing (maintaining strict hard maximum risk)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pandas as pd

from scanner.config import Settings, get_settings
from scanner.research.meta_scorer import SetupGrade


class DrawdownMode(StrEnum):
    NORMAL = "NORMAL"          # 0 to 5% DD: Full risk
    CAUTION = "CAUTION"        # 5 to 8% DD: Reduced risk (0.50%)
    DEFENSIVE = "DEFENSIVE"    # 8 to 12% DD: 0.25% risk, max 1 position
    PAUSED = "PAUSED"          # >12% DD: 0 positions, paused


@dataclass
class DrawdownStatus:
    current_drawdown_pct: float
    mode: DrawdownMode
    max_allowed_positions: int
    allowed_risk_multiplier: float
    message: str


@dataclass
class CorrelationCheckResult:
    candidate_symbol: str
    correlated_with: str | None
    max_correlation: float
    is_safe: bool
    warning: str | None


class AdaptiveRiskManager:
    """
    Governs portfolio exposure, drawdown throttle states, and correlation checks.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def get_drawdown_state(self, current_equity: float, peak_equity: float) -> DrawdownStatus:
        """
        Determines current portfolio risk mode based on peak-to-trough drawdown.
        """
        if peak_equity <= 0:
            dd_pct = 0.0
        else:
            dd_pct = max(0.0, (peak_equity - current_equity) / peak_equity * 100.0)

        dd_pct = round(dd_pct, 2)

        if dd_pct >= 12.0:
            return DrawdownStatus(
                current_drawdown_pct=dd_pct,
                mode=DrawdownMode.PAUSED,
                max_allowed_positions=0,
                allowed_risk_multiplier=0.0,
                message=f"Drawdown ({dd_pct}%) exceeds 12% threshold. New trade entries PAUSED.",
            )
        elif dd_pct >= 8.0:
            return DrawdownStatus(
                current_drawdown_pct=dd_pct,
                mode=DrawdownMode.DEFENSIVE,
                max_allowed_positions=1,
                allowed_risk_multiplier=0.33,
                message=f"Drawdown ({dd_pct}%) in defensive range (8-12%). Risk reduced to 0.25%, max 1 position.",
            )
        elif dd_pct >= 5.0:
            return DrawdownStatus(
                current_drawdown_pct=dd_pct,
                mode=DrawdownMode.CAUTION,
                max_allowed_positions=3,
                allowed_risk_multiplier=0.66,
                message=f"Drawdown ({dd_pct}%) in caution range (5-8%). Risk scaled to 0.50%, max 3 positions.",
            )
        else:
            return DrawdownStatus(
                current_drawdown_pct=dd_pct,
                mode=DrawdownMode.NORMAL,
                max_allowed_positions=5,
                allowed_risk_multiplier=1.0,
                message=f"Drawdown ({dd_pct}%) within normal parameters (<5%). Standard risk active.",
            )

    def check_portfolio_correlation(
        self,
        candidate_symbol: str,
        candidate_returns: pd.Series,
        open_positions_returns: dict[str, pd.Series],
        threshold: float = 0.65,
    ) -> CorrelationCheckResult:
        """
        Verifies that candidate doesn't have an excessive correlation with an existing position.
        """
        if not open_positions_returns:
            return CorrelationCheckResult(
                candidate_symbol=candidate_symbol,
                correlated_with=None,
                max_correlation=0.0,
                is_safe=True,
                warning=None,
            )

        max_corr = 0.0
        correlated_sym = None

        for sym, ret_series in open_positions_returns.items():
            if len(candidate_returns) > 10 and len(ret_series) > 10:
                # Align series
                aligned = pd.concat([candidate_returns, ret_series], axis=1).dropna()
                if len(aligned) >= 10:
                    corr = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
                    if corr > max_corr:
                        max_corr = corr
                        correlated_sym = sym

        max_corr = round(max_corr, 2)
        if max_corr >= threshold and correlated_sym:
            return CorrelationCheckResult(
                candidate_symbol=candidate_symbol,
                correlated_with=correlated_sym,
                max_correlation=max_corr,
                is_safe=False,
                warning=f"High correlation ({max_corr:.2f}) with open position {correlated_sym}. Risk concentration alert.",
            )

        return CorrelationCheckResult(
            candidate_symbol=candidate_symbol,
            correlated_with=correlated_sym,
            max_correlation=max_corr,
            is_safe=True,
            warning=None,
        )

    def calculate_adaptive_sizing(
        self,
        entry_price: float,
        stop_loss: float,
        grade: SetupGrade,
        dd_status: DrawdownStatus,
        capital: float = 100_000.0,
    ) -> dict[str, Any]:
        """
        Calculates position size factoring in:
        1. Hard maximum risk per trade cap (0.75%)
        2. Drawdown mode multiplier
        3. Setup grade scaling (A+ vs B)
        """
        if dd_status.mode == DrawdownMode.PAUSED:
            return {
                "quantity": 0,
                "position_value": 0.0,
                "risk_amount": 0.0,
                "risk_pct": 0.0,
                "reason": "Trading is paused due to drawdown protection.",
            }

        # Grade scaling factor
        grade_multipliers = {
            SetupGrade.A_PLUS: 1.0,
            SetupGrade.A: 0.85,
            SetupGrade.B: 0.60,
            SetupGrade.C: 0.35,
            SetupGrade.REJECT: 0.0,
        }
        grade_mult = grade_multipliers.get(grade, 0.0)

        # Base risk percentage (e.g. 0.0075 = 0.75%)
        base_risk = self.settings.risk_per_trade
        effective_risk_pct = base_risk * grade_mult * dd_status.allowed_risk_multiplier
        # Ensure it never exceeds the hard configured maximum risk
        effective_risk_pct = min(base_risk, max(0.001, effective_risk_pct))

        risk_amount = capital * effective_risk_pct
        risk_per_share = max(0.01, entry_price - stop_loss)

        qty_by_risk = math.floor(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        max_capital_for_pos = capital * self.settings.max_single_position_pct
        qty_by_cap = math.floor(max_capital_for_pos / entry_price) if entry_price > 0 else 0

        final_qty = max(0, min(qty_by_risk, qty_by_cap))
        pos_val = round(final_qty * entry_price, 2)

        return {
            "quantity": final_qty,
            "position_value": pos_val,
            "risk_amount": round(final_qty * risk_per_share, 2),
            "risk_pct": round((final_qty * risk_per_share / capital) * 100.0, 3) if capital > 0 else 0.0,
            "grade_multiplier": grade_mult,
            "drawdown_multiplier": dd_status.allowed_risk_multiplier,
            "drawdown_mode": dd_status.mode.value,
        }
