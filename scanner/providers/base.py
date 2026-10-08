"""
Abstract market data provider interface.

All data providers must implement this interface. This allows the application
to swap providers without changing business logic.
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class InstrumentInfo:
    """Information about a tradeable instrument from the data provider."""

    symbol: str
    exchange: str
    company_name: str
    sector: str | None = None
    industry: str | None = None
    isin: str | None = None
    listing_date: datetime.date | None = None


@dataclass
class CorporateAction:
    """Represents a corporate action (split, bonus, dividend)."""

    symbol: str
    action_type: str  # SPLIT, BONUS, DIVIDEND, SYMBOL_CHANGE
    ex_date: datetime.date
    ratio: float | None = None  # e.g., 2.0 for 1:2 split
    old_symbol: str | None = None
    new_symbol: str | None = None
    amount: float | None = None  # dividend amount
    details: str = ""


@dataclass
class DataQualityReport:
    """Report of data quality issues found during validation."""

    symbol: str
    issues: list[str] = field(default_factory=list)
    missing_dates: list[datetime.date] = field(default_factory=list)
    duplicate_dates: list[datetime.date] = field(default_factory=list)
    suspicious_candles: list[dict] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues or self.missing_dates or self.duplicate_dates or self.suspicious_candles)


class MarketDataProvider(ABC):
    """
    Abstract interface for market data providers.

    Implementations can wrap Yahoo Finance, official NSE feeds,
    broker APIs, or any other data source.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the data provider."""
        ...

    @abstractmethod
    def get_instruments(self, exchange: str = "NSE") -> list[InstrumentInfo]:
        """
        Get list of all available instruments for the given exchange.

        Args:
            exchange: Exchange code (NSE or BSE).

        Returns:
            List of InstrumentInfo objects.
        """
        ...

    @abstractmethod
    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: datetime.date,
        end_date: datetime.date,
        exchange: str = "NSE",
    ) -> pd.DataFrame:
        """
        Get daily OHLCV data for a symbol.

        Args:
            symbol: Stock symbol (e.g., RELIANCE).
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            exchange: Exchange code.

        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume, adjusted_close]
            Index should be DatetimeIndex in UTC.
        """
        ...

    @abstractmethod
    def get_intraday_ohlcv(
        self,
        symbol: str,
        interval: str = "15m",
        days: int = 5,
        exchange: str = "NSE",
    ) -> pd.DataFrame:
        """
        Get intraday OHLCV data for a symbol.

        Args:
            symbol: Stock symbol.
            interval: Candle interval (1m, 5m, 15m, 1h).
            days: Number of days of intraday data.
            exchange: Exchange code.

        Returns:
            DataFrame with OHLCV columns.
        """
        ...

    @abstractmethod
    def get_quote(self, symbol: str, exchange: str = "NSE") -> dict:
        """
        Get current/latest quote for a symbol.

        Returns:
            Dictionary with at least: last_price, open, high, low, close,
            volume, timestamp.
        """
        ...

    @abstractmethod
    def get_corporate_actions(
        self,
        symbol: str,
        start_date: datetime.date,
        end_date: datetime.date,
        exchange: str = "NSE",
    ) -> list[CorporateAction]:
        """
        Get corporate actions (splits, bonuses, dividends) for a symbol.

        Args:
            symbol: Stock symbol.
            start_date: Start date.
            end_date: End date.
            exchange: Exchange code.

        Returns:
            List of CorporateAction objects.
        """
        ...
