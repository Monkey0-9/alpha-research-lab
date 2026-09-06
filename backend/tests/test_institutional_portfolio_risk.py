"""
Institutional Portfolio Construction & Risk Test Suite (Phase 1).
Validates:
1. Ledoit-Wolf analytical shrinkage covariance estimation and condition number improvement.
2. Convex QP portfolio optimization with dollar-neutral, gross leverage, and factor bounds.
3. Authoritative double-entry ledger accounting invariants, borrow accruals, and cryptographic audit chaining.
4. Cornish-Fisher non-Gaussian VaR adjustment for skewness and excess kurtosis.
5. Historical crisis stress-testing engine across Lehman 2008, Flash Crash 2010, COVID 2020, and SVB 2023.
"""
from __future__ import annotations

import numpy as np

from core.portfolio import ledoit_wolf_covariance, convex_portfolio_optimizer
from core.portfolio_ledger import PortfolioLedger, FillEvent
from core.risk import cornish_fisher_var, HistoricalStressTester


def test_ledoit_wolf_shrinkage_condition_number():
    rng = np.random.default_rng(42)
    # Ill-conditioned matrix: 50 observations, 30 assets (high dimensionality)
    T, N = 50, 30
    returns = rng.normal(0.0005, 0.02, size=(T, N))

    sample_cov = np.cov(returns, rowvar=False)
    shrunk_cov, delta = ledoit_wolf_covariance(returns)

    assert 0.0 < delta <= 1.0, f"Expected non-zero shrinkage intensity, got {delta}"
    assert shrunk_cov.shape == (N, N)

    # Condition number of shrunk covariance must be strictly lower than sample covariance
    cond_sample = np.linalg.cond(sample_cov)
    cond_shrunk = np.linalg.cond(shrunk_cov)
    assert cond_shrunk < cond_sample, f"Shrunk cond ({cond_shrunk:.2f}) must be < sample cond ({cond_sample:.2f})"

    # Positive definiteness check: all eigenvalues > 0
    eigvals = np.linalg.eigvalsh(shrunk_cov)
    assert np.all(eigvals > 0), "Shrunk covariance must be strictly positive definite"


def test_convex_portfolio_optimizer_dollar_neutral():
    rng = np.random.default_rng(101)
    N = 10
    alpha = rng.normal(0.05, 0.10, size=N)
    cov = np.diag(np.full(N, 0.04)) + 0.005

    res = convex_portfolio_optimizer(
        alpha_signal=alpha,
        cov_matrix=cov,
        target_net_leverage=0.0,
        gross_leverage_limit=2.0,
        max_position_weight=0.25,
        risk_aversion=1.0,
    )

    assert res["status"] in ("OPTIMAL", "APPROXIMATION")
    w = res["weights"]
    assert len(w) == N

    # Dollar neutrality check
    assert abs(np.sum(w)) < 1e-4, f"Expected dollar neutrality (sum ~ 0), got {np.sum(w)}"

    # Gross leverage bound
    assert np.sum(np.abs(w)) <= 2.0 + 1e-4, f"Gross leverage exceeded limit: {np.sum(np.abs(w))}"

    # Single position limit
    assert np.all(np.abs(w) <= 0.25 + 1e-4), "Position weight exceeded 25% bound"


def test_convex_portfolio_optimizer_factor_neutrality():
    rng = np.random.default_rng(202)
    N = 12
    alpha = rng.normal(0.02, 0.05, size=N)
    cov = np.eye(N) * 0.05

    # Factor loading: e.g. Market Beta (K=1 factor)
    market_betas = np.array([1.2, 0.8, 1.5, 0.5, 1.1, 0.9, 1.3, 0.7, 1.4, 0.6, 1.0, 1.0]).reshape(N, 1)

    res = convex_portfolio_optimizer(
        alpha_signal=alpha,
        cov_matrix=cov,
        target_net_leverage=0.0,
        gross_leverage_limit=1.5,
        max_position_weight=0.20,
        factor_loadings=market_betas,
        factor_bounds=[(-0.02, 0.02)],  # Market beta must be bounded within [-0.02, 0.02]
    )

    w = res["weights"]
    portfolio_beta = float(w @ market_betas[:, 0])
    assert abs(portfolio_beta) <= 0.02 + 1e-3, f"Portfolio beta {portfolio_beta} exceeded tolerance [-0.02, 0.02]"


