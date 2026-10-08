"""Technical features model — pre-computed indicator values."""

from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scanner.models.base import Base


class TechnicalFeatures(Base):
    """
    Stores pre-computed technical indicator values for each instrument/date.

    These are computed from OHLCV data and stored for fast querying
    and signal generation. All values are point-in-time — no look-ahead.
    """

    __tablename__ = "technical_features"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="1d")

    # Moving Averages
    sma20: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    sma50: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    sma200: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ema20: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ema50: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ema200: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    # Momentum
    rsi14: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    atr14: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    adx14: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    # MACD
    macd: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    macd_signal: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    macd_histogram: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    # Volume
    volume_sma20: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    relative_volume: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    # Other
    roc: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    volatility: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    high20: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    high50: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    low20: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    low50: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    # Relationships
    instrument: Mapped[Instrument] = relationship(  # noqa: F821
        "Instrument", back_populates="technical_features"
    )

    __table_args__ = (
        Index(
            "ix_techfeat_instrument_timeframe_timestamp",
            "instrument_id",
            "timeframe",
            "timestamp",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TechnicalFeatures(instrument_id={self.instrument_id}, "
            f"timestamp={self.timestamp})>"
        )
