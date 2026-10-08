# Data Sources & Ingestion Pipeline

## Provider Architecture

Data ingestion is strictly decoupled behind the `MarketDataProvider` protocol.

### Primary Free Implementation: Yahoo Finance (`yfinance`)
- NSE Equities are resolved with the `.NS` suffix (e.g. `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`).
- BSE Equities are resolved with the `.BO` suffix.
- Benchmark index: `^NSEI` (NIFTY 50).
- Intraday resolution: 15m, 1h.
- Historical data depth: 10+ years daily.

### Caching Strategy
- To avoid rate limits and minimize redundant network requests, daily OHLCV series are cached locally in high-performance Apache Parquet format under `data_cache/` using the `pyarrow` engine.
- A scan over 50 stocks takes ~10 seconds with warm cache, compared to ~30 seconds cold.
- Cache invalidation can be triggered using `--no-cache` via CLI or the Refresh button in the UI.

---

## Validation Checks Applied to Every Candle

Every batch of downloaded candles is passed through `DataValidator`:

1. **Columns Existence:** Verifies existence of `open`, `high`, `low`, `close`, `volume`.
2. **Duplicate Detection:** Identifies duplicate timestamp entries and retains the latest candle.
3. **Impossible OHLC:**
   - Rejects if $\text{High} < \text{Low}$.
   - Rejects if $\text{High} < \text{Open}$ or $\text{High} < \text{Close}$.
   - Rejects if $\text{Low} > \text{Open}$ or $\text{Low} > \text{Close}$.
   - Rejects zero or negative prices.
4. **Volume Sanity:**
   - Negative volume is strictly an error.
   - Zero volume triggers an anomaly warning.
5. **Abnormal Jump Detection:**
   - Day-over-day price jumps exceeding $35\%$ are flagged as potential unadjusted splits or abnormal data artifacts.
6. **Timezone Normalization:**
   - Enforces timezone awareness, localizing naive dates to `Asia/Kolkata` and converting to UTC for storage.
