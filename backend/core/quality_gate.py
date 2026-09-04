"""
Quality Gate Engine — 9 Institutional Production Criteria.

Guarantees only institutional-grade, statistically sound alphas are promoted to live execution.
Evaluated via OCaml type-safe verification bridge.
"""
from __future__ import annotations

from typing import Dict, Any, List
from native.native_bridge import accelerator


def run_quality_gate(
    in_sample_sharpe: float = 1.45,
    oos_sharpe: float = 1.32,
    oos_ic: float = 0.052,
    fdr_pvalue: float = 0.01,
    alpha_decay_halflife: float = 240,
    turnover: float = 0.22,
    max_drawdown: float = 0.11,
    regime_robustness: float = 0.72,
    capacity: float = 50_000_000
) -> Dict[str, Any]:
    """
    Run full 9-criteria quality gate evaluation.
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

    # Pass through OCaml verified gate
    ocaml_res = accelerator.ocaml_quality_gate(criteria_specs)
    all_pass = ocaml_res["all_passed"]
    results = ocaml_res["results"]

    radar_scores = {
        "Sharpe Ratio": min(1.0, oos_sharpe / 2.0),
        "IC (Alpha Strength)": min(1.0, oos_ic / 0.10),
        "Significance (FDR)": max(0.0, 1.0 - fdr_pvalue / 0.05),
        "Longevity (Decay)": min(1.0, alpha_decay_halflife / 365.0),
        "Execution Efficiency": max(0.0, 1.0 - turnover / 0.40),
        "Capital Preservation": max(0.0, 1.0 - max_drawdown / 0.20),
        "Regime Stability": min(1.0, regime_robustness / 1.0),
        "Capacity Scale": min(1.0, capacity / 100_000_000.0)
    }

    return {
        "overall_pass": all_pass,
        "engine": ocaml_res["engine"],
        "criteria": results,
        "radar_scores": radar_scores
    }
