# Strategy Specification: TREND_PULLBACK_V1

## Overview
`TREND_PULLBACK_V1` is a robust trend-following swing strategy designed for liquid Indian equities (NSE). Rather than chasing breakout extensions, the strategy isolates equities in sustained multi-month uptrends, waits for a controlled, low-volatility pullback to key exponential moving averages, and seeks entry upon structural confirmation.

---

## 1. Hard Eligibility Filters (Binary Disqualification)

A stock is immediately disqualified if any of the following are breached:
1. **Liquidity:**
   - $\text{Price} \ge ₹50.00$
   - $\text{20-day Average Volume} \ge 100,000$ shares
   - $\text{Average Daily Turnover} \ge ₹50,00,000$ (₹50 Lakhs)
2. **Trend Alignment:**
   - $\text{Close} > \text{SMA}_{50}$
   - $\text{SMA}_{50} > \text{SMA}_{200}$
3. **Momentum Bounds:**
   - $\text{RSI}_{14} \ge 45.0$ (Must not have broken momentum structure)
   - $\text{RSI}_{14} \le 75.0$ (Must not be overbought/overextended)
4. **Data Adequacy:**
   - Minimum 250 trading sessions of clean historical data.

---

## 2. Multi-Factor Scoring Model (0–100 Points)

Candidates that pass the binary filters receive an integer score from 0 to 100 reflecting the setup's quality and alignment with the strategy definition.

| Component | Default Weight | Criteria & Point Allocation |
| :--- | :---: | :--- |
| **Trend Strength** | **25 pts** | • Price > SMA 50 (+10 pts)<br>• SMA 50 > SMA 200 (+8 pts)<br>• Rising SMA 200 slope over 20 days (+7 pts) |
| **Momentum Quality** | **15 pts** | • RSI in optimal swing zone $[50, 65]$ (15 pts)<br>• RSI in recovery zone $[45, 50)$ (10 pts)<br>• RSI in strong zone $(65, 70]$ (12 pts)<br>• RSI in cautionary zone $(70, 75]$ (6 pts) |
| **Pullback Quality** | **20 pts** | • Tested EMA 20 within 1.5% without violation (+12 pts)<br>• Tested EMA 50 (+10 pts)<br>• Normal ATR volatility $(< 3.5\%$ of price) during retracement (+8 pts) |
| **Volume Confirmation** | **15 pts** | • Relative Volume $\ge 1.5\times$ (+15 pts)<br>• Relative Volume $\ge 1.2\times$ (+12 pts)<br>• Relative Volume $\ge 1.0\times$ (+8 pts) |
| **Breakout Confirmation** | **10 pts** | • Close > Prior 5-day High with Bullish Candle (+10 pts)<br>• Close > Prior 5-day High (+8 pts)<br>• Bullish reversal candle closing in top 35% of daily range (+7 pts) |
| **Market Regime** | **10 pts** | • NIFTY 50 Regime `BULLISH` (+10 pts)<br>• NIFTY 50 Regime `NEUTRAL` (+5 pts)<br>• NIFTY 50 Regime `BEARISH` (+1 pt) |
| **Turnover Liquidity** | **5 pts** | • Daily Turnover $\ge ₹5\text{ Cr}$ (+5 pts)<br>• Daily Turnover $\ge ₹2\text{ Cr}$ (+4 pts) |
| **Total Available** | **100 pts** | Minimum threshold to trigger signal: **70 / 100** |

---

## 3. Entry, Stop Loss, and Target Mathematics

The strategy eliminates arbitrary percentage targets in favor of market structure and Average True Range (ATR):

### Entry Zone
$$\text{Entry Low} = \text{Close}$$
$$\text{Entry High} = \max(\text{Close}, \text{High})$$
$$\text{Entry Mid} = \frac{\text{Entry Low} + \text{Entry High}}{2}$$

### Stop Loss
Calculated by taking the safer distance between structural swing support and ATR distance:
$$\text{Structural Stop} = \text{Recent Swing Low (10-bar)} - (0.2 \times \text{ATR}_{14})$$
$$\text{ATR Stop} = \text{Entry Mid} - (1.5 \times \text{ATR}_{14})$$
$$\text{Stop Loss} = \max(\text{Entry Mid} - 3.0 \times \text{ATR}_{14}, \min(\text{Structural Stop}, \text{ATR Stop}))$$

### Profit Targets & Risk/Reward
$$\text{Risk Per Share} = \text{Entry Mid} - \text{Stop Loss}$$
$$\text{Target 1} = \text{Entry Mid} + (\text{Risk Per Share} \times 2.0)$$
$$\text{Target 2} = \text{Entry Mid} + (\text{Risk Per Share} \times 3.5)$$
$$\text{Risk/Reward Ratio} = \frac{\text{Target 1} - \text{Entry Mid}}{\text{Risk Per Share}} \ge 2.0$$

*If the setup cannot provide at least a $1:2.0$ Risk/Reward ratio, it is discarded.*

---

## 4. Invalidation Criteria
A setup is considered invalidated if:
1. The stock prints a daily close below the computed Stop Loss.
2. The stock prints a daily close below its 50-day Simple Moving Average.
