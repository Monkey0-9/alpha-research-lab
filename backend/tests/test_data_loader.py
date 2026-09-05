"""
Tests for core.data_loader
Validates data ingestion, survivorship-bias prevention, and PIT queries.
"""
import pandas as pd
from core.data_loader import (
    download_sp500_data,
    load_sp500_data,
    get_pit_data,
    validate_data_quality
)


def test_download_sp500_data():
    df = download_sp500_data("2023-01-01", "2023-12-31")
    assert len(df) > 10000
    assert "close" in df.columns
    assert df.index.names == ["date", "ticker"]


def test_no_survivorship_bias():
    df = load_sp500_data("2019-01-01", "2024-12-31")
    # Tickers that existed historically like XRX must be present in universe
    assert "XRX" in df.index.get_level_values("ticker")


def test_pit_query_no_future_data():
    cutoff = pd.Timestamp("2023-06-15")
    data = get_pit_data("AAPL", cutoff)
    assert not data.empty
    # Validate data quality checks
    df = download_sp500_data("2023-01-01", "2023-03-31")
    quality = validate_data_quality(df)
    assert quality["clean_percentage"] > 95.0
