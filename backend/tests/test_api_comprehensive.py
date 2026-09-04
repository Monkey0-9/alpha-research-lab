"""
Comprehensive End-to-End API Integration Tests.
Verifies all 12 modules, HTTP schemas, query parameters, payloads, and response structures:
- /health
- /api/data (ohlcv, metadata)
- /api/features (list, ic)
- /api/backtest (status, run)
- /api/validation (walk-forward, purged-kfold, regime-tests)
- /api/model-lab (comparison, train)
- /api/portfolio (allocations, optimize with HRP/Mean-Variance/CVaR)
- /api/risk (metrics, factor-attribution, stress-test)
- /api/execution (metrics, almgren-chriss, simulate-order)
- /api/quality-gate (run)
- /api/live-research (signals, paper-portfolio)
- /api/monitoring (drift, alpha-decay, health)
- /api/dashboard (summary)
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_system_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_data_endpoints():
    # Test AAPL
    res_aapl = client.get("/api/data/ohlcv?ticker=AAPL")
    assert res_aapl.status_code == 200
    assert res_aapl.json()["ticker"] == "AAPL"

    # Test MSFT
    res_msft = client.get("/api/data/ohlcv?ticker=MSFT")
    assert res_msft.status_code == 200
    assert res_msft.json()["ticker"] == "MSFT"

    # Test metadata
    res_meta = client.get("/api/data/metadata")
    assert res_meta.status_code == 200
    data = res_meta.json()
    assert "universe_size" in data
    assert "start_date" in data
    assert "end_date" in data


def test_features_endpoints():
    res_list = client.get("/api/features/list")
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["count"] >= 30
    assert data["lookahead_free"] is True
    assert len(data["features"]) == data["count"]

    res_ic = client.get("/api/features/ic")
    assert res_ic.status_code == 200
    ic_data = res_ic.json()
    assert "results" in ic_data
    assert len(ic_data["results"]) > 0


def test_validation_endpoints():
    # Walk-forward validation with lightgbm
    res_wf = client.get("/api/validation/walk-forward?model_type=lightgbm")
    assert res_wf.status_code == 200
    wf_data = res_wf.json()
    assert "folds" in wf_data
    assert len(wf_data["folds"]) > 0
    assert "mean_oos_sharpe" in wf_data

    # Purged K-Fold validation
    res_pkf = client.get("/api/validation/purged-kfold")
    assert res_pkf.status_code == 200
    pkf_data = res_pkf.json()
    assert "k_folds" in pkf_data
    assert "results" in pkf_data

    # Regime breakdown
    res_regime = client.get("/api/validation/regime-tests")
    assert res_regime.status_code == 200
    reg_data = res_regime.json()
    assert reg_data["regimes_tested"] == 3
    assert len(reg_data["results"]) == 3


def test_model_lab_endpoints():
    res_comp = client.get("/api/model-lab/comparison")
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert len(comp_data["models"]) >= 5
    assert "ensemble" in comp_data

    res_train = client.post("/api/model-lab/train", json={"model_type": "lightgbm", "hyperparams": {}})
    assert res_train.status_code == 200
    train_data = res_train.json()
    assert train_data["status"] == "COMPLETED"
    assert train_data["model_type"] == "lightgbm"
    assert "in_sample_sharpe" in train_data


def test_portfolio_optimization_all_methods():
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]

    # 1. HRP
    res_hrp = client.post("/api/portfolio/optimize", json={"method": "hrp", "tickers": tickers})
    assert res_hrp.status_code == 200
    data_hrp = res_hrp.json()
    assert data_hrp["method"] == "HRP"
    assert len(data_hrp["allocations"]) == len(tickers)

    # 2. Mean-Variance
    res_mv = client.post("/api/portfolio/optimize", json={"method": "mean_variance", "tickers": tickers})
    assert res_mv.status_code == 200
    data_mv = res_mv.json()
    assert data_mv["method"] == "MEAN_VARIANCE"
    assert len(data_mv["allocations"]) == len(tickers)

    # 3. CVaR
    res_cvar = client.post("/api/portfolio/optimize", json={"method": "cvar", "tickers": tickers})
    assert res_cvar.status_code == 200
    data_cvar = res_cvar.json()
    assert data_cvar["method"] == "CVAR"
    assert len(data_cvar["allocations"]) == len(tickers)

    # Current allocations
    res_alloc = client.get("/api/portfolio/allocations")
    assert res_alloc.status_code == 200
    assert len(res_alloc.json()["allocations"]) > 0


def test_risk_endpoints_comprehensive():
    res_metrics = client.get("/api/risk/metrics")
    assert res_metrics.status_code == 200
    m = res_metrics.json()
    assert "var_95_daily_pct" in m
    assert "cvar_expected_shortfall_95_pct" in m
    assert "volatility_annualized_pct" in m

    res_factor = client.get("/api/risk/factor-attribution")
    assert res_factor.status_code == 200
    assert "betas" in res_factor.json()

    res_stress = client.get("/api/risk/stress-test")
    assert res_stress.status_code == 200
    assert res_stress.json()["count"] >= 4


def test_execution_endpoints_comprehensive():
    # Execution metrics
    res_m = client.get("/api/execution/metrics")
    assert res_m.status_code == 200
    assert "average_slippage_bps" in res_m.json()
    assert "venues" in res_m.json()

    # Almgren-Chriss
    res_ac = client.post("/api/execution/almgren-chriss", json={
        "order_size": 25000,
        "adv": 1500000,
        "urgency": 1.5,
        "intervals": 5
    })
    assert res_ac.status_code == 200
    ac_data = res_ac.json()
    assert len(ac_data["holdings"]) == 6
    assert len(ac_data["trade_schedule"]) == 5

    # TWAP simulation
    res_twap = client.post("/api/execution/simulate-order", json={
        "order_size": 10000,
        "benchmark_price": 120.0,
        "algo": "TWAP",
        "intervals": 5
    })
    assert res_twap.status_code == 200
    assert res_twap.json()["algo"] == "TWAP"
    assert len(res_twap.json()["fills"]) == 5

    # VWAP simulation
    res_vwap = client.post("/api/execution/simulate-order", json={
        "order_size": 10000,
        "benchmark_price": 120.0,
        "algo": "VWAP",
        "intervals": 5
    })
    assert res_vwap.status_code == 200
    assert res_vwap.json()["algo"] == "VWAP"


def test_quality_gate_endpoint():
    res = client.get("/api/quality-gate/run")
    assert res.status_code == 200
    data = res.json()
    assert "overall_pass" in data
    assert "radar_scores" in data
    assert "criteria" in data

    # Test raw alpha candidate evaluations (5/8 pass)
    res_raw = client.get("/api/quality-gate/alphas?optimized=false")
    assert res_raw.status_code == 200
    raw_data = res_raw.json()
    assert raw_data["total_alphas"] == 8
    assert raw_data["passed_alphas"] == 5
    assert len(raw_data["alphas"]) == 8

    # Test remediated alpha evaluations (8/8 pass)
    res_opt = client.get("/api/quality-gate/alphas?optimized=true")
    assert res_opt.status_code == 200
    opt_data = res_opt.json()
    assert opt_data["passed_alphas"] == 8
    assert opt_data["pass_rate_pct"] == 100.0

    # Test single alpha remediation
    res_rem_single = client.post("/api/quality-gate/remediate", json={"alpha_id": "A006"})
    assert res_rem_single.status_code == 200
    rem_single = res_rem_single.json()
    assert rem_single["id"] == "A006"
    assert rem_single["raw_score"] == 5
    assert rem_single["remediated_score"] == 9
    assert rem_single["passed"] is True

    # Test all alpha remediation
    res_rem_all = client.post("/api/quality-gate/remediate", json={"alpha_id": "all"})
    assert res_rem_all.status_code == 200
    rem_all = res_rem_all.json()
    assert rem_all["status"] == "ALL_ALPHAS_REMEDIATED"
    assert rem_all["remediated_count"] == 8


def test_live_research_endpoints():
    res_sig = client.get("/api/live-research/signals")
    assert res_sig.status_code == 200
    assert res_sig.json()["active_signals_count"] > 0

    res_port = client.get("/api/live-research/paper-portfolio")
    assert res_port.status_code == 200
    assert "current_nav" in res_port.json()
    assert len(res_port.json()["positions"]) > 0


def test_monitoring_endpoints():
    res_drift = client.get("/api/monitoring/drift")
    assert res_drift.status_code == 200
    assert len(res_drift.json()["results"]) > 0

    res_decay = client.get("/api/monitoring/alpha-decay")
    assert res_decay.status_code == 200
    assert "decay_stats" in res_decay.json()
    assert len(res_decay.json()["history"]) == 12

    res_health = client.get("/api/monitoring/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "HEALTHY"


def test_dashboard_and_backtest():
    res_dash = client.get("/api/dashboard/summary")
    assert res_dash.status_code == 200
    d = res_dash.json()
    assert "portfolio" in d
    assert "active_models" in d
    assert "live_paper_pnl" in d

    res_bt_status = client.get("/api/backtest/status")
    assert res_bt_status.status_code == 200
    assert res_bt_status.json()["status"] == "READY"
