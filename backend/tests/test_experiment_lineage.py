"""
Unit tests for Pre-Registration, Immutable Experiment Lineage, and Manifest Cryptographic Verification.
"""
import pytest
from pathlib import Path
import tempfile

from core.experiment import (
    PreRegistrationSpec,
    ExperimentRegistry,
    ExperimentImmutableError,
)


@pytest.fixture
def temp_registry():
    with tempfile.TemporaryDirectory() as tmp_dir:
        reg = ExperimentRegistry(store_dir=Path(tmp_dir))
        yield reg


def test_preregistration_lifecycle(temp_registry):
    """Verify pre-registration, immutability on re-registration, results recording, and freeze."""
    spec = PreRegistrationSpec(
        experiment_id="EXP-2026-001",
        hypothesis_name="Cross-Sectional 12M Momentum Drift",
        economic_rationale="Slow information diffusion creates intermediate term price momentum.",
        expected_direction="positive",
        universe_type="SP500_PIT",
        features=["momentum_20d", "momentum_60d"],
        target_label="fwd_return_1d",
        validation_method="CPCV",
        multiple_testing_correction="BH"
    )

    # 1. Pre-register
    manifest = temp_registry.preregister(spec)
    assert manifest.execution_status == "PRE_REGISTERED"
    assert manifest.spec.spec_hash != ""

    # 2. Cannot re-register same experiment ID with different hypothesis
    with pytest.raises(ExperimentImmutableError, match="already pre-registered"):
        temp_registry.preregister(spec)

    # 3. Record empirical results and freeze
    metrics = {"sharpe": 1.45, "ic": 0.052, "turnover": 0.12, "pbo": 0.08}
    completed = temp_registry.record_results("EXP-2026-001", metrics=metrics, status="COMPLETED")
    assert completed.is_frozen is True
    assert completed.manifest_hash != ""

    # 4. Cannot modify frozen results
    with pytest.raises(ExperimentImmutableError, match="Cannot alter frozen experiment"):
        temp_registry.record_results("EXP-2026-001", metrics={"sharpe": 99.0})

    # 5. Verify reproduction and cryptographic integrity
    repro = temp_registry.reproduce("EXP-2026-001")
    assert repro["status"] == "VERIFIED_REPRODUCIBLE"
    assert repro["reported_metrics"]["sharpe"] == 1.45
    assert temp_registry.verify_integrity("EXP-2026-001") is True
