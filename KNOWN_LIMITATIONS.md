# Known Limitations & Honest Disclosures

## 1. Survivorship Bias
- When backtesting current NIFTY constituent lists (e.g., today's NIFTY 500), historical tests exclude companies that were delisted, went bankrupt, or were dropped from the index in past years.
- Historical tests conducted with current index constituents inherently exhibit survivorship bias. Results should be viewed as illustrative of strategy behavior on surviving equities rather than guaranteed historical performance of the broad index.

## 2. Intraday Gap Risk
- Stop losses are evaluated against daily low prices. In reality, a stock may open with a massive gap down below the stop price (e.g. following quarterly earnings or macroeconomic events).
- The backtest engine handles this by exiting at `min(open, stop_loss)`, taking the full gap loss, but intraday flash crashes between open and close cannot be perfectly modeled with daily resolution data alone.

## 3. Yahoo Finance Data Nuances
- Yahoo Finance data is occasionally delayed or may retroactively adjust prices after splits.
- For true institutional live execution, a direct tick feed from authorized NSE vendors (e.g. TrueData or Zerodha Kite Connect) should be integrated behind the `MarketDataProvider` interface.

## 4. No Live Order Execution
- `LIVE_TRADING_ENABLED` is intentionally defaulted to `false`.
- This platform provides quantitative research, explainable scanning, and paper trading. Real order placement requires manual review and conscious decision-making by the user.
