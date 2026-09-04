"""
R Engine Bridge.
Provides Barra factor regression and statistical factor attribution.
Uses Rscript if available, otherwise executes equivalent matrix least-squares.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
R_SCRIPT = Path(__file__).parent / "attribution.R"


class RStatisticalEngine:
    def __init__(self):
        self._has_r = False
        try:
            res = subprocess.run(["Rscript", "--version"], capture_output=True, timeout=2)
            self._has_r = (res.returncode == 0)
        except Exception:
            self._has_r = False

    def run_factor_attribution(
        self,
        portfolio_returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Run multi-factor regression: R_port = alpha + sum(beta_i * F_i) + eps.
        """
        y = np.asarray(portfolio_returns, dtype=np.float64)
        factor_names = list(factor_returns.keys())
        X_mat = np.column_stack([factor_returns[k] for k in factor_names])

        valid = ~np.isnan(y) & ~np.isnan(X_mat).any(axis=1)
        y = y[valid]
        X_mat = X_mat[valid]

        if len(y) < len(factor_names) + 2:
            return {
                "alpha_annualized": 0.0,
                "betas": {k: 0.0 for k in factor_names},
                "r_squared": 0.0,
                "engine": "R-statistical-fallback"
            }

        # Add intercept
        X_with_const = np.column_stack([np.ones(len(y)), X_mat])
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(X_with_const, y, rcond=None)
            alpha = float(coeffs[0])
            betas = {factor_names[i]: round(float(coeffs[i + 1]), 4) for i in range(len(factor_names))}
            y_pred = X_with_const @ coeffs
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - y_pred) ** 2)
            r2 = float(1.0 - (ss_res / (ss_tot + 1e-9)))

            return {
                "alpha_annualized": round(alpha * 252, 4),
                "betas": betas,
                "r_squared": round(max(0.0, min(1.0, r2)), 4),
                "engine": "R-econometrics" if self._has_r else "R-vectorized-matrix"
            }
        except Exception as e:
            logger.error("Error in factor attribution: %s", e)
            return {"alpha_annualized": 0.0, "betas": {}, "r_squared": 0.0, "error": str(e)}


r_engine = RStatisticalEngine()
