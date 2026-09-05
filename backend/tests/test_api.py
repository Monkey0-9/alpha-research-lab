"""
Comprehensive API Integration Tests.
Verifies HTTP contract for all 12 modules:
- /health
- /api/data/ohlcv
- /api/features/list
- /api/features/ic
- /api/backtest/status
- /api/validation/walk-forward
- /api/validation/regime-tests
- /api/model-lab/comparison
- /api/portfolio/allocations
- /api/risk/metrics
- /api/execution/metrics
- /api/quality-gate/run
- /api/live-research/signals
- /api/monitoring/drift
- /api/dashboard/summary
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_data_ohlcv():
    res = client.get("/api/data/ohlcv?ticker=AAPL")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "AAPL"
    assert len(data["data"]) > 0
    # verify OHLCV structure
    first = data["data"][0]
    assert "open" in first and "close" in first and "volume" in first


def test_features_list():
    res = client.get("/api/features/list")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 30
    assert data["lookahead_free"] is True


def test_features_ic():
    res = client.get("/api/features/ic")
    assert res.status_code == 200
    assert len(res.json()["results"]) > 0


def test_validation_walk_forward():
    res = client.get("/api/validation/walk-forward")
    assert res.status_code == 200
    data = res.json()
    assert len(data["folds"]) > 0
    assert "mean_oos_sharpe" in data


def test_model_lab_comparison():
    res = client.get("/api/model-lab/comparison")
    assert res.status_code == 200
    data = res.json()
    assert len(data["models"]) >= 5
    assert "ensemble" in data


def test_portfolio_endpoints():
    res = client.get("/api/portfolio/allocations")
    assert res.status_code == 200
    assert len(res.json()["allocations"]) > 0

    opt_res = client.post("/api/portfolio/optimize", json={"method": "hrp", "tickers": ["AAPL", "MSFT", "NVDA"]})
    assert opt_res.status_code == 200
    assert len(opt_res.json()["allocations"]) == 3


def test_risk_metrics():
    res = client.get("/api/risk/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "var_95_daily_pct" in data
    assert "cvar_expected_shortfall_95_pct" in data


def test_execution_endpoints():
    res = client.get("/api/execution/metrics")
    assert res.status_code == 200
    assert "average_slippage_bps" in res.json()

    ac_res = client.post("/api/execution/almgren-chriss", json={"order_size": 50000, "adv": 2000000, "urgency": 1.0, "intervals": 5})
    assert ac_res.status_code == 200
    assert len(ac_res.json()["holdings"]) == 6


def test_quality_gate():
    res = client.get("/api/quality-gate/run")
    assert res.status_code == 200
    data = res.json()
    assert "overall_pass" in data
    assert "criteria" in data


def test_live_research():
    res = client.get("/api/live-research/signals")
    assert res.status_code == 200
    assert len(res.json()["signals"]) > 0


def test_monitoring():
    res = client.get("/api/monitoring/drift")
    assert res.status_code == 200
    assert len(res.json()["results"]) > 0


def test_dashboard_summary():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "portfolio" in data
    assert "live_paper_pnl" in data


def test_alpha_discovery_endpoints():
    res_hyp = client.get("/api/alpha-discovery/hypotheses")
    assert res_hyp.status_code == 200
    # Hypotheses requires a hypothesis store — empty until registered
    assert isinstance(res_hyp.json(), list)

    res_gp = client.post("/api/alpha-discovery/gp", json={"population_size": 20, "generations": 2})
    assert res_gp.status_code == 200
    assert "best_formula" in res_gp.json()


def test_statistical_engine_endpoints():
    res_mtc = client.get("/api/statistical-engine/mtc")
    assert res_mtc.status_code == 200
    # GET returns REQUIRES_INPUT message
    data = res_mtc.json()
    assert "status" in data or "bonferroni_significant" in data

    res_dsr = client.post("/api/statistical-engine/dsr", json={"sharpe": 1.65, "n_trials": 100})
    assert res_dsr.status_code == 200
    assert "deflated_sharpe" in res_dsr.json()


def test_backtest_run():
    res = client.post("/api/backtest/run", json={"start_date": "2022-01-01", "end_date": "2023-12-31", "model_type": "lightgbm"})
    assert res.status_code == 200
    data = res.json()
    assert "sharpe" in data or "annualized_sharpe" in data

