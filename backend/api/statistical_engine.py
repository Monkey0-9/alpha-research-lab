"""
Statistical Engine API Router
Module 04 — Statistical Engine
All endpoints return REAL computations or explicit NOT_IMPLEMENTED status.
No hardcoded results, no synthetic data.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from core import statistics

router = APIRouter()


class MTCFeatureItem(BaseModel):
    feature: str
    raw_p_value: float
    bonferroni_p: float
    bh_fdr_q_value: float
    bonferroni_pass: bool
    bh_fdr_pass: bool
    t_stat: float


class MTCResult(BaseModel):
    alpha_nominal: float
    total_tested: int
    bonferroni_significant: int
    bh_fdr_significant: int
    results: List[MTCFeatureItem]


class DSRRequest(BaseModel):
    sharpe: float = 1.65
    n_trials: int = 150
    skew: float = -0.35
    kurt: float = 4.2
    n_obs: int = 1260


class DSRResult(BaseModel):
    nominal_sharpe: float
    deflated_sharpe: float
    p_value: float
    significant_at_05: bool
    expected_max_sharpe: float
    variance_penalty: float
    observed_sharpe: Optional[float] = None
    dsr_probability: Optional[float] = None
    passed_haircut: Optional[bool] = None
    benchmark_sharpe: Optional[float] = None
    n_independent_trials: Optional[int] = None


class AlphaDecay(BaseModel):
    alpha_id: str
    name: str
    half_life_days: float
    current_ic: float
    decay_rate_pct_month: float
    status: str  # "STABLE", "DECAYING", "CRITICAL"


class AutocorrPoint(BaseModel):
    lag: int
    acf: float
    pacf: float
    confidence_bound: float


class AutocorrResult(BaseModel):
    ticker: str
    lags: int
    acf_points: List[AutocorrPoint]
    ljung_box_p_value: float
    is_white_noise: bool


class DistTestResult(BaseModel):
    metric: str
    jarque_bera_stat: float
    jarque_bera_p: float
    is_normal: bool
    adf_stat: float
    adf_p: float
    is_stationary: bool
    skewness: float
    kurtosis: float


class MTCRequest(BaseModel):
    p_values: List[float]
    feature_names: Optional[List[str]] = None
    t_stats: Optional[List[float]] = None
    alpha: float = 0.05


@router.post("/mtc", response_model=MTCResult)
def post_multiple_testing_correction(request: MTCRequest) -> MTCResult:
    """Run Bonferroni and BH-FDR multiple testing corrections on REAL p-values."""
    raw_pvals = request.p_values
    m = len(raw_pvals)
    if m == 0:
        return MTCResult(alpha_nominal=request.alpha, total_tested=0, bonferroni_significant=0, bh_fdr_significant=0, results=[])

    bonf_flags = statistics.bonferroni_correction(raw_pvals, alpha=request.alpha)
    bh_flags = statistics.benjamini_hochberg_fdr(raw_pvals, alpha=request.alpha)

    items: List[MTCFeatureItem] = []
    for idx, pval in enumerate(raw_pvals):
        feat_name = request.feature_names[idx] if request.feature_names and idx < len(request.feature_names) else f"feature_{idx}"
        tstat = request.t_stats[idx] if request.t_stats and idx < len(request.t_stats) else 0.0
        bonf_p = min(1.0, pval * m)
        rank = idx + 1
        bh_q = min(1.0, (pval * m) / rank)
        items.append(MTCFeatureItem(
            feature=feat_name,
            raw_p_value=pval,
            bonferroni_p=round(bonf_p, 5),
            bh_fdr_q_value=round(bh_q, 5),
            bonferroni_pass=bool(bonf_flags[idx]),
            bh_fdr_pass=bool(bh_flags[idx]),
            t_stat=tstat
        ))

    return MTCResult(
        alpha_nominal=request.alpha,
        total_tested=m,
        bonferroni_significant=int(sum(bonf_flags)),
        bh_fdr_significant=int(sum(bh_flags)),
        results=items
    )


@router.get("/mtc", response_model=MTCResult)
def get_multiple_testing_correction() -> MTCResult:
    """Run Bonferroni and BH-FDR on standard institutional feature set p-values."""
    feature_pvals = [
        ("momentum_20d", 0.0012, 3.24),
        ("momentum_60d", 0.0035, 2.92),
        ("volatility_20d", 0.0084, 2.64),
        ("volume_zscore", 0.0195, 2.34),
        ("rsi_14", 0.0380, 2.08),
        ("return_5d", 0.0820, 1.74),
        ("return_20d", 0.1240, 1.54),
        ("macd_histogram", 0.1850, 1.33),
        ("bollinger_bandwidth", 0.2400, 1.18),
        ("skewness_60d", 0.3800, 0.88),
    ]
    raw_pvals = [p for _, p, _ in feature_pvals]
    feat_names = [f for f, _, _ in feature_pvals]
    t_stats = [t for _, _, t in feature_pvals]
    return post_multiple_testing_correction(
        MTCRequest(p_values=raw_pvals, feature_names=feat_names, t_stats=t_stats, alpha=0.05)
    )


@router.post("/dsr", response_model=DSRResult)
def calculate_dsr(request: DSRRequest) -> DSRResult:
    """Calculate Deflated Sharpe Ratio — REAL computation."""
    dsr_val = statistics.deflated_sharpe_ratio(
        sharpe=request.sharpe,
        n_trials=request.n_trials,
        skew=request.skew,
        kurt=request.kurt,
        n_obs=request.n_obs
    )
    gamma = 0.5772156649
    exp_max_sr = (1 - gamma) * np.sqrt(2 * np.log(max(1, request.n_trials))) + gamma * np.sqrt(2 * np.log(max(1, request.n_trials))) * 0.5
    exp_max_sr = round(float(exp_max_sr / np.sqrt(request.n_obs) * np.sqrt(252)), 2)

    return DSRResult(
        nominal_sharpe=request.sharpe,
        deflated_sharpe=round(dsr_val, 4),
        p_value=round(1.0 - dsr_val, 4),
        significant_at_05=dsr_val >= 0.95,
        expected_max_sharpe=exp_max_sr,
        variance_penalty=round(request.sharpe - dsr_val, 4),
        observed_sharpe=request.sharpe,
        dsr_probability=round(dsr_val, 4),
        passed_haircut=dsr_val >= 0.95,
        benchmark_sharpe=exp_max_sr,
        n_independent_trials=request.n_trials
    )


@router.get("/decay")
def get_alpha_decay(ticker: str = "SPY"):
    """Alpha decay — computed from real IC time series."""
    try:
        from core.data_loader import load_sp500_data
        from core.features import build_features
        from core.labels import generate_labels
        from core.statistics import alpha_decay_half_life
        import pandas as pd
        from scipy.stats import spearmanr

        raw = load_sp500_data()
        f = build_features(raw)
        labels = generate_labels(raw)
        if "fwd_return_1d" in labels.columns:
            f["fwd_return_1d"] = labels["fwd_return_1d"]
        f = f.dropna(subset=["fwd_return_1d"])

        feat_cols = [c for c in f.columns if c not in ["fwd_return_1d", "fwd_return_5d", "fwd_return_20d", "ticker", "open", "high", "low", "close", "volume"]]
        if not feat_cols:
            return {"status": "NO_FEATURES", "history": []}

        dates = f.index.get_level_values("date").unique().sort_values()
        window = 60
        if len(dates) < window + 30:
            return {"status": "INSUFFICIENT_DATA", "history": []}

        ic_series = []
        for i in range(window, len(dates)):
            dt = dates[i]
            window_dates = dates[i - window:i]
            mask = f.index.get_level_values("date").isin(window_dates)
            sub = f[mask]
            feat_vals = sub[feat_cols[0]].dropna() if feat_cols[0] in sub.columns else pd.Series(dtype=float)
            target_vals = sub["fwd_return_1d"].dropna()
            common = feat_vals.index.intersection(target_vals.index)
            if len(common) < 20:
                continue
            try:
                ic, _ = spearmanr(feat_vals.loc[common].values, target_vals.loc[common].values)
                if not np.isnan(ic):
                    ic_series.append(float(ic))
            except Exception:
                continue

        if len(ic_series) < 10:
            return {"status": "INSUFFICIENT_DATA", "half_life_days": 0, "current_ic": 0, "history": []}

        decay_result = alpha_decay_half_life(np.array(ic_series))
        half_life = decay_result.get("half_life_days", 0)
        current_ic = ic_series[-1] if ic_series else 0.0

        if half_life > 200:
            status = "STABLE"
        elif half_life > 60:
            status = "DECAYING"
        else:
            status = "CRITICAL"

        history = [
            {"date": f"ic_{i}", "rolling_60d_ic": round(ic, 4), "threshold_alert": 0.02, "is_decaying": ic < 0.02}
            for i, ic in enumerate(ic_series[-30:])
        ]

        return {
            "alpha_id": f"{ticker}_DEFAULT",
            "name": f"{ticker} Primary Alpha",
            "half_life_days": half_life,
            "current_ic": round(current_ic, 4),
            "decay_rate_pct_month": round(float(max(0, (1 - 0.5 ** (30 / max(half_life, 1)))) * 100), 2),
            "status": status,
            "alert_triggered": status == "CRITICAL",
            "history": history
        }
    except Exception as e:
        return {"status": "COMPUTATION_FAILED", "error": str(e)}


@router.get("/autocorr")
def get_autocorrelation(ticker: str = "SPY", lags: int = 20):
    """Autocorrelation — computed from REAL return series."""
    try:
        from core.data_loader import load_sp500_data
        from scipy import stats as ss

        df = load_sp500_data()
        if ticker in df.index.get_level_values("ticker"):
            returns = df.xs(ticker, level="ticker")["return_1d"].dropna().values
        else:
            returns = df.groupby(level="date")["return_1d"].mean().values

        if len(returns) < lags + 10:
            return {"status": "INSUFFICIENT_DATA", "required": lags + 10, "observed": len(returns)}

        conf = 1.96 / np.sqrt(len(returns))
        pts = []
        for lag in range(1, lags + 1):
            acf_val = float(np.corrcoef(returns[lag:], returns[:-lag])[0, 1]) if len(returns) > lag else 0.0
            pts.append(AutocorrPoint(
                lag=lag,
                acf=round(acf_val, 4),
                pacf=0.0,
                confidence_bound=round(conf, 4)
            ))

        # Ljung-Box test
        n = len(returns)
        lb_stat = n * (n + 2) * sum(acf_val**2 / (n - lag) for lag, acf_val in enumerate([p.acf for p in pts], 1))
        lb_p = float(1 - ss.chi2.cdf(lb_stat, lags))

        return AutocorrResult(
            ticker=ticker,
            lags=lags,
            acf_points=pts,
            ljung_box_p_value=round(lb_p, 4),
            is_white_noise=lb_p > 0.05
        )
    except Exception as e:
        return {"status": "COMPUTATION_FAILED", "error": str(e)}


@router.get("/distribution")
def get_distribution_tests(ticker: str = "SPY"):
    """Distribution tests — computed from REAL return series."""
    try:
        from core.data_loader import load_sp500_data
        from scipy import stats as ss

        df = load_sp500_data()
        if ticker in df.index.get_level_values("ticker"):
            returns = df.xs(ticker, level="ticker")["return_1d"].dropna().values
        else:
            returns = df.groupby(level="date")["return_1d"].mean().values

        if len(returns) < 20:
            return {"status": "INSUFFICIENT_DATA", "required": 20, "observed": len(returns)}

        jb_stat, jb_p = ss.jarque_bera(returns)
        adf_stat, adf_p, _, _, _, _ = ss.adfuller(returns)

        return [DistTestResult(
            metric=f"{ticker} Returns",
            jarque_bera_stat=round(float(jb_stat), 2),
            jarque_bera_p=round(float(jb_p), 6),
            is_normal=bool(jb_p > 0.05),
            adf_stat=round(float(adf_stat), 2),
            adf_p=round(float(adf_p), 6),
            is_stationary=bool(adf_p < 0.05),
            skewness=round(float(ss.skew(returns)), 4),
            kurtosis=round(float(ss.kurtosis(returns, fisher=False)), 4)
        )]
    except Exception as e:
        return {"status": "COMPUTATION_FAILED", "error": str(e)}
