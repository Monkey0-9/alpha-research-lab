"""
Backtest API Router.
POST /api/backtest/run: Runs temporal walk-forward backtest and returns equity curve, metrics, trades.
"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from core.backtester import backtester_engine

router = APIRouter()


class BacktestRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    start_date: str = Field("2020-01-01", description="Backtest start date")
    end_date: str = Field("2024-12-31", description="Backtest end date")
    model_type: str = Field("lightgbm", description="ML model type (lightgbm, ridge)")
    features: List[str] = Field(
        default=["momentum_20d", "volatility_20d", "rsi_14", "return_20d"],
        description="Features list"
    )
    universe: str = Field("sp500", description="Universe")
    rebalance_freq: str = Field("M", description="Rebalance frequency (M=monthly)")
    position_sizing: str = Field("vol_target", description="vol_target or equal_weight")
    target_vol: float = Field(0.10, description="Annualized target volatility")


@router.post("/run")
def run_backtest(req: BacktestRequest):
    """
    Run temporal walk-forward backtest without lookahead bias.
    """
    if hasattr(backtester_engine, "rebalance_freq"):
        from core.backtester import _safe_freq
        backtester_engine.rebalance_freq = _safe_freq(req.rebalance_freq)
    results = backtester_engine.run(
        start_date=req.start_date,
        end_date=req.end_date,
        model_type=req.model_type,
        position_sizing=req.position_sizing,
        target_vol=req.target_vol
    )
    return dict(results) if isinstance(results, dict) else results


@router.get("/status")
def get_backtest_status():
    return {
        "status": "READY",
        "engine": "EventDrivenBacktester",
        "acceleration": "Rust / C Native FFI"
    }
