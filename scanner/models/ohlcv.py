"""OHLCV model — stores price and volume data."""

from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scanner.models.base import Base


class OHLCV(Base):
    """
    Stores OHLCV (Open, High, Low, Close, Volume) data for instruments.

    Each record represents one candle for one instrument at a specific timeframe.
    Timestamps are stored in UTC but should be converted to Asia/Kolkata
    for market-session calculations.
    """

    __tablename__ = "ohlcv"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="1d")
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    # Relationships
    instrument: Mapped[Instrument] = relationship(  # noqa: F821
        "Instrument", back_populates="ohlcv_records"
    )

    __table_args__ = (
        Index(
            "ix_ohlcv_instrument_timeframe_timestamp",
            "instrument_id",
            "timeframe",
            "timestamp",
            unique=True,
        ),
        Index("ix_ohlcv_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<OHLCV(instrument_id={self.instrument_id}, "
            f"timestamp={self.timestamp}, close={self.close})>"
        )
