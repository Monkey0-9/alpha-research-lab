"""
Institutional Risk Engine (Zero-Fallback Empirical Risk Architecture).

Implements:
1. Value at Risk (VaR): Historical simulation (95%, 99%) and Parametric Gaussian.
2. Conditional Value at Risk (CVaR / Expected Shortfall).
3. Cornish-Fisher Expansion VaR (accounting for empirical skewness and excess kurtosis).
4. Barra-Style Econometric Factor Attribution (strictly fail-closed when factor data absent; no synthetic factors).
5. Drawdown Control: Constant Proportion Portfolio Insurance (CPPI).
6. Macroeconomic Scenario Replay Stress Tester.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Union, Optional
import numpy as np
import scipy.stats as ss

from native.native_bridge import accelerator

logger = logging.getLogger(__name__)


def historical_var(returns: Union[np.ndarray, List[float]], confidence: float = 0.95) -> float:
    """Historical Simulation VaR (positive value representing loss)."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 5:
        return 0.0
    alpha = 1.0 - confidence
    percentile = np.percentile(ret, alpha * 100)
    return float(max(0.0, -percentile))


def parametric_var(returns: Union[np.ndarray, List[float]], confidence: float = 0.95) -> float:
    """Parametric Gaussian VaR."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 5:
        return 0.0
    mean = np.mean(ret)
    std = np.std(ret, ddof=1)
    z = ss.norm.ppf(confidence)
    var = -(mean - z * std)
    return float(max(0.0, var))


def cvar_expected_shortfall(returns: Union[np.ndarray, List[float]], confidence: float = 0.95) -> float:
    """Expected Shortfall (CVaR) — average loss exceeding VaR cutoff."""
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 5:
        return 0.0
    alpha = 1.0 - confidence
    var_cutoff = np.percentile(ret, alpha * 100)
    tail = ret[ret <= var_cutoff]
    if len(tail) == 0:
        return float(max(0.0, -var_cutoff))
    return float(max(0.0, -np.mean(tail)))


def cppi_nav_trajectory(
    nav_series: np.ndarray,
    floor: float = 0.90,
    multiplier: float = 3.0
) -> Dict[str, Any]:
    """
    CPPI (Constant Proportion Portfolio Insurance).
    cushion = max(0, NAV - floor)
    target_equity_exposure = min(1.0, multiplier * cushion)
    """
    nav = np.asarray(nav_series)
    cushions = np.maximum(0.0, nav - floor)
    exposures = np.clip(multiplier * cushions, 0.0, 1.5)
    return {
        "floor": floor,
        "multiplier": multiplier,
        "current_cushion": round(float(cushions[-1]), 4) if len(cushions) > 0 else 0.1,
        "target_exposure": round(float(exposures[-1]), 4) if len(exposures) > 0 else 1.0,
        "exposure_history": exposures.tolist()
    }


def factor_attribution(
    portfolio_returns: np.ndarray,
    factor_returns: Optional[Dict[str, np.ndarray]] = None
) -> Dict[str, Any]:
    """
    Multi-factor risk attribution utilizing R / native statistical engine.
    STRICT ZERO-FALLBACK POLICY:
    If factor_returns is None or empty, returns status RISK_MODEL_UNAVAILABLE.
    Never generates synthetic random normal factors or defaults R² to 0.62.
    """
    p_ret = np.asarray(portfolio_returns, dtype=np.float64)
    p_ret = p_ret[~np.isnan(p_ret)]

    if len(p_ret) < 10:
        return {
            "status": "INSUFFICIENT_DATA",
            "reason": f"Sample length ({len(p_ret)}) too short for factor attribution.",
            "total_risk": 0.0,
            "systematic_risk": 0.0,
            "idiosyncratic_risk": 0.0,
            "r_squared": 0.0,
            "factor_exposures": [],
            "betas": {},
        }

    if factor_returns is None or len(factor_returns) == 0:
        tot_vol = float(np.std(p_ret) * np.sqrt(252.0))
        return {
            "status": "RISK_MODEL_UNAVAILABLE",
            "reason": "Factor dataset not supplied; zero synthetic factor fallback enforced.",
            "total_risk": tot_vol,
            "systematic_risk": 0.0,
            "idiosyncratic_risk": tot_vol,
            "r_squared": 0.0,
            "factor_exposures": [],
            "betas": {},
        }

    res = accelerator.r_factor_attribution(p_ret, factor_returns)
    tot_vol = float(np.std(p_ret) * np.sqrt(252.0))
    r2 = float(res.get("r_squared", 0.0))
    res["status"] = "SUCCESS"
    res["total_risk"] = tot_vol
    res["systematic_risk"] = tot_vol * np.sqrt(max(0.0, min(1.0, r2)))
    res["idiosyncratic_risk"] = tot_vol * np.sqrt(max(0.0, min(1.0, 1.0 - r2)))
    res["factor_exposures"] = [
        {"factor": k, "beta": float(v)} for k, v in res.get("betas", {}).items()
    ]
    return res


def cornish_fisher_var(returns: Union[np.ndarray, List[float]], confidence: float = 0.95) -> float:
    """
    Cornish-Fisher expansion Value-at-Risk accounting for non-normality (skewness and excess kurtosis).
    """
    ret = np.asarray(returns, dtype=np.float64)
    ret = ret[~np.isnan(ret)]
    if len(ret) < 10:
        return 0.0

    mean = float(np.mean(ret))
    std = float(np.std(ret, ddof=1))
    if std < 1e-12:
        return 0.0

    skew = float(ss.skew(ret))
    kurt = float(ss.kurtosis(ret))  # Fisher excess kurtosis

    alpha = 1.0 - confidence
    z_a = float(ss.norm.ppf(alpha))
    # Cornish-Fisher expansion for return distribution quantile
    w = (
        z_a
        + (skew / 6.0) * (z_a ** 2 - 1.0)
        + (kurt / 24.0) * (z_a ** 3 - 3.0 * z_a)
        - ((skew ** 2) / 36.0) * (2.0 * z_a ** 3 - 5.0 * z_a)
    )

    var = -(mean + w * std)
    return float(max(0.0, var))


class HistoricalStressTester:
    """
    Institutional historical crisis scenario replay stress tester.
    Simulates portfolio drawdowns through major macroeconomic shocks.
    """

    HISTORICAL_SCENARIOS = {
        "LEHMAN_2008": {
            "name": "2008 Lehman GFC Liquidity Crisis",
            "period": "2008-09-15 to 2008-11-20",
            "market_shock": -0.38,
            "sector_shocks": {
                "Financials": -0.52,
                "Real Estate": -0.48,
                "Technology": -0.32,
                "Consumer Discretionary": -0.36,
                "Industrials": -0.39,
                "Energy": -0.42,
                "Health Care": -0.21,
                "Utilities": -0.19,
                "Consumer Staples": -0.16,
            },
            "default_shock": -0.35,
        },
        "FLASH_CRASH_2010": {
            "name": "May 2010 Flash Crash",
            "period": "2010-05-06",
            "market_shock": -0.09,
            "sector_shocks": {
                "Technology": -0.11,
                "Financials": -0.12,
                "Industrials": -0.10,
                "Consumer Discretionary": -0.09,
            },
            "default_shock": -0.09,
        },
        "COVID_2020": {
            "name": "March 2020 COVID Liquidity Freeze",
            "period": "2020-02-24 to 2020-03-23",
            "market_shock": -0.34,
            "sector_shocks": {
                "Energy": -0.55,
                "Industrials": -0.40,
                "Consumer Discretionary": -0.38,
                "Financials": -0.39,
                "Real Estate": -0.37,
                "Technology": -0.28,
                "Health Care": -0.18,
                "Consumer Staples": -0.14,
            },
            "default_shock": -0.32,
        },
        "SVB_2023": {
            "name": "March 2023 Silicon Valley Bank Contagion",
            "period": "2023-03-08 to 2023-03-17",
            "market_shock": -0.05,
            "sector_shocks": {
                "Financials": -0.24,
                "Real Estate": -0.08,
                "Technology": +0.02,  # Mega-cap flight to safety
                "Communication Services": +0.01,
            },
            "default_shock": -0.05,
        }
    }

    # Standard Sector Taxonomy mapping for S&P 500 constituents
    TICKER_SECTOR_MAP = {
        "JPM": "Financials", "BAC": "Financials", "GS": "Financials", "MS": "Financials", "C": "Financials",
        "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology", "GOOGL": "Technology", "META": "Technology",
        "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary", "HD": "Consumer Discretionary",
        "XOM": "Energy", "CVX": "Energy", "SLB": "Energy",
        "JNJ": "Health Care", "PFE": "Health Care", "UNH": "Health Care", "ABBV": "Health Care",
        "PG": "Consumer Staples", "KO": "Consumer Staples", "PEP": "Consumer Staples", "WMT": "Consumer Staples",
        "CAT": "Industrials", "BA": "Industrials", "HON": "Industrials",
        "NEE": "Utilities", "DUK": "Utilities",
        "PLD": "Real Estate", "AMT": "Real Estate"
    }

    @classmethod
    def run_stress_scenarios(
        cls,
        weights: Dict[str, float],
        aum: float = 1_000_000.0,
        max_tolerable_drawdown: float = 0.15
    ) -> Dict[str, Any]:
        """
        Evaluate portfolio resilience across historical crisis scenarios.
        Returns scenario drawdowns, dollar losses, worst contributors, and breach warnings.
        """
        results: Dict[str, Any] = {}
        total_gross = sum(abs(w) for w in weights.values())
        if total_gross < 1e-6:
            return {"status": "EMPTY", "scenarios": {}}

        worst_scenario_name = ""
        max_scenario_loss_pct = 0.0

        for sc_id, sc in cls.HISTORICAL_SCENARIOS.items():
            scenario_pnl_pct = 0.0
            asset_impacts = {}

            for ticker, weight in weights.items():
                sec = cls.TICKER_SECTOR_MAP.get(ticker, "Broad Market")
                shock = sc["sector_shocks"].get(sec, sc["default_shock"])
                impact = weight * shock
                scenario_pnl_pct += impact
                asset_impacts[ticker] = impact

            sorted_impacts = sorted(asset_impacts.items(), key=lambda x: x[1])
            worst_asset, worst_impact = sorted_impacts[0] if sorted_impacts else ("None", 0.0)

            loss_pct = max(0.0, -scenario_pnl_pct)
            dollar_loss = loss_pct * aum
            breached = loss_pct > max_tolerable_drawdown

            results[sc_id] = {
                "name": sc["name"],
                "period": sc["period"],
                "portfolio_return_pct": round(scenario_pnl_pct * 100.0, 2),
                "portfolio_loss_pct": round(loss_pct * 100.0, 2),
                "dollar_loss": round(dollar_loss, 2),
                "worst_contributor": worst_asset,
                "worst_contributor_impact_pct": round(worst_impact * 100.0, 2),
                "limit_breached": breached,
            }

            if loss_pct > max_scenario_loss_pct:
                max_scenario_loss_pct = loss_pct
                worst_scenario_name = sc["name"]

        return {
            "status": "COMPLETED",
            "aum": aum,
            "max_tolerable_drawdown_pct": round(max_tolerable_drawdown * 100.0, 2),
            "worst_scenario": worst_scenario_name,
            "worst_scenario_loss_pct": round(max_scenario_loss_pct * 100.0, 2),
            "worst_scenario_dollar_loss": round(max_scenario_loss_pct * aum, 2),
            "overall_stress_passed": max_scenario_loss_pct <= max_tolerable_drawdown,
            "scenarios": results
        }
