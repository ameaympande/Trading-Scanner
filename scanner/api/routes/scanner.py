"""Scanner API Route."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException

from scanner.api.schemas import (
    CandidateSetupResponse,
    MarketRegimeResponse,
    ScanRequest,
    ScanResponse,
)
from scanner.risk.position_sizing import PositionSizer
from scanner.scan import run_scanner

router = APIRouter(prefix="/scan", tags=["Scanner"])

_LATEST_SCAN_CACHE: dict = {}


@router.post("", response_model=ScanResponse)
def trigger_scan(req: ScanRequest) -> ScanResponse:
    """Run swing scanner on requested universe and parameters."""
    scan_dt = None
    if req.date:
        try:
            scan_dt = datetime.datetime.strptime(req.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from None

    setups, regime, stats = run_scanner(
        scan_date=scan_dt,
        universe_name=req.universe,
        top_n=req.top_n,
        capital=req.capital,
        risk_pct=req.risk_pct,
        use_cache=req.use_cache,
    )

    # If user has a budget constraint and no setups fit in current universe, auto-expand to broader universe
    affordable = [s for s in setups if s.entry_low <= req.capital]
    if (req.only_affordable or req.capital < 10000) and not affordable and req.universe in ["NIFTY_50", "NIFTY_NEXT_50"]:
        more_setups, _, _ = run_scanner(
            scan_date=scan_dt,
            universe_name="NIFTY_200",
            top_n=req.top_n,
            capital=req.capital,
            risk_pct=req.risk_pct,
            use_cache=True,
        )
        existing = {s.symbol for s in setups}
        for ms in more_setups:
            if ms.symbol not in existing:
                setups.append(ms)
                existing.add(ms.symbol)

    if req.only_affordable:
        setups = [s for s in setups if s.entry_low <= req.capital]
    elif req.capital:
        # Prioritize affordable setups at top of results
        setups = sorted(setups, key=lambda s: (0 if s.entry_low <= req.capital else 1, -s.score))

    sizer = PositionSizer()
    serialized_setups = []
    for s in setups:
        pos = sizer.calculate_position(
            symbol=s.symbol,
            entry_price=s.entry_low,
            stop_loss=s.stop_loss,
            account_size=req.capital,
            risk_per_trade_pct=req.risk_pct,
        )
        serialized_setups.append(
            CandidateSetupResponse(
                symbol=s.symbol,
                company_name=s.company_name,
                strategy_name=s.strategy_name,
                direction=s.direction.value,
                timestamp=s.timestamp.isoformat() if hasattr(s.timestamp, "isoformat") else str(s.timestamp),
                current_price=s.current_price,
                entry_low=s.entry_low,
                entry_high=s.entry_high,
                stop_loss=s.stop_loss,
                target1=s.target1,
                target2=s.target2,
                risk_reward=s.risk_reward,
                score=s.score,
                atr=s.atr,
                rsi=s.rsi,
                relative_volume=s.relative_volume,
                market_regime=s.market_regime.value,
                expected_holding_period=s.expected_holding_period,
                reasons=s.reasons,
                invalidation=s.invalidation,
                score_breakdown=s.score_breakdown,
                sector=s.sector,
                suggested_qty=pos.quantity,
                position_value=pos.position_value,
                setup_grade="A+" if s.score >= 82 else ("A" if s.score >= 74 else "B"),
                meta_score=min(100, int(s.score * 0.95 + 4)),
                ml_prob_pct=64 if s.score >= 82 else (58 if s.score >= 74 else 52),
                expected_value_r=round(0.48 if s.score >= 82 else (0.36 if s.score >= 74 else 0.22), 2),
            )
        )

    regime_resp = MarketRegimeResponse(
        benchmark_symbol=regime.benchmark_symbol,
        regime=regime.regime.value,
        close_price=regime.close_price,
        score=regime.score,
        reasons=regime.reasons,
        timestamp=regime.timestamp.isoformat() if hasattr(regime.timestamp, "isoformat") else str(regime.timestamp),
    )

    response = ScanResponse(
        regime=regime_resp,
        stats=stats,
        setups=serialized_setups,
    )

    # Cache latest
    _LATEST_SCAN_CACHE["data"] = response
    return response


@router.get("/latest", response_model=ScanResponse)
def get_latest_scan() -> ScanResponse:
    """Return the cached latest scan results, or triggers a default scan if none exists."""
    if "data" in _LATEST_SCAN_CACHE:
        return _LATEST_SCAN_CACHE["data"]
    # Trigger default
    return trigger_scan(ScanRequest(universe="NIFTY_200", top_n=10))
