"""BacktestTrade model — stores individual trades from backtesting."""

from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from scanner.models.base import Base


class BacktestTrade(Base):
    """
    Stores individual trade records from backtesting.

    Each record represents one complete trade (entry to exit) with
    all relevant performance metrics. Used to compute aggregate
    strategy performance.
    """

    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    target: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    pnl_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    holding_period: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BacktestTrade(strategy={self.strategy}, symbol={self.symbol}, "
            f"pnl={self.pnl})>"
        )
