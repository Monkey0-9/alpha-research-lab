"""
Rigorous Reproducibility 2.0 Adversarial Test Suite.

Tests A through H:
- Test A: Same everything -> MATCH
- Test B: Modify one dataset row -> DATASET_CHECKSUM_FAILURE
- Test C: Modify feature code / git version -> CODE_VERSION_FAILURE
- Test D: Modify alpha expression AST -> AST_HASH_FAILURE
- Test E: Modify hyperparameter configuration -> CONFIG_HASH_FAILURE
- Test F: Modify random seed -> REPRODUCTION_MISMATCH
- Test G: Delete dataset artifact -> DATASET_UNAVAILABLE
- Test H: Restore exact dataset -> MATCH
"""
import shutil
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backend.core.experiment import (
    ExperimentRegistry,
    PreRegistrationSpec,
    compute_sha256,
)
from backend.core.reproduce import (
    reproduce_experiment,
    execute_research_pipeline,
)


@pytest.fixture
def test_env():
    """Create isolated sandbox directory with clean dataset artifact and experiment registry."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store_dir = tmp_path / "experiments"
        data_dir = tmp_path / "data"
        store_dir.mkdir()
        data_dir.mkdir()

        # Build realistic sample dataset
        np.random.seed(42)
        dates = pd.date_range("2022-01-01", periods=100, freq="B")
        rows = []
        for d in dates:
            for ticker in ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]:
                rows.append({
                    "date": d,
                    "ticker": ticker,
                    "close": float(100.0 + np.random.normal(0, 2)),
                    "volume": float(1_000_000 + np.random.normal(0, 50_000)),
                    "return_1d": float(np.random.normal(0.0005, 0.015)),
                })
        df = pd.DataFrame(rows)
        dataset_path = data_dir / "sp500_sample.parquet"
        df.to_parquet(dataset_path)

        # Backup pristine copy for restore test
        backup_path = data_dir / "sp500_sample_pristine.parquet"
        shutil.copyfile(dataset_path, backup_path)

        registry = ExperimentRegistry(store_dir=store_dir)

        yield {
            "registry": registry,
            "dataset_path": dataset_path,
            "backup_path": backup_path,
            "df": df,
            "store_dir": store_dir,
            "tmp_path": tmp_path,
        }


def test_reproducibility_suite_a_to_h(test_env, monkeypatch):
    registry = test_env["registry"]
    dataset_path = test_env["dataset_path"]
    backup_path = test_env["backup_path"]
    df = test_env["df"]

    # Point global experiment_registry to our isolated registry
    from backend.core import reproduce
    monkeypatch.setattr(reproduce, "experiment_registry", registry)

    # 1. Pre-register baseline experiment
    spec = PreRegistrationSpec(
        experiment_id="EXP-RIGOROUS-001",
        hypothesis_name="CrossSectionalMomentumReversion",
        economic_rationale="Multi-factor blend of intermediate momentum and volume anomaly.",
        expected_direction="positive",
        universe_type="SP500_PIT",
        features=["momentum_20d", "volatility_20d"],
        target_label="fwd_return_1d",
        validation_method="CPCV",
        multiple_testing_correction="BH",
        dataset_id="SP500_SAMPLE",
        dataset_version=1,
        dataset_path=str(dataset_path),
        alpha_expression="rank(return_1d) - rank(volume)",
        parameters={"lookback": 20, "quantile": 0.3, "leverage": 1.0},
        random_seed=42,
    )

    manifest = registry.preregister(spec, dataset_path_override=dataset_path)
    exp_id = manifest.experiment_id

    # Compute baseline empirical metrics using the deterministic research pipeline
    baseline_metrics = execute_research_pipeline(df, spec=spec, seed=spec.random_seed)
    assert baseline_metrics["sharpe"] != 0.0

    # Record results and freeze manifest
    registry.record_results(exp_id, metrics=baseline_metrics, status="COMPLETED")
    assert registry.get(exp_id).is_frozen is True

    # ----------------------------------------------------
    # TEST A: Same everything -> MATCH
    # ----------------------------------------------------
    res_a = reproduce_experiment(exp_id, dataset_override_path=dataset_path)
    assert res_a["status"] == "REPRODUCED_MATCH"
    assert res_a["is_exact_match"] is True
    assert res_a["sharpe_difference"] < 1e-4
    assert res_a["spec_integrity_verified"] is True
    assert res_a["dataset_checksum_verified"] is True
    print("\n[PASS] Test A: Exact baseline match confirmed.")

    # ----------------------------------------------------
    # TEST B: Modify one dataset row -> CHECKSUM FAILURE
    # ----------------------------------------------------
    tampered_df = df.copy()
    tampered_df.iloc[0, tampered_df.columns.get_loc("close")] += 1.00  # Modify 1 single price value
    tampered_path = test_env["tmp_path"] / "tampered.parquet"
    tampered_df.to_parquet(tampered_path)

    res_b = reproduce_experiment(exp_id, dataset_override_path=tampered_path)
    assert res_b["status"] == "DATASET_CHECKSUM_FAILURE"
    assert res_b["dataset_checksum_verified"] is False
    assert "checksum mismatch" in res_b["reason"].lower()
    print("[PASS] Test B: Row tampering detected via cryptographic SHA-256 failure.")

    # ----------------------------------------------------
    # TEST C: Modify feature code / Git version -> CODE VERSION FAILURE
    # ----------------------------------------------------
    res_c = reproduce_experiment(
        exp_id,
        dataset_override_path=dataset_path,
        code_version_override="TAMPERED_COMMIT_SHA_999999",
    )
    assert res_c["status"] == "CODE_VERSION_FAILURE"
    assert "code version mismatch" in res_c["reason"].lower()
    print("[PASS] Test C: Modified code version correctly rejected.")

    # ----------------------------------------------------
    # TEST D: Modify alpha expression -> AST HASH FAILURE
    # ----------------------------------------------------
    altered_ast_hash = compute_sha256({"ast_expr": "rank(close) + rank(volume)"})
    res_d = reproduce_experiment(
        exp_id,
        dataset_override_path=dataset_path,
        ast_hash_override=altered_ast_hash,
    )
    assert res_d["status"] == "AST_HASH_FAILURE"
    assert "ast expression altered" in res_d["reason"].lower()
    print("[PASS] Test D: Altered alpha expression AST detected and rejected.")

    # ----------------------------------------------------
    # TEST E: Modify hyperparameter -> CONFIG HASH FAILURE
    # ----------------------------------------------------
    altered_params = {"lookback": 60, "quantile": 0.1, "leverage": 2.0}  # altered parameters
    res_e = reproduce_experiment(
        exp_id,
        dataset_override_path=dataset_path,
        config_override=altered_params,
    )
    assert res_e["status"] == "CONFIG_HASH_FAILURE"
    assert "configuration altered" in res_e["reason"].lower()
    print("[PASS] Test E: Hyperparameter configuration tampering rejected.")

    # ----------------------------------------------------
    # TEST F: Modify random seed -> REPRODUCTION MISMATCH
    # ----------------------------------------------------
    res_f = reproduce_experiment(
        exp_id,
        dataset_override_path=dataset_path,
        seed_override=9999,  # Different seed generates different stochastic signal perturbation
    )
    assert res_f["status"] == "REPRODUCTION_MISMATCH"
    assert res_f["sharpe_difference"] > 0.0
    assert "metric drift detected" in res_f["reason"].lower()
    print("[PASS] Test F: Seed perturbation resulted in non-zero delta and failure.")

    # ----------------------------------------------------
    # TEST G: Delete dataset artifact -> DATASET UNAVAILABLE
    # ----------------------------------------------------
    dataset_path.unlink()  # Delete the physical file
    assert not dataset_path.exists()

    res_g = reproduce_experiment(exp_id, dataset_override_path=dataset_path)
    assert res_g["status"] == "DATASET_UNAVAILABLE"
    assert "missing on disk" in res_g["reason"].lower()
    print("[PASS] Test G: Missing/deleted dataset artifact flagged as DATASET_UNAVAILABLE.")

    # ----------------------------------------------------
    # TEST H: Restore exact dataset artifact -> MATCH
    # ----------------------------------------------------
    shutil.copyfile(backup_path, dataset_path)
    assert dataset_path.exists()

    res_h = reproduce_experiment(exp_id, dataset_override_path=dataset_path)
    assert res_h["status"] == "REPRODUCED_MATCH"
    assert res_h["is_exact_match"] is True
    assert res_h["sharpe_difference"] < 1e-4
    print("[PASS] Test H: Exact restored artifact reproduces results with zero drift.")
