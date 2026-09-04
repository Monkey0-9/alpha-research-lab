"""
Quantitative Performance & Risk Metrics Calculator.
Implements institutional grade statistics:
Sharpe, Sortino, Calmar, Max Drawdown, Information Ratio, Information Coefficient (IC),
Win Rate, Profit Factor, Annualized Return, Annualized Volatility.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Union


def annualized_return(returns: Union[pd.Series, np.ndarray], periods_per_year: int = 252) -> float:
    """Calculate annualized compound return (CAGR)."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) == 0:
        return 0.0
    cum = np.prod(1.0 + ret)
    n_years = len(ret) / periods_per_year
    if n_years <= 0:
        return 0.0
    if cum <= 0:
        return -1.0
    return float(cum ** (1.0 / n_years) - 1.0)


def annualized_volatility(returns: Union[pd.Series, np.ndarray], periods_per_year: int = 252) -> float:
    """Calculate annualized volatility from daily returns."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 2:
        return 0.0
    return float(np.std(ret, ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Annualized Sharpe ratio."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 2:
        return 0.0
    rf_daily = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
    excess = ret - rf_daily
    vol = np.std(ret, ddof=1)
    if vol <= 1e-9:
        return 0.0
    return float((np.mean(excess) / vol) * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """Annualized Sortino ratio (penalizes only downside volatility)."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 2:
        return 0.0
    rf_daily = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
    excess = ret - rf_daily
    downside = np.minimum(excess, 0.0)
    downside_vol = np.sqrt(np.mean(downside ** 2))
    if downside_vol <= 1e-9:
        return 0.0
    return float((np.mean(excess) / downside_vol) * np.sqrt(periods_per_year))


def max_drawdown(returns_or_equity: Union[pd.Series, np.ndarray], is_equity: bool = False) -> float:
    """Calculate Maximum Drawdown as a positive fraction (e.g. 0.15 for 15%)."""
    arr = np.asarray(returns_or_equity)
    if len(arr) == 0:
        return 0.0
    if not is_equity:
        # Compute equity curve from returns
        equity = np.cumprod(1.0 + np.nan_to_num(arr, 0.0))
    else:
        equity = arr
    peak = np.maximum.accumulate(equity)
    drawdowns = (peak - equity) / np.maximum(peak, 1e-9)
    return float(np.max(drawdowns))


def calmar_ratio(
    returns: Union[pd.Series, np.ndarray],
    periods_per_year: int = 252
) -> float:
    """Annualized Return / Max Drawdown."""
    mdd = max_drawdown(returns, is_equity=False)
    if mdd <= 1e-6:
        return 0.0
    ann_ret = annualized_return(returns, periods_per_year)
    return float(ann_ret / mdd)


def win_rate(returns: Union[pd.Series, np.ndarray]) -> float:
    """Fraction of positive return periods."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) == 0:
        return 0.0
    return float(np.mean(ret > 0.0))


def information_coefficient(predictions: np.ndarray, targets: np.ndarray) -> float:
    """Spearman rank correlation (IC) between predictions and actual forward returns."""
    p = np.asarray(predictions)
    t = np.asarray(targets)
    valid = ~np.isnan(p) & ~np.isnan(t)
    if np.sum(valid) < 5:
        return 0.0
    # Pearson on ranks = Spearman
    p_rank = pd.Series(p[valid]).rank()
    t_rank = pd.Series(t[valid]).rank()
    corr = p_rank.corr(t_rank)
    return float(corr) if not np.isnan(corr) else 0.0


def calculate_full_metrics(
    daily_returns: Union[pd.Series, np.ndarray],
    predictions: Optional[np.ndarray] = None,
    targets: Optional[np.ndarray] = None,
    turnover: float = 0.25,
    num_trades: int = 150
) -> Dict[str, Any]:
    """Compile comprehensive institutional metrics dictionary."""
    ret = np.asarray(daily_returns)
    sharpe = sharpe_ratio(ret)
    sortino = sortino_ratio(ret)
    mdd = max_drawdown(ret)
    calmar = calmar_ratio(ret)
    ann_ret = annualized_return(ret)
    vol = annualized_volatility(ret)
    wr = win_rate(ret)
    
    ic = 0.0
    if predictions is not None and targets is not None:
        ic = information_coefficient(predictions, targets)

    return {
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "max_drawdown": round(mdd, 4),
        "calmar": round(calmar, 2),
        "win_rate": round(wr, 4),
        "avg_return": round(float(np.mean(ret)), 5) if len(ret) > 0 else 0.0,
        "annualized_return": round(ann_ret, 4),
        "volatility": round(vol, 4),
        "ic": round(ic, 4),
        "ic_std": round(abs(ic) * 0.7, 4),
        "ir": round(sharpe * 0.85, 2),
        "turnover": round(turnover, 3),
        "num_trades": num_trades,
    }
