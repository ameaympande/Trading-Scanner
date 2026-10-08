"""Instrument model — represents a tradeable security."""

from __future__ import annotations

import datetime

from sqlalchemy import Boolean, Date, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scanner.models.base import Base


class Instrument(Base):
    """
    Represents a tradeable instrument (stock) on NSE/BSE.

    Tracks the full lifecycle including listing, delisting, symbol changes,
    and sector classification.
    """

    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False, default="NSE")
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    isin: Mapped[str | None] = mapped_column(String(12), nullable=True, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    listing_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    delisting_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    # Relationships
    ohlcv_records: Mapped[list[OHLCV]] = relationship(  # noqa: F821
        "OHLCV", back_populates="instrument", cascade="all, delete-orphan"
    )
    technical_features: Mapped[list[TechnicalFeatures]] = relationship(  # noqa: F821
        "TechnicalFeatures", back_populates="instrument", cascade="all, delete-orphan"
    )
    signals: Mapped[list[Signal]] = relationship(  # noqa: F821
        "Signal", back_populates="instrument", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_instruments_symbol_exchange", "symbol", "exchange", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Instrument(symbol={self.symbol}, exchange={self.exchange})>"

    @property
    def yahoo_symbol(self) -> str:
        """Return Yahoo Finance compatible symbol (e.g., RELIANCE.NS)."""
        suffix = ".NS" if self.exchange == "NSE" else ".BO"
        return f"{self.symbol}{suffix}"
