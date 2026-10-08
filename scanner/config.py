"""
Central configuration for the Trading Scanner.

All strategy parameters, risk limits, and system settings are defined here.
Values are loaded from environment variables / .env file with sensible defaults.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MarketRegimeLabel(StrEnum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class Exchange(StrEnum):
    NSE = "NSE"
    BSE = "BSE"


class SignalDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class SignalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"


class Timeframe(StrEnum):
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"
    HOURLY = "1h"
    FIFTEEN_MIN = "15m"


# ---------------------------------------------------------------------------
# Strategy scoring weights — must sum to 100
# ---------------------------------------------------------------------------

class ScoringWeights(BaseSettings):
    """Configurable weights for the TREND_PULLBACK_V1 scoring system."""

    model_config = SettingsConfigDict(env_prefix="SCORE_WEIGHT_")

    trend: int = 25
    momentum: int = 15
    pullback_quality: int = 20
    volume_confirmation: int = 15
    breakout_confirmation: int = 10
    market_regime: int = 10
    liquidity: int = 5

    @field_validator("*", mode="before")
    @classmethod
    def ensure_non_negative(cls, v: int) -> int:
        if int(v) < 0:
            raise ValueError("Score weight cannot be negative")
        return int(v)

    @property
    def total(self) -> int:
        return (
            self.trend
            + self.momentum
            + self.pullback_quality
            + self.volume_confirmation
            + self.breakout_confirmation
            + self.market_regime
            + self.liquidity
        )


# ---------------------------------------------------------------------------
# Transaction costs — Indian equity realistic defaults
# ---------------------------------------------------------------------------

class TransactionCosts(BaseSettings):
    """Indian equity transaction cost assumptions (delivery-based)."""

    model_config = SettingsConfigDict(env_prefix="TXN_")

    brokerage_pct: float = 0.0  # Many discount brokers charge zero for delivery
    stt_buy_pct: float = 0.001  # 0.1% on buy (delivery)
    stt_sell_pct: float = 0.001  # 0.1% on sell (delivery)
    exchange_txn_pct: float = 0.0000345  # NSE transaction charges
    sebi_charges_pct: float = 0.000001  # SEBI turnover fee
    gst_pct: float = 0.18  # GST on brokerage + exchange txn
    stamp_duty_pct: float = 0.00015  # Stamp duty on buy side
    slippage_pct: float = 0.001  # 0.1% estimated slippage


# ---------------------------------------------------------------------------
# Main application settings
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """Main application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "postgresql://scanner:scanner@localhost:5432/trading_scanner"

    # --- Market Data ---
    market_data_provider: str = "yahoo"
    market: Exchange = Exchange.NSE
    timezone: str = "Asia/Kolkata"

    # --- Liquidity Filters ---
    min_price: float = 50.0
    min_avg_volume: int = 100_000
    min_avg_traded_value: float = 5_000_000.0

    # --- Risk Management ---
    account_size: float = 100_000.0
    risk_per_trade: float = 0.0075  # 0.75%
    max_portfolio_risk: float = 0.03  # 3%
    max_positions: int = 5
    max_single_position_pct: float = 0.25  # 25% of capital

    # --- Strategy Parameters ---
    min_rr: float = 2.0
    min_score: int = 70
    atr_stop_multiplier: float = 1.5
    atr_target_multiplier: float = 3.0
    rsi_lower: float = 45.0
    rsi_upper: float = 70.0
    rsi_extreme_upper: float = 75.0
    pullback_atr_max: float = 2.0  # max pullback depth in ATR units
    volume_confirmation_threshold: float = 1.2  # relative volume threshold
    breakout_lookback: int = 5  # bars to look back for breakout
    swing_lookback: int = 10  # bars for swing high/low detection
    min_history_days: int = 250  # minimum trading days of history required

    # --- Market Regime ---
    regime_benchmark: str = "^NSEI"  # NIFTY 50
    regime_sma_period: int = 200
    regime_sma_short: int = 50

    # --- Indicator Periods ---
    sma_periods: list[int] = Field(default=[20, 50, 200])
    ema_periods: list[int] = Field(default=[20, 50, 200])
    rsi_period: int = 14
    atr_period: int = 14
    adx_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    volume_sma_period: int = 20

    # --- Notifications ---
    notification_provider: str = "console"

    # --- Broker ---
    live_trading_enabled: bool = False

    # --- Logging ---
    log_level: str = "INFO"

    # --- Scoring ---
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)

    # --- Transaction Costs ---
    transaction_costs: TransactionCosts = Field(default_factory=TransactionCosts)

    # --- Universes ---
    default_universe: str = "NIFTY_500"

    # --- Data ---
    data_cache_dir: Path = Path("data_cache")


def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
