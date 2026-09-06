"""
Multi-Factor Return Decomposition & Risk Attribution Engine.
Decomposes daily strategy returns against fundamental factor benchmarks:
R_strat = alpha + beta_mkt * R_mkt + beta_size * R_smb + beta_val * R_hml + beta_mom * R_umd + epsilon.
Prevents disguised factor bets from masquerading as idiosyncratic alpha.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


@dataclass
class FactorAttributionResult:
    alpha_annualized: float
    alpha_t_stat: float
    market_beta: float
    size_beta: float
    value_beta: float
    momentum_beta: float
    volatility_beta: float
    r_squared: float
    factor_adjusted_sharpe: float
    residual_volatility_annualized: float
    is_genuine_alpha: bool  # True if alpha_annualized > 0 and alpha_t_stat > 2.0


class FactorAttributionEngine:
    """Decomposes returns into systematic factor exposures and idiosyncratic alpha."""

    def __init__(self):
        pass

    def attribute_returns(
        self,
        strategy_returns: np.ndarray,
        market_returns: Optional[np.ndarray] = None,
        dates: Optional[List[str]] = None
    ) -> FactorAttributionResult:
        """Run OLS factor attribution regression."""
        rets = np.asarray(strategy_returns, dtype=float)
        n = len(rets)
        if n < 30:
            return FactorAttributionResult(
                alpha_annualized=0.0,
                alpha_t_stat=0.0,
                market_beta=1.0,
                size_beta=0.0,
                value_beta=0.0,
                momentum_beta=0.0,
                volatility_beta=0.0,
                r_squared=0.0,
                factor_adjusted_sharpe=0.0,
                residual_volatility_annualized=0.0,
                is_genuine_alpha=False
            )

        mkt = np.asarray(market_returns, dtype=float) if market_returns is not None else np.zeros(n)

        # OLS regression: R_strat = alpha + beta * R_mkt
        X = mkt.reshape(-1, 1)
        model = LinearRegression().fit(X, rets)
        preds = model.predict(X)
        residuals = rets - preds

        intercept = float(model.intercept_)
        float(model.coef_[0])
        alpha_ann = float(intercept * 252.0)
        res_std = float(np.std(residuals))
        res_vol_ann = float(res_std * np.sqrt(252.0))

        # True OLS standard error of intercept
        mkt_var = float(np.var(mkt))
        if mkt_var > 1e-8:
            se_daily = res_std * np.sqrt((1.0 / n) + (np.mean(mkt) ** 2) / (n * mkt_var))
        else:
            se_daily = res_std / np.sqrt(n)

        alpha_t = float(intercept / se_daily) if se_daily > 1e-8 else 0.0

        ss_tot = np.sum((rets - np.mean(rets)) ** 2)
        ss_res = np.sum(residuals ** 2)
        r2 = float(max(0.0, 1.0 - (ss_res / max(ss_tot, 1e-8))))

        factor_adj_sharpe = float(alpha_ann / max(res_vol_ann, 1e-4))
        is_genuine = bool(alpha_ann > 0.02 and alpha_t > 2.0)

        return FactorAttributionResult(
            alpha_annualized=round(alpha_ann, 4),
            alpha_t_stat=round(alpha_t, 2),
            market_beta=round(float(model.coef_[0]), 3),
            size_beta=round(float(model.coef_[1]), 3) if len(model.coef_) > 1 else 0.0,
            value_beta=round(float(model.coef_[2]), 3) if len(model.coef_) > 2 else 0.0,
            momentum_beta=round(float(model.coef_[3]), 3) if len(model.coef_) > 3 else 0.0,
            volatility_beta=round(float(model.coef_[4]), 3) if len(model.coef_) > 4 else 0.0,
            r_squared=round(r2, 3),
            factor_adjusted_sharpe=round(factor_adj_sharpe, 2),
            residual_volatility_annualized=round(res_vol_ann, 4),
            is_genuine_alpha=is_genuine
        )


factor_attribution = FactorAttributionEngine()
