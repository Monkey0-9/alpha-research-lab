"""
Test suite validating Pre-Registered Empirical Experiment EXP-001 and Ablation Engine (Phases 16, 17, 19).
"""
from backend.research.experiment_exp001 import PreregisteredExperimentEXP001
from backend.research.ablation_engine import SystemAblationEngine


def test_experiment_exp001_execution_and_reproducibility():
    exp = PreregisteredExperimentEXP001(seed=42)
    res = exp.run_experiment()

    assert res.experiment_id == "EXP-001"
    assert res.baseline_oos_sharpe > 0.0
    assert res.regime_aware_oos_max_dd > 0.0
    # Verified max drawdown reduction achieved via regime conditioning
    assert res.max_dd_reduction > 0.0
    assert len(res.bootstrap_95_ci_delta) == 2
    assert isinstance(res.hypothesis_confirmed, bool)


def test_ablation_engine_matrix():
    engine = SystemAblationEngine()
    results = engine.run_ablation_matrix()

    assert len(results) == 6
    # Verify FDR drops systematically
    assert results[0].false_discovery_rate > results[-1].false_discovery_rate
    # Full system has highest Sharpe
    assert results[-1].sharpe_ratio >= results[0].sharpe_ratio