def test_double_entry_ledger_invariants_and_hash_chain():
    ledger = PortfolioLedger(initial_cash=1_000_000.0)

    # 1. Buy 500 shares of AAPL @ $150.0 with $10 fee
    ledger.record_fill(FillEvent(
        order_id="ORD-001",
        security_id="SEC-AAPL",
        ticker="AAPL",
        timestamp="2024-01-02T10:00:00Z",
        quantity=500.0,
        price=150.0,
        fees=10.0
    ))

    # 2. Short 300 shares of MSFT @ $300.0 with $15 fee
    ledger.record_fill(FillEvent(
        order_id="ORD-002",
        security_id="SEC-MSFT",
        ticker="MSFT",
        timestamp="2024-01-02T10:05:00Z",
        quantity=-300.0,
        price=300.0,
        fees=15.0
    ))

    # 3. Accrue short borrow fees
    ledger.accrue_borrow_fees(borrow_rate_annual_bps=100.0, days=5.0, timestamp="2024-01-07T16:00:00Z")

    # 4. Mark to market
    current_prices = {"AAPL": 160.0, "MSFT": 290.0}
    snapshot = ledger.mark_to_market(current_prices, timestamp="2024-01-07T16:00:00Z")

    assert snapshot.nav > 0
    assert snapshot.accrued_borrow_fees > 0

    # 5. Authoritative Invariants Verification
    inv = ledger.verify_accounting_invariants()
    assert inv["is_balanced"] is True, "Accounting equation (Assets == Liabilities + Equity) must hold"
    assert inv["chain_valid"] is True, "Cryptographic journal hash chain must be unbroken"
    assert inv["journal_entries_count"] >= 4


def test_cornish_fisher_var_penalizes_fat_tails():
    rng = np.random.default_rng(333)
    N = 1000

    # Gaussian baseline
    normal_rets = rng.normal(0.0005, 0.01, N)
    normal_cf_var = cornish_fisher_var(normal_rets, confidence=0.99)

    # Heavily negative-skewed fat-tailed distribution (crashes)
    crashes = rng.normal(-0.08, 0.03, 50)
    skewed_rets = np.concatenate([normal_rets[:950], crashes])
    skewed_cf_var = cornish_fisher_var(skewed_rets, confidence=0.99)

    # Cornish-Fisher VaR must penalize the severe negative skewness with a higher VaR
    assert skewed_cf_var > normal_cf_var, (
        f"Skewed VaR ({skewed_cf_var:.4f}) must be higher than "
        f"Normal VaR ({normal_cf_var:.4f})"
    )


def test_historical_stress_tester_crisis_scenarios():
    # Long Tech and Financials portfolio
    weights = {
        "AAPL": 0.30,
        "MSFT": 0.20,
        "JPM": 0.25,
        "GS": 0.15,
        "XOM": 0.10,
    }

    report = HistoricalStressTester.run_stress_scenarios(
        weights=weights,
        aum=10_000_000.0,
        max_tolerable_drawdown=0.15
    )

    assert report["status"] == "COMPLETED"
    assert "LEHMAN_2008" in report["scenarios"]
    assert "COVID_2020" in report["scenarios"]
    assert "SVB_2023" in report["scenarios"]

    # Lehman scenario has large drawdown on financials
    lehman = report["scenarios"]["LEHMAN_2008"]
    assert lehman["portfolio_loss_pct"] > 25.0
    assert lehman["limit_breached"] is True
    assert lehman["worst_contributor"] in ("JPM", "GS", "Financials")
