"""
Test Suite: High-Performance C Native Kernels and KDB+/Q Vector Engine
Validates sub-microsecond C computational primitives, Q vector algebra, and API endpoints.
"""
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.native.native_bridge import accelerator, _c_lib
from backend.native.q_engine.q_service import q_engine

client = TestClient(app)


# ── C NATIVE ENGINE UNIT TESTS ────────────────────────────────────────────────

def test_c_engine_loaded():
    """Verify that the C shared library was compiled and loaded successfully."""
    assert _c_lib is not None, "C native engine must be loaded."
    assert hasattr(_c_lib, "c_kalman_filter")
    assert hasattr(_c_lib, "c_order_flow_imbalance")
    assert hasattr(_c_lib, "c_microprice")
    assert hasattr(_c_lib, "c_ewma_volatility")
    assert hasattr(_c_lib, "c_rescaled_range_hurst")


def test_c_rolling_zscore():
    """Verify C rolling z-score accuracy against analytical benchmark."""
    vals = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0], dtype=np.float64)
    z = accelerator.fast_zscore(vals, window=5)
    assert len(z) == len(vals)
    # The last element of [15, 16, 17, 18, 19] has mean 17, std ~ 1.58, z > 1.0
    assert z[-1] > 1.0


def test_c_kalman_filter():
    """Verify C Kalman filter noise reduction."""
    np.random.seed(42)
    true_val = 100.0
    noisy = true_val + np.random.normal(0, 2.0, 50)
    res = accelerator.fast_kalman_filter(noisy, q_process_noise=1e-5, r_measurement_noise=0.1)

    assert "filtered_state" in res
    assert len(res["filtered_state"]) == 50
    # Final estimate should converge close to true value
    assert abs(res["filtered_state"][-1] - true_val) < 1.5
    # Variance should decrease over time
    assert res["filtered_cov"][-1] < res["filtered_cov"][0]


def test_c_order_flow_imbalance_and_microprice():
    """Verify C OFI and microprice calculation."""
    bp = np.array([100.0, 100.05, 100.05, 100.00])
    bs = np.array([500.0, 600.0, 400.0, 300.0])
    ap = np.array([100.10, 100.15, 100.15, 100.10])
    as_ = np.array([400.0, 500.0, 700.0, 800.0])

    mp = accelerator.fast_microprice(bp, bs, ap, as_)
    assert len(mp) == 4
    # Microprice must lie between bid and ask
    for i in range(4):
        assert bp[i] <= mp[i] <= ap[i]

    ofi = accelerator.fast_order_flow_imbalance(bp, bs, ap, as_)
    assert len(ofi) == 4
    assert ofi[0] == 0.0  # Initial quote has no delta


def test_c_ewma_volatility_and_hurst():
    """Verify C EWMA volatility and Hurst exponent calculation."""
    returns = np.array([0.01, -0.015, 0.02, -0.005, 0.012, -0.018] * 10)
    vol = accelerator.fast_ewma_volatility(returns, lambda_decay=0.94)
    assert len(vol) == len(returns)
    assert np.all(vol > 0.0)

    prices = 100.0 * np.cumprod(1.0 + returns)
    hurst = accelerator.fast_hurst_exponent(prices, window=20)
    assert len(hurst) == len(prices)
    assert np.all((hurst >= 0.0) & (hurst <= 1.0))


# ── Q / KDB+ VECTOR ENGINE UNIT TESTS ─────────────────────────────────────────

def test_q_vwap():
    """Verify Q vector calculation: volumes wavg prices."""
    prices = np.array([100.0, 102.0, 101.0])
    vols = np.array([100.0, 200.0, 100.0])
    vwap = accelerator.q_vwap(prices, vols)
    # Expected: (100*100 + 102*200 + 101*100) / 400 = (10000 + 20400 + 10100) / 400 = 40500 / 400 = 101.25
    assert abs(vwap - 101.25) < 1e-4


def test_q_asof_join():
    """Verify Q Asof Join: aj[`sym`time; trades; quotes]."""
    res = accelerator.q_asof_join()
    assert isinstance(res, pd.DataFrame)
    assert "bid" in res.columns
    assert "ask" in res.columns
    assert "price" in res.columns
    assert "eff_spread_bps" in res.columns
    assert len(res) > 0


def test_q_bars():
    """Verify Q bar aggregation (OHLCV + VWAP)."""
    bars = accelerator.q_bars(bar_seconds=60)
    assert isinstance(bars, pd.DataFrame)
    assert "open" in bars.columns
    assert "vwap" in bars.columns
    assert len(bars) > 0


def test_q_query_execution():
    """Verify production Q vector query execution."""
    res = accelerator.q_query("select vwap: size wavg price by sym from trades")
    assert res["status"] == "SUCCESS"
    assert "elapsed_microseconds" in res
    assert res["elapsed_microseconds"] >= 0.0


# ── FASTAPI ENDPOINT INTEGRATION TESTS ────────────────────────────────────────

def test_api_c_kalman():
    resp = client.post("/api/native/c/kalman", json={
        "observations": [100.0, 100.5, 99.8, 101.2, 100.9],
        "q_process_noise": 1e-5,
        "r_measurement_noise": 0.01
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "filtered_state" in data
    assert len(data["filtered_state"]) == 5


def test_api_c_hurst():
    resp = client.post("/api/native/c/hurst", json={"window": 15})
    assert resp.status_code == 200
    data = resp.json()
    assert "current_hurst" in data
    assert "regime" in data


def test_api_c_microprice():
    resp = client.post("/api/native/c/microprice", json={
        "bid_prices": [150.0, 150.1],
        "bid_sizes": [100.0, 200.0],
        "ask_prices": [150.2, 150.3],
        "ask_sizes": [150.0, 250.0]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "microprice" in data
    assert "order_flow_imbalance" in data


def test_api_q_query():
    resp = client.post("/api/native/q/query", json={
        "query": "select open, high, low, close, volume, vwap from trades"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"


def test_api_q_ticks_and_asof():
    resp_ticks = client.get("/api/native/q/ticks?limit=10")
    assert resp_ticks.status_code == 200
    assert len(resp_ticks.json()["trades"]) == 10

    resp_aj = client.get("/api/native/q/asof-join?limit=10")
    assert resp_aj.status_code == 200
    assert len(resp_aj.json()["data"]) == 10


def test_api_polyglot_benchmarks():
    resp = client.get("/api/native/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["benchmarks"]) >= 4
