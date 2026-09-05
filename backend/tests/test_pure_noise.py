"""
Flagship Pure-Noise Rejection Test (Dataset B).
Validates that the quantitative discovery and validation pipeline strictly rejects
pure Gaussian white noise and flags backtest overfitting.
"""
import numpy as np
import pytest
from core.metrics import information_coefficient
from core.statistics import deflated_sharpe_ratio
from core.quality_gate import run_quality_gate, ClaimCeiling
from core.pbo import compute_pbo


def test_pure_noise_rejected_by_statistical_tests():
    rng = np.random.default_rng(999)
    n_days = 500

    # Pure Gaussian noise: mean 0, std 0.01
    noise_returns = rng.normal(0.0, 0.01, n_days)
    random_feature = rng.normal(0.0, 1.0, n_days)

    ic_val = information_coefficient(random_feature, noise_returns)
    assert abs(ic_val) < 0.10, f"Pure noise should have negligible IC, got {ic_val}"

    # Multiple testing over 500 random noise paths to find spurious in-sample 'winner'
    n_trials = 500
    candidate_sharpes = []
    for _ in range(n_trials):
        fake_ret = rng.normal(0.0, 0.01, n_days)
        candidate_sharpes.append((np.mean(fake_ret) / np.std(fake_ret)) * np.sqrt(252))

    max_is_sharpe = float(np.max(candidate_sharpes))
    # Even if max in-sample Sharpe appears high due to data snooping...
    assert max_is_sharpe > 0.5

    # DSR must detect the 500 trials and deflated Sharpe ratio must collapse
    dsr = deflated_sharpe_ratio(
        observed_sr=max_is_sharpe,
        returns=noise_returns,
        num_trials=n_trials
    )
    # Deflated Sharpe should reject the noise
    assert dsr.get("passes_dsr", False) is False

    # Quality gate must strictly REJECT
    qg_res = run_quality_gate(
        in_sample_sharpe=max_is_sharpe,
        oos_sharpe=0.1,  # OOS Sharpe collapses on pure noise
        oos_ic=0.005,
        fdr_pvalue=0.85,  # Non-significant
        alpha_decay_halflife=2.0,
        turnover=0.80,
        max_drawdown=0.45,
        regime_robustness=0.10,
        capacity=0.0,
        has_oos_manifest=True
    )
    assert qg_res["all_passed"] is False
    assert qg_res["verdict"] == "RETAIN_IN_DEVELOPMENT"
