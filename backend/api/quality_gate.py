"""
Quality Gate API Router.
Endpoint:
- GET /api/quality-gate/run: Evaluates strategy against 9 rigorous institutional standards.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from core.quality_gate import run_quality_gate

router = APIRouter()


@router.get("/run")
def get_quality_gate_run(backtest_id: str = Query("latest", description="Backtest identifier")):
    """
    Evaluates strategy against 9 institutional gates via OCaml type-safe verification engine.
    """
    res = run_quality_gate()
    return res
