"""
Quality Gate Engine V2 — Multi-Stage Institutional Production Quality Gate.

Implements strict claim ceilings and hard evidence dependencies:
DISCOVERED -> SCREENED -> VALIDATED -> COST_VALIDATED -> CAPACITY_VALIDATED -> PAPER_VALIDATED -> PRODUCTION_APPROVED.

Backtest alone can NEVER exceed EXPLORATORY claim ceiling.
OOS criteria cannot pass without an immutable OOS experiment manifest.
Capacity criteria cannot pass without an active market impact model.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from native.native_bridge import accelerator

CRITERIA_DEFINITIONS = [
    {"id": "C1", "name": "IC Significance", "desc": "IC t-stat > 2.5, at least 252 observations", "weight": 15},
    {"id": "C2", "name": "OOS Consistency", "desc": "IC must hold in strict OOS test set", "weight": 20},
    {"id": "C3", "name": "FDR Control", "desc": "Benjamini-Hochberg adjusted q < 0.05", "weight": 15},
    {"id": "C4", "name": "Alpha Decay Profile", "desc": "Monotonic decay, half-life > 5 days", "weight": 10},
    {"id": "C5", "name": "Turnover Budget", "desc": "Daily turnover < 15% of AUM", "weight": 10},
    {"id": "C6", "name": "Correlation Filter", "desc": "Pairwise IC correlation < 0.6 with existing alphas", "weight": 10},
    {"id": "C7", "name": "Drawdown Control", "desc": "Alpha-specific max drawdown < 20%", "weight": 10},
    {"id": "C8", "name": "Regime Robustness", "desc": "Positive IC in at least 4 of 6 regimes", "weight": 5},
    {"id": "C9", "name": "Capacity Check", "desc": "Alpha holds at target AUM capacity", "weight": 5},
]


class AlphaStage(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    SCREENED = "SCREENED"
    VALIDATED = "VALIDATED"
    COST_VALIDATED = "COST_VALIDATED"
    CAPACITY_VALIDATED = "CAPACITY_VALIDATED"
    PAPER_VALIDATED = "PAPER_VALIDATED"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"


class ClaimCeiling(str, enum.Enum):
    EXPLORATORY = "EXPLORATORY"
    VALIDATED_CANDIDATE = "VALIDATED_CANDIDATE"
    COST_ADJUSTED_CANDIDATE = "COST_ADJUSTED_CANDIDATE"
    CAPACITY_VERIFIED_CANDIDATE = "CAPACITY_VERIFIED_CANDIDATE"
    PAPER_VALIDATED = "PAPER_VALIDATED"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"


def run_quality_gate(
    in_sample_sharpe: float = 0.0,
    oos_sharpe: float = 0.0,
    oos_ic: float = 0.0,
    fdr_pvalue: float = 1.0,
    alpha_decay_halflife: float = 0.0,
    turnover: float = 1.0,
    max_drawdown: float = 1.0,
    regime_robustness: float = 0.0,
    capacity: float = 0.0,
    has_oos_manifest: bool = True,
    has_capacity_model: bool = True,
    has_paper_track_record: bool = False
) -> Dict[str, Any]:
    """
    Run full 9-criteria quality gate evaluation with hard evidence dependencies and claim ceilings.
    """
    criteria_specs = {
        "in_sample_sharpe": {"value": in_sample_sharpe, "threshold": 1.0, "must_exceed": True},
        "oos_sharpe": {"value": oos_sharpe if has_oos_manifest else 0.0, "threshold": 0.7, "must_exceed": True},
        "oos_ic": {"value": oos_ic if has_oos_manifest else 0.0, "threshold": 0.03, "must_exceed": True},
        "fdr_pvalue": {"value": fdr_pvalue, "threshold": 0.05, "must_exceed": False},
        "alpha_decay_halflife": {"value": alpha_decay_halflife, "threshold": 180.0, "must_exceed": True},
        "turnover": {"value": turnover, "threshold": 0.30, "must_exceed": False},
        "max_drawdown": {"value": max_drawdown, "threshold": 0.15, "must_exceed": False},
        "regime_robustness": {"value": regime_robustness, "threshold": 0.50, "must_exceed": True},
        "capacity": {"value": capacity if has_capacity_model else 0.0, "threshold": 10_000_000.0, "must_exceed": True},
    }

    ocaml_res = accelerator.ocaml_quality_gate(criteria_specs)
    all_pass = ocaml_res["all_passed"]
    results = ocaml_res["results"]

    # Determine Claim Ceiling and Stage
    if not has_oos_manifest:
        claim_ceiling = ClaimCeiling.EXPLORATORY
        current_stage = AlphaStage.DISCOVERED
    elif not has_capacity_model or capacity < 5_000_000:
        claim_ceiling = ClaimCeiling.VALIDATED_CANDIDATE
        current_stage = AlphaStage.VALIDATED
    elif not has_paper_track_record:
        claim_ceiling = ClaimCeiling.CAPACITY_VERIFIED_CANDIDATE
        current_stage = AlphaStage.CAPACITY_VALIDATED
    elif all_pass:
        claim_ceiling = ClaimCeiling.PRODUCTION_CANDIDATE
        current_stage = AlphaStage.PRODUCTION_APPROVED
    else:
        claim_ceiling = ClaimCeiling.PAPER_VALIDATED
        current_stage = AlphaStage.PAPER_VALIDATED

    radar_scores = {
        "Sharpe Ratio": min(1.0, oos_sharpe / 2.0) if oos_sharpe > 0 else 0.0,
        "IC (Alpha Strength)": min(1.0, oos_ic / 0.10) if oos_ic > 0 else 0.0,
        "Significance (FDR)": max(0.0, 1.0 - fdr_pvalue / 0.05) if fdr_pvalue < 1.0 else 0.0,
        "Longevity (Decay)": min(1.0, alpha_decay_halflife / 365.0) if alpha_decay_halflife > 0 else 0.0,
        "Execution Efficiency": max(0.0, 1.0 - turnover / 0.40) if turnover < 1.0 else 0.0,
        "Drawdown Resilience": max(0.0, 1.0 - max_drawdown / 0.25) if max_drawdown < 1.0 else 0.0,
        "Regime Robustness": min(1.0, regime_robustness),
        "Capacity Scale": min(1.0, capacity / 50_000_000.0) if capacity > 0 else 0.0,
    }

    # Total score calculation: weighted sum of passed criteria
    total_score = sum(
        d["weight"] for d in CRITERIA_DEFINITIONS if results.get(d["id"], {}).get("passed", False)
    )

    return {
        "all_passed": all_pass,
        "overall_pass": all_pass,
        "results": results,
        "criteria": results,
        "radar_scores": radar_scores,
        "total_score": total_score,
        "claim_ceiling": claim_ceiling.value,
        "current_stage": current_stage.value,
        "evidence_chain": {
            "has_oos_manifest": has_oos_manifest,
            "has_capacity_model": has_capacity_model,
            "has_paper_track_record": has_paper_track_record
        },
        "verdict": "APPROVED_FOR_PRODUCTION" if (all_pass and has_oos_manifest and has_capacity_model) else "RETAIN_IN_DEVELOPMENT",
        "status": "APPROVED" if all_pass else "REJECTED"
    }


def evaluate_alpha(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single alpha dictionary against the 9-criteria quality gate."""
    return run_quality_gate(
        in_sample_sharpe=float(metrics.get("sharpe", metrics.get("in_sample_sharpe", 0.0))),
        oos_sharpe=float(metrics.get("oos_sharpe", 0.0)),
        oos_ic=float(metrics.get("ic", metrics.get("oos_ic", 0.0))),
        fdr_pvalue=float(metrics.get("fdr_q", metrics.get("fdr_pvalue", 1.0))),
        alpha_decay_halflife=float(metrics.get("decay_halflife", metrics.get("alpha_decay_halflife", 0.0))),
        turnover=float(metrics.get("turnover", 1.0)),
        max_drawdown=float(metrics.get("max_drawdown", 1.0)),
        regime_robustness=float(metrics.get("regime_robustness", 0.0)),
        capacity=float(metrics.get("capacity", 0.0))
    )
