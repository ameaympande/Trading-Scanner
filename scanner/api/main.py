"""
FastAPI Backend Application Entry Point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scanner.api.routes import backtest, paper, regime, research, scanner, stocks
from scanner.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    settings = get_settings()
    settings.data_cache_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown actions


app = FastAPI(
    title="Indian Stock Swing-Trading Scanner API",
    description="Production-grade swing-trading scanner and research platform for NSE/BSE stocks.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(scanner.router, prefix="/api")
app.include_router(regime.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(paper.router, prefix="/api")
app.include_router(research.router, prefix="/api")


@app.get("/api/health")
def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "market": settings.market.value,
        "provider": settings.market_data_provider,
        "timezone": settings.timezone,
        "live_trading_enabled": settings.live_trading_enabled,
        "version": "0.1.0",
    }


def start_server():
    import uvicorn
    uvicorn.run("scanner.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
