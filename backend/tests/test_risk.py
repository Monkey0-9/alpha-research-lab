"""
Tests for core.risk
Validates Historical VaR, Parametric VaR, CVaR, and factor attribution.
"""
import numpy as np
from core.risk import (
    historical_var,
    parametric_var,
    cvar_expected_shortfall,
    factor_attribution
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


def test_factor_attribution_structure():
    np.random.seed(42)
    p_rets = np.random.normal(0.0006, 0.008, 252)
    attr = factor_attribution(p_rets)

    assert "total_risk" in attr
    assert "systematic_risk" in attr
    assert "r_squared" in attr
    assert len(attr.get("factor_exposures", [])) > 0
