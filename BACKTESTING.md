# Backtesting Methodology & Realism Standards

## 1. Look-Ahead Bias Prevention

A common flaw in retail backtesting is evaluating an indicator using the closing price of Day $T$ and assuming the trade entered at the open of Day $T$.

In this engine:
- Daily scan occurs at or after **15:30 IST**. All candles up to Day $T$ Close are frozen.
- Simulated orders generated at Day $T$ Close execute strictly on **Day $T+1$ Open** (or the first tradable price on Day $T+1$).
- If Day $T+1$ opens with an adverse gap below the computed stop loss, the trade exits at **Day $T+1$ Open**, taking the full gap slippage.

---

## 2. Indian Equity Delivery Transaction Friction Model

Every round-trip trade deducts full statutory friction:

| Fee / Component | Rate / Schedule | Side Charged |
| :--- | :--- | :--- |
| **Brokerage** | 0% (Standard delivery model) | Buy & Sell |
| **Securities Transaction Tax (STT)** | 0.10% of turnover | Buy & Sell |
| **NSE Transaction Charges** | 0.00345% of turnover | Buy & Sell |
| **SEBI Turnover Fee** | 0.00010% (₹10 per Crore) | Buy & Sell |
| **GST** | 18% on (Brokerage + Exchange + SEBI) | Buy & Sell |
| **Stamp Duty** | 0.015% of turnover | Buy only |
| **Demat DP Charges** | ₹15.93 flat per company | Sell only |
| **Execution Slippage** | 0.10% of turnover | Buy & Sell |

$$\text{Net P&L} = \text{Gross P&L} - \text{Total Statutory Charges} - \text{Slippage}$$

---

## 3. Walk-Forward Validation

To prevent parameter curve-fitting:
1. **In-Sample Period (70%):** Parameter exploration and baseline metrics.
2. **Out-of-Sample Period (30%):** Tested with frozen parameters to evaluate persistence.
3. **Robustness Ratio:** Evaluates the retention of Sharpe and Return in out-of-sample periods:
   $$\text{Robustness Ratio} = \frac{\text{Out-of-Sample Annualized Return}}{\text{In-Sample Annualized Return}}$$
   A ratio significantly below $0.50$ indicates curve-fitting.
