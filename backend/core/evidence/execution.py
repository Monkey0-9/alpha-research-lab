"""
Execution Cost & Capacity Evidence.

Covers:
- ExecutionCostEvidence (turnover budget, slippage, spread, borrow financing, max drawdown)
- CapacityEvidence (non-linear market impact, break-even AUM)
"""
from __future__ import annotations

from typing import Optional
from .base import Evidence, EvidenceStatus


class ExecutionCostEvidence(Evidence):
    """Evidence object representing transaction cost and turnover feasibility."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        annualized_turnover: float,
        max_drawdown: float,
        net_sharpe_after_costs: float,
        tc_bps: float = 5.0,
        max_turnover: float = 0.30,
        max_allowable_dd: float = 0.20,
        min_net_sharpe: float = 0.50,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> ExecutionCostEvidence:
        passed = (
            (annualized_turnover <= max_turnover)
            and (max_drawdown <= max_allowable_dd)
            and (net_sharpe_after_costs >= min_net_sharpe)
        )
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"Execution Feasibility: Turnover {annualized_turnover:.1%} (max {max_turnover:.1%}), "
            f"Max DD {max_drawdown:.1%} (max {max_allowable_dd:.1%}), "
            f"Net Sharpe after {tc_bps:.1f}bps costs: {net_sharpe_after_costs:.2f}."
        )

        return cls(
            evidence_id=f"EV-COST-{alpha_id}",
            stage_id="COST_VALIDATION",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Transaction Cost, Slippage & Turnover Validation",
            metrics={
                "annualized_turnover": round(annualized_turnover, 4),
                "max_drawdown": round(max_drawdown, 4),
                "net_sharpe_after_costs": round(net_sharpe_after_costs, 4),
                "tc_bps": tc_bps,
            },
        )


class CapacityEvidence(Evidence):
    """Evidence object representing alpha capacity scaling under non-linear market impact."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        capacity_usd: float,
        has_capacity_model: bool = True,
        min_capacity_usd: float = 10_000_000.0,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> CapacityEvidence:
        passed = has_capacity_model and (capacity_usd >= min_capacity_usd)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"Alpha Capacity: ${capacity_usd:,.0f} (hurdle ${min_capacity_usd:,.0f}) "
            f"under square-root Almgren-Chriss market impact model."
        )

        return cls(
            evidence_id=f"EV-CAP-{alpha_id}",
            stage_id="CAPACITY_TEST",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Almgren-Chriss Square-Root Market Impact Capacity Estimation",
            metrics={
                "capacity_usd": capacity_usd,
                "has_capacity_model": has_capacity_model,
                "min_capacity_threshold": min_capacity_usd,
            },
        )
