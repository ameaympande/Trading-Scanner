"""
Base Strategy Interface and Setup Data Structures.
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd

from scanner.config import MarketRegimeLabel, SignalDirection


@dataclass
class CandidateSetup:
    """
    Detailed setup evaluated by a strategy.
    Contains complete explainability data: reasons, invalidation criteria,
    risk parameters, score breakdown, and position levels.
    """

    symbol: str
    company_name: str
    strategy_name: str
    direction: SignalDirection
    timestamp: datetime.datetime | pd.Timestamp
    current_price: float
    entry_low: float
    entry_high: float
    stop_loss: float
    target1: float
    target2: float
    risk_reward: float
    score: int  # 0 to 100
    atr: float
    rsi: float
    relative_volume: float
    market_regime: MarketRegimeLabel
    expected_holding_period: str
    reasons: list[str] = field(default_factory=list)
    invalidation: str = ""
    score_breakdown: dict[str, int] = field(default_factory=dict)
    sector: str = ""

    @property
    def risk_per_share(self) -> float:
        return max(0.01, self.current_price - self.stop_loss)

    @property
    def reward_per_share(self) -> float:
        return max(0.01, self.target1 - self.current_price)


class Strategy(ABC):
    """Abstract Base Class for swing-trading strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier, e.g. TREND_PULLBACK_V1."""
        ...

    @abstractmethod
    def evaluate(
        self,
        symbol: str,
        company_name: str,
        df: pd.DataFrame,
        market_regime: MarketRegimeLabel,
        sector: str = "",
    ) -> CandidateSetup | None:
        """
        Evaluate a single stock at the latest candle.
        Returns CandidateSetup if criteria are met (or above threshold), else None.
        """
        ...
