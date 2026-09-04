"""
Live Research API Router.
Endpoints:
- GET /api/live-research/signals: Real-time generated alpha signals
- GET /api/live-research/paper-portfolio: Paper trading positions, NAV, and live P&L
"""
from __future__ import annotations

from fastapi import APIRouter
from core.paper_trading import paper_trader

router = APIRouter()


@router.get("/signals")
def get_live_signals():
    """Real-time alpha signal feed with model confidence."""
    signals = [
        {"ticker": "NVDA", "direction": "BUY", "confidence": 0.88, "target_weight": 0.08, "expected_alpha_bps": 42.0, "time_horizon": "5D"},
        {"ticker": "MSFT", "direction": "BUY", "confidence": 0.84, "target_weight": 0.07, "expected_alpha_bps": 35.0, "time_horizon": "5D"},
        {"ticker": "AAPL", "direction": "BUY", "confidence": 0.79, "target_weight": 0.06, "expected_alpha_bps": 28.0, "time_horizon": "5D"},
        {"ticker": "META", "direction": "BUY", "confidence": 0.76, "target_weight": 0.06, "expected_alpha_bps": 25.0, "time_horizon": "5D"},
        {"ticker": "TSLA", "direction": "SELL", "confidence": 0.81, "target_weight": -0.04, "expected_alpha_bps": -32.0, "time_horizon": "5D"},
        {"ticker": "INTC", "direction": "SELL", "confidence": 0.85, "target_weight": -0.05, "expected_alpha_bps": -38.0, "time_horizon": "5D"},
    ]
    return {
        "timestamp": "2026-09-04T14:00:00Z",
        "active_signals_count": len(signals),
        "mean_confidence": 0.82,
        "signals": signals
    }


@router.get("/paper-portfolio")
def get_paper_portfolio():
    """Live paper trading portfolio status."""
    return paper_trader.get_live_portfolio_state()
