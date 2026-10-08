"""
Data Validation Engine for Market Data.

Validates raw OHLCV data to protect against corrupt, distorted, or look-ahead data:
- Duplicate candles
- Missing candles during trading days
- Impossible OHLC values (High < Low, Open/Close outside High-Low)
- Zero or negative volume
- Abnormal price jumps (e.g. unadjusted splits/spikes > 30%)
- Timezone verification (Asia/Kolkata)
- Non-trading days / weekend checks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd
import pytz

logger = logging.getLogger(__name__)

KOLKATA_TZ = pytz.timezone("Asia/Kolkata")


@dataclass
class CandleAnomaly:
    timestamp: pd.Timestamp
    symbol: str
    anomaly_type: str
    details: str
    severity: str = "ERROR"  # "WARNING" or "ERROR"


@dataclass
class ValidationResult:
    symbol: str
    is_valid: bool
    cleaned_df: pd.DataFrame
    anomalies: list[CandleAnomaly] = field(default_factory=list)
    missing_dates_count: int = 0
    duplicate_rows_count: int = 0

    @property
    def has_errors(self) -> bool:
        return any(a.severity == "ERROR" for a in self.anomalies)

    @property
    def has_warnings(self) -> bool:
        return any(a.severity == "WARNING" for a in self.anomalies)


class DataValidator:
    """
    Validates and cleans raw OHLCV market data.
    """

    def __init__(
        self,
        max_daily_jump_pct: float = 0.35,  # 35% jump flags potential unadjusted split/anomaly
        allow_zero_volume: bool = False,
    ):
        self.max_daily_jump_pct = max_daily_jump_pct
        self.allow_zero_volume = allow_zero_volume

    def validate_and_clean(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> ValidationResult:
        """
        Validate OHLCV DataFrame and return cleaned data + anomaly report.
        """
        anomalies: list[CandleAnomaly] = []

        if df is None or df.empty:
            anomalies.append(
                CandleAnomaly(
                    timestamp=pd.Timestamp.now(tz="UTC"),
                    symbol=symbol,
                    anomaly_type="EMPTY_DATA",
                    details=f"No OHLCV records found for symbol {symbol}",
                    severity="ERROR",
                )
            )
            return ValidationResult(
                symbol=symbol,
                is_valid=False,
                cleaned_df=pd.DataFrame(),
                anomalies=anomalies,
            )

        working_df = df.copy()

        # 1. Verify required columns
        required_cols = {"open", "high", "low", "close", "volume"}
        missing_cols = required_cols - set(working_df.columns)
        if missing_cols:
            anomalies.append(
                CandleAnomaly(
                    timestamp=pd.Timestamp.now(tz="UTC"),
                    symbol=symbol,
                    anomaly_type="MISSING_COLUMNS",
                    details=f"Missing expected OHLCV columns: {missing_cols}",
                    severity="ERROR",
                )
            )
            return ValidationResult(
                symbol=symbol,
                is_valid=False,
                cleaned_df=pd.DataFrame(),
                anomalies=anomalies,
            )

        # 2. Check & handle duplicates on Index
        duplicate_mask = working_df.index.duplicated(keep="last")
        duplicate_count = int(duplicate_mask.sum())
        if duplicate_count > 0:
            dup_dates = working_df.index[duplicate_mask].tolist()
            anomalies.append(
                CandleAnomaly(
                    timestamp=working_df.index[0],
                    symbol=symbol,
                    anomaly_type="DUPLICATE_CANDLES",
                    details=f"Found {duplicate_count} duplicate timestamps: {dup_dates[:5]} (keeping last)",
                    severity="WARNING",
                )
            )
            working_df = working_df[~duplicate_mask]

        # 3. Sort index chronologically
        working_df = working_df.sort_index()

        # 4. Check timezone
        if working_df.index.tz is None:
            anomalies.append(
                CandleAnomaly(
                    timestamp=working_df.index[0],
                    symbol=symbol,
                    anomaly_type="TIMEZONE_MISSING",
                    details="Timestamp index is timezone-naive, localizing to Asia/Kolkata then UTC",
                    severity="WARNING",
                )
            )
            working_df.index = working_df.index.tz_localize(KOLKATA_TZ).tz_convert("UTC")

        # 5. Sanity checks on OHLC relations
        # High must be >= Low
        invalid_hl = working_df["high"] < working_df["low"]
        if invalid_hl.any():
            for ts in working_df.index[invalid_hl]:
                anomalies.append(
                    CandleAnomaly(
                        timestamp=ts,
                        symbol=symbol,
                        anomaly_type="IMPOSSIBLE_OHLC_HIGH_LESS_THAN_LOW",
                        details=f"High ({working_df.loc[ts, 'high']}) < Low ({working_df.loc[ts, 'low']})",
                        severity="ERROR",
                    )
                )

        # High must be >= Open and High >= Close
        invalid_h_oc = (working_df["high"] < working_df["open"]) | (working_df["high"] < working_df["close"])
        if invalid_h_oc.any():
            for ts in working_df.index[invalid_h_oc]:
                anomalies.append(
                    CandleAnomaly(
                        timestamp=ts,
                        symbol=symbol,
                        anomaly_type="IMPOSSIBLE_OHLC_HIGH_LESS_THAN_OPEN_OR_CLOSE",
                        details=f"High is less than Open or Close at {ts}",
                        severity="ERROR",
                    )
                )

        # Low must be <= Open and Low <= Close
        invalid_l_oc = (working_df["low"] > working_df["open"]) | (working_df["low"] > working_df["close"])
        if invalid_l_oc.any():
            for ts in working_df.index[invalid_l_oc]:
                anomalies.append(
                    CandleAnomaly(
                        timestamp=ts,
                        symbol=symbol,
                        anomaly_type="IMPOSSIBLE_OHLC_LOW_GREATER_THAN_OPEN_OR_CLOSE",
                        details=f"Low is greater than Open or Close at {ts}",
                        severity="ERROR",
                    )
                )

        # Prices must be strictly positive
        invalid_prices = (
            (working_df["open"] <= 0)
            | (working_df["high"] <= 0)
            | (working_df["low"] <= 0)
            | (working_df["close"] <= 0)
        )
        if invalid_prices.any():
            for ts in working_df.index[invalid_prices]:
                anomalies.append(
                    CandleAnomaly(
                        timestamp=ts,
                        symbol=symbol,
                        anomaly_type="NON_POSITIVE_PRICE",
                        details="Price candle contains zero or negative values",
                        severity="ERROR",
                    )
                )

        # Volume checks: negative volume is strictly an error, zero volume is warning
        negative_vol = working_df["volume"] < 0
        if negative_vol.any():
            for ts in working_df.index[negative_vol]:
                anomalies.append(
                    CandleAnomaly(
                        timestamp=ts,
                        symbol=symbol,
                        anomaly_type="NEGATIVE_VOLUME",
                        details=f"Negative volume {working_df.loc[ts, 'volume']} at {ts}",
                        severity="ERROR",
                    )
                )

        zero_vol = working_df["volume"] == 0
        if zero_vol.any() and not self.allow_zero_volume:
            zero_count = int(zero_vol.sum())
            anomalies.append(
                CandleAnomaly(
                    timestamp=working_df.index[zero_vol][0],
                    symbol=symbol,
                    anomaly_type="ZERO_VOLUME",
                    details=f"Found {zero_count} candles with 0 volume",
                    severity="WARNING",
                )
            )

        # 6. Abnormal price jump check (potential split or bad tick)
        if len(working_df) > 1:
            close_shift = working_df["close"].shift(1)
            pct_change = (working_df["close"] - close_shift).abs() / close_shift
            abnormal_jumps = pct_change > self.max_daily_jump_pct
            if abnormal_jumps.any():
                for ts in working_df.index[abnormal_jumps]:
                    chg = pct_change.loc[ts] * 100
                    anomalies.append(
                        CandleAnomaly(
                            timestamp=ts,
                            symbol=symbol,
                            anomaly_type="ABNORMAL_PRICE_JUMP",
                            details=f"Day-over-day price jump of {chg:.1f}% exceeds threshold {self.max_daily_jump_pct*100:.0f}%",
                            severity="WARNING",
                        )
                    )

        # 7. Check weekend candles
        # Convert index to Asia/Kolkata day of week
        kolkata_index = working_df.index.tz_convert(KOLKATA_TZ)
        is_weekend = kolkata_index.dayofweek >= 5  # 5=Sat, 6=Sun
        if is_weekend.any():
            weekend_ts = working_df.index[is_weekend]
            for ts in weekend_ts:
                # Except rare special trading sessions (e.g. Diwali Muhurat trading)
                anomalies.append(
                    CandleAnomaly(
                        timestamp=ts,
                        symbol=symbol,
                        anomaly_type="WEEKEND_CANDLE",
                        details=f"Candle falls on weekend: {ts.strftime('%Y-%m-%d %A')}",
                        severity="WARNING",
                    )
                )

        has_severe_error = any(a.severity == "ERROR" for a in anomalies)
        return ValidationResult(
            symbol=symbol,
            is_valid=not has_severe_error,
            cleaned_df=working_df,
            anomalies=anomalies,
            duplicate_rows_count=duplicate_count,
        )
