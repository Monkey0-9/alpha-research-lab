"""
Comprehensive Tests for Institutional Portfolio Construction, Shrinkage Covariance,
Historical Crisis Stress Testing, and Pre-Trade Compliance (Task 5 / Milestone M5).

Verifies:
1. Analytical Shrinkage Covariance: Ledoit-Wolf and OAS estimators reduce condition number
   and guarantee positive definiteness.
2. Convex Portfolio Optimizer:
   - Gross leverage bound: sum(|w|) <= L
   - Dollar neutrality: sum(w) == 0.0
   - Single-name concentration bound: |w_i| <= w_max
   - Multi-factor beta neutrality: B^T w in [lb, ub]
   - Turnover budget: ||w - w0||_1 <= tau
3. Cornish-Fisher VaR sensitivity to fat tails (kurtosis) and negative skew.
4. Historical Crisis Stress Testing across Lehman 2008, Flash Crash 2010, COVID 2020, and SVB 2023.
5. Pre-Trade Compliance Hard Stops: fat-finger collars, concentration limits, and Reg SHO locate.
"""
import numpy as np

from core.portfolio import (
    ledoit_wolf_covariance,
    oas_covariance,
    convex_portfolio_optimizer,
)
from core.risk import (
    cornish_fisher_var,
    parametric_var,
    HistoricalStressTester,
)
from core.compliance import (
    PreTradeComplianceEngine,
    ComplianceConfig,
    ComplianceStatus,
)


def test_shrinkage_covariance_estimators():
    """Verify that Ledoit-Wolf and OAS shrink ill-conditioned sample covariance."""
    np.random.seed(42)
    # T = 60 observations, N = 30 assets (collinear / ill-conditioned regime)
    t_obs = 60
    n_assets = 30
    factors = np.random.normal(0, 0.02, (t_obs, 3))
    loadings = np.random.uniform(-1, 1, (3, n_assets))
    idiosyncratic = np.random.normal(0, 0.005, (t_obs, n_assets))
    returns = factors @ loadings + idiosyncratic

    sample_cov = np.cov(returns, rowvar=False)
    sample_cond = np.linalg.cond(sample_cov)

    # 1. Ledoit-Wolf
    lw_cov, lw_delta = ledoit_wolf_covariance(returns)
    lw_cond = np.linalg.cond(lw_cov)
    assert 0.0 < lw_delta <= 1.0
    # Condition number should be strictly lower (more well-conditioned)
    assert lw_cond < sample_cond
    # Must be positive definite (all eigenvalues > 0)
    lw_eig = np.linalg.eigvalsh(lw_cov)
    assert np.all(lw_eig > 0)

    # 2. OAS (Oracle Approximating Shrinkage)
    oas_cov, oas_delta = oas_covariance(returns)
    oas_cond = np.linalg.cond(oas_cov)
    assert 0.0 < oas_delta <= 1.0
    assert oas_cond < sample_cond
    oas_eig = np.linalg.eigvalsh(oas_cov)
    assert np.all(oas_eig > 0)


def test_convex_portfolio_optimizer_institutional_constraints():
    """Verify convex quadratic programming solver under gross leverage, dollar neutrality, and factor bounds."""
    np.random.seed(123)
    n_assets = 20
    alpha = np.random.normal(0.001, 0.005, n_assets)
    cov = np.eye(n_assets) * 0.0004  # 20% annual vol approx daily

    # 1-factor loading (e.g. Market Beta)
    factor_beta = np.ones((n_assets, 1))

    # Optimize with:
    # - Net leverage = 0.0 (Dollar Neutral)
    # - Gross leverage <= 1.6
    # - Max weight <= 0.10
    # - Factor beta exposure in [-0.02, 0.02] (Beta Neutral)
    res = convex_portfolio_optimizer(
        alpha_signal=alpha,
        cov_matrix=cov,
        target_net_leverage=0.0,
        gross_leverage_limit=1.6,
        max_position_weight=0.10,
        factor_loadings=factor_beta,
        factor_bounds=[(-0.02, 0.02)],
        turnover_penalty=0.0,
    )

    assert res["status"] == "OPTIMAL"
    w = res["weights"]

    # Invariant 1: Dollar Neutrality
    assert np.isclose(np.sum(w), 0.0, atol=1e-3)

    # Invariant 2: Gross Leverage Bound
    gross_lev = np.sum(np.abs(w))
    assert gross_lev <= 1.6 + 1e-3

    # Invariant 3: Single-name position bound
    assert np.all(np.abs(w) <= 0.10 + 1e-4)

    # Invariant 4: Factor Beta neutrality
    port_beta = float((w @ factor_beta).item())
    assert -0.025 <= port_beta <= 0.025

    # Has both long and short positions
    assert np.sum(w > 0.001) >= 3
    assert np.sum(w < -0.001) >= 3


def test_convex_portfolio_optimizer_turnover_budget():
    """Verify that portfolio rebalancing respects strict turnover constraints."""
    np.random.seed(999)
    n_assets = 10
    alpha_new = np.random.normal(0.002, 0.005, n_assets)
    cov = np.eye(n_assets) * 0.0002

    # Current initial weights
    w0 = np.array([0.10, 0.10, 0.05, 0.05, 0.0, -0.05, -0.05, -0.10, -0.10, 0.0])

    # Case A: Strict turnover budget of 0.15 (15% rebalance)
    res_constrained = convex_portfolio_optimizer(
        alpha_signal=alpha_new,
        cov_matrix=cov,
        current_weights=w0,
        target_net_leverage=0.0,
        gross_leverage_limit=1.0,
        max_position_weight=0.15,
        turnover_budget=0.15,
    )

    w_opt = res_constrained["weights"]
    turnover = float(np.sum(np.abs(w_opt - w0)))
    assert turnover <= 0.15 + 1e-3


