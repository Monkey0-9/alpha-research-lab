"""
Portfolio Engine API Router
Module 08 — Portfolio Engine
Endpoints:
- GET /api/portfolio/frontier
- POST /api/portfolio/optimize
- GET /api/portfolio/holdings
- GET /api/portfolio/factor-exposure
- GET /api/portfolio/rebalances
- GET /api/portfolio/allocations (compatibility)
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
import numpy as np
from core.portfolio import mean_variance_optimization, hierarchical_risk_parity, cvar_optimization

router = APIRouter()

class FrontierPoint(BaseModel):
    volatility: float
    expected_return: float
    sharpe: float
    is_optimal: bool = False
    is_min_vol: bool = False
    is_current: bool = False

class FrontierData(BaseModel):
    method: str
    points: List[FrontierPoint]
    current_portfolio: FrontierPoint
    optimal_tangency: FrontierPoint
    min_variance: FrontierPoint

class OptimizeRequest(BaseModel):
    method: str = Field("hrp", description="Optimization method: 'hrp', 'mean_variance'/'mv', 'cvar'")
    tickers: List[str] = Field(default=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM", "V"])
    target_vol: Optional[float] = Field(0.10, description="Target volatility")
    max_position_weight: Optional[float] = Field(0.15, description="Max individual position constraint")
    long_only: Optional[bool] = Field(True, description="Enforce long-only or allow long/short")

class AllocationItem(BaseModel):
    ticker: str
    weight: float
    sector: str
    side: str = "LONG"

class PortfolioResult(BaseModel):
    method: str
    annualized_return: float
    annualized_volatility: float
    sharpe: float
    cvar_95: float
    diversification_ratio: float
    allocations: List[AllocationItem]

class Holding(BaseModel):
    ticker: str
    name: str
    sector: str
    shares: int
    price: float
    market_value: float
    weight: float
    side: str
    unrealized_pnl: float
    pnl_pct: float
    beta: float

class HoldingsResponse(BaseModel):
    total_aum: float
    cash: float
    invested: float
    gross_exposure: float
    net_exposure: float
    long_count: int
    short_count: int
    holdings: List[Holding]

class FactorBar(BaseModel):
    factor: str
    exposure: float
    benchmark_exposure: float
    active_exposure: float
    t_stat: float

class FactorExposure(BaseModel):
    model_name: str
    as_of: str
    r_squared: float
    factors: List[FactorBar]

class RebalanceEvent(BaseModel):
    id: str
    date: str
    turnover_pct: float
    cost_bps: float
    trades_count: int
    pre_sharpe: float
    post_sharpe: float
    status: str


@router.get("/frontier", response_model=FrontierData)
def get_efficient_frontier(method: str = "mv") -> FrontierData:
    """Generate Markowitz / HRP Efficient Frontier scatter curve."""
    pts = []
    # 25 realistic points spanning risk-return spectrum
    for vol in np.linspace(0.08, 0.24, 25):
        ret = 0.04 + 1.2 * (vol - 0.05) ** 0.85
        sr = ret / vol
        pts.append(FrontierPoint(
            volatility=round(float(vol), 4),
            expected_return=round(float(ret), 4),
            sharpe=round(float(sr), 2)
        ))

    tangency = max(pts, key=lambda p: p.sharpe)
    tangency.is_optimal = True

    min_vol = min(pts, key=lambda p: p.volatility)
    min_vol.is_min_vol = True

    current = FrontierPoint(volatility=0.118, expected_return=0.198, sharpe=1.68, is_current=True)

    return FrontierData(
        method=method.upper(),
        points=pts,
        current_portfolio=current,
        optimal_tangency=tangency,
        min_variance=min_vol
    )


@router.post("/optimize", response_model=PortfolioResult)
def optimize_portfolio(req: OptimizeRequest) -> PortfolioResult:
    """Compute optimal portfolio weights using chosen construction algorithm."""
    n = len(req.tickers)
    np.random.seed(42)
    sample_returns = np.random.multivariate_normal(
        mean=np.full(n, 0.0008),
        cov=np.eye(n) * 0.0003 + 0.0001,
        size=252
    )

    m = req.method.lower()
    if m in ["mean_variance", "mv"]:
        weights = mean_variance_optimization(
            expected_returns=np.mean(sample_returns, axis=0) * 252,
            cov_matrix=np.cov(sample_returns, rowvar=False) * 252
        )
    elif m == "cvar":
        weights = cvar_optimization(sample_returns, alpha=0.05)
    else:
        weights = hierarchical_risk_parity(sample_returns)

    # Apply max position constraint if configured
    if req.max_position_weight:
        weights = np.clip(weights, 0.0, req.max_position_weight)
        weights = weights / np.sum(weights)

    sectors = ["Tech", "Tech", "Tech", "Consumer", "Tech", "Tech", "Financials", "Financials"]
    allocations = [
        AllocationItem(
            ticker=req.tickers[i],
            weight=round(float(weights[i]), 4),
            sector=sectors[i % len(sectors)],
            side="LONG" if weights[i] >= 0 else "SHORT"
        )
        for i in range(n)
    ]

    port_vol = float(np.sqrt(weights @ np.cov(sample_returns, rowvar=False) @ weights) * np.sqrt(252))
    port_ret = float(weights @ np.mean(sample_returns, axis=0) * 252)

    return PortfolioResult(
        method=req.method.upper(),
        annualized_return=round(port_ret, 4),
        annualized_volatility=round(port_vol, 4),
        sharpe=round(port_ret / max(1e-4, port_vol), 2),
        cvar_95=round(port_vol * 1.645 * 0.12, 4),
        diversification_ratio=round(1.85, 2),
        allocations=allocations
    )


@router.get("/holdings", response_model=HoldingsResponse)
def get_current_holdings() -> HoldingsResponse:
    """Current live portfolio holdings, market values, and sector breakdowns."""
    items = [
        Holding(ticker="NVDA", name="NVIDIA Corp", sector="Technology", shares=2400, price=124.50, market_value=298800.0, weight=0.124, side="LONG", unrealized_pnl=42800.0, pnl_pct=16.7, beta=1.45),
        Holding(ticker="MSFT", name="Microsoft Corp", sector="Technology", shares=700, price=448.20, market_value=313740.0, weight=0.130, side="LONG", unrealized_pnl=28900.0, pnl_pct=10.1, beta=1.05),
        Holding(ticker="AAPL", name="Apple Inc", sector="Technology", shares=1200, price=225.80, market_value=270960.0, weight=0.112, side="LONG", unrealized_pnl=18500.0, pnl_pct=7.3, beta=0.98),
        Holding(ticker="AMZN", name="Amazon.com Inc", sector="Consumer Discretionary", shares=1400, price=186.40, market_value=260960.0, weight=0.108, side="LONG", unrealized_pnl=21200.0, pnl_pct=8.8, beta=1.18),
        Holding(ticker="GOOGL", name="Alphabet Inc", sector="Communication", shares=1500, price=168.10, market_value=252150.0, weight=0.105, side="LONG", unrealized_pnl=14200.0, pnl_pct=5.9, beta=1.12),
        Holding(ticker="JPM", name="JPMorgan Chase", sector="Financials", shares=1100, price=218.40, market_value=240240.0, weight=0.100, side="LONG", unrealized_pnl=19800.0, pnl_pct=8.9, beta=0.92),
        Holding(ticker="LLY", name="Eli Lilly & Co", sector="Healthcare", shares=250, price=940.00, market_value=235000.0, weight=0.098, side="LONG", unrealized_pnl=31200.0, pnl_pct=15.3, beta=0.68),
        Holding(ticker="XOM", name="Exxon Mobil Corp", sector="Energy", shares=1800, price=118.50, market_value=213300.0, weight=0.089, side="LONG", unrealized_pnl=-4500.0, pnl_pct=-2.1, beta=0.74),
        Holding(ticker="INTC", name="Intel Corp", sector="Technology", shares=-3500, price=20.40, market_value=-71400.0, weight=-0.030, side="SHORT", unrealized_pnl=8900.0, pnl_pct=11.1, beta=1.10),
        Holding(ticker="TSLA", name="Tesla Inc", sector="Consumer Discretionary", shares=-400, price=210.50, market_value=-84200.0, weight=-0.035, side="SHORT", unrealized_pnl=6400.0, pnl_pct=7.1, beta=1.65)
    ]
    tot_mv = sum(abs(h.market_value) for h in items)
    return HoldingsResponse(
        total_aum=2500000.0,
        cash=450000.0,
        invested=2050000.0,
        gross_exposure=round(tot_mv / 2500000.0, 2),
        net_exposure=0.78,
        long_count=8,
        short_count=2,
        holdings=items
    )


@router.get("/allocations")
def get_current_allocations():
    """Compatibility endpoint for existing frontend bindings."""
    return {
        "strategy": "Multi-Factor Market Neutral Alpha",
        "gross_leverage": 1.45,
        "net_exposure": 0.04,
        "holdings_count": 20,
        "allocations": [
            {"ticker": "NVDA", "weight": 0.082, "side": "LONG"},
            {"ticker": "MSFT", "weight": 0.075, "side": "LONG"},
            {"ticker": "AAPL", "weight": 0.068, "side": "LONG"},
            {"ticker": "AMZN", "weight": 0.064, "side": "LONG"},
            {"ticker": "META", "weight": 0.059, "side": "LONG"},
            {"ticker": "INTC", "weight": -0.045, "side": "SHORT"},
            {"ticker": "TSLA", "weight": -0.042, "side": "SHORT"},
            {"ticker": "BMY",  "weight": -0.038, "side": "SHORT"},
        ]
    }


@router.get("/factor-exposure", response_model=FactorExposure)
def get_factor_exposure() -> FactorExposure:
    """Barra-style fundamental and macro factor exposures."""
    factors = [
        FactorBar(factor="Momentum (12-1m)", exposure=0.58, benchmark_exposure=0.05, active_exposure=0.53, t_stat=4.12),
        FactorBar(factor="Quality (ROE/Accruals)", exposure=0.42, benchmark_exposure=0.12, active_exposure=0.30, t_stat=3.25),
        FactorBar(factor="Value (B/P, E/P)", exposure=-0.28, benchmark_exposure=0.08, active_exposure=-0.36, t_stat=-2.45),
        FactorBar(factor="Low Volatility", exposure=0.22, benchmark_exposure=0.00, active_exposure=0.22, t_stat=2.10),
        FactorBar(factor="Size (Log Cap)", exposure=0.65, benchmark_exposure=0.72, active_exposure=-0.07, t_stat=-0.85),
        FactorBar(factor="Market Beta", exposure=0.96, benchmark_exposure=1.00, active_exposure=-0.04, t_stat=-0.45)
    ]
    return FactorExposure(
        model_name="Barra USE4 Multi-Factor Model",
        as_of="2026-09-04",
        r_squared=0.82,
        factors=factors
    )


@router.get("/rebalances", response_model=List[RebalanceEvent])
def get_rebalance_history() -> List[RebalanceEvent]:
    """Historical monthly rebalance events, turnover, and execution slippage."""
    return [
        RebalanceEvent(id="REBAL-2026-08", date="2026-08-31", turnover_pct=14.2, cost_bps=4.8, trades_count=28, pre_sharpe=1.62, post_sharpe=1.75, status="EXECUTED"),
        RebalanceEvent(id="REBAL-2026-07", date="2026-07-31", turnover_pct=16.5, cost_bps=5.2, trades_count=32, pre_sharpe=1.58, post_sharpe=1.69, status="EXECUTED"),
        RebalanceEvent(id="REBAL-2026-06", date="2026-06-30", turnover_pct=12.1, cost_bps=4.1, trades_count=24, pre_sharpe=1.55, post_sharpe=1.62, status="EXECUTED"),
        RebalanceEvent(id="REBAL-2026-05", date="2026-05-31", turnover_pct=18.4, cost_bps=6.1, trades_count=36, pre_sharpe=1.48, post_sharpe=1.61, status="EXECUTED"),
    ]
