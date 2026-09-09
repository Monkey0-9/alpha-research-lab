"""
Tests for core.risk
Validates Historical VaR, Parametric VaR, CVaR, and factor attribution.
"""
import numpy as np
from core.risk import (
    historical_var,
    parametric_var,
    cornish_fisher_var,
    cvar_expected_shortfall,
    factor_attribution,
    cppi_nav_trajectory,
    HistoricalStressTester,
)


def test_var_and_cvar_bounds():
    np.random.seed(42)
    rets = np.random.normal(0.0006, 0.012, 1000)

    h_var_95 = historical_var(rets, 0.95)
    p_var_95 = parametric_var(rets, 0.95)
    cvar_95 = cvar_expected_shortfall(rets, 0.95)

    assert h_var_95 > 0
    assert p_var_95 > 0
    # CVaR (Expected Shortfall) >= VaR for continuous distributions
    assert cvar_95 >= h_var_95 * 0.95


def test_cornish_fisher_var():
    np.random.seed(42)
    # Negatively skewed, fat-tailed distribution
    rets = np.concatenate([
        np.random.normal(0.001, 0.01, 950),
        np.random.normal(-0.05, 0.02, 50),
    ])

    p_var_99 = parametric_var(rets, 0.99)
    cf_var_99 = cornish_fisher_var(rets, 0.99)

    # Cornish-Fisher VaR should adjust upward for negative skewness and excess kurtosis
    assert cf_var_99 > 0
    assert cf_var_99 >= p_var_99 * 0.9


def test_cppi_nav_trajectory():
    np.random.seed(42)
    # Simulated NAV series declining towards floor
    nav_series = np.linspace(1.0, 0.88, 50)
    res = cppi_nav_trajectory(
        nav_series=nav_series,
        floor=0.85,
        multiplier=3.0,
    )

    assert "floor" in res
    assert "current_cushion" in res
    assert "target_exposure" in res
    assert "exposure_history" in res
    assert res["floor"] == 0.85
    assert res["current_cushion"] > 0
    assert len(res["exposure_history"]) == 50


def test_historical_stress_tester():
    weights = {"AAPL": 0.40, "MSFT": 0.35, "NVDA": 0.25}
    res = HistoricalStressTester.run_stress_scenarios(weights)

    assert "scenarios" in res
    assert len(res["scenarios"]) >= 4
    for sc in res["scenarios"].values():
        assert "name" in sc
        assert "portfolio_return_pct" in sc
        assert "worst_contributor" in sc
    # 2008 Lehman GFC and 2020 COVID inflict severe negative impact on long equities
    assert res["scenarios"]["LEHMAN_2008"]["portfolio_return_pct"] < -20.0
    assert res["scenarios"]["COVID_2020"]["portfolio_return_pct"] < -20.0
    assert res["worst_scenario_loss_pct"] > 20.0
    # SVB 2023 reflects econometric mega-cap tech flight to safety (+2%)
    assert res["scenarios"]["SVB_2023"]["portfolio_return_pct"] > 0.0


def test_factor_attribution_structure():
    np.random.seed(42)
    p_rets = np.random.normal(0.0006, 0.008, 252)

    # 1. Test fail-closed zero-fallback behavior when factor dataset is missing
    attr_none = factor_attribution(p_rets)
    assert attr_none["status"] == "RISK_MODEL_UNAVAILABLE"
    assert attr_none["systematic_risk"] == 0.0
    assert attr_none["r_squared"] == 0.0
    assert len(attr_none["factor_exposures"]) == 0

    # 2. Test insufficient sample length handling (< 10 observations)
    attr_short = factor_attribution(p_rets[:5])
    assert attr_short["status"] == "INSUFFICIENT_DATA"

    # 3. Test factor attribution structure with provided empirical factor panel
    mkt = np.random.normal(0.0004, 0.010, 252)
    smb = np.random.normal(0.0001, 0.005, 252)
    attr = factor_attribution(p_rets, factor_returns={"Market": mkt, "Size": smb})

    assert attr["status"] == "SUCCESS"
    assert "total_risk" in attr
    assert "systematic_risk" in attr
    assert "r_squared" in attr
    assert len(attr.get("factor_exposures", [])) > 0
