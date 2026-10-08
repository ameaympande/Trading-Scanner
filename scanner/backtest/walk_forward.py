"""
Walk-Forward Validation Engine.

Splits data into In-Sample (Train/Validation) and Out-Of-Sample (OOS) windows
to evaluate real-world strategy robustness and prevent curve-fitting.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

import pandas as pd

from scanner.backtest.engine import BacktestEngine, BacktestResult


@dataclass
class WalkForwardWindow:
    name: str  # "IN_SAMPLE" or "OUT_OF_SAMPLE"
    start_date: datetime.date
    end_date: datetime.date
    result: BacktestResult


@dataclass
class WalkForwardResult:
    symbol: str
    strategy_name: str
    in_sample: WalkForwardWindow
    out_of_sample: WalkForwardWindow
    in_sample_return_pct: float
    out_of_sample_return_pct: float
    in_sample_sharpe: float
    out_of_sample_sharpe: float
    in_sample_win_rate: float
    out_of_sample_win_rate: float
    robustness_ratio: float  # OOS return / IS return annualized
    warning: str


class WalkForwardEngine:
    """Executes Walk-Forward validation on historical data."""

    def __init__(self, backtest_engine: BacktestEngine | None = None):
        self.engine = backtest_engine or BacktestEngine()

    def run_split(
        self,
        symbol: str,
        df: pd.DataFrame,
        split_date: datetime.date | None = None,
        company_name: str = "",
        initial_capital: float = 100_000.0,
    ) -> WalkForwardResult:
        """
        Splits dataset at split_date into In-Sample and Out-Of-Sample periods.
        Default split: 70% In-Sample, 30% Out-Of-Sample.
        """
        if df.empty or len(df) < 300:
            raise ValueError(f"Insufficient data for walk-forward testing: {len(df)} rows.")

        if split_date is None:
            split_idx = int(len(df) * 0.70)
            split_dt = df.index[split_idx].date()
        else:
            split_dt = split_date

        df_is = df.loc[df.index.date <= split_dt].copy()
        # Out of sample includes lookback buffer for indicators
        lookback_buffer = 260
        split_loc = df.index.get_indexer([pd.Timestamp(split_dt, tz="UTC")], method="nearest")[0]
        oos_start_idx = max(0, split_loc - lookback_buffer)
        df_oos = df.iloc[oos_start_idx:].copy()

        # Run Backtests
        res_is = self.engine.run_single_stock(
            symbol=symbol,
            df=df_is,
            company_name=company_name,
            initial_capital=initial_capital,
        )

        res_oos = self.engine.run_single_stock(
            symbol=symbol,
            df=df_oos,
            company_name=company_name,
            initial_capital=initial_capital,
        )

        is_ret = res_is.metrics.total_return_pct
        oos_ret = res_oos.metrics.total_return_pct
        is_sharpe = res_is.metrics.sharpe_ratio
        oos_sharpe = res_oos.metrics.sharpe_ratio

        robustness = round(oos_ret / is_ret, 2) if is_ret > 0 else 0.0

        warning_text = (
            "NOTICE: Out-of-sample testing guards against look-ahead and curve fitting. "
            "However, survivorship bias may still exist if testing only surviving symbols."
        )

        return WalkForwardResult(
            symbol=symbol,
            strategy_name=self.engine.strategy.name,
            in_sample=WalkForwardWindow(
                name="IN_SAMPLE",
                start_date=df_is.index[0].date(),
                end_date=split_dt,
                result=res_is,
            ),
            out_of_sample=WalkForwardWindow(
                name="OUT_OF_SAMPLE",
                start_date=split_dt,
                end_date=df.index[-1].date(),
                result=res_oos,
            ),
            in_sample_return_pct=is_ret,
            out_of_sample_return_pct=oos_ret,
            in_sample_sharpe=is_sharpe,
            out_of_sample_sharpe=oos_sharpe,
            in_sample_win_rate=res_is.metrics.win_rate_pct,
            out_of_sample_win_rate=res_oos.metrics.win_rate_pct,
            robustness_ratio=robustness,
            warning=warning_text,
        )
