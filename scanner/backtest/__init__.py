"""Backtesting engine module."""

from scanner.backtest.costs import IndianEquityCostCalculator
from scanner.backtest.engine import BacktestEngine, BacktestResult, SimulatedTrade
from scanner.backtest.metrics import PerformanceMetrics, calculate_metrics
from scanner.backtest.walk_forward import WalkForwardEngine, WalkForwardResult

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "IndianEquityCostCalculator",
    "PerformanceMetrics",
    "SimulatedTrade",
    "WalkForwardEngine",
    "WalkForwardResult",
    "calculate_metrics",
]
