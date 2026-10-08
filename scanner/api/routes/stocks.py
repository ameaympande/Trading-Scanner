"""Stocks & OHLCV Data API Route."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException, Query

from scanner.data.loader import DataLoader
from scanner.data.universes import get_universe_stocks
from scanner.indicators.calculator import IndicatorCalculator

router = APIRouter(prefix="/stocks", tags=["Stocks & Charts"])


@router.get("")
def list_stocks(universe: str = Query(default="NIFTY_50")):
    """List all constituents in a given universe."""
    try:
        stocks = get_universe_stocks(universe)
        return [
            {
                "symbol": s.symbol,
                "company_name": s.company_name,
                "sector": s.sector,
                "exchange": s.exchange,
            }
            for s in stocks
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.get("/{symbol}/ohlcv")
def get_stock_ohlcv(
    symbol: str,
    days: int = Query(default=300, ge=30, le=1200),
):
    """
    Get historical OHLCV and indicator data for candlestick charting.
    """
    loader = DataLoader()
    calc = IndicatorCalculator()

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=int(days * 1.5))

    df, val_res = loader.fetch_daily_ohlcv(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        exchange="NSE",
        use_cache=True,
    )

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data available for symbol {symbol}")

    enriched = calc.calculate_all(df)
    candles = []
    for ts, row in enriched.iloc[-days:].iterrows():
        candles.append({
            "time": ts.strftime("%Y-%m-%d"),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": int(row["volume"]),
            "sma20": round(float(row["sma20"]), 2) if "sma20" in row and row["sma20"] == row["sma20"] else None,
            "sma50": round(float(row["sma50"]), 2) if "sma50" in row and row["sma50"] == row["sma50"] else None,
            "sma200": round(float(row["sma200"]), 2) if "sma200" in row and row["sma200"] == row["sma200"] else None,
            "ema20": round(float(row["ema20"]), 2) if "ema20" in row and row["ema20"] == row["ema20"] else None,
            "ema50": round(float(row["ema50"]), 2) if "ema50" in row and row["ema50"] == row["ema50"] else None,
            "rsi14": round(float(row["rsi14"]), 1) if "rsi14" in row and row["rsi14"] == row["rsi14"] else None,
            "atr14": round(float(row["atr14"]), 2) if "atr14" in row and row["atr14"] == row["atr14"] else None,
        })

    return {
        "symbol": symbol,
        "candles": candles,
        "is_valid": val_res.is_valid,
        "anomalies": [a.details for a in val_res.anomalies],
    }
