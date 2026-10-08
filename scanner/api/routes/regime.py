"""Market Regime API Route."""

from __future__ import annotations

import datetime

from fastapi import APIRouter

from scanner.api.schemas import MarketRegimeResponse
from scanner.regime.market_regime import MarketRegimeEngine

router = APIRouter(prefix="/regime", tags=["Market Regime"])


@router.get("", response_model=MarketRegimeResponse)
def get_current_regime() -> MarketRegimeResponse:
    """Get the latest NIFTY 50 broad market regime assessment."""
    engine = MarketRegimeEngine()
    result = engine.evaluate(as_of_date=datetime.date.today(), lookback_days=400)
    return MarketRegimeResponse(
        benchmark_symbol=result.benchmark_symbol,
        regime=result.regime.value,
        close_price=result.close_price,
        score=result.score,
        reasons=result.reasons,
        timestamp=result.timestamp.isoformat() if hasattr(result.timestamp, "isoformat") else str(result.timestamp),
    )
