"""
Event-Driven Backtesting Engine.

Simulates trading with strict execution realism:
- Zero look-ahead bias: Signal triggered at Close of Day T enters ONLY at Day T+1 Open.
- Realistic transaction costs and slippage via IndianEquityCostCalculator.
- Stop loss and profit target checked against subsequent daily candles.
- Portfolio constraints enforced: max open positions, capital sizing per trade.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

from scanner.backtest.costs import IndianEquityCostCalculator, TradeFriction
from scanner.backtest.metrics import PerformanceMetrics, calculate_metrics
from scanner.config import MarketRegimeLabel, get_settings
from scanner.indicators.calculator import IndicatorCalculator
from scanner.risk.position_sizing import PositionSizer
from scanner.strategies.base import Strategy
from scanner.strategies.trend_pullback import TrendPullbackV1

if TYPE_CHECKING:
    pass


@dataclass
class SimulatedTrade:
    symbol: str
    entry_date: datetime.date | pd.Timestamp
    exit_date: datetime.date | pd.Timestamp
    entry_price: float
    exit_price: float
    stop_loss: float
    target1: float
    quantity: int
    gross_pnl: float
    net_pnl: float
    net_pnl_pct: float
    holding_days: int
    exit_reason: str  # TARGET, STOP_LOSS, TIME_STOP, INVALIDATION
    setup_score: int
    friction: TradeFriction
    turnover: float
    friction_cost: float


@dataclass
class BacktestResult:
    strategy_name: str
    universe_name: str
    start_date: datetime.date
    end_date: datetime.date
    initial_capital: float
    metrics: PerformanceMetrics
    trades: list[SimulatedTrade]
    warnings: list[str] = field(default_factory=list)


class BacktestEngine:
    """
    Executes realistic backtests across single stocks or universes.
    """

    def __init__(
        self,
        strategy: Strategy | None = None,
        cost_calculator: IndianEquityCostCalculator | None = None,
        position_sizer: PositionSizer | None = None,
        max_positions: int = 5,
        max_holding_bars: int = 20,
    ):
        self.strategy = strategy or TrendPullbackV1()
        self.cost_calculator = cost_calculator or IndianEquityCostCalculator()
        self.position_sizer = position_sizer or PositionSizer()
        self.max_positions = max_positions
        self.max_holding_bars = max_holding_bars
        self.settings = get_settings()

    def run_single_stock(
        self,
        symbol: str,
        df: pd.DataFrame,
        company_name: str = "",
        initial_capital: float = 100_000.0,
        risk_pct: float = 0.0075,
    ) -> BacktestResult:
        """
        Run backtest on a single stock's historical OHLCV DataFrame.
        """
        if df.empty or len(df) < self.settings.min_history_days + 10:
            return BacktestResult(
                strategy_name=self.strategy.name,
                universe_name=symbol,
                start_date=datetime.date.today(),
                end_date=datetime.date.today(),
                initial_capital=initial_capital,
                metrics=calculate_metrics([], initial_capital=initial_capital),
                trades=[],
                warnings=["Insufficient historical data"],
            )

        calc = IndicatorCalculator()
        enriched = calc.calculate_all(df)

        capital = initial_capital
        current_equity = initial_capital
        completed_trades: list[SimulatedTrade] = []
        trade_dicts: list[dict] = []
        daily_equity: dict[pd.Timestamp, float] = {}

        open_position: dict | None = None

        min_lookback = self.settings.min_history_days

        for i in range(min_lookback, len(enriched)):
            current_bar = enriched.iloc[i]
            current_dt = enriched.index[i]

            # 1. Manage currently open position first
            if open_position is not None:
                holding_days = open_position["bars_held"] + 1
                open_position["bars_held"] = holding_days
                entry_price = open_position["entry_price"]
                sl = open_position["stop_loss"]
                tgt = open_position["target1"]
                qty = open_position["quantity"]
                setup_score = open_position["score"]

                low = float(current_bar["low"])
                high = float(current_bar["high"])
                open_p = float(current_bar["open"])
                close_p = float(current_bar["close"])

                exit_triggered = False
                exit_price = close_p
                exit_reason = "TIME_STOP"

                # Check Stop Loss first (worst-case assumption)
                if low <= sl:
                    exit_triggered = True
                    # If opened below stop, exit at open (gap down), else at stop loss
                    exit_price = min(open_p, sl)
                    exit_reason = "STOP_LOSS"
                # Check Target 1
                elif high >= tgt:
                    exit_triggered = True
                    # If opened above target, exit at open (gap up), else at target
                    exit_price = max(open_p, tgt)
                    exit_reason = "TARGET"
                # Check time-based stop (max holding bars)
                elif holding_days >= self.max_holding_bars:
                    exit_triggered = True
                    exit_price = close_p
                    exit_reason = "TIME_STOP"

                if exit_triggered:
                    friction = self.cost_calculator.calculate_costs(
                        entry_price=entry_price,
                        exit_price=exit_price,
                        quantity=qty,
                    )
                    gross_pnl = (exit_price - entry_price) * qty
                    net_pnl = gross_pnl - friction.total_charges
                    net_pnl_pct = (net_pnl / (entry_price * qty)) * 100.0

                    trade = SimulatedTrade(
                        symbol=symbol,
                        entry_date=open_position["entry_date"],
                        exit_date=current_dt,
                        entry_price=round(entry_price, 2),
                        exit_price=round(exit_price, 2),
                        stop_loss=round(sl, 2),
                        target1=round(tgt, 2),
                        quantity=qty,
                        gross_pnl=round(gross_pnl, 2),
                        net_pnl=round(net_pnl, 2),
                        net_pnl_pct=round(net_pnl_pct, 2),
                        holding_days=holding_days,
                        exit_reason=exit_reason,
                        setup_score=setup_score,
                        friction=friction,
                        turnover=friction.buy_turnover + friction.sell_turnover,
                        friction_cost=friction.total_charges,
                    )
                    completed_trades.append(trade)
                    trade_dicts.append({
                        "symbol": symbol,
                        "entry_date": trade.entry_date,
                        "exit_date": trade.exit_date,
                        "net_pnl": trade.net_pnl,
                        "net_pnl_pct": trade.net_pnl_pct,
                        "holding_days": trade.holding_days,
                        "exit_reason": trade.exit_reason,
                        "turnover": trade.turnover,
                        "friction_cost": trade.friction_cost,
                    })

                    capital += net_pnl
                    current_equity = capital
                    open_position = None
                else:
                    # Mark-to-market equity for open trade
                    mtm_pnl = (close_p - entry_price) * qty
                    current_equity = capital + mtm_pnl

            # 2. Check for new entry signal (ONLY if no open position)
            # Evaluate using slice up to Day i-1 (strictly candle close of previous day)
            if open_position is None and i < len(enriched) - 1:
                hist_slice = enriched.iloc[:i]  # up to previous bar
                setup = self.strategy.evaluate(
                    symbol=symbol,
                    company_name=company_name or symbol,
                    df=hist_slice,
                    market_regime=MarketRegimeLabel.BULLISH,  # or benchmark evaluated up to i-1
                )

                if setup is not None:
                    # Execute entry at CURRENT bar Open (Day T+1 Open)
                    next_open = float(current_bar["open"])
                    pos = self.position_sizer.calculate_position(
                        symbol=symbol,
                        entry_price=next_open,
                        stop_loss=setup.stop_loss,
                        account_size=capital,
                        risk_per_trade_pct=risk_pct,
                    )
                    if pos.quantity > 0:
                        open_position = {
                            "entry_date": current_dt,
                            "entry_price": next_open,
                            "stop_loss": setup.stop_loss,
                            "target1": setup.target1,
                            "quantity": pos.quantity,
                            "score": setup.score,
                            "bars_held": 0,
                        }

            daily_equity[current_dt] = current_equity

        equity_series = pd.Series(daily_equity)
        metrics = calculate_metrics(
            trades=trade_dicts,
            daily_equity_series=equity_series,
            initial_capital=initial_capital,
        )

        warnings = ["Backtest uses single instrument. Diversification effects are excluded."]
        return BacktestResult(
            strategy_name=self.strategy.name,
            universe_name=symbol,
            start_date=enriched.index[min_lookback].date(),
            end_date=enriched.index[-1].date(),
            initial_capital=initial_capital,
            metrics=metrics,
            trades=completed_trades,
            warnings=warnings,
        )
