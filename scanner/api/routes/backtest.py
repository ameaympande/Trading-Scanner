"""Backtest API Route."""

from __future__ import annotations

import datetime
from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from scanner.api.schemas import BacktestRequest
from scanner.backtest.engine import BacktestEngine
from scanner.backtest.walk_forward import WalkForwardEngine
from scanner.data.loader import DataLoader

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


@router.post("/run")
def run_backtest(req: BacktestRequest):
    """Run historical backtest on a single stock."""
    loader = DataLoader()
    engine = BacktestEngine()

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=req.lookback_days + 300)

    df, _ = loader.fetch_daily_ohlcv(
        symbol=req.symbol,
        start_date=start_date,
        end_date=end_date,
        exchange="NSE",
        use_cache=True,
    )

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data available for symbol {req.symbol}")

    res = engine.run_single_stock(
        symbol=req.symbol,
        df=df,
        initial_capital=req.initial_capital,
        risk_pct=req.risk_pct,
    )

    # Format trades for JSON
    trades_json = []
    for t in res.trades:
        trades_json.append({
            "symbol": t.symbol,
            "entry_date": t.entry_date.strftime("%Y-%m-%d") if hasattr(t.entry_date, "strftime") else str(t.entry_date),
            "exit_date": t.exit_date.strftime("%Y-%m-%d") if hasattr(t.exit_date, "strftime") else str(t.exit_date),
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "stop_loss": t.stop_loss,
            "target1": t.target1,
            "quantity": t.quantity,
            "gross_pnl": t.gross_pnl,
            "net_pnl": t.net_pnl,
            "net_pnl_pct": t.net_pnl_pct,
            "holding_days": t.holding_days,
            "exit_reason": t.exit_reason,
            "friction_cost": t.friction_cost,
        })

    return {
        "strategy_name": res.strategy_name,
        "symbol": req.symbol,
        "start_date": str(res.start_date),
        "end_date": str(res.end_date),
        "metrics": asdict(res.metrics),
        "trades": trades_json,
        "warnings": res.warnings,
        "disclaimer": "Historical backtests do not guarantee future performance. Strategy assumes execution at next day open with slippage and realistic fees.",
    }


@router.post("/walk-forward")
def run_walk_forward(req: BacktestRequest):
    """Run Walk-Forward train vs out-of-sample split analysis."""
    loader = DataLoader()
    wf_engine = WalkForwardEngine()

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=max(req.lookback_days, 600) + 300)

    df, _ = loader.fetch_daily_ohlcv(
        symbol=req.symbol,
        start_date=start_date,
        end_date=end_date,
        exchange="NSE",
        use_cache=True,
    )

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {req.symbol}")

    wf_res = wf_engine.run_split(
        symbol=req.symbol,
        df=df,
        initial_capital=req.initial_capital,
    )

    return {
        "symbol": req.symbol,
        "strategy": wf_res.strategy_name,
        "in_sample": {
            "period": f"{wf_res.in_sample.start_date} to {wf_res.in_sample.end_date}",
            "return_pct": wf_res.in_sample_return_pct,
            "sharpe": wf_res.in_sample_sharpe,
            "win_rate": wf_res.in_sample_win_rate,
            "total_trades": wf_res.in_sample.result.metrics.total_trades,
            "max_drawdown_pct": wf_res.in_sample.result.metrics.max_drawdown_pct,
        },
        "out_of_sample": {
            "period": f"{wf_res.out_of_sample.start_date} to {wf_res.out_of_sample.end_date}",
            "return_pct": wf_res.out_of_sample_return_pct,
            "sharpe": wf_res.out_of_sample_sharpe,
            "win_rate": wf_res.out_of_sample_win_rate,
            "total_trades": wf_res.out_of_sample.result.metrics.total_trades,
            "max_drawdown_pct": wf_res.out_of_sample.result.metrics.max_drawdown_pct,
        },
        "robustness_ratio": wf_res.robustness_ratio,
        "warning": wf_res.warning,
    }
