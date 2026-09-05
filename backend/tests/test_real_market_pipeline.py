"""
Unit & Integration Tests for Real Market Data Pipeline
Validates Yahoo Finance client, Robinhood client, and unified ingestion pipeline.
"""
import pandas as pd
from core.yfinance_client import yfinance_client
from core.robinhood_client import robinhood_client
from core.data_pipeline import data_pipeline
from core.data_loader import fetch_market_overview


def test_yfinance_live_quote():
    """Verify Yahoo Finance live quote retrieval."""
    q = yfinance_client.fetch_live_quote("AAPL")
    assert q["ticker"] == "AAPL"
    assert "price" in q
    assert q["price"] > 0
    assert q["provider"] == "yfinance"
    assert q["status"] in ("LIVE", "FALLBACK")


def test_robinhood_live_quote():
    """Verify Robinhood live quote retrieval and fallback handling."""
    q = robinhood_client.get_realtime_quote("AAPL")
    assert q["ticker"] == "AAPL"
    assert "price" in q
    assert q["price"] > 0
    assert q["provider"] == "robinhood"


def test_robinhood_market_hours():
    """Verify market hours detector returns valid operating state."""
    hours = robinhood_client.get_market_hours()
    assert hours["market"] == "US_EQUITIES"
    assert hours["state"] in ("OPEN", "CLOSED", "EXTENDED_HOURS")
    assert isinstance(hours["is_open"], bool)


def test_robinhood_crypto_quote():
    """Verify crypto quote functionality."""
    cq = robinhood_client.get_crypto_quote("BTC")
    assert "BTC" in cq["ticker"]
    assert "price" in cq
    assert cq["price"] > 0


def test_market_overview_endpoint():
    """Verify broad benchmark market indices overview."""
    overview = fetch_market_overview()
    assert "indices" in overview
    assert len(overview["indices"]) >= 3
    symbols = [idx["symbol"] for idx in overview["indices"]]
    assert "SPY" in symbols or "^GSPC" in symbols


def test_data_pipeline_cleaning():
    """Verify data cleaning, outlier clipping, and quality metrics."""
    dates = pd.date_range("2024-01-01", "2024-01-20", freq="B")
    raw_df = pd.DataFrame({
        "open": [150.0] * len(dates),
        "high": [152.0] * len(dates),
        "low": [148.0] * len(dates),
        "close": [150.0] * len(dates),
        "volume": [1_000_000] * len(dates),
        "return_1d": [0.0] * len(dates)
    }, index=pd.MultiIndex.from_tuples([(d, "AAPL") for d in dates], names=["date", "ticker"]))

    cleaned_df, report = data_pipeline.clean_and_normalize(raw_df)
    assert len(cleaned_df) == len(raw_df)
    assert report["clean_pct"] >= 95.0
    assert "outliers_flagged" in report


def test_data_pipeline_status():
    """Verify pipeline status reporting."""
    status = data_pipeline.get_status()
    assert "status" in status
    assert "clean_pct" in status
    assert "quality_score" in status


def test_api_pipeline_endpoints():
    """Verify FastAPI integration for the new pipeline endpoints."""
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)

    # Test pipeline status endpoint
    r = client.get("/api/data/pipeline/status")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data

    # Test live quote endpoint (yfinance)
    r = client.get("/api/data/live-quote?ticker=AAPL&provider=yfinance")
    assert r.status_code == 200
    q = r.json()
    assert q["ticker"] == "AAPL"
    assert q["price"] > 0

    # Test live quote endpoint (robinhood)
    r = client.get("/api/data/live-quote?ticker=MSFT&provider=robinhood")
    assert r.status_code == 200
    q = r.json()
    assert q["ticker"] == "MSFT"
    assert q["price"] > 0

    # Test market overview endpoint
    r = client.get("/api/data/market-overview")
    assert r.status_code == 200
    ov = r.json()
    assert len(ov["indices"]) > 0
