"""
Institutional Verification Tests for Research Governance Gatekeeper.
Verifies:
1. Mandatory hypothesis pre-registration and cryptographic manifest hashing.
2. The Execution Survival Gatekeeper Rule:
   Automatic rejection of high-gross / low-net strategies (First-Class Negative Results).
3. Search budget exhaustion and Deflated Sharpe Ratio multiple testing penalty accumulation.
"""
import pytest
from backend.core.governance_gatekeeper import (
    GovernanceVerdict,
    ResearchGovernanceGatekeeper,
)


def test_mandatory_pre_registration():
    gatekeeper = ResearchGovernanceGatekeeper()

    # Pre-register valid hypothesis
    m_hash = gatekeeper.pre_register(
        hypothesis_id="HYP-MOMENTUM-2026",
        hypothesis_statement="Cross-sectional momentum with volatility scaling produces alpha in equities.",
        alpha_dsl_ast="Rank(Ts_Mean(Returns(20), 5)) / Volatility(60)",
        search_budget=3,
        random_seed=12345
    )

    assert len(m_hash) == 64

    # Evaluating unregistered experiment must fail-closed
    with pytest.raises(KeyError, match="Unregistered experiment"):
        gatekeeper.evaluate_alpha(
            manifest_hash="UNREGISTERED_HASH_999",
            gross_sharpe=1.80,
            net_sharpe=1.50,
            total_is_bps=10.0
        )


def test_first_class_negative_result_execution_rejection():
    gatekeeper = ResearchGovernanceGatekeeper(gross_hurdle=1.50, net_survival_hurdle=0.50)

    m_hash = gatekeeper.pre_register(
        hypothesis_id="HYP-MEAN-REVERSION-HIGH-TURNOVER",
        hypothesis_statement="Short-term order flow imbalance mean-reversion.",
        alpha_dsl_ast="Sign(Ts_Delta(Volume, 1)) * -1",
        search_budget=5
    )

    # Strategy has paper Sharpe of 1.75!
    # But high turnover causes 85 bps Implementation Shortfall, collapsing Net Sharpe to 0.22.
    record = gatekeeper.evaluate_alpha(
        manifest_hash=m_hash,
        gross_sharpe=1.75,
        net_sharpe=0.22,
        total_is_bps=85.0
    )

    # Policy: Must REJECT, never optimize or mask
    assert record.verdict == GovernanceVerdict.REJECT_EXECUTION_UNVIABLE
    assert "collapsed below survival hurdle" in record.rejection_details
    assert gatekeeper.total_trials_count == 1
    assert gatekeeper.negative_results_count == 1


def test_search_budget_enforcement_and_approval():
    gatekeeper = ResearchGovernanceGatekeeper(gross_hurdle=1.50, net_survival_hurdle=0.50)

    # Pre-register with budget of 2
    m_hash = gatekeeper.pre_register(
        hypothesis_id="HYP-VALUE-FACTOR",
        hypothesis_statement="Book to market ratio alpha.",
        alpha_dsl_ast="Rank(Fundamental('book_value') / Price)",
        search_budget=2
    )

    # Trial 1: Approved strategy (Gross 1.90, Net 1.65, IS 12 bps)
    trial_1 = gatekeeper.evaluate_alpha(m_hash, gross_sharpe=1.90, net_sharpe=1.65, total_is_bps=12.0)
    assert trial_1.verdict == GovernanceVerdict.APPROVED

    # Trial 2: Rejected strategy (Net 0.40)
    trial_2 = gatekeeper.evaluate_alpha(m_hash, gross_sharpe=1.20, net_sharpe=0.40, total_is_bps=20.0)
    assert trial_2.verdict == GovernanceVerdict.REJECT_STATISTICAL_SIGNIFICANCE

    # Trial 3: Budget exceeded!
    trial_3 = gatekeeper.evaluate_alpha(m_hash, gross_sharpe=2.10, net_sharpe=1.80, total_is_bps=10.0)
    assert trial_3.verdict == GovernanceVerdict.REJECT_BUDGET_EXCEEDED
    assert trial_3.rejection_details == "Search budget exhausted for hypothesis."
