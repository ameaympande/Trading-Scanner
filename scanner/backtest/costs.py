"""
Indian Equity Transaction Cost Calculator.

Calculates realistic trading friction for delivery-based swing trades on NSE:
- Brokerage (configurable, e.g. 0 or ₹20)
- STT (Securities Transaction Tax: 0.1% on buy and 0.1% on sell)
- NSE Exchange Transaction Charges (0.00345%)
- GST (18% on brokerage + exchange charges)
- SEBI Turnover Charges (0.0001% = ₹10 per crore)
- Stamp Duty (0.015% on buy side)
- DP Charges (Depository Participant charge on sell side: ~₹15.93 flat per company)
- Slippage (configurable, default 0.1% on execution)
"""

from __future__ import annotations

from dataclasses import dataclass

from scanner.config import TransactionCosts, get_settings


@dataclass
class TradeFriction:
    buy_turnover: float
    sell_turnover: float
    brokerage: float
    stt: float
    exchange_charges: float
    sebi_charges: float
    gst: float
    stamp_duty: float
    dp_charges: float
    slippage_cost: float
    total_charges: float

    @property
    def total_cost_pct(self) -> float:
        total_turnover = self.buy_turnover + self.sell_turnover
        return (self.total_charges / total_turnover * 100.0) if total_turnover > 0 else 0.0


class IndianEquityCostCalculator:
    """Calculates all statutory and execution costs for an Indian equity swing trade."""

    def __init__(self, costs_config: TransactionCosts | None = None):
        settings = get_settings()
        self.config = costs_config or settings.transaction_costs
        self.flat_dp_charge = 15.93  # Standard CDSL/NSDL DP charge on sell

    def calculate_costs(
        self,
        entry_price: float,
        exit_price: float,
        quantity: int,
    ) -> TradeFriction:
        """Calculate complete breakdown of fees and slippage for a completed round-trip trade."""
        if quantity <= 0:
            return TradeFriction(
                buy_turnover=0.0,
                sell_turnover=0.0,
                brokerage=0.0,
                stt=0.0,
                exchange_charges=0.0,
                sebi_charges=0.0,
                gst=0.0,
                stamp_duty=0.0,
                dp_charges=0.0,
                slippage_cost=0.0,
                total_charges=0.0,
            )

        buy_turnover = entry_price * quantity
        sell_turnover = exit_price * quantity
        total_turnover = buy_turnover + sell_turnover

        # 1. Brokerage: Zero delivery for discount brokers or min(20, 0.03%)
        brokerage_buy = buy_turnover * self.config.brokerage_pct
        brokerage_sell = sell_turnover * self.config.brokerage_pct
        total_brokerage = round(brokerage_buy + brokerage_sell, 2)

        # 2. STT (0.1% on buy + 0.1% on sell for equity delivery)
        stt_buy = buy_turnover * self.config.stt_buy_pct
        stt_sell = sell_turnover * self.config.stt_sell_pct
        total_stt = round(stt_buy + stt_sell, 2)

        # 3. Exchange transaction charges (NSE: 0.00345%)
        exchange_charges = round(total_turnover * self.config.exchange_txn_pct, 2)

        # 4. SEBI turnover charge (₹10 / crore = 0.0001%)
        sebi_charges = round(total_turnover * self.config.sebi_charges_pct, 2)

        # 5. GST (18% on Brokerage + Exchange charges + SEBI charges)
        gst = round(0.18 * (total_brokerage + exchange_charges + sebi_charges), 2)

        # 6. Stamp duty (0.015% on buy side only)
        stamp_duty = round(buy_turnover * self.config.stamp_duty_pct, 2)

        # 7. DP Charges (Flat per scrip on sell side)
        dp_charges = self.flat_dp_charge

        # 8. Slippage (0.1% on both entry and exit)
        slippage_cost = round(total_turnover * self.config.slippage_pct, 2)

        total_charges = round(
            total_brokerage
            + total_stt
            + exchange_charges
            + sebi_charges
            + gst
            + stamp_duty
            + dp_charges
            + slippage_cost,
            2,
        )

        return TradeFriction(
            buy_turnover=round(buy_turnover, 2),
            sell_turnover=round(sell_turnover, 2),
            brokerage=total_brokerage,
            stt=total_stt,
            exchange_charges=exchange_charges,
            sebi_charges=sebi_charges,
            gst=gst,
            stamp_duty=stamp_duty,
            dp_charges=round(dp_charges, 2),
            slippage_cost=slippage_cost,
            total_charges=total_charges,
        )
