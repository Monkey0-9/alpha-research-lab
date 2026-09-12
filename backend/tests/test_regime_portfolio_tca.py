"""
Test suite validating Multi-Asset Regime Models, Comparative Portfolio Optimizers, and Execution TCA (Phases 9–12).
"""
import numpy as np
import pytest
from backend.models.regime_models import MarketRegime, MultiAssetRegimeDetector
from backend.portfolio.comparative_optimizers import ComparativePortfolioOptimizer
from backend.execution.tca_engine import ExecutionAlgorithm, TransactionCostAnalysisEngine


def test_regime_detector_identifies_regimes_and_adjusts_weights():
    detector = MultiAssetRegimeDetector(n_states=3)

    # Bullish returns series
    bull_returns = [0.002, 0.001, 0.003, 0.0015, 0.0025] * 10
    regimes = detector.detect_regimes_hmm(bull_returns)
    assert len(regimes) > 0
    assert regimes[-1].current_regime == MarketRegime.RISK_ON_BULL

    base_weights = {"EQUITY": 0.5, "RATES": 0.3, "GOLD": 0.2}
    adj_weights = detector.condition_multi_asset_weights(base_weights, MarketRegime.RISK_ON_BULL)
    assert np.isclose(sum(adj_weights.values()), 1.0, atol=1e-3)
    assert adj_weights["EQUITY"] > base_weights["EQUITY"]


def test_comparative_portfolio_optimizers():
    assets = ["AAPL", "MSFT", "GOOGL"]
    exp_ret = np.array([0.0006, 0.0005, 0.0004])
    cov = np.array([
        [0.0004, 0.0002, 0.00015],
        [0.0002, 0.00035, 0.00018],
        [0.00015, 0.00018, 0.0003]
    ])

    optimizer = ComparativePortfolioOptimizer(risk_free_rate=0.02)
    results = optimizer.run_comparative_benchmark(assets, exp_ret, cov)

    assert len(results) == 5
    for res in results:
        w_sum = sum(res.weights.values())
        assert np.isclose(w_sum, 1.0, atol=1e-3)
        assert res.expected_volatility_annual > 0.0


def test_tca_engine_calculates_implementation_shortfall():
    tca = TransactionCostAnalysisEngine(half_spread_bps=2.0)
    report = tca.simulate_execution_and_tca(
        order_id="ORD-999",
        ticker="AAPL",
        side="BUY",
        shares=1000,
        arrival_price=150.0,
        daily_volume=50_000_000,
        algo=ExecutionAlgorithm.TWAP
    )

    assert report.order_id == "ORD-999"
    assert report.average_fill_price > report.arrival_price  # Slippage exists for BUY
    assert report.implementation_shortfall_bps > 0.0
    assert report.total_cost_dollars > 0.0
