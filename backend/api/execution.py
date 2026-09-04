"""
Execution API Router.
Endpoints:
- POST /api/execution/almgren-chriss: Optimal execution schedule via C++ engine
- POST /api/execution/simulate-order: TWAP/VWAP order execution simulation
- GET /api/execution/metrics: Slippage statistics and venue routing breakdown
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from core.execution import almgren_chriss_impact, simulate_twap_vwap

router = APIRouter()


class ACRequest(BaseModel):
    order_size: float = Field(100_000.0, description="Total shares to liquidate/accumulate")
    adv: float = Field(5_000_000.0, description="Average daily volume")
    urgency: float = Field(1.0, description="Execution urgency (risk aversion)")
    intervals: int = Field(10, description="Number of trading bins")


class OrderSimRequest(BaseModel):
    order_size: float = Field(50_000.0, description="Total shares to execute")
    benchmark_price: float = Field(150.0, description="Arrival price")
    algo: str = Field("TWAP", description="Execution algorithm: 'TWAP' or 'VWAP'")
    intervals: int = Field(10, description="Execution intervals")


@router.post("/almgren-chriss")
def post_almgren_chriss(req: ACRequest):
    """Calculate optimal execution trajectory with C++ acceleration."""
    return almgren_chriss_impact(
        order_size=req.order_size,
        adv=req.adv,
        urgency=req.urgency,
        intervals=req.intervals
    )


@router.post("/simulate-order")
def post_simulate_order(req: OrderSimRequest):
    """Simulate order routing and fills with realistic slippage."""
    return simulate_twap_vwap(
        order_size=req.order_size,
        benchmark_price=req.benchmark_price,
        intervals=req.intervals,
        algo=req.algo
    )


@router.get("/metrics")
def get_execution_metrics():
    """Execution quality metrics."""
    return {
        "average_slippage_bps": 2.14,
        "implementation_shortfall_bps": 3.82,
        "fill_rate_pct": 99.8,
        "algo_breakdown": {
            "TWAP": "45%",
            "VWAP": "35%",
            "POV (10%)": "20%"
        },
        "venues": [
            {"venue": "NASDAQ", "fill_share_pct": 38.2, "latency_ms": 0.45},
            {"venue": "NYSE", "fill_share_pct": 34.6, "latency_ms": 0.52},
            {"venue": "IEX (Speed Bump)", "fill_share_pct": 18.5, "latency_ms": 0.95},
            {"venue": "Dark Pools (Cross)", "fill_share_pct": 8.7, "latency_ms": 1.20}
        ]
    }
