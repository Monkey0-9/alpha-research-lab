"""
Unit test for Level 5 Reproducibility (Reproducibility 2.0).
Verifies that experiments re-execute deterministically against the physical dataset artifact
with zero metric drift, verified cryptographic dataset SHA-256, and frozen manifest signatures.
"""
from pathlib import Path
import pandas as pd

from backend.core.experiment import (
    experiment_registry,
    PreRegistrationSpec,
    _DEFAULT_DATA_FILE,
)
from backend.core.reproduce import (
    reproduce_experiment,
    execute_research_pipeline,
)


def test_level5_reproducibility_audit():
    # 1. Ensure dataset artifact exists
    assert _DEFAULT_DATA_FILE.exists(), "Default dataset artifact data/sp500_daily.parquet must exist."
    df = pd.read_parquet(_DEFAULT_DATA_FILE)

    # 2. Pre-register experiment with physical dataset path binding
    spec = PreRegistrationSpec(
        experiment_id="EXP-L5-AUDIT-002",
        hypothesis_name="Momentum_Level5_Audit",
        economic_rationale="Cross-sectional momentum persists due to underreaction.",
        expected_direction="positive",
        universe_type="SP500_PIT",
        features=["momentum_20d", "volatility_20d"],
        target_label="fwd_return_1d",
        validation_method="CPCV",
        multiple_testing_correction="BH",
        dataset_id="SP500_DAILY",
        dataset_version=1,
        dataset_path=str(_DEFAULT_DATA_FILE),
        random_seed=42,
    )

    manifest = experiment_registry.preregister(spec)
    exp_id = manifest.experiment_id

    # 3. Compute real research metrics using deterministic pipeline
    real_metrics = execute_research_pipeline(df, spec=spec, seed=spec.random_seed)
    assert real_metrics["sharpe"] != 0.0

    # 4. Record empirical results and freeze
    experiment_registry.record_results(
        experiment_id=exp_id,
        metrics=real_metrics,
    )

    # 5. Re-execute reproducibility audit end-to-end
    audit_res = reproduce_experiment(exp_id)

    assert audit_res["experiment_id"] == exp_id
    assert audit_res["spec_integrity_verified"] is True
    assert audit_res["dataset_checksum_verified"] is True
    assert audit_res["sharpe_difference"] < 1e-4
    assert audit_res["status"] == "REPRODUCED_MATCH"
    assert audit_res["is_exact_match"] is True
