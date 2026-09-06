"""
Comprehensive Tests for Institutional Statistical Governance (Task 3 / Milestone M3).
Verifies:
1. Combinatorial Purged Cross-Validation (CPCV) empirical distribution generation.
2. Probability of Backtest Overfitting (PBO) rank degradation and logit scoring.
3. Deflated Sharpe Ratio (DSR) trial-calibrated penalty.
4. Hansen's SPA and White's Reality Check bootstrap hypothesis tests.
5. Alpha Evidence Card synthesis with immutable cryptographic decision hash.
"""
import numpy as np
import pandas as pd

from core.cpcv import CombinatorialPurgedCV, run_cpcv_evaluation
from core.pbo import compute_pbo
from core.statistics import (
    deflated_sharpe_ratio,
    hansens_spa_test,
    whites_reality_check,
)
from core.quality_gate import (
    generate_alpha_evidence_card,
    evaluate_alpha,
)


def test_cpcv_combinatorial_splits_and_embargo():
    """Verify that CPCV generates C(N, k) splits with correct purging and embargo windows."""
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    cpcv = CombinatorialPurgedCV(n_groups=6, k_test=2, purge_window=10, embargo_window=5)

    splits = cpcv.split(dates)
    assert len(splits) == 15  # C(6, 2) = 15

    for sp in splits:
        assert len(sp.test_groups) == 2
        assert len(sp.train_indices) > 0
        assert len(sp.test_indices) > 0
        assert sp.purged_count >= 0
        assert sp.embargo_count >= 0
        # Check no overlap between train and test
        overlap = set(sp.train_indices).intersection(set(sp.test_indices))
        assert len(overlap) == 0


def test_pbo_candidate_matrix_evaluation():
    """Verify Probability of Backtest Overfitting across candidate models."""
    rng = np.random.RandomState(42)
    n_splits = 20
    n_candidates = 10

    # Scenario A: In-sample winners are genuinely good out-of-sample (Low PBO)
    is_matrix_good = rng.normal(1.5, 0.3, (n_splits, n_candidates))
    oos_matrix_good = is_matrix_good + rng.normal(0.0, 0.1, (n_splits, n_candidates))
    pbo_good = compute_pbo(is_matrix_good, oos_matrix_good, n_trials=n_candidates)
    assert pbo_good["pbo"] < 0.30
    assert pbo_good["is_overfit"] is False

    # Scenario B: Pure noise (High PBO)
    is_matrix_noise = rng.normal(0.0, 1.0, (n_splits, n_candidates))
    oos_matrix_noise = rng.normal(0.0, 1.0, (n_splits, n_candidates))
    pbo_noise = compute_pbo(is_matrix_noise, oos_matrix_noise, n_trials=n_candidates)
    assert pbo_noise["pbo"] > 0.30


def test_deflated_sharpe_ratio_trial_penalty():
    """Verify that DSR properly discounts Sharpe ratio as trial count increases."""
    observed_sr = 1.6
    n_obs = 500

    # 1 trial: DSR is high
    dsr_single = deflated_sharpe_ratio(observed_sr, n_trials=1, n_observations=n_obs)
    # 500 trials: DSR is penalized
    dsr_many = deflated_sharpe_ratio(observed_sr, n_trials=500, n_observations=n_obs)

    assert dsr_single > dsr_many
    assert dsr_single >= 0.95


def test_hansens_spa_and_whites_reality_check():
    """Verify White's Reality Check and Hansen's SPA bootstrap against candidate loss distribution."""
    rng = np.random.RandomState(42)
    n_obs = 150
    n_benchmarks = 8

    # Benchmark strategies with zero or negative mean returns
    benchmarks = rng.normal(-0.0002, 0.01, (n_obs, n_benchmarks))

    # Candidate with strong positive performance
    strong_alpha = rng.normal(0.002, 0.01, n_obs)
    spa_strong = hansens_spa_test(strong_alpha, benchmarks, n_bootstraps=100)
    wrc_strong = whites_reality_check(strong_alpha, benchmarks, n_bootstraps=100)

    assert spa_strong["p_value"] < 0.05
    assert wrc_strong["p_value"] < 0.05
    assert spa_strong["superiority_demonstrated"] is True

    # Candidate with pure noise
    noise_alpha = rng.normal(-0.0003, 0.01, n_obs)
    spa_noise = hansens_spa_test(noise_alpha, benchmarks, n_bootstraps=100)
    assert spa_noise["p_value"] >= 0.05
    assert spa_noise["superiority_demonstrated"] is False


def test_alpha_evidence_card_generation():
    """Verify creation of an immutable Alpha Evidence Card with cryptographic decision hash."""
    card = generate_alpha_evidence_card(
        alpha_id="ALPHA-TEST-001",
        hypothesis="5-Day Momentum with Volume Confirmation",
        economic_rationale="Underreaction to institutional volume accumulation",
        ast_expression="ts_rank(delta(close, 5), 20) * ts_rank(volume, 20)",
        ast_hash="f5a7b8c9d0e1f2a3...",
        dataset_id="DS-000001",
        universe="SP500_SURVIVORSHIP_FREE",
        metrics={
            "sharpe": 1.85,
            "oos_sharpe": 1.62,
            "ic": 0.065,
            "oos_ic": 0.052,
            "turnover": 0.11,
            "capacity": 30_000_000.0,
            "max_drawdown": 0.09,
        },
        cpcv_results={"positive_oos_ratio": 0.80, "mean_oos_sharpe": 1.55},
        pbo_results={"pbo": 0.05},
        dsr_score=0.98,
        spa_pvalue=0.008,
        white_reality_pvalue=0.012,
    )

    assert card["alpha_id"] == "ALPHA-TEST-001"
    assert card["formal_decision"] == "PROMOTED_TO_PRODUCTION_CANDIDATE"
    assert card["falsification_passed"] is True
    assert len(card["decision_hash"]) == 64
    assert card["statistical_governance"]["pbo_score"] == 0.05
    assert card["statistical_governance"]["dsr_score"] == 0.98
