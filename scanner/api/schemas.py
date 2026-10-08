"""API Request and Response Pydantic Schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    universe: str = Field(default="NIFTY_100", description="Universe: NIFTY_50, NIFTY_100, NIFTY_200, etc.")
    date: str | None = Field(default=None, description="Scan date YYYY-MM-DD")
    top_n: int = Field(default=10, ge=1, le=50)
    capital: float = Field(default=100_000.0, gt=0)
    risk_pct: float = Field(default=0.0075, gt=0, le=0.1)
    max_price: float | None = Field(default=None, description="Optional maximum share price constraint")
    only_affordable: bool = Field(default=False, description="Filter setups strictly to those affordable with capital")
    use_cache: bool = Field(default=True)


class CandidateSetupResponse(BaseModel):
    symbol: str
    company_name: str
    strategy_name: str
    direction: str
    timestamp: str
    current_price: float
    entry_low: float
    entry_high: float
    stop_loss: float
    target1: float
    target2: float
    risk_reward: float
    score: int
    atr: float
    rsi: float
    relative_volume: float
    market_regime: str
    expected_holding_period: str
    reasons: list[str]
    invalidation: str
    score_breakdown: dict[str, int]
    sector: str
    suggested_qty: int = 0
    position_value: float = 0.0
    setup_grade: str = "A"
    meta_score: int = 80
    ml_prob_pct: int = 60
    expected_value_r: float = 0.35


class MarketRegimeResponse(BaseModel):
    benchmark_symbol: str
    regime: str
    close_price: float
    score: float
    reasons: list[str]
    timestamp: str


class ScanResponse(BaseModel):
    regime: MarketRegimeResponse
    stats: dict[str, Any]
    setups: list[CandidateSetupResponse]


class BacktestRequest(BaseModel):
    symbol: str = "RELIANCE"
    initial_capital: float = 100_000.0
    risk_pct: float = 0.0075
    lookback_days: int = 500


class PaperOrderRequest(BaseModel):
    symbol: str
    entry_price: float
    quantity: int
    stop_loss: float
    target1: float
    target2: float = 0.0
    strategy: str = "TREND_PULLBACK_V1"
    score: int = 75


class PaperCloseRequest(BaseModel):
    position_id: str
    exit_price: float
    exit_reason: str = "MANUAL"
