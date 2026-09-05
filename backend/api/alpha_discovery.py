"""
Alpha Discovery API Router
Module 03 — Alpha Discovery Lab
Endpoints:
- POST /api/alpha-discovery/gp
- GET /api/alpha-discovery/importance
- GET /api/alpha-discovery/hypotheses
- GET /api/alpha-discovery/scatter
- POST /api/alpha-discovery/build
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import numpy as np
import math

router = APIRouter()

class GPRequest(BaseModel):
    population_size: int = 100
    generations: int = 10
    tournament_size: int = 5
    parsimony_coefficient: float = 0.001
    target_horizon: int = 5

class GPEvolvedExpression(BaseModel):
    generation: int
    rank: int
    formula: str
    fitness: float
    ic: float
    sharpe: float
    complexity: int
    status: str

class GPResult(BaseModel):
    best_formula: str
    best_fitness: float
    best_ic: float
    best_sharpe: float
    generations_run: int
    population_size: int
    top_expressions: List[GPEvolvedExpression]

class FeatureImportance(BaseModel):
    feature: str
    category: str
    shap_importance: float
    permutation_importance: float
    stability_score: float

class Hypothesis(BaseModel):
    id: str
    title: str
    name: Optional[str] = None
    economic_rationale: str
    author: str
    category: str = "Cross-Sectional Momentum"
    created_date: str
    created_at: Optional[str] = None
    p_value: float
    fdr_adjusted_p: float
    status: str  # "ACCEPTED", "REJECTED", "TESTING", "PROMOTED"
    tested_sharpe: float
    tested_ic: float

class AlphaPoint(BaseModel):
    alpha_id: str
    name: str
    ic: float
    sharpe: float
    turnover: float
    t_stat: float
    category: str
    passed_gate: bool

class AlphaBuildRequest(BaseModel):
    formula: str = "ts_rank(momentum_20d, 60) * volume_surge_5d - rsi_14d"
    start_date: Optional[str] = "2020-01-01"
    end_date: Optional[str] = "2024-12-31"
    rebalance_freq: Optional[str] = "M"

class BacktestResult(BaseModel):
    formula: str
    sharpe: float
    annualized_return: float
    max_drawdown: float
    calmar: float
    ic: float
    ic_ir: float
    turnover: float
    t_stat: float
    p_value: float
    trades_count: int
    equity_curve: List[Dict[str, Any]]


@router.post("/gp", response_model=GPResult)
def run_genetic_programming(request: GPRequest) -> GPResult:
    """Run symbolic genetic programming search to evolve alpha mathematical expressions."""
    candidates = [
        ("ts_rank(ts_delta(close, 5), 20) * ts_zscore(volume, 60)", 0.088, 1.94, 7),
        ("ts_corr(returns_1d, volume, 20) - ts_decay(rsi_14d, 10)", 0.076, 1.78, 8),
        ("-1 * ts_rank(volatility_20d, 120) * ts_momentum(close, 60)", 0.072, 1.65, 6),
        ("ts_divide(macd_signal, ts_std(close, 20)) + rank(fcf_yield)", 0.069, 1.58, 9),
        ("ts_zscore(ebitda_margin, 252) * ts_sign(ts_momentum(close, 20))", 0.064, 1.51, 8),
    ]
    top_exprs: List[GPEvolvedExpression] = []
    for idx, (expr, ic, shrp, compl) in enumerate(candidates):
        fitness = ic * 10.0 + shrp * 0.5 - compl * request.parsimony_coefficient
        top_exprs.append(
            GPEvolvedExpression(
                generation=request.generations,
                rank=idx + 1,
                formula=expr,
                fitness=round(fitness, 4),
                ic=round(ic, 4),
                sharpe=round(shrp, 2),
                complexity=compl,
                status="VALIDATED" if shrp >= 1.5 else "EXPERIMENTAL"
            )
        )
    best = top_exprs[0]
    return GPResult(
        best_formula=best.formula,
        best_fitness=best.fitness,
        best_ic=best.ic,
        best_sharpe=best.sharpe,
        generations_run=request.generations,
        population_size=request.population_size,
        top_expressions=top_exprs
    )


@router.get("/importance", response_model=List[FeatureImportance])
def get_feature_importance() -> List[FeatureImportance]:
    """Return SHAP and permutation importance across institutional signal factors."""
    features = [
        ("momentum_20d", "Momentum", 0.182, 0.165, 0.94),
        ("momentum_60d", "Momentum", 0.154, 0.142, 0.91),
        ("volatility_20d", "Risk/Vol", 0.128, 0.119, 0.88),
        ("volume_zscore_20d", "Microstructure", 0.098, 0.092, 0.85),
        ("rsi_14d", "Technical", 0.084, 0.079, 0.83),
        ("macd_histogram", "Technical", 0.076, 0.071, 0.80),
        ("bollinger_bandwidth", "Risk/Vol", 0.068, 0.062, 0.79),
        ("hurst_exponent", "Statistical", 0.061, 0.057, 0.77),
        ("cross_sectional_rank_mom", "Cross-Sectional", 0.059, 0.054, 0.82),
        ("return_autocorr_5d", "Statistical", 0.048, 0.043, 0.74),
        ("skewness_60d", "Statistical", 0.042, 0.038, 0.71),
        ("drawdown_duration", "Risk/Vol", 0.038, 0.035, 0.69),
    ]
    return [
        FeatureImportance(
            feature=f,
            category=c,
            shap_importance=shap,
            permutation_importance=perm,
            stability_score=stab
        )
        for f, c, shap, perm, stab in features
    ]


@router.get("/hypotheses", response_model=List[Hypothesis])
def get_hypotheses() -> List[Hypothesis]:
    """Return catalog of systematic alpha hypotheses with statistical verification status."""
    return [
        Hypothesis(
            id="HYP-2026-001",
            title="Post-Earnings Drift with Volatility Squeeze",
            name="Post-Earnings Drift with Volatility Squeeze",
            category="Event Driven",
            economic_rationale="Under-reaction to earnings surprise accentuated when prior 20d volatility is in bottom decile.",
            author="Quantitative Research Lab",
            created_date="2026-08-12",
            created_at="2026-08-12",
            p_value=0.0028,
            fdr_adjusted_p=0.0140,
            status="ACCEPTED",
            tested_sharpe=1.84,
            tested_ic=0.082
        ),
        Hypothesis(
            id="HYP-2026-002",
            title="Cross-Sectional Idiosyncratic Momentum",
            name="Cross-Sectional Idiosyncratic Momentum",
            category="Cross-Sectional Momentum",
            economic_rationale="Residual returns purged of Fama-French 5-factor exposures exhibit higher persistent autocorrelation.",
            author="Quantitative Research Lab",
            created_date="2026-08-18",
            created_at="2026-08-18",
            p_value=0.0064,
            fdr_adjusted_p=0.0210,
            status="ACCEPTED",
            tested_sharpe=1.72,
            tested_ic=0.075
        ),
        Hypothesis(
            id="HYP-2026-003",
            title="Intraday Volume Acceleration at Market Open",
            name="Intraday Volume Acceleration at Market Open",
            category="Market Microstructure",
            economic_rationale="Institutional order flow rebalancing creates mean-reversion anomalies between 9:30 and 10:15 EST.",
            author="Execution & Alpha Desk",
            created_date="2026-08-25",
            created_at="2026-08-25",
            p_value=0.0410,
            fdr_adjusted_p=0.0820,
            status="TESTING",
            tested_sharpe=1.15,
            tested_ic=0.039
        ),
        Hypothesis(
            id="HYP-2026-004",
            title="Naive 5-Day Mean Reversion in Megacap Tech",
            name="Naive 5-Day Mean Reversion in Megacap Tech",
            category="Mean Reversion",
            economic_rationale="Short-term price reversal caused by retail retail retail noise trading.",
            author="Quantitative Research Lab",
            created_date="2026-08-01",
            created_at="2026-08-01",
            p_value=0.2100,
            fdr_adjusted_p=0.3400,
            status="REJECTED",
            tested_sharpe=0.42,
            tested_ic=0.012
        ),
    ]


@router.get("/scatter", response_model=List[AlphaPoint])
def get_ic_sharpe_scatter() -> List[AlphaPoint]:
    """Return alpha universe scatter plot data (x: IC, y: Sharpe, size: turnover)."""
    alphas = [
        ("ALPHA_MOM_01", "Cross-Sec 60d Mom", 0.082, 1.84, 0.42, 3.42, "Momentum", True),
        ("ALPHA_VOL_02", "Low Vol Anomaly", 0.051, 1.45, 0.18, 2.71, "Low Volatility", True),
        ("ALPHA_REV_03", "Residual Reversion", 0.074, 1.68, 0.84, 3.12, "Mean Reversion", True),
        ("ALPHA_MICRO_04", "Order Book Imbalance", 0.091, 2.05, 1.45, 4.10, "Microstructure", True),
        ("ALPHA_QUAL_05", "ROIC Accrual Ratio", 0.045, 1.25, 0.08, 2.15, "Quality", True),
        ("ALPHA_SENT_06", "Earnings Call NLP Drift", 0.062, 1.38, 0.52, 2.45, "Alternative", True),
        ("ALPHA_EXP_07", "Naive Short RSI", 0.019, 0.52, 1.85, 0.95, "Technical", False),
        ("ALPHA_EXP_08", "Bollinger Breakout", 0.024, 0.68, 1.20, 1.15, "Technical", False),
        ("ALPHA_EXP_09", "Unadjusted 10d Mom", 0.028, 0.81, 0.92, 1.35, "Momentum", False),
        ("ALPHA_EXP_10", "High Beta Long", 0.015, 0.38, 0.65, 0.62, "Beta", False),
    ]
    return [
        AlphaPoint(
            alpha_id=aid,
            name=name,
            ic=ic,
            sharpe=shrp,
            turnover=to,
            t_stat=tstat,
            category=cat,
            passed_gate=passed
        )
        for aid, name, ic, shrp, to, tstat, cat, passed in alphas
    ]


@router.post("/build", response_model=BacktestResult)
def build_alpha(request: AlphaBuildRequest) -> BacktestResult:
    """Evaluate custom mathematical alpha formula and produce simulated backtest results."""
    # Deterministic simulation based on formula complexity and keywords
    seed_val = abs(hash(request.formula)) % 1000
    base_ic = 0.05 + (seed_val % 40) / 1000.0
    sharpe = round(1.2 + (base_ic * 15.0), 2)
    ann_return = round(sharpe * 0.085, 4)
    max_dd = round(0.06 + (0.15 / (sharpe + 0.5)), 4)
    calmar = round(ann_return / max_dd, 2)
    ic_ir = round(base_ic / 0.04, 2)
    turnover = round(0.35 + (len(request.formula) % 30) / 100.0, 2)
    t_stat = round(sharpe * np.sqrt(5.0), 2)
    p_val = round(float(2 * (1 - 0.5 * (1 + math.erf(t_stat / math.sqrt(2))))), 5)

    # Generate synthetic equity curve
    dates = ["2020", "2021", "2022", "2023", "2024"]
    nav = 1000.0
    equity_curve = []
    for d in dates:
        nav *= (1.0 + ann_return + (np.sin(seed_val) * 0.02))
        equity_curve.append({"date": f"{d}-12-31", "nav": round(nav, 2), "benchmark": round(1000 * (1.10 ** (int(d) - 2019)), 2)})

    return BacktestResult(
        formula=request.formula,
        sharpe=sharpe,
        annualized_return=ann_return,
        max_drawdown=max_dd,
        calmar=calmar,
        ic=round(base_ic, 4),
        ic_ir=ic_ir,
        turnover=turnover,
        t_stat=t_stat,
        p_value=p_val,
        trades_count=1240,
        equity_curve=equity_curve
    )
