"""
Backtest Performance Metrics Calculator.

Computes comprehensive hedge-fund style risk and return metrics:
- Total Return, CAGR
- Win Rate, Profit Factor, Expectancy
- Max Drawdown (%), Max Drawdown Duration (days)
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Average Win / Average Loss ratio
- Maximum consecutive losses
- Equity & Drawdown curves
- Monthly & Annual returns breakdown
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    initial_capital: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    expectancy_per_trade: float
    average_trade_pnl_pct: float
    average_win_pct: float
    average_loss_pct: float
    win_loss_ratio: float
    largest_win_pct: float
    largest_loss_pct: float
    max_consecutive_losses: int
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    average_holding_period_days: float
    total_turnover: float
    total_transaction_costs: float
    equity_curve: list[dict] = field(default_factory=list)
    monthly_returns: dict[str, dict[str, float]] = field(default_factory=dict)
    annual_returns: dict[str, float] = field(default_factory=dict)


def calculate_metrics(
    trades: list[dict],
    daily_equity_series: pd.Series | None = None,
    initial_capital: float = 100_000.0,
    risk_free_rate: float = 0.065,  # 6.5% Indian 10y G-Sec yield
) -> PerformanceMetrics:
    """
    Computes all standard backtesting metrics from a list of completed trades
    and a daily equity series.
    """
    if not trades:
        return PerformanceMetrics(
            initial_capital=initial_capital,
            final_equity=initial_capital,
            total_return_pct=0.0,
            cagr_pct=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate_pct=0.0,
            profit_factor=0.0,
            expectancy_per_trade=0.0,
            average_trade_pnl_pct=0.0,
            average_win_pct=0.0,
            average_loss_pct=0.0,
            win_loss_ratio=0.0,
            largest_win_pct=0.0,
            largest_loss_pct=0.0,
            max_consecutive_losses=0,
            max_drawdown_pct=0.0,
            max_drawdown_duration_days=0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            average_holding_period_days=0.0,
            total_turnover=0.0,
            total_transaction_costs=0.0,
            equity_curve=[],
            monthly_returns={},
            annual_returns={},
        )

    df_trades = pd.DataFrame(trades)
    pnls = df_trades["net_pnl"].values
    pnl_pcts = df_trades["net_pnl_pct"].values

    total_trades = len(pnls)
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    winning_trades = len(wins)
    losing_trades = len(losses)
    win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

    gross_profits = float(wins.sum()) if len(wins) > 0 else 0.0
    gross_losses = float(abs(losses.sum())) if len(losses) > 0 else 0.0
    profit_factor = round(gross_profits / gross_losses, 2) if gross_losses > 0 else (99.0 if gross_profits > 0 else 0.0)

    avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0.0
    win_loss_ratio = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0

    avg_win_pct = float(pnl_pcts[pnl_pcts > 0].mean()) if (pnl_pcts > 0).any() else 0.0
    avg_loss_pct = float(pnl_pcts[pnl_pcts < 0].mean()) if (pnl_pcts < 0).any() else 0.0

    expectancy = float(pnls.mean())
    avg_trade_pnl_pct = float(pnl_pcts.mean())

    largest_win_pct = float(pnl_pcts.max()) if len(pnl_pcts) > 0 else 0.0
    largest_loss_pct = float(pnl_pcts.min()) if len(pnl_pcts) > 0 else 0.0

    # Max consecutive losses
    max_consec_losses = 0
    current_consec = 0
    for p in pnls:
        if p < 0:
            current_consec += 1
            max_consec_losses = max(max_consec_losses, current_consec)
        else:
            current_consec = 0

    avg_holding = float(df_trades["holding_days"].mean()) if "holding_days" in df_trades else 0.0
    total_costs = float(df_trades["friction_cost"].sum()) if "friction_cost" in df_trades else 0.0
    total_turnover = float(df_trades["turnover"].sum()) if "turnover" in df_trades else 0.0

    # Equity Curve & Drawdown Analysis
    if daily_equity_series is not None and not daily_equity_series.empty:
        equity_series = daily_equity_series
    else:
        # Construct approximate equity series from trade cumulative pnls
        cum_pnl = np.cumsum(pnls)
        equity_series = pd.Series(initial_capital + cum_pnl)

    final_equity = float(equity_series.iloc[-1])
    total_return_pct = round(((final_equity - initial_capital) / initial_capital) * 100.0, 2)

    # Drawdown
    rolling_max = equity_series.cummax()
    drawdowns = (equity_series - rolling_max) / rolling_max * 100.0
    max_drawdown = float(abs(drawdowns.min())) if len(drawdowns) > 0 else 0.0

    # Drawdown duration
    max_dd_duration = 0
    cur_dd_duration = 0
    for dd in drawdowns:
        if dd < 0:
            cur_dd_duration += 1
            max_dd_duration = max(max_dd_duration, cur_dd_duration)
        else:
            cur_dd_duration = 0

    # Sharpe & Sortino & CAGR
    if isinstance(equity_series.index, pd.DatetimeIndex) and len(equity_series) > 1:
        days_span = (equity_series.index[-1] - equity_series.index[0]).days
        years_span = max(0.1, days_span / 365.25)
        cagr = round(((final_equity / initial_capital) ** (1.0 / years_span) - 1.0) * 100.0, 2)

        daily_returns = equity_series.pct_change().dropna()
        excess_daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1.0
        excess_returns = daily_returns - excess_daily_rf

        std_dev = daily_returns.std()
        sharpe = round(float(np.sqrt(252) * excess_returns.mean() / std_dev), 2) if std_dev > 0 else 0.0

        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std()
        sortino = round(float(np.sqrt(252) * excess_returns.mean() / downside_std), 2) if downside_std > 0 else 0.0
        calmar = round(cagr / max_drawdown, 2) if max_drawdown > 0 else 0.0

        # Monthly & Annual returns
        monthly_table: dict[str, dict[str, float]] = {}
        annual_table: dict[str, float] = {}
        try:
            monthly_resampled = equity_series.resample("ME").last().pct_change().dropna() * 100.0
            for dt, val in monthly_resampled.items():
                yr = str(dt.year)
                mo = dt.strftime("%b")
                if yr not in monthly_table:
                    monthly_table[yr] = {}
                monthly_table[yr][mo] = round(val, 2)

            annual_resampled = equity_series.resample("YE").last().pct_change().dropna() * 100.0
            for dt, val in annual_resampled.items():
                annual_table[str(dt.year)] = round(val, 2)
        except Exception:
            pass

    else:
        cagr = total_return_pct
        sharpe = 0.0
        sortino = 0.0
        calmar = 0.0
        monthly_table = {}
        annual_table = {}

    # Format points for UI chart
    equity_curve_points = []
    for idx_val, val in equity_series.items():
        dt_str = idx_val.strftime("%Y-%m-%d") if hasattr(idx_val, "strftime") else str(idx_val)
        peak = float(rolling_max.loc[idx_val]) if idx_val in rolling_max else val
        dd = float(drawdowns.loc[idx_val]) if idx_val in drawdowns else 0.0
        equity_curve_points.append({
            "date": dt_str,
            "equity": round(float(val), 2),
            "peak": round(peak, 2),
            "drawdown_pct": round(dd, 2),
        })

    return PerformanceMetrics(
        initial_capital=initial_capital,
        final_equity=round(final_equity, 2),
        total_return_pct=total_return_pct,
        cagr_pct=cagr,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate_pct=round(win_rate, 1),
        profit_factor=profit_factor,
        expectancy_per_trade=round(expectancy, 2),
        average_trade_pnl_pct=round(avg_trade_pnl_pct, 2),
        average_win_pct=round(avg_win_pct, 2),
        average_loss_pct=round(avg_loss_pct, 2),
        win_loss_ratio=win_loss_ratio,
        largest_win_pct=round(largest_win_pct, 2),
        largest_loss_pct=round(largest_loss_pct, 2),
        max_consecutive_losses=max_consec_losses,
        max_drawdown_pct=round(max_drawdown, 2),
        max_drawdown_duration_days=max_dd_duration,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        calmar_ratio=calmar,
        average_holding_period_days=round(avg_holding, 1),
        total_turnover=round(total_turnover, 2),
        total_transaction_costs=round(total_costs, 2),
        equity_curve=equity_curve_points,
        monthly_returns=monthly_table,
        annual_returns=annual_table,
    )
