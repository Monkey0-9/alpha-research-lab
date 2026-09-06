"""
Tests for Capacity Model & Factor Attribution Engine.
"""
import numpy as np
from core.capacity import capacity_model
from core.factor_attribution import factor_attribution


def test_capacity_model_drag_increases_with_aum():
    # Strategy with 25% gross return, 12% vol, 1.5 annual turnover
    res = capacity_model.evaluate_capacity(
        gross_annual_return=0.25,
        annual_volatility=0.12,
        annual_turnover=1.5
    )

    tiers = res["tiers"]
    assert len(tiers) >= 5
    # Drag must monotonically increase with AUM
    drags = [t["total_drag_bps"] for t in tiers]
    for i in range(len(drags) - 1):
        assert drags[i] <= drags[i + 1]

    # Net Sharpe must monotonically decrease with AUM
    net_sharpes = [t["net_sharpe"] for t in tiers]
    for i in range(len(net_sharpes) - 1):
        assert net_sharpes[i] >= net_sharpes[i + 1]

    assert res["max_sustainable_capacity_aum"] > 0


def test_factor_attribution_genuine_vs_market_beta():
    rng = np.random.default_rng(42)
    n_days = 252

    # Genuine alpha: daily mean positive alpha + small market exposure
    mkt = rng.normal(0.0004, 0.010, n_days)
    true_alpha_ret = 0.0008 + 0.3 * mkt + rng.normal(0.0, 0.003, n_days)

    attr = factor_attribution.attribute_returns(true_alpha_ret, market_returns=mkt)
    assert attr.alpha_annualized > 0.05
    assert attr.alpha_t_stat > 2.0
    assert attr.is_genuine_alpha is True
    assert 0.1 <= attr.market_beta <= 0.5
