"""
Data Loader module.

Fetches data via configured provider, passes it through DataValidator,
handles local caching to avoid duplicate requests, and prepares analysis-ready DataFrames.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path

import pandas as pd

from scanner.config import get_settings
from scanner.data.validator import DataValidator, ValidationResult
from scanner.providers.base import MarketDataProvider
from scanner.providers.registry import get_provider

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Coordinates data ingestion, validation, and caching.
    """

    def __init__(
        self,
        provider: MarketDataProvider | None = None,
        validator: DataValidator | None = None,
        cache_dir: Path | str | None = None,
    ):
        settings = get_settings()
        self.provider = provider or get_provider()
        self.validator = validator or DataValidator()
        self.cache_dir = Path(cache_dir or settings.data_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, symbol: str, timeframe: str = "1d") -> Path:
        clean_sym = symbol.replace("^", "INDEX_").replace(".", "_")
        return self.cache_dir / f"{clean_sym}_{timeframe}.parquet"

    def fetch_daily_ohlcv(
        self,
        symbol: str,
        start_date: datetime.date,
        end_date: datetime.date,
        exchange: str = "NSE",
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> tuple[pd.DataFrame, ValidationResult]:
        """
        Fetch validated daily OHLCV dataframe.
        Returns (cleaned_df, validation_result).
        """
        cache_file = self._get_cache_path(symbol, "1d")

        df: pd.DataFrame | None = None

        if use_cache and not force_refresh and cache_file.exists():
            try:
                cached_df = pd.read_parquet(cache_file)
                # Verify that cache covers the needed dates
                if not cached_df.empty:
                    min_date = cached_df.index.min().date()
                    max_date = cached_df.index.max().date()
                    # If cached data covers the range
                    if min_date <= start_date and max_date >= end_date:
                        logger.debug(f"Using cached data for {symbol} ({min_date} to {max_date})")
                        df = cached_df.loc[
                            (cached_df.index.date >= start_date) & (cached_df.index.date <= end_date)
                        ]
            except Exception as e:
                logger.warning(f"Error reading cache for {symbol}: {e}. Fetching fresh.")

        if df is None or df.empty:
            logger.info(f"Fetching fresh data for {symbol} from provider {self.provider.name}")
            raw_df = self.provider.get_daily_ohlcv(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
            )
            df = raw_df

        # Run validation
        val_result = self.validator.validate_and_clean(df, symbol=symbol)

        if not val_result.is_valid:
            logger.error(
                f"Data validation failed for {symbol}: {[a.details for a in val_result.anomalies if a.severity == 'ERROR']}"
            )
            return pd.DataFrame(), val_result

        cleaned_df = val_result.cleaned_df

        # Save to cache if valid and not empty
        if use_cache and not cleaned_df.empty:
            try:
                cleaned_df.to_parquet(cache_file)
            except Exception as e:
                logger.warning(f"Failed to cache data to {cache_file}: {e}")

        return cleaned_df, val_result
