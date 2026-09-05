"""
Quality Gate API Router
Module 07 — Alpha Quality Gate
Endpoints:
- POST /api/quality-gate/evaluate
- POST /api/quality-gate/run
- GET /api/quality-gate/criteria
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from core.quality_gate import run_quality_gate, evaluate_alpha, CRITERIA_DEFINITIONS

router = APIRouter()


class EvaluateAlphaRequest(BaseModel):
    ic: float = Field(0.0, description="Information Coefficient")
    sharpe: float = Field(0.0, description="In-sample Sharpe ratio")
    oos_sharpe: float = Field(0.0, description="Out-of-sample Sharpe ratio")
    fdr_q: float = Field(1.0, description="FDR-adjusted q-value")
    decay_halflife: float = Field(0.0, description="Alpha decay half-life in days")
    turnover: float = Field(1.0, description="Daily turnover")
    max_drawdown: float = Field(1.0, description="Maximum drawdown")
    regime_robustness: float = Field(0.0, description="Fraction of regimes with positive IC")
    capacity: float = Field(0.0, description="Estimated capacity in USD")


class GateRunRequest(BaseModel):
    in_sample_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    oos_ic: float = 0.0
    fdr_pvalue: float = 1.0
    alpha_decay_halflife: float = 0.0
    turnover: float = 1.0
    max_drawdown: float = 1.0
    regime_robustness: float = 0.0
    capacity: float = 0.0


@router.post("/evaluate")
def post_evaluate_alpha(request: EvaluateAlphaRequest):
    """Evaluate a single alpha against the 9-criteria quality gate using REAL metrics."""
    metrics = {
        "ic": request.ic,
        "sharpe": request.sharpe,
        "oos_sharpe": request.oos_sharpe,
        "fdr_q": request.fdr_q,
        "decay_halflife": request.decay_halflife,
        "turnover": request.turnover,
        "max_drawdown": request.max_drawdown,
        "regime_robustness": request.regime_robustness,
        "capacity": request.capacity,
    }
    return evaluate_alpha(metrics)


@router.get("/run")
def get_quality_gate_run():
    """Run 9-criteria quality gate with zero baseline — requires POST with real metrics for meaningful results."""
    return run_quality_gate()


@router.post("/run")
def post_quality_gate_run(request: GateRunRequest):
    """Run the 9-criteria quality gate with explicit real metrics."""
    return run_quality_gate(
        in_sample_sharpe=request.in_sample_sharpe,
        oos_sharpe=request.oos_sharpe,
        oos_ic=request.oos_ic,
        fdr_pvalue=request.fdr_pvalue,
        alpha_decay_halflife=request.alpha_decay_halflife,
        turnover=request.turnover,
        max_drawdown=request.max_drawdown,
        regime_robustness=request.regime_robustness,
        capacity=request.capacity,
    )


@router.get("/criteria")
def get_quality_gate_criteria():
    """Return the 9 institutional quality gate criteria definitions."""
    return {
        "criteria": CRITERIA_DEFINITIONS,
        "total": len(CRITERIA_DEFINITIONS),
    }
