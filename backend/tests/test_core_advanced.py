"""
Advanced Algorithmic and Quantitative Engine Unit Tests.
Covers:
- Point-in-time temporal boundaries (no lookahead bias)
- Forward-return and triple-barrier target labels
- Volatility targeting and fractional Kelly position sizing
- Historical, Parametric VaR, and Expected Shortfall CVaR
- Constant Proportion Portfolio Insurance (CPPI)
- Mean-Variance, Hierarchical Risk Parity (HRP), and CVaR Portfolio Optimizers
- 3-State Gaussian Mixture Regime Detection
- Almgren-Chriss Optimal Liquidation and TWAP/VWAP Execution
- Population Stability Index (PSI) Feature Drift Detection & Exponential Half-Life
- López de Prado Meta-Labeling System
- Paper Trading Execution Engine
"""
import pytest
import numpy as np
import pandas as pd

from core.pit_store import PointInTimeStore, get_pit_store
from core.labels import generate_labels
from core.sizing import vol_target_sizing, kelly_criterion_sizing
from core.risk import (
    historical_var,
    parametric_var,
    cvar_expected_shortfall,
    cppi_nav_trajectory,
)
from core.portfolio import (
    mean_variance_optimization,
    hierarchical_risk_parity,
    cvar_optimization,
)
from core.regime import RegimeEngine
from core.execution import almgren_chriss_impact, estimate_slippage, simulate_twap_vwap
from core.monitor import calculate_psi, calculate_decay_half_life, get_production_health
from core.meta_labeling import MetaLabelingSystem
from core.paper_trading import PaperTradingEngine


# ==========================================
# 1. Point-in-Time Data Store
# ==========================================
def test_pit_store_temporal_isolation():
    dates = pd.date_range("2023-01-01", "2023-01-10", freq="D")
    data = []
    for d in dates:
        data.append({"date": d, "ticker": "TEST1", "close": 100.0 + (d - dates[0]).days})
        data.append({"date": d, "ticker": "TEST2", "close": 200.0 + (d - dates[0]).days})
    df = pd.DataFrame(data)

    pit = PointInTimeStore(df)
    snapshot = pit.get_snapshot("2023-01-05")
    assert len(snapshot) == 2
    assert snapshot.loc["TEST1", "close"] == 104.0

    # Test universe on date
    universe = pit.get_universe_on("2023-01-05")
    assert universe == ["TEST1", "TEST2"]

    # History as of date
    hist = pit.get_history_as_of("TEST1", "2023-01-05", lookback_days=3)
    assert len(hist) <= 3
    assert hist.index.max() <= pd.Timestamp("2023-01-05")


# ==========================================
# 2. Target Labels Generator
# ==========================================
def test_labels_generation_and_temporal_alignment():
    dates = pd.date_range("2023-01-01", periods=30, freq="B")
    tuples = [(d, "ABC") for d in dates]
    idx = pd.MultiIndex.from_tuples(tuples, names=["date", "ticker"])
    closes = [100.0 * (1.01 ** i) for i in range(30)]
    df = pd.DataFrame({"close": closes}, index=idx)

    labeled = generate_labels(df)
    assert "fwd_return_1d" in labeled.columns
    assert "fwd_return_5d" in labeled.columns
    assert "label_1d" in labeled.columns

    # Check 1-day forward return alignment
    first_ret = labeled.loc[(dates[0], "ABC"), "fwd_return_1d"]
    expected_ret = closes[1] / closes[0] - 1.0
    assert abs(first_ret - expected_ret) < 1e-6
    assert labeled.loc[(dates[0], "ABC"), "label_1d"] == 1


# ==========================================
# 3. Position Sizing
# ==========================================
def test_vol_target_sizing():
    # Target 10% vol on asset with 20% vol -> weight = 0.5
    weight = vol_target_sizing(asset_volatility_annualized=0.20, target_vol_annualized=0.10)
    assert abs(weight - 0.5) < 1e-4

    # Zero or near-zero vol handles safely
    assert vol_target_sizing(0.0) == 0.0

    # Max leverage ceiling
    weight_high = vol_target_sizing(asset_volatility_annualized=0.02, target_vol_annualized=0.10, max_leverage=1.5)
    assert weight_high == 1.5


def test_kelly_criterion_sizing():
    # 60% win rate, 1.5 win/loss ratio, half-kelly
    # full kelly = (0.6 * 1.5 - 0.4) / 1.5 = (0.9 - 0.4) / 1.5 = 0.5 / 1.5 = 0.3333
    # half kelly = 0.1667
    size = kelly_criterion_sizing(win_rate=0.6, win_loss_ratio=1.5, fraction=0.5, max_position=0.25)
    assert abs(size - 0.1667) < 1e-3

    # Negative edge should result in 0 allocation
    assert kelly_criterion_sizing(win_rate=0.3, win_loss_ratio=1.0) == 0.0
    assert kelly_criterion_sizing(win_rate=0.0, win_loss_ratio=1.5) == 0.0


# ==========================================
# 4. Institutional Risk Engine
# ==========================================
def test_var_and_cvar():
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.012, 1000)

    h_var_95 = historical_var(returns, 0.95)
    h_var_99 = historical_var(returns, 0.99)
    p_var_95 = parametric_var(returns, 0.95)
    cvar_95 = cvar_expected_shortfall(returns, 0.95)

    assert h_var_95 > 0
    assert h_var_99 >= h_var_95
    assert p_var_95 > 0
    assert cvar_95 >= h_var_95


