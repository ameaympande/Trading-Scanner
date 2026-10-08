"""
Position Sizing and Portfolio Risk Engine.

Calculates realistic share quantity based on account capital, per-trade risk %,
stop-loss distance, maximum single-position allocation, and portfolio risk limits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scanner.config import Settings, get_settings


@dataclass
class PositionSizeResult:
    symbol: str
    account_size: float
    risk_percentage: float
    max_risk_amount: float
    entry_price: float
    stop_loss: float
    risk_per_share: float
    quantity: int
    position_value: float
    position_pct_of_capital: float
    is_constrained_by_max_position: bool
    notes: list[str]


class PositionSizer:
    """
    Computes position sizes respecting risk-per-trade and capital constraints.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def calculate_position(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account_size: float | None = None,
        risk_per_trade_pct: float | None = None,
        max_single_pos_pct: float | None = None,
    ) -> PositionSizeResult:
        """
        Calculate safe quantity and exposure for a setup.
        """
        capital = account_size if account_size is not None else self.settings.account_size
        risk_pct = risk_per_trade_pct if risk_per_trade_pct is not None else self.settings.risk_per_trade
        max_pos_pct = max_single_pos_pct if max_single_pos_pct is not None else self.settings.max_single_position_pct

        notes: list[str] = []

        if entry_price <= stop_loss:
            raise ValueError(f"Entry price ({entry_price}) must be strictly higher than stop loss ({stop_loss}) for long trades.")

        risk_per_share = entry_price - stop_loss
        max_risk_amount = capital * risk_pct

        effective_max_pos_pct = 1.0 if (capital <= 25000 and max_single_pos_pct is None) else max_pos_pct

        # 1. Unconstrained quantity based strictly on risk budget
        qty_by_risk = math.floor(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0

        # 2. Capital constraint: Max single-position capital limit (e.g. 25% of account, or 100% for micro budgets)
        max_position_capital = capital * effective_max_pos_pct
        qty_by_capital = math.floor(max_position_capital / entry_price) if entry_price > 0 else 0

        # 3. Take the minimum to guarantee neither risk nor position size limits are breached
        constrained_by_max_pos = False
        if qty_by_capital < qty_by_risk:
            quantity = max(0, qty_by_capital)
            constrained_by_max_pos = True
            notes.append(
                f"Position capped at {int(effective_max_pos_pct * 100)}% of account capital (₹{max_position_capital:,.2f})"
            )
        else:
            quantity = max(0, qty_by_risk)

        # For micro accounts (<= ₹25,000), if stock is affordable within total capital, allow at least 1 share
        max_affordable_qty = math.floor(capital / entry_price) if entry_price > 0 else 0
        if capital <= 25000 and max_affordable_qty >= 1:
            quantity = max(1, min(max(quantity, 1), max_affordable_qty))
        else:
            quantity = min(quantity, max_affordable_qty)

        if quantity == 0:
            deficit = max(0, entry_price - capital)
            if deficit > 0:
                notes.append(f"Capital insufficient to purchase 1 share (requires ₹{entry_price:,.2f}, deficit: ₹{deficit:,.2f}).")
            else:
                notes.append("Risk budget insufficient to purchase even 1 share.")

        position_value = round(quantity * entry_price, 2)
        pos_pct = round((position_value / capital) * 100.0, 2) if capital > 0 else 0.0

        return PositionSizeResult(
            symbol=symbol,
            account_size=capital,
            risk_percentage=risk_pct,
            max_risk_amount=round(max_risk_amount, 2),
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            risk_per_share=round(risk_per_share, 2),
            quantity=quantity,
            position_value=position_value,
            position_pct_of_capital=pos_pct,
            is_constrained_by_max_position=constrained_by_max_pos,
            notes=notes,
        )
