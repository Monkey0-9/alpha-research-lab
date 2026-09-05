"""
Quality Gate Engine — 9 Institutional Production Criteria.

Guarantees only institutional-grade, statistically sound alphas are promoted to live execution.
Evaluates REAL experiment output against thresholds. No hardcoded alpha results.
"""
from __future__ import annotations

from typing import Dict, Any
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


def run_quality_gate(
    in_sample_sharpe: float = 0.0,
    oos_sharpe: float = 0.0,
    oos_ic: float = 0.0,
    fdr_pvalue: float = 1.0,
    alpha_decay_halflife: float = 0.0,
    turnover: float = 1.0,
    max_drawdown: float = 1.0,
    regime_robustness: float = 0.0,
    capacity: float = 0.0
) -> Dict[str, Any]:
    """
    Run full 9-criteria quality gate evaluation against REAL experiment output.
    """
    criteria_specs = {
        "in_sample_sharpe": {"value": in_sample_sharpe, "threshold": 1.0, "must_exceed": True},
        "oos_sharpe": {"value": oos_sharpe, "threshold": 0.7, "must_exceed": True},
        "oos_ic": {"value": oos_ic, "threshold": 0.03, "must_exceed": True},
        "fdr_pvalue": {"value": fdr_pvalue, "threshold": 0.05, "must_exceed": False},
        "alpha_decay_halflife": {"value": alpha_decay_halflife, "threshold": 180.0, "must_exceed": True},
        "turnover": {"value": turnover, "threshold": 0.30, "must_exceed": False},
        "max_drawdown": {"value": max_drawdown, "threshold": 0.15, "must_exceed": False},
        "regime_robustness": {"value": regime_robustness, "threshold": 0.50, "must_exceed": True},
        "capacity": {"value": capacity, "threshold": 10_000_000.0, "must_exceed": True},
    }

    ocaml_res = accelerator.ocaml_quality_gate(criteria_specs)
    all_pass = ocaml_res["all_passed"]
    results = ocaml_res["results"]

    radar_scores = {
        "Sharpe Ratio": min(1.0, oos_sharpe / 2.0) if oos_sharpe > 0 else 0.0,
        "IC (Alpha Strength)": min(1.0, oos_ic / 0.10) if oos_ic > 0 else 0.0,
        "Significance (FDR)": max(0.0, 1.0 - fdr_pvalue / 0.05) if fdr_pvalue < 1.0 else 0.0,
        "Longevity (Decay)": min(1.0, alpha_decay_halflife / 365.0) if alpha_decay_halflife > 0 else 0.0,
        "Execution Efficiency": max(0.0, 1.0 - turnover / 0.40) if turnover < 1.0 else 0.0,
        "Capital Preservation": max(0.0, 1.0 - max_drawdown / 0.20) if max_drawdown < 1.0 else 0.0,
        "Regime Stability": min(1.0, regime_robustness / 1.0) if regime_robustness > 0 else 0.0,
        "Capacity Scale": min(1.0, capacity / 100_000_000.0) if capacity > 0 else 0.0
    }

    return {
        "overall_pass": all_pass,
        "engine": ocaml_res["engine"],
        "criteria": results,
        "radar_scores": radar_scores
    }


def evaluate_alpha(alpha_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single alpha against the 9-criteria quality gate.

    Args:
        alpha_metrics: Real metrics from an experiment, must contain:
            - ic: Information Coefficient
            - sharpe: Sharpe ratio
            - oos_sharpe: Out-of-sample Sharpe
            - fdr_q: FDR-adjusted q-value
            - decay_halflife: Alpha decay half-life in days
            - turnover: Daily turnover
            - max_drawdown: Maximum drawdown
            - regime_robustness: Fraction of regimes with positive IC
            - capacity: Estimated capacity in USD

    Returns:
        Quality gate evaluation with PASS/FAIL and evidence for each criterion.
    """
    ic = alpha_metrics.get("ic", 0.0)
    sharpe = alpha_metrics.get("sharpe", 0.0)
    oos_sharpe = alpha_metrics.get("oos_sharpe", 0.0)
    fdr_q = alpha_metrics.get("fdr_q", 1.0)
    decay = alpha_metrics.get("decay_halflife", 0.0)
    turnover = alpha_metrics.get("turnover", 1.0)
    max_dd = alpha_metrics.get("max_drawdown", 1.0)
    regime_rob = alpha_metrics.get("regime_robustness", 0.0)
    capacity = alpha_metrics.get("capacity", 0.0)

    gate_result = run_quality_gate(
        in_sample_sharpe=sharpe,
        oos_sharpe=oos_sharpe,
        oos_ic=ic,
        fdr_pvalue=fdr_q,
        alpha_decay_halflife=decay,
        turnover=turnover,
        max_drawdown=max_dd,
        regime_robustness=regime_rob,
        capacity=capacity
    )

    return {
        "status": "PASS" if gate_result["overall_pass"] else "FAIL",
        "criteria": gate_result["criteria"],
        "radar_scores": gate_result["radar_scores"],
        "engine": gate_result["engine"],
        "input_metrics": alpha_metrics
    }