def test_cppi_portfolio_insurance():
    nav_series = np.array([1.0, 1.05, 0.98, 0.92, 0.89, 0.95])
    cppi = cppi_nav_trajectory(nav_series, floor=0.90, multiplier=3.0)
    assert cppi["floor"] == 0.90
    assert len(cppi["exposure_history"]) == 6
    # When nav is 0.89 (< floor 0.90), cushion is 0, target exposure is 0
    assert cppi["exposure_history"][4] == 0.0


# ==========================================
# 5. Portfolio Optimizers
# ==========================================
def test_mean_variance_optimization():
    expected_returns = np.array([0.12, 0.10, 0.08, 0.06])
    cov = np.diag([0.04, 0.03, 0.02, 0.01])
    weights = mean_variance_optimization(expected_returns, cov, risk_aversion=1.0, max_weight=0.50)

    assert len(weights) == 4
    assert abs(np.sum(weights) - 1.0) < 1e-4
    assert all(w >= -1e-6 for w in weights)
    assert all(w <= 0.50 + 1e-4 for w in weights)


def test_hierarchical_risk_parity():
    np.random.seed(42)
    returns_matrix = np.random.normal(0.001, 0.015, size=(252, 6))
    weights = hierarchical_risk_parity(returns_matrix)

    assert len(weights) == 6
    assert abs(np.sum(weights) - 1.0) < 1e-4
    assert all(w > 0 for w in weights)


def test_cvar_optimization():
    np.random.seed(42)
    returns_matrix = np.random.normal(0.0008, 0.012, size=(252, 5))
    weights = cvar_optimization(returns_matrix, alpha=0.05, max_weight=0.35)

    assert len(weights) == 5
    assert abs(np.sum(weights) - 1.0) < 1e-4
    assert all(w >= -1e-6 for w in weights)


# ==========================================
# 6. Regime Detection Engine
# ==========================================
def test_regime_engine():
    np.random.seed(42)
    dates = pd.date_range("2021-01-01", periods=300, freq="B")
    rets = pd.Series(np.random.normal(0.0005, 0.01, 300), index=dates)

    engine = RegimeEngine()
    regimes_df = engine.fit_regimes(rets)
    assert "regime_id" in regimes_df.columns
    assert set(regimes_df["regime_id"].unique()).issubset({0, 1, 2})

    robustness = engine.test_robustness(rets)
    assert len(robustness) == 3
    assert all("sharpe" in r for r in robustness)


# ==========================================
# 7. Execution and Market Impact
# ==========================================
def test_almgren_chriss_execution():
    res = almgren_chriss_impact(order_size=50000, adv=2000000, urgency=1.0, intervals=5)
    assert len(res["holdings"]) == 6
    assert len(res["trade_schedule"]) == 5
    # Total shares traded must equal initial order size
    assert abs(sum(res["trade_schedule"]) - 50000) < 1.0
    assert res["expected_impact_cost"] > 0


def test_slippage_and_algorithms():
    slippage = estimate_slippage(spread_bps=2.0, volatility=0.015, order_size=10000, adv=1000000)
    assert slippage > 1.0

    twap = simulate_twap_vwap(order_size=20000, intervals=10, algo="TWAP")
    assert len(twap["fills"]) == 10
    total_shares = sum(f["shares"] for f in twap["fills"])
    assert abs(total_shares - 20000) < 1.0

    vwap = simulate_twap_vwap(order_size=20000, intervals=10, algo="VWAP")
    assert len(vwap["fills"]) == 10


# ==========================================
# 8. Monitoring: PSI & Decay Half-Life
# ==========================================
def test_population_stability_index():
    np.random.seed(42)
    expected = np.random.normal(0, 1, 1000)
    actual_same = np.random.normal(0, 1, 1000)
    actual_drift = np.random.normal(1.5, 1.2, 1000)

    psi_same = calculate_psi(expected, actual_same)
    psi_drift = calculate_psi(expected, actual_drift)

    assert psi_same < 0.10  # Stable
    assert psi_drift > 0.20  # Significant drift


def test_decay_half_life():
    # Monotonically decaying IC
    ic_decay = np.array([0.10 * np.exp(-0.02 * i) for i in range(50)])
    decay_res = calculate_decay_half_life(ic_decay)

    assert decay_res["half_life_days"] > 0
    assert "status" in decay_res

    health = get_production_health()
    assert health["status"] == "HEALTHY"
    assert health["uptime_seconds"] > 0


# ==========================================
# 9. Meta-Labeling López de Prado System
# ==========================================
def test_meta_labeling_system():
    np.random.seed(42)
    X = np.random.normal(0, 1, size=(200, 5))
    # Synthetic return correlated with first feature
    returns = X[:, 0] * 0.05 + np.random.normal(0, 0.02, size=200)

    system = MetaLabelingSystem(confidence_threshold=0.55)
    system.fit(X, returns)

    signals = system.generate_signals(X[:20])
    assert len(signals["filtered_signals"]) == 20
    assert signals["trade_execution_rate"] <= 1.0
    assert all(0.0 <= p <= 1.0 for p in signals["confidence_probabilities"])


# ==========================================
# 10. Paper Trading Simulator
# ==========================================
def test_paper_trading_simulator():
    engine = PaperTradingEngine(initial_capital=500_000.0)
    state = engine.get_live_portfolio_state()

    assert state["initial_capital"] == 500_000.0
    assert state["current_nav"] > 0
    assert len(state["positions"]) > 0
    assert len(state["recent_fills"]) > 0
