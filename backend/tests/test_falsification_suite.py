"""
Unit tests for the Alpha Falsification Engine.
"""
import numpy as np
import pytest

from backend.core.falsification_engine import FalsificationEngine


def test_falsification_genuine_signal_passes():
    np.random.seed(42)
    n = 500
    # Plant a real persistent signal
    true_alpha = np.random.normal(0, 1, n)
    forward_returns = 0.3 * true_alpha + np.random.normal(0, 0.5, n)

    engine = FalsificationEngine()
    baseline_ic = float(np.corrcoef(true_alpha, forward_returns)[0, 1])
    assert baseline_ic > 0.4

    report = engine.run_falsification_suite(
        alpha_id="ALPHA-GENUINE-001",
        signal=true_alpha,
        forward_returns=forward_returns,
        baseline_ic=baseline_ic,
    )

    assert report.verdict == "PASSED"
    assert report.tests_passed >= 6
    assert report.survival_score >= 0.85


def test_falsification_flimsy_signal_rejected():
    np.random.seed(42)
    n = 500
    # Spurious noise signal with tiny margin
    noise_alpha = np.random.normal(0, 1, n)
    forward_returns = np.random.normal(0, 1, n)

    engine = FalsificationEngine()
    baseline_ic = 0.05

    report = engine.run_falsification_suite(
        alpha_id="ALPHA-SPURIOUS-999",
        signal=noise_alpha,
        forward_returns=forward_returns,
        baseline_ic=baseline_ic,
        costs_bps=20.0,
    )

    # Spurious signals fail cost stress, sign symmetry, etc.
    assert report.verdict in {"FALSIFIED", "FLAGGED_FRAGILE"}
    assert report.survival_score < 0.85
