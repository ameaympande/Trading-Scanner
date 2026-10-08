"""Paper Trading API Route."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from scanner.api.schemas import PaperCloseRequest, PaperOrderRequest
from scanner.paper.engine import PaperTradingEngine

router = APIRouter(prefix="/paper", tags=["Paper Trading"])


@router.get("/portfolio")
def get_paper_portfolio():
    """Get current paper trading account state, open positions, and closed trades."""
    engine = PaperTradingEngine()
    acc = engine.account
    return {
        "initial_capital": acc.initial_capital,
        "cash_balance": acc.cash_balance,
        "current_equity": acc.current_equity,
        "total_invested": acc.total_invested,
        "total_current_value": acc.total_current_value,
        "realized_pnl": acc.realized_pnl,
        "unrealized_pnl": acc.total_unrealized_pnl,
        "total_return_pct": acc.total_return_pct,
        "total_fees_paid": acc.total_fees_paid,
        "win_rate_pct": acc.win_rate_pct,
        "open_positions": [asdict(p) for p in acc.open_positions],
        "trade_history": [asdict(t) for t in acc.trade_history],
    }


@router.post("/order")
def place_paper_order(req: PaperOrderRequest):
    """Place a simulated paper trading entry order."""
    engine = PaperTradingEngine()
    try:
        pos = engine.open_position(
            symbol=req.symbol,
            entry_price=req.entry_price,
            quantity=req.quantity,
            stop_loss=req.stop_loss,
            target1=req.target1,
            target2=req.target2,
            strategy=req.strategy,
            score=req.score,
        )
        return {"status": "SUCCESS", "position": asdict(pos)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/close")
def close_paper_order(req: PaperCloseRequest):
    """Close an open paper position at simulated exit price."""
    engine = PaperTradingEngine()
    try:
        trade = engine.close_position(
            position_id=req.position_id,
            exit_price=req.exit_price,
            exit_reason=req.exit_reason,
        )
        return {"status": "SUCCESS", "closed_trade": asdict(trade)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
