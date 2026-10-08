"""Tests for DataValidator engine."""

import pandas as pd

from scanner.data.validator import DataValidator


def test_validator_detects_impossible_high_low():
    dates = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0, 102.0, 101.0, 104.0, 105.0],
            "high": [105.0, 106.0, 95.0, 108.0, 110.0],  # Day 3: High (95) < Low (98)
            "low": [98.0, 99.0, 98.0, 102.0, 103.0],
            "close": [102.0, 101.0, 96.0, 105.0, 108.0],
            "volume": [10000, 15000, 20000, 12000, 18000],
        },
        index=dates,
    )
    validator = DataValidator()
    result = validator.validate_and_clean(df, symbol="BAD_HL")

    assert not result.is_valid
    assert any("HIGH_LESS_THAN_LOW" in a.anomaly_type for a in result.anomalies)


def test_validator_detects_negative_volume():
    dates = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [95.0, 96.0, 97.0],
            "close": [102.0, 103.0, 104.0],
            "volume": [10000, -500, 12000],
        },
        index=dates,
    )
    validator = DataValidator()
    result = validator.validate_and_clean(df, symbol="NEG_VOL")

    assert not result.is_valid
    assert any("NEGATIVE_VOLUME" in a.anomaly_type for a in result.anomalies)


def test_validator_handles_duplicate_timestamps():
    dates = [
        pd.Timestamp("2024-01-01", tz="UTC"),
        pd.Timestamp("2024-01-02", tz="UTC"),
        pd.Timestamp("2024-01-02", tz="UTC"),  # Duplicate
        pd.Timestamp("2024-01-03", tz="UTC"),
    ]
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 101.5, 103.0],
            "high": [105.0, 106.0, 106.5, 108.0],
            "low": [95.0, 96.0, 96.0, 98.0],
            "close": [102.0, 103.0, 103.5, 105.0],
            "volume": [10000, 12000, 12500, 15000],
        },
        index=dates,
    )
    validator = DataValidator()
    result = validator.validate_and_clean(df, symbol="DUP_TEST")

    assert result.duplicate_rows_count == 1
    assert len(result.cleaned_df) == 3  # Deduped
    assert result.is_valid  # Still valid after deduping
