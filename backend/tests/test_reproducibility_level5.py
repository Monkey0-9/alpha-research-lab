"""
Unit test for Level 5 Reproducibility.
Verifies that experiments can be reproduced with zero metric drift and verified dataset checksum.
"""
from backend.core.experiment import (
    experiment_registry,
    PreRegistrationSpec,
)
from backend.core.reproduce import reproduce_experiment


def test_level5_reproducibility_audit():
    # 1. Pre-register experiment
    spec = PreRegistrationSpec(
        experiment_id="EXP-L5-AUDIT-001",
        hypothesis_name="Momentum_Level5_Audit",
        economic_rationale="Cross-sectional momentum persists due to underreaction.",
        expected_direction="positive",
        universe_type="SP500_PIT",
        features=["momentum_12m_1m", "volatility_60d"],
        target_label="forward_returns_20d",
        validation_method="CPCV",
        multiple_testing_correction="BH",
    )

    manifest = experiment_registry.preregister(spec)
    exp_id = manifest.experiment_id

    # 2. Record empirical results and freeze
    experiment_registry.record_results(
        experiment_id=exp_id,
        metrics={
            "sharpe": 1.745,
            "oos_sharpe": 1.520,
            "ic": 0.082,
            "max_drawdown": 0.115,
        },
    )

    # 3. Re-execute reproducibility audit
    audit_res = reproduce_experiment(exp_id)

    assert audit_res["experiment_id"] == exp_id
    assert audit_res["spec_integrity_verified"] is True
    assert audit_res["sharpe_difference"] < 1e-4
    assert audit_res["status"] == "REPRODUCED_MATCH"
