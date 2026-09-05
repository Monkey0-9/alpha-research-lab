"""
Benchmark Dataset Pipeline Tests: Planted Signal, Pure Noise, and Deliberate Leakage.

Verifies:
1. Dataset A (Signal): Genuine alpha signal is successfully detected, passes FDR, and qualifies for promotion.
2. Dataset B (Noise): Pure Gaussian noise features are 100% rejected by multiple-testing FDR gates.
3. Dataset C (Leakage): Injected lookahead leakage is caught and quarantined by the leakage detector.
"""
import pytest
import numpy as np
import scipy.stats as ss

from core.benchmarks import (
    generate_dataset_a_known_signal,
    generate_dataset_b_pure_noise,
    generate_dataset_c_known_leakage,
    audit_dataset_for_leakage,
)
from core.statistics import benjamini_hochberg_fdr, bonferroni_correction
from core.integrity_guard import detect_future_leakage, FutureLeakageError


# ===========================================================================
# 1. Dataset A: Planted Known Signal Recovery
# ===========================================================================

def test_benchmark_dataset_a_recovers_known_signal():
    """Verify that ground-truth planted alpha is discovered and passes FDR significance."""
    features, labels = generate_dataset_a_known_signal(n_days=500, n_tickers=8, seed=42)

    signal = features["planted_momentum"].values
    target = labels["fwd_return_1d"].values

    valid = ~(np.isnan(signal) | np.isnan(target))
    ic, pval = ss.spearmanr(signal[valid], target[valid])

    # True signal must be statistically detectable (IC > 0.02, p-value < 0.01)
    assert abs(ic) > 0.02
    assert pval < 0.01

    # Multiple-testing control (FDR) on candidate set including noise features
    all_pvals = [pval]
    for feat in ["noise_feat_1", "noise_feat_2"]:
        s = features[feat].values
        _, p = ss.spearmanr(s[valid], target[valid])
        all_pvals.append(p)

    fdr_res = benjamini_hochberg_fdr(all_pvals, q=0.05)
    # The first candidate (ground truth signal) must be retained as significant
    assert fdr_res[0] is True or fdr_res.meta["significant_count"] >= 1


# ===========================================================================
# 2. Dataset B: Pure Noise Rejection
# ===========================================================================

def test_benchmark_dataset_b_rejects_pure_noise():
    """Verify that multiple testing gates reject all pure noise features."""
    features, labels = generate_dataset_b_pure_noise(n_days=500, n_tickers=8, seed=101)
    target = labels["fwd_return_1d"].values

    noise_cols = [c for c in features.columns if c.startswith("noise_")]
    p_values = []
    for col in noise_cols:
        valid = ~(np.isnan(features[col]) | np.isnan(target))
        _, p = ss.spearmanr(features[col][valid], target[valid])
        p_values.append(p)

    # Apply FDR multiple testing control with strict threshold
    fdr_res = benjamini_hochberg_fdr(p_values, q=0.01)
    bonf_res = bonferroni_correction(p_values, alpha=0.01)

    # In pure noise, Bonferroni / conservative FDR must not falsely discover signals
    assert bonf_res.meta["significant_count"] == 0
    assert fdr_res.meta["significant_count"] == 0


# ===========================================================================
# 3. Dataset C: Deliberate Leakage Detection
# ===========================================================================

def test_benchmark_dataset_c_detects_deliberate_leakage():
    """Verify that injected lookahead leakage is identified and rejected by the leakage auditor."""
    leak_df = generate_dataset_c_known_leakage(n_days=252, seed=999)

    audit_result = audit_dataset_for_leakage(leak_df)

    assert audit_result["passed"] is False
    assert "leaked_feature" in audit_result["leaks_detected"]
    assert audit_result["details"]["legitimate_lagged"] == "PASS"

    # Direct detector verification
    with pytest.raises(FutureLeakageError):
        detect_future_leakage(leak_df["leaked_feature"], leak_df["close"])
