"""
Test suite validating Alpha Trial Registry and Research Discovery Pipeline (Phases 6, 7, 8).
Verifies trial logging, PBO fail-closed gating, and retention of negative/overfit research results.
"""
import pandas as pd
import pytest
from backend.alpha.trial_registry import AlphaTrialRegistry, TrialStatus
from backend.alpha.research_pipeline import DisciplinedAlphaPipeline


@pytest.fixture
def clean_registry(tmp_path):
    return AlphaTrialRegistry(storage_path=tmp_path / "trials.json")


def test_trial_registry_logs_accepted_and_rejected_trials(clean_registry):
    # Trial 1: High quality alpha
    t1 = clean_registry.register_trial(
        expression="ts_mean(close, 20) / close - 1.0",
        hypothesis="20-day mean reversion",
        dataset_id="DS_SP500",
        in_sample_period="2018-2021",
        out_of_sample_period="2022-2023",
        in_sample_sharpe=1.45,
        out_of_sample_sharpe=1.20,
        pbo=0.15,
        deflated_sharpe_ratio=0.96,
    )
    assert t1.trial_id == "TRIAL-000001"
    assert t1.status == TrialStatus.ACCEPTED.value

    # Trial 2: Overfit alpha with high PBO
    t2 = clean_registry.register_trial(
        expression="ts_rank(volume, 5) * ts_std(close, 100) + sin(rsi(14))",
        hypothesis="Complex curve-fitted indicator",
        dataset_id="DS_SP500",
        in_sample_period="2018-2021",
        out_of_sample_period="2022-2023",
        in_sample_sharpe=2.40,
        out_of_sample_sharpe=0.10,
        pbo=0.65,
        deflated_sharpe_ratio=0.70,
    )
    assert t2.trial_id == "TRIAL-000002"
    assert t2.status == TrialStatus.OVERFIT.value
    assert "PBO failure" in t2.rejection_reason

    stats = clean_registry.get_summary_statistics()
    assert stats["total_trials"] == 2
    assert stats["accepted_count"] == 1
    assert stats["rejected_count"] == 1


def test_disciplined_pipeline_execution(clean_registry):
    pipeline = DisciplinedAlphaPipeline(registry=clean_registry)
    dummy_df = pd.DataFrame({"close": [100.0] * 500})

    res = pipeline.evaluate_candidate_expression(
        expression_str="ts_zscore(close, 10)",
        hypothesis="Short-term momentum z-score",
        dataset_df=dummy_df
    )

    assert "trial_id" in res
    assert res["trial_id"] == "TRIAL-000001"
    assert "status" in res
