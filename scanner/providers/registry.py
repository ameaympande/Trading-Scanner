"""
Registry for market data providers.
Allows dynamically resolving providers by name or configuration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scanner.providers.base import MarketDataProvider

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, type[MarketDataProvider]] = {}


def register_provider(name: str, provider_cls: type[MarketDataProvider]) -> None:
    """Register a provider class with a given key name."""
    _PROVIDERS[name.lower()] = provider_cls
    logger.debug(f"Registered market data provider: {name.lower()}")


def get_provider(name: str | None = None) -> MarketDataProvider:
    """
    Get an instance of a registered provider.
    Defaults to configuration if name is not passed.
    """
    from scanner.config import get_settings
    from scanner.providers.yahoo import YahooFinanceProvider

    # Ensure default providers are registered
    if "yahoo" not in _PROVIDERS:
        register_provider("yahoo", YahooFinanceProvider)

    settings = get_settings()
    provider_name = (name or settings.market_data_provider).lower()

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown market data provider: '{provider_name}'. "
            f"Available providers: {list(_PROVIDERS.keys())}"
        )

    provider_cls = _PROVIDERS[provider_name]
    return provider_cls()