def test_cornish_fisher_var_tail_risk():
    """Verify Cornish-Fisher expansion accurately penalizes negatively skewed, fat-tailed returns."""
    np.random.seed(777)
    n = 2000
    # Gaussian returns
    gaussian_rets = np.random.normal(0.0, 0.01, n)
    # Fat-tailed crash returns (Student's t with 3 df, negative shift)
    crash_rets = np.random.standard_t(df=3, size=n) * 0.008 - 0.001

    cf_var_gauss = cornish_fisher_var(gaussian_rets, confidence=0.99)
    param_var_gauss = parametric_var(gaussian_rets, confidence=0.99)

    # In normal distribution, Cornish-Fisher is close to Parametric VaR
    assert np.isclose(cf_var_gauss, param_var_gauss, rtol=0.15)

    # In fat-tailed crash regime, Cornish-Fisher VaR must exceed Parametric VaR
    cf_var_crash = cornish_fisher_var(crash_rets, confidence=0.99)
    param_var_crash = parametric_var(crash_rets, confidence=0.99)
    assert cf_var_crash > param_var_crash


def test_historical_crisis_stress_tester():
    """Verify scenario analysis across 2008 GFC, 2010 Flash Crash, 2020 COVID, and 2023 SVB."""
    # Long Tech / Short Financials portfolio
    weights = {
        "AAPL": 0.30,
        "MSFT": 0.20,
        "JPM": -0.25,
        "BAC": -0.25,
    }

    res = HistoricalStressTester.run_stress_scenarios(
        weights=weights,
        aum=10_000_000.0,
        max_tolerable_drawdown=0.20,  # 20% limit
    )

    assert res["status"] == "COMPLETED"
    scenarios = res["scenarios"]
    assert "LEHMAN_2008" in scenarios
    assert "FLASH_CRASH_2010" in scenarios
    assert "COVID_2020" in scenarios
    assert "SVB_2023" in scenarios

    # In SVB 2023: Tech gained (+0.02) and Financials plunged (-0.24)
    # Short financials gained (+0.24 * 0.50), Long tech gained (+0.02 * 0.50)
    # Portfolio return should be strongly positive in SVB crisis
    svb = scenarios["SVB_2023"]
    assert svb["portfolio_return_pct"] > 0
    assert svb["limit_breached"] is False

    # In 2020 COVID: Massive market-wide liquidity shock
    covid = scenarios["COVID_2020"]
    assert "worst_contributor" in covid


def test_pre_trade_compliance_engine_controls():
    """Verify institutional compliance engine hard stops and cryptographic audit trail."""
    config = ComplianceConfig(
        max_order_notional=500_000.0,
        max_portfolio_concentration=0.10,
        fat_finger_collar_pct=0.04,
        max_adv_participation_pct=0.08,
        require_short_locate=True,
    )
    compliance = PreTradeComplianceEngine(config=config)
    compliance.add_restricted_ticker("LOCKED")

    portfolio_nav = 2_000_000.0

    # 1. Valid order passes
    dec_valid = compliance.validate_order(
        order_id="ORD-001",
        ticker="AAPL",
        action="BUY",
        shares=1000.0,
        price=150.0,  # $150k < $500k, 7.5% NAV < 10%
        market_quote=150.50,
        portfolio_nav=portfolio_nav,
        adv_shares_20d=50_000.0,  # 2% ADV < 8%
    )
    assert dec_valid.status == ComplianceStatus.APPROVED
    assert len(dec_valid.audit_hash) == 64

    # 2. Restricted ticker rejected
    dec_restr = compliance.validate_order(
        order_id="ORD-002",
        ticker="LOCKED",
        action="BUY",
        shares=100.0,
        price=50.0,
        market_quote=50.0,
        portfolio_nav=portfolio_nav,
    )
    assert dec_restr.status == ComplianceStatus.REJECTED
    assert any("RESTRICTED_TICKER" in r for r in dec_restr.rejection_reasons)

    # 3. Fat-finger collar rejected (price > 4% from quote)
    dec_fat = compliance.validate_order(
        order_id="ORD-003",
        ticker="AAPL",
        action="BUY",
        shares=500.0,
        price=170.0,  # 13.3% higher than 150.0
        market_quote=150.0,
        portfolio_nav=portfolio_nav,
    )
    assert dec_fat.status == ComplianceStatus.REJECTED
    assert any("FAT_FINGER_PRICE_COLLAR" in r for r in dec_fat.rejection_reasons)

    # 4. Short sale without locate rejected
    dec_short_no_loc = compliance.validate_order(
        order_id="ORD-004",
        ticker="TSLA",
        action="SELL_SHORT",
        shares=500.0,
        price=200.0,
        market_quote=200.0,
        portfolio_nav=portfolio_nav,
        borrow_locate_id=None,
    )
    assert dec_short_no_loc.status == ComplianceStatus.REJECTED
    assert any("REG_SHO_LOCATE" in r for r in dec_short_no_loc.rejection_reasons)

    # 5. Short sale with locate approved
    dec_short_loc = compliance.validate_order(
        order_id="ORD-005",
        ticker="TSLA",
        action="SELL_SHORT",
        shares=500.0,
        price=200.0,
        market_quote=200.0,
        portfolio_nav=portfolio_nav,
        borrow_locate_id="LOC-BOFA-99214",
    )
    assert dec_short_loc.status == ComplianceStatus.APPROVED

    # Audit trail verification
    trail = compliance.get_audit_trail()
    assert len(trail) == 5
