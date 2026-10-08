"""
Broker Adapter Interface with strict live trading safeguard.

Per requirement 21:
DO NOT implement live trading initially.
Live trading MUST be disabled by default (LIVE_TRADING_ENABLED=false).
Any attempt to execute an order while live trading is disabled raises a strict safety error.
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from scanner.config import get_settings


@dataclass
class PositionInfo:
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    exchange: str = "NSE"


@dataclass
class OrderDetails:
    order_id: str
    symbol: str
    transaction_type: str  # BUY or SELL
    quantity: int
    price: float
    order_type: str  # LIMIT, MARKET, SL, SL-M
    status: str
    timestamp: datetime.datetime


class LiveTradingSafetyError(RuntimeError):
    """Raised when an action requires live trading but LIVE_TRADING_ENABLED is False."""
    pass


class BrokerAdapter(ABC):
    """
    Abstract interface for broker integrations (e.g. Zerodha Kite, Upstox, Angel One).
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def _assert_live_enabled(self) -> None:
        """Enforces that live trading cannot be executed unless explicitly configured."""
        if not self.settings.live_trading_enabled:
            raise LiveTradingSafetyError(
                "CRITICAL SAFETY VIOLATION: LIVE_TRADING_ENABLED is set to False. "
                "No live orders can be placed or executed. Use paper trading instead."
            )

    @abstractmethod
    def get_positions(self) -> list[PositionInfo]:
        """Fetch current open broker positions."""
        ...

    @abstractmethod
    def get_orders(self) -> list[OrderDetails]:
        """Fetch order book for the day."""
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Fetch real-time LTP and quote from broker."""
        ...

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "LIMIT",
        price: float | None = None,
        stop_loss: float | None = None,
    ) -> str:
        """
        Place an order. Must call self._assert_live_enabled() first.
        """
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        ...
