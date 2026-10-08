"""
Monte Carlo Simulation & Bootstrap Confidence Intervals.

Evaluates strategy robustness against sequence risk, calculates:
- Probability of Drawdown > X%
- Risk of Ruin estimation
- Bootstrap 95% Confidence Intervals for Expectancy, Win Rate, and Profit Factor
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BootstrapMetricCI:
    estimate: float
    lower_bound_95: float
    upper_bound_95: float


@dataclass
class MonteCarloSimulationResult:
    iterations: int
    num_trades: int
    median_max_drawdown_pct: float
    drawdown_95th_percentile_pct: float
    worst_case_drawdown_pct: float
    risk_of_ruin_pct: float  # Probability of drawdown > 25%
    median_ending_equity: float
    equity_10th_percentile: float
    equity_90th_percentile: float
    expectancy_ci: BootstrapMetricCI
    win_rate_ci: BootstrapMetricCI
    profit_factor_ci: BootstrapMetricCI
    simulation_curves: list[list[float]] = field(default_factory=list)


class MonteCarloEngine:
    """
    Simulates sequence permutations of historical trades to evaluate tail risks.
    """

    def __init__(self, iterations: int = 1000):
        self.iterations = iterations

    def run_simulation(
        self,
        trade_returns_r: list[float],
        initial_capital: float = 100_000.0,
        risk_per_trade_pct: float = 0.0075,
        ruin_drawdown_threshold: float = 25.0,
    ) -> MonteCarloSimulationResult:
        """
        Runs Monte Carlo trade reshuffling and bootstrap confidence calculations.
        """
        if not trade_returns_r or len(trade_returns_r) < 5:
            empty_ci = BootstrapMetricCI(0.0, 0.0, 0.0)
            return MonteCarloSimulationResult(
                iterations=0,
                num_trades=0,
                median_max_drawdown_pct=0.0,
                drawdown_95th_percentile_pct=0.0,
                worst_case_drawdown_pct=0.0,
                risk_of_ruin_pct=0.0,
                median_ending_equity=initial_capital,
                equity_10th_percentile=initial_capital,
                equity_90th_percentile=initial_capital,
                expectancy_ci=empty_ci,
                win_rate_ci=empty_ci,
                profit_factor_ci=empty_ci,
            )

        returns = np.array(trade_returns_r, dtype=float)
        n_trades = len(returns)

        # 1. Bootstrap Confidence Intervals
        bootstrap_ev = []
        bootstrap_wr = []
        bootstrap_pf = []

        for _ in range(self.iterations):
            sample = np.random.choice(returns, size=n_trades, replace=True)
            ev = float(np.mean(sample))
            wr = float(np.mean(sample > 0) * 100.0)

            wins = sample[sample > 0]
            losses = np.abs(sample[sample < 0])
            gross_win = float(np.sum(wins)) if len(wins) > 0 else 0.0
            gross_loss = float(np.sum(losses)) if len(losses) > 0 else 0.0
            pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)

            bootstrap_ev.append(ev)
            bootstrap_wr.append(wr)
            bootstrap_pf.append(pf)

        ev_ci = BootstrapMetricCI(
            estimate=round(float(np.mean(returns)), 3),
            lower_bound_95=round(float(np.percentile(bootstrap_ev, 2.5)), 3),
            upper_bound_95=round(float(np.percentile(bootstrap_ev, 97.5)), 3),
        )
        wr_ci = BootstrapMetricCI(
            estimate=round(float(np.mean(returns > 0) * 100.0), 1),
            lower_bound_95=round(float(np.percentile(bootstrap_wr, 2.5)), 1),
            upper_bound_95=round(float(np.percentile(bootstrap_wr, 97.5)), 1),
        )
        pf_ci = BootstrapMetricCI(
            estimate=round(float(np.median(bootstrap_pf)), 2),
            lower_bound_95=round(float(np.percentile(bootstrap_pf, 2.5)), 2),
            upper_bound_95=round(float(np.percentile(bootstrap_pf, 97.5)), 2),
        )

        # 2. Monte Carlo Sequence Reshuffling for Drawdowns
        max_drawdowns = []
        ending_equities = []
        sample_curves: list[list[float]] = []

        ruin_count = 0

        for it in range(self.iterations):
            # Reshuffle order without replacement
            shuffled_r = np.random.permutation(returns)

            # Simulate equity compounding with fixed percentage risk
            eq = initial_capital
            peak = initial_capital
            max_dd = 0.0
            curve = [eq]

            for r in shuffled_r:
                risk_amt = eq * risk_per_trade_pct
                pnl = risk_amt * r
                eq = max(100.0, eq + pnl)

                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

                curve.append(round(eq, 2))

            max_drawdowns.append(max_dd)
            ending_equities.append(eq)

            if max_dd >= ruin_drawdown_threshold:
                ruin_count += 1

            if it < 8:  # Store first 8 curves for visualization
                # Sample down curve if long
                step = max(1, len(curve) // 25)
                sample_curves.append(curve[::step])

        return MonteCarloSimulationResult(
            iterations=self.iterations,
            num_trades=n_trades,
            median_max_drawdown_pct=round(float(np.median(max_drawdowns)), 2),
            drawdown_95th_percentile_pct=round(float(np.percentile(max_drawdowns, 95)), 2),
            worst_case_drawdown_pct=round(float(np.max(max_drawdowns)), 2),
            risk_of_ruin_pct=round((ruin_count / self.iterations) * 100.0, 2),
            median_ending_equity=round(float(np.median(ending_equities)), 2),
            equity_10th_percentile=round(float(np.percentile(ending_equities, 10)), 2),
            equity_90th_percentile=round(float(np.percentile(ending_equities, 90)), 2),
            expectancy_ci=ev_ci,
            win_rate_ci=wr_ci,
            profit_factor_ci=pf_ci,
            simulation_curves=sample_curves,
        )
