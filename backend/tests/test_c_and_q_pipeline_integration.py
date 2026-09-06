import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.features import build_features
from backend.core.alpha_gp import TimeSeriesOpNode, FeatureNode


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_market_df():
    np.random.seed(42)
    n = 120
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    prices = 150.0 + np.cumsum(np.random.normal(0.05, 1.2, n))
    volumes = np.random.randint(50000, 200000, n)
    idx = pd.MultiIndex.from_tuples([(d, "AAPL") for d in dates], names=["date", "ticker"])
    return pd.DataFrame({
        "open": prices * 0.998,
        "high": prices * 1.005,
        "low": prices * 0.995,
        "close": prices,
        "volume": volumes
    }, index=idx)


def test_c_and_q_features_in_feature_matrix(sample_market_df):
    """Verify C-accelerated and Q-integrated features calculate cleanly in the feature matrix."""
    feat_matrix = build_features(sample_market_df)

    # Check that native C Kalman features exist and are populated
    assert "kalman_fair_value" in feat_matrix.columns
    assert "kalman_residual" in feat_matrix.columns
    assert feat_matrix["kalman_fair_value"].dropna().shape[0] > 50
    assert feat_matrix["kalman_residual"].dropna().shape[0] > 50

    # Check C EWMA Volatility and C ZScore
    assert "ewma_volatility_20d" in feat_matrix.columns
    assert "c_zscore_20d" in feat_matrix.columns
    assert feat_matrix["ewma_volatility_20d"].dropna().shape[0] > 50
    assert feat_matrix["c_zscore_20d"].dropna().shape[0] > 50


def test_gp_ast_c_accelerated_nodes(sample_market_df):
    """Verify Genetic Programming AST nodes for ts_kalman and ts_hurst execute C kernels."""
    var_node = FeatureNode("close")
    kalman_node = TimeSeriesOpNode("ts_kalman", var_node, window=20)
    res_kalman = kalman_node.evaluate(sample_market_df)
    assert isinstance(res_kalman, pd.Series)
    assert len(res_kalman) == len(sample_market_df)
    assert not res_kalman.dropna().empty

    hurst_node = TimeSeriesOpNode("ts_hurst", var_node, window=50)
    res_hurst = hurst_node.evaluate(sample_market_df)
    assert isinstance(res_hurst, pd.Series)
    assert len(res_hurst) == len(sample_market_df)
    assert not res_hurst.dropna().empty


def test_api_features_native_telemetry(client):
    """Verify the /api/features/native-telemetry endpoint returns live C and Q benchmarks."""
    response = client.get("/api/features/native-telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "kernels" in data
    assert len(data["kernels"]) >= 5
    for k in data["kernels"]:
        assert "feature" in k
        assert "latency_micros" in k
        assert k["latency_micros"] > 0.0
        assert k["status"] == "ACCELERATED"


def test_api_execution_microstructure_live(client):
    """Verify the /api/execution/microstructure-live endpoint executes C OFI and Microprice kernels."""
    response = client.get("/api/execution/microstructure-live?ticker=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["ticker"] == "AAPL"
    assert "telemetry" in data
    assert data["telemetry"]["c_ofi_latency_micros"] > 0.0
    assert data["telemetry"]["c_microprice_latency_micros"] > 0.0
    assert "metrics" in data
    assert "microprice" in data["metrics"]
    assert "cumulative_ofi" in data["metrics"]
    assert len(data["recent_snapshots"]) > 0


def test_api_data_q_bars(client):
    """Verify the /api/data/q-bars endpoint produces vector OHLCV bars via KDB+/Q."""
    response = client.get("/api/data/q-bars?ticker=AAPL&interval_seconds=60")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["ticker"] == "AAPL"
    assert "bars" in data
    assert len(data["bars"]) > 0
    bar = data["bars"][0]
    assert "open" in bar and "high" in bar and "low" in bar and "close" in bar and "vwap" in bar


def test_api_data_q_asof_sync(client):
    """Verify the /api/data/q-asof-sync endpoint performs temporal trades x quotes matching via KDB+/Q."""
    response = client.get("/api/data/q-asof-sync?ticker=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["ticker"] == "AAPL"
    assert "records" in data
    assert len(data["records"]) > 0
    rec = data["records"][0]
    assert "trade_price" in rec and "bid" in rec and "ask" in rec and "effective_spread" in rec
