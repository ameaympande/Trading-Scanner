"""
Yahoo Finance market data provider.

Uses the yfinance library to fetch NSE/BSE stock data.
Yahoo Finance uses the .NS suffix for NSE and .BO for BSE.

Limitations:
- No official NSE constituent lists (we maintain our own)
- Intraday data limited to ~60 days
- Rate limiting may apply
- Data may be delayed
"""

from __future__ import annotations

import datetime
import logging

import pandas as pd
import yfinance as yf

from scanner.providers.base import (
    CorporateAction,
    InstrumentInfo,
    MarketDataProvider,
)

logger = logging.getLogger(__name__)


class YahooFinanceProvider(MarketDataProvider):
    """Market data provider using Yahoo Finance (yfinance)."""

    @property
    def name(self) -> str:
        return "Yahoo Finance"

    def _yahoo_symbol(self, symbol: str, exchange: str = "NSE") -> str:
        """Convert a plain symbol to Yahoo Finance format."""
        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        # Handle index symbols
        if symbol.startswith("^"):
            return symbol
        return f"{symbol}{suffix}"

    def get_instruments(self, exchange: str = "NSE") -> list[InstrumentInfo]:
        """
        Get instruments list.

        NOTE: Yahoo Finance does not provide a comprehensive instrument list.
        We use our own curated universe files instead. This method returns
        an empty list — use scanner.data.universes for instrument lists.
        """
        logger.warning(
            "Yahoo Finance does not provide instrument lists. "
            "Use scanner.data.universes to load instrument universes."
        )
        return []

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: datetime.date,
        end_date: datetime.date,
        exchange: str = "NSE",
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV data from Yahoo Finance.

        Returns a DataFrame with columns:
        [open, high, low, close, volume, adjusted_close]
        Index is a DatetimeIndex (timezone-aware, UTC).
        """
        yahoo_sym = self._yahoo_symbol(symbol, exchange)
        logger.info(f"Fetching daily OHLCV for {yahoo_sym} from {start_date} to {end_date}")

        try:
            ticker = yf.Ticker(yahoo_sym)
            # Add one day to end_date because yfinance end is exclusive
            df = ticker.history(
                start=start_date.isoformat(),
                end=(end_date + datetime.timedelta(days=1)).isoformat(),
                interval="1d",
                auto_adjust=False,
                actions=False,
            )

            if df.empty:
                logger.warning(f"No data returned for {yahoo_sym}")
                return pd.DataFrame()

            # Standardize column names
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Adj Close": "adjusted_close",
            })

            # Keep only the columns we need
            expected_cols = ["open", "high", "low", "close", "volume", "adjusted_close"]
            available_cols = [c for c in expected_cols if c in df.columns]
            df = df[available_cols]

            # Ensure adjusted_close exists
            if "adjusted_close" not in df.columns:
                df["adjusted_close"] = df["close"]

            # Ensure index is timezone-aware
            if df.index.tz is None:
                df.index = df.index.tz_localize("Asia/Kolkata")

            # Convert to UTC for storage
            df.index = df.index.tz_convert("UTC")
            df.index.name = "timestamp"

            logger.info(f"Fetched {len(df)} daily candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {yahoo_sym}: {e}")
            raise

    def get_intraday_ohlcv(
        self,
        symbol: str,
        interval: str = "15m",
        days: int = 5,
        exchange: str = "NSE",
    ) -> pd.DataFrame:
        """Fetch intraday OHLCV data from Yahoo Finance."""
        yahoo_sym = self._yahoo_symbol(symbol, exchange)
        logger.info(f"Fetching intraday ({interval}) OHLCV for {yahoo_sym}")

        try:
            ticker = yf.Ticker(yahoo_sym)
            df = ticker.history(
                period=f"{days}d",
                interval=interval,
                auto_adjust=False,
                actions=False,
            )

            if df.empty:
                logger.warning(f"No intraday data for {yahoo_sym}")
                return pd.DataFrame()

            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Adj Close": "adjusted_close",
            })

            expected_cols = ["open", "high", "low", "close", "volume"]
            available_cols = [c for c in expected_cols if c in df.columns]
            df = df[available_cols]

            if df.index.tz is None:
                df.index = df.index.tz_localize("Asia/Kolkata")
            df.index = df.index.tz_convert("UTC")
            df.index.name = "timestamp"

            return df

        except Exception as e:
            logger.error(f"Error fetching intraday data for {yahoo_sym}: {e}")
            raise

    def get_quote(self, symbol: str, exchange: str = "NSE") -> dict:
        """Get the latest quote for a symbol."""
        yahoo_sym = self._yahoo_symbol(symbol, exchange)

        try:
            ticker = yf.Ticker(yahoo_sym)
            info = ticker.info

            return {
                "symbol": symbol,
                "exchange": exchange,
                "last_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "company_name": info.get("longName") or info.get("shortName") or symbol,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "source": self.name,
            }

        except Exception as e:
            logger.error(f"Error fetching quote for {yahoo_sym}: {e}")
            raise

    def get_corporate_actions(
        self,
        symbol: str,
        start_date: datetime.date,
        end_date: datetime.date,
        exchange: str = "NSE",
    ) -> list[CorporateAction]:
        """Get corporate actions from Yahoo Finance."""
        yahoo_sym = self._yahoo_symbol(symbol, exchange)
        actions: list[CorporateAction] = []

        try:
            ticker = yf.Ticker(yahoo_sym)

            # Get splits
            splits = ticker.splits
            if splits is not None and not splits.empty:
                for date_idx, ratio in splits.items():
                    action_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
                    if start_date <= action_date <= end_date:
                        actions.append(CorporateAction(
                            symbol=symbol,
                            action_type="SPLIT",
                            ex_date=action_date,
                            ratio=float(ratio),
                            details=f"Stock split ratio: {ratio}",
                        ))

            # Get dividends
            dividends = ticker.dividends
            if dividends is not None and not dividends.empty:
                for date_idx, amount in dividends.items():
                    action_date = date_idx.date() if hasattr(date_idx, "date") else date_idx
                    if start_date <= action_date <= end_date:
                        actions.append(CorporateAction(
                            symbol=symbol,
                            action_type="DIVIDEND",
                            ex_date=action_date,
                            amount=float(amount),
                            details=f"Dividend: ₹{amount}",
                        ))

            logger.info(f"Found {len(actions)} corporate actions for {symbol}")
            return actions

        except Exception as e:
            logger.error(f"Error fetching corporate actions for {yahoo_sym}: {e}")
            return []
