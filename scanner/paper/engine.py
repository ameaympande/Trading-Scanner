"""
Paper Trading Simulation Engine.

Allows simulated execution of swing trade setups without risking real capital:
- Accept / reject signals
- Custom or signal-suggested quantities
- Tracking open positions with mark-to-market valuations
- Realized & Unrealized P&L tracking
- Full persistence to local JSON storage
"""

from __future__ import annotations

import datetime
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from scanner.backtest.costs import IndianEquityCostCalculator
from scanner.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    id: str
    symbol: str
    entry_date: str
    entry_price: float
    quantity: int
    stop_loss: float
    target1: float
    target2: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    strategy: str
    score: int
    status: str = "OPEN"  # OPEN, CLOSED


@dataclass
class PaperClosedTrade:
    id: str
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: int
    stop_loss: float
    target: float
    gross_pnl: float
    fees: float
    net_pnl: float
    net_pnl_pct: float
    exit_reason: str
    strategy: str


@dataclass
class PaperTradingAccount:
    initial_capital: float = 100_000.0
    cash_balance: float = 100_000.0
    realized_pnl: float = 0.0
    total_fees_paid: float = 0.0
    open_positions: list[PaperPosition] = field(default_factory=list)
    trade_history: list[PaperClosedTrade] = field(default_factory=list)

    @property
    def total_invested(self) -> float:
        return sum(p.entry_price * p.quantity for p in self.open_positions)

    @property
    def total_current_value(self) -> float:
        return sum(p.current_price * p.quantity for p in self.open_positions)

    @property
    def total_unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.open_positions)

    @property
    def current_equity(self) -> float:
        return round(self.cash_balance + self.total_current_value, 2)

    @property
    def total_return_pct(self) -> float:
        return round(((self.current_equity - self.initial_capital) / self.initial_capital) * 100.0, 2)

    @property
    def win_rate_pct(self) -> float:
        if not self.trade_history:
            return 0.0
        wins = sum(1 for t in self.trade_history if t.net_pnl > 0)
        return round(wins / len(self.trade_history) * 100.0, 1)


class PaperTradingEngine:
    """Manages paper trading operations and disk persistence."""

    def __init__(self, storage_path: Path | str | None = None):
        settings = get_settings()
        self.storage_file = Path(storage_path or (settings.data_cache_dir / "paper_account.json"))
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.cost_calc = IndianEquityCostCalculator()
        self.account = self._load_account()

    def _load_account(self) -> PaperTradingAccount:
        if self.storage_file.exists():
            try:
                with open(self.storage_file) as f:
                    data = json.load(f)
                open_pos = [PaperPosition(**p) for p in data.get("open_positions", [])]
                trades = [PaperClosedTrade(**t) for t in data.get("trade_history", [])]
                return PaperTradingAccount(
                    initial_capital=data.get("initial_capital", 100_000.0),
                    cash_balance=data.get("cash_balance", 100_000.0),
                    realized_pnl=data.get("realized_pnl", 0.0),
                    total_fees_paid=data.get("total_fees_paid", 0.0),
                    open_positions=open_pos,
                    trade_history=trades,
                )
            except Exception as e:
                logger.error(f"Error reading paper account state: {e}. Starting fresh.")
        return PaperTradingAccount()

    def save(self) -> None:
        """Persist state to JSON file."""
        data = {
            "initial_capital": self.account.initial_capital,
            "cash_balance": self.account.cash_balance,
            "realized_pnl": self.account.realized_pnl,
            "total_fees_paid": self.account.total_fees_paid,
            "open_positions": [asdict(p) for p in self.account.open_positions],
            "trade_history": [asdict(t) for t in self.account.trade_history],
        }
        with open(self.storage_file, "w") as f:
            json.dump(data, f, indent=2)

    def open_position(
        self,
        symbol: str,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        target1: float,
        target2: float = 0.0,
        strategy: str = "TREND_PULLBACK_V1",
        score: int = 75,
    ) -> PaperPosition:
        """Open a new simulated paper trade position."""
        cost = entry_price * quantity
        if cost > self.account.cash_balance:
            raise ValueError(
                f"Insufficient paper cash: Need ₹{cost:,.2f}, available ₹{self.account.cash_balance:,.2f}"
            )

        pos_id = f"POS-{symbol}-{int(datetime.datetime.now().timestamp())}"
        pos = PaperPosition(
            id=pos_id,
            symbol=symbol,
            entry_date=datetime.date.today().isoformat(),
            entry_price=round(entry_price, 2),
            quantity=quantity,
            stop_loss=round(stop_loss, 2),
            target1=round(target1, 2),
            target2=round(target2, 2) if target2 > 0 else round(target1 * 1.05, 2),
            current_price=round(entry_price, 2),
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            strategy=strategy,
            score=score,
            status="OPEN",
        )

        self.account.cash_balance = round(self.account.cash_balance - cost, 2)
        self.account.open_positions.append(pos)
        self.save()
        return pos

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        exit_reason: str = "MANUAL",
    ) -> PaperClosedTrade:
        """Close an open paper position and record realized P&L with fees."""
        pos = next((p for p in self.account.open_positions if p.id == position_id), None)
        if not pos:
            raise ValueError(f"Position ID {position_id} not found.")

        friction = self.cost_calc.calculate_costs(
            entry_price=pos.entry_price,
            exit_price=exit_price,
            quantity=pos.quantity,
        )

        gross_pnl = (exit_price - pos.entry_price) * pos.quantity
        net_pnl = round(gross_pnl - friction.total_charges, 2)
        net_pnl_pct = round((net_pnl / (pos.entry_price * pos.quantity)) * 100.0, 2)

        proceeds = exit_price * pos.quantity - friction.total_charges
        self.account.cash_balance = round(self.account.cash_balance + proceeds, 2)
        self.account.realized_pnl = round(self.account.realized_pnl + net_pnl, 2)
        self.account.total_fees_paid = round(self.account.total_fees_paid + friction.total_charges, 2)

        closed = PaperClosedTrade(
            id=pos.id,
            symbol=pos.symbol,
            entry_date=pos.entry_date,
            exit_date=datetime.date.today().isoformat(),
            entry_price=pos.entry_price,
            exit_price=round(exit_price, 2),
            quantity=pos.quantity,
            stop_loss=pos.stop_loss,
            target=pos.target1,
            gross_pnl=round(gross_pnl, 2),
            fees=friction.total_charges,
            net_pnl=net_pnl,
            net_pnl_pct=net_pnl_pct,
            exit_reason=exit_reason,
            strategy=pos.strategy,
        )

        self.account.open_positions = [p for p in self.account.open_positions if p.id != position_id]
        self.account.trade_history.append(closed)
        self.save()
        return closed

    def update_prices(self, price_map: dict[str, float]) -> None:
        """Update LTPs for open positions and update mark-to-market PnL."""
        for p in self.account.open_positions:
            if p.symbol in price_map:
                ltp = price_map[p.symbol]
                p.current_price = round(ltp, 2)
                p.unrealized_pnl = round((ltp - p.entry_price) * p.quantity, 2)
                p.unrealized_pnl_pct = round(((ltp - p.entry_price) / p.entry_price) * 100.0, 2)
        self.save()
