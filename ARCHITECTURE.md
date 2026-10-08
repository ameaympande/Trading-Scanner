# Architecture & Technical Design

## High-Level System Architecture

```
                    ┌────────────────────────────┐
                    │   Market Data Providers    │
                    │  (Yahoo Finance / NSE API) │
                    └─────────────┬──────────────┘
                                  │ Raw OHLCV
                                  ▼
                    ┌────────────────────────────┐
                    │    Data Validation Engine  │
                    │  (Sanity, Gaps, Split Chk) │
                    └─────────────┬──────────────┘
                                  │ Cleaned Point-in-Time Data
                                  ▼
                    ┌────────────────────────────┐
                    │   Local Parquet Cache / DB │
                    │   (Fast Zero-IO Ingestion) │
                    └─────────────┬──────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌────────────────────────────┐               ┌────────────────────────────┐
│    Market Regime Engine    │               │    Technical Calculator    │
│    (NIFTY 50 Evaluation)   │               │   (SMA, EMA, RSI, ATR, etc)│
└────────┬───────────────────┘               └─────────────┬──────────────┘
         │ Regime State                                    │ Indicators
         └────────────────────────┬────────────────────────┘
                                  ▼
                    ┌────────────────────────────┐
                    │    TREND_PULLBACK_V1       │
                    │    Strategy Evaluator      │
                    └─────────────┬──────────────┘
                                  │ Candidate Setups
                                  ▼
                    ┌────────────────────────────┐
                    │    Position Sizing Engine  │
                    │    (Risk % + Capital Cap)  │
                    └─────────────┬──────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  CLI Scanner     │    │  FastAPI REST    │    │ Event-Driven     │
│  (Console / Cron)│    │  Backend (Port   │    │ Backtest Engine  │
│                  │    │  8000)           │    │ & Walk-Forward   │
└──────────────────┘    └────────┬─────────┘    └──────────────────┘
                                 │ JSON API
                                 ▼
                        ┌──────────────────┐
                        │  React 19 + Vite │
                        │  Terminal UI     │
                        └──────────────────┘
```

## Architectural Principles

### 1. Modular Provider Abstraction
Market data providers implement `scanner.providers.base.MarketDataProvider`:
- `get_instruments(exchange)`
- `get_daily_ohlcv(symbol, start_date, end_date, exchange)`
- `get_intraday_ohlcv(symbol, interval, days, exchange)`
- `get_quote(symbol, exchange)`
- `get_corporate_actions(symbol, start_date, end_date, exchange)`

The application code never hardcodes provider-specific endpoints. To add an institutional feed (e.g. TrueData, GlobalDataFeeds, Zerodha Kite Connect), implement the protocol and register it in `scanner.providers.registry`.

### 2. Timezone & Market Session Integrity
All NSE/BSE transactions follow `Asia/Kolkata` time:
- Timestamps are normalized to UTC for database and parquet storage.
- Day and session boundaries are calculated explicitly in `Asia/Kolkata` (09:15 AM to 03:30 PM IST).
- Weekend sessions are flagged and isolated.

### 3. Separation of Strategy & Risk Management
A setup signal (`CandidateSetup`) only identifies the technical trigger, structural stop, and structural targets. It never assumes capital or portfolio state. Sizing is governed independently by `PositionSizer`:
$$\text{Max Risk Budget} = \text{Account Capital} \times \text{Risk Per Trade } (0.75\%)$$
$$\text{Risk Per Share} = \text{Entry Price} - \text{Stop Loss}$$
$$\text{Quantity} = \min\left(\left\lfloor \frac{\text{Max Risk Budget}}{\text{Risk Per Share}} \right\rfloor, \left\lfloor \frac{\text{Account Capital} \times 25\%}{\text{Entry Price}} \right\rfloor\right)$$

### 4. Zero Look-Ahead Bias Guarantee
In live scanning, the scan runs at or after 3:30 PM IST on candle close. In backtesting, signals evaluated on Day $T$ close are strictly barred from entering at Day $T$ prices; executions occur on Day $T+1$ Open.
