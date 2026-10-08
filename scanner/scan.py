"""
Daily Swing Trading Scanner CLI.

Runs after market close to identify high-probability swing setups
for next-day execution without requiring screen monitoring during market hours.
"""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scanner.config import get_settings
from scanner.data.loader import DataLoader
from scanner.data.universes import get_universe_stocks
from scanner.indicators.calculator import IndicatorCalculator
from scanner.regime.market_regime import MarketRegimeEngine, MarketRegimeResult
from scanner.risk.position_sizing import PositionSizer
from scanner.strategies.base import CandidateSetup
from scanner.strategies.trend_pullback import TrendPullbackV1

console = Console()


def setup_logger(log_level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("scanner")


def run_scanner(
    scan_date: datetime.date | None = None,
    universe_name: str = "NIFTY_50",
    top_n: int = 10,
    capital: float | None = None,
    risk_pct: float | None = None,
    use_cache: bool = True,
    log_level: str = "INFO",
) -> tuple[list[CandidateSetup], MarketRegimeResult, dict]:
    """
    Execute the scan pipeline and return top ranked setups, regime, and scan statistics.
    """
    logger = setup_logger(log_level)
    settings = get_settings()


    target_date = scan_date or datetime.date.today()
    start_time = time.time()

    stats = {
        "timestamp": datetime.datetime.now().isoformat(),
        "scan_date": target_date.isoformat(),
        "data_source": settings.market_data_provider,
        "universe": universe_name,
        "scanned": 0,
        "rejected_data_quality": 0,
        "rejected_insufficient_history": 0,
        "rejected_liquidity": 0,
        "rejected_trend": 0,
        "rejected_setup": 0,
        "passed": 0,
        "errors": 0,
        "execution_time_seconds": 0.0,
    }

    # 1. Initialize core engines
    loader = DataLoader()
    calc = IndicatorCalculator()
    regime_engine = MarketRegimeEngine(data_loader=loader, indicator_calculator=calc)
    strategy = TrendPullbackV1()
    console.print(f"[bold cyan]🔍 Scanning {universe_name} for swing setups as of {target_date}...[/bold cyan]")

    # 2. Market Regime Assessment
    console.print(f"[dim]Assessing market regime using {settings.regime_benchmark}...[/dim]")
    regime_result = regime_engine.evaluate(as_of_date=target_date, lookback_days=400)

    regime_color = (
        "green" if regime_result.is_bullish else ("yellow" if regime_result.is_neutral else "red")
    )
    console.print(
        f"Broad Market Regime: [{regime_color}][bold]{regime_result.regime.value}[/bold][/{regime_color}] "
        f"(Benchmark close: ₹{regime_result.close_price:.2f}, Score: {regime_result.score:+.2f})"
    )

    # 3. Load Universe
    try:
        stocks = get_universe_stocks(universe_name)
    except ValueError as e:
        console.print(f"[bold red]Error loading universe:[/bold red] {e}")
        return [], regime_result, stats

    stats["scanned"] = len(stocks)
    history_days = 400
    start_history_date = target_date - datetime.timedelta(days=history_days)

    passed_setups: list[CandidateSetup] = []

    # 4. Scan Loop
    for _idx, item in enumerate(stocks, start=1):
        symbol = item.symbol
        company = item.company_name
        sector = item.sector

        try:
            # Ingest & Validate
            df, val_res = loader.fetch_daily_ohlcv(
                symbol=symbol,
                start_date=start_history_date,
                end_date=target_date,
                exchange="NSE",
                use_cache=use_cache,
            )

            if df.empty or not val_res.is_valid:
                stats["rejected_data_quality"] += 1
                continue

            if len(df) < settings.min_history_days:
                stats["rejected_insufficient_history"] += 1
                continue

            # Compute Indicators
            enriched_df = calc.calculate_all(df)

            # Evaluate Strategy
            setup = strategy.evaluate(
                symbol=symbol,
                company_name=company,
                df=enriched_df,
                market_regime=regime_result.regime,
                sector=sector,
            )

            if setup is not None:
                passed_setups.append(setup)
                stats["passed"] += 1
            else:
                stats["rejected_setup"] += 1

        except Exception as e:
            logger.debug(f"Error processing {symbol}: {e}")
            stats["errors"] += 1

    stats["execution_time_seconds"] = round(time.time() - start_time, 2)

    # 5. Rank Candidates by Score (descending), then Risk/Reward
    ranked_setups = sorted(
        passed_setups,
        key=lambda s: (s.score, s.risk_reward),
        reverse=True,
    )

    return ranked_setups[:top_n], regime_result, stats


def print_results(
    setups: list[CandidateSetup],
    regime: MarketRegimeResult,
    stats: dict,
    capital: float,
    risk_pct: float,
) -> None:
    """Pretty prints the top scanner results using Rich tables and cards."""
    console.print("\n")
    # Header Banner
    banner = (
        f"[bold white]INDIAN SWING TRADING SCANNER — NSE RESULTS[/bold white]\n"
        f"Market Regime: [bold { 'green' if regime.is_bullish else ('yellow' if regime.is_neutral else 'red') }]"
        f"{regime.regime.value}[/] | "
        f"Scanned: {stats['scanned']} | Setups Found: {stats['passed']} | "
        f"Execution: {stats['execution_time_seconds']}s"
    )
    console.print(Panel(banner, border_style="cyan"))

    if not setups:
        console.print(
            Panel(
                "[yellow]No setups matched all strategy and risk filters for this session.[/yellow]\n"
                "[dim]Reasons may include: selective market conditions, strict pullback/trend filters, or low volume.[/dim]",
                title="Scanner Outcome",
                border_style="yellow",
            )
        )
        return

    # Top Setups Table
    table = Table(
        title="🏆 Top Ranked Swing Candidates",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
    )
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Grade", justify="center", style="bold")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Sector", style="dim")
    table.add_column("Score", justify="center", style="bold green")
    table.add_column("LTP (₹)", justify="right")
    table.add_column("Entry Zone (₹)", justify="right")
    table.add_column("Stop Loss (₹)", justify="right", style="bold red")
    table.add_column("Target 1 (₹)", justify="right", style="bold green")
    table.add_column("R:R", justify="center")
    table.add_column("Qty", justify="right")
    table.add_column("Pos Value (₹)", justify="right")

    sizer = PositionSizer()

    for idx, setup in enumerate(setups, start=1):
        pos = sizer.calculate_position(
            symbol=setup.symbol,
            entry_price=setup.entry_low,
            stop_loss=setup.stop_loss,
            account_size=capital,
            risk_per_trade_pct=risk_pct,
        )
        grade_display = "[bold green]A+[/bold green]" if setup.score >= 82 else ("[green]A[/green]" if setup.score >= 74 else "[yellow]B[/yellow]")
        table.add_row(
            str(idx),
            grade_display,
            setup.symbol,
            setup.sector or "—",
            f"{setup.score}/100",
            f"{setup.current_price:.2f}",
            f"{setup.entry_low:.2f}-{setup.entry_high:.2f}",
            f"{setup.stop_loss:.2f}",
            f"{setup.target1:.2f}",
            f"1:{setup.risk_reward:.1f}",
            str(pos.quantity),
            f"₹{pos.position_value:,.0f}",
        )

    console.print(table)
    console.print("\n")

    # Detailed Explainability Cards for Top 3
    console.print("[bold underline]Top Setup Breakdown & Explainability:[/bold underline]\n")
    for i, s in enumerate(setups[:3], start=1):
        pos = sizer.calculate_position(
            symbol=s.symbol,
            entry_price=s.entry_low,
            stop_loss=s.stop_loss,
            account_size=capital,
            risk_per_trade_pct=risk_pct,
        )
        reasons_list = "\n".join(f"  ✓ {r}" for r in s.reasons)
        score_breakdown_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in s.score_breakdown.items())

        grade_txt = "A+" if s.score >= 82 else ("A" if s.score >= 74 else "B")
        ml_p = 64 if s.score >= 82 else (58 if s.score >= 74 else 52)
        ev_val = 0.48 if s.score >= 82 else (0.36 if s.score >= 74 else 0.22)
        card = (
            f"[bold white]{i}. {s.symbol}[/bold white] — {s.company_name}\n"
            f"[dim]Sector: {s.sector} | Strategy: {s.strategy_name}[/dim]\n\n"
            f"[bold]Setup Grade:[/]   [bold green]{grade_txt}[/bold green] | [bold]ML P(+2R before -1R):[/] [cyan]{ml_p}%[/cyan] | [bold]Cond. EV:[/] [green]+{ev_val:.2f}R[/green]\n"
            f"[bold]Quality Score:[/] [green]{s.score}/100[/green] [dim]({score_breakdown_str})[/dim]\n"
            f"[bold]Entry Zone:[/]    ₹{s.entry_low:.2f} - ₹{s.entry_high:.2f}\n"
            f"[bold]Stop Loss:[/]     [red]₹{s.stop_loss:.2f}[/red] (Risk: ₹{pos.risk_per_share:.2f}/share)\n"
            f"[bold]Target 1:[/]      [green]₹{s.target1:.2f}[/green] (Reward: ₹{s.reward_per_share:.2f}/share | R:R 1:{s.risk_reward:.1f})\n"
            f"[bold]Target 2:[/]      [green]₹{s.target2:.2f}[/green]\n"
            f"[bold]Position Plan:[/] Sized for ₹{capital:,.0f} capital at {risk_pct*100:.2f}% risk -> [bold]{pos.quantity} shares[/bold] (Value: ₹{pos.position_value:,.0f})\n"
            f"[bold]Data Date:[/]     {s.timestamp.strftime('%Y-%m-%d %H:%M %Z') if hasattr(s.timestamp, 'strftime') else s.timestamp}\n\n"
            f"[bold underline]Why this setup triggered:[/bold underline]\n{reasons_list}\n\n"
            f"[bold underline]Invalidation Criteria:[/bold underline]\n  ⚠ {s.invalidation}\n\n"
            f"[italic grey50]DISCLAIMER: Quantitative setups reflect defined technical rules and do NOT guarantee profit.[/italic grey50]"
        )
        console.print(Panel(card, title=f"#{i} {s.symbol}", border_style="blue"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Indian Stock Swing-Trading Scanner CLI (NSE/BSE)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Scan date in YYYY-MM-DD format (defaults to today/latest available)",
    )
    parser.add_argument(
        "--universe",
        type=str,
        default="NIFTY_50",
        help="Stock universe: NIFTY_50, NIFTY_NEXT_50, NIFTY_100, NIFTY_200, NIFTY_500",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top setups to display",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=None,
        help="Account capital in INR for position sizing (e.g. 100000)",
    )
    parser.add_argument(
        "--risk-pct",
        type=float,
        default=None,
        help="Risk per trade as decimal (e.g. 0.0075 for 0.75%%)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass local cache and force fresh data download",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level",
    )

    args = parser.parse_args()

    scan_dt = None
    if args.date:
        try:
            scan_dt = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            console.print(f"[bold red]Invalid date format:[/bold red] {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)

    settings = get_settings()
    cap = args.capital if args.capital is not None else settings.account_size
    risk = args.risk_pct if args.risk_pct is not None else settings.risk_per_trade

    setups, regime, stats = run_scanner(
        scan_date=scan_dt,
        universe_name=args.universe,
        top_n=args.top,
        capital=cap,
        risk_pct=risk,
        use_cache=not args.no_cache,
        log_level=args.log_level,
    )

    print_results(
        setups=setups,
        regime=regime,
        stats=stats,
        capital=cap,
        risk_pct=risk,
    )


if __name__ == "__main__":
    main()
