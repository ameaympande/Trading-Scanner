"""
Notification Provider Abstraction and Implementations.
Supports alerting after market close for people reviewing setups for the next day.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from rich.console import Console
from rich.panel import Panel

from scanner.config import get_settings
from scanner.strategies.base import CandidateSetup

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract interface for notifying about scan setups."""

    @abstractmethod
    def send_setup_alert(self, setup: CandidateSetup) -> bool:
        """Send an individual setup alert."""
        ...

    @abstractmethod
    def send_daily_summary(
        self,
        market_regime: str,
        setups: list[CandidateSetup],
        total_scanned: int,
    ) -> bool:
        """Send end-of-day summary report."""
        ...


class ConsoleNotifier(NotificationProvider):
    """Outputs formatted alerts to standard output using Rich."""

    def __init__(self) -> None:
        self.console = Console()

    def send_setup_alert(self, setup: CandidateSetup) -> bool:
        content = (
            f"[bold cyan]NEW SETUP DETECTED[/bold cyan]\n"
            f"[bold white]{setup.symbol}[/bold white] ({setup.company_name})\n"
            f"Strategy: [yellow]{setup.strategy_name}[/yellow] | Score: [bold green]{setup.score}/100[/bold green]\n"
            f"Market Regime: [magenta]{setup.market_regime.value}[/magenta]\n\n"
            f"Entry Zone: ₹{setup.entry_low:.2f} - ₹{setup.entry_high:.2f}\n"
            f"Stop Loss:  [bold red]₹{setup.stop_loss:.2f}[/bold red]\n"
            f"Target 1:   [bold green]₹{setup.target1:.2f}[/bold green] (R:R {setup.risk_reward:.1f})\n"
            f"Target 2:   [bold green]₹{setup.target2:.2f}[/bold green]\n"
            f"Holding:    {setup.expected_holding_period}\n\n"
            f"[bold underline]Why it triggered:[/bold underline]\n"
            + "\n".join(f"  ✓ {r}" for r in setup.reasons)
            + f"\n\n[bold underline]Invalidation:[/bold underline]\n  ⚠ {setup.invalidation}\n\n"
            f"[italic grey50]Review required before placing any order. Never risk more than configured.[/italic grey50]"
        )
        self.console.print(Panel(content, title=f"Swing Signal: {setup.symbol}", border_style="cyan"))
        return True

    def send_daily_summary(
        self,
        market_regime: str,
        setups: list[CandidateSetup],
        total_scanned: int,
    ) -> bool:
        summary_text = (
            f"[bold]EOD SCAN REPORT[/bold]\n"
            f"Market Regime: [magenta]{market_regime}[/magenta]\n"
            f"Total Instruments Scanned: {total_scanned}\n"
            f"Top Setups Found: {len(setups)}\n\n"
        )
        for i, s in enumerate(setups[:10], start=1):
            summary_text += f"{i}. [bold]{s.symbol}[/bold] — Score: [green]{s.score}/100[/green] | Entry: ₹{s.entry_low:.2f} | SL: ₹{s.stop_loss:.2f} | R:R: 1:{s.risk_reward:.1f}\n"

        self.console.print(Panel(summary_text, title="Daily Swing Market Summary", border_style="green"))
        return True


def get_notifier() -> NotificationProvider:
    """Factory to retrieve configured notification provider."""
    settings = get_settings()
    provider_name = settings.notification_provider.lower()
    if provider_name == "console":
        return ConsoleNotifier()
    # Default fallback
    return ConsoleNotifier()
