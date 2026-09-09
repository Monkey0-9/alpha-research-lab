"""
Institutional Governance Policy & Hurdle Thresholds.
Defines non-negotiable mathematical hurdles required to clear quality gate stages.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InstitutionalHurdlePolicy:
    """Institutional quantitative hurdles."""
    # Data & Temporal
    min_history_days: int = 252
    max_missing_pct: float = 0.01
    require_pit_clean: bool = True

    # Out-of-Sample Performance
    min_oos_sharpe: float = 1.50
    min_ic: float = 0.05
    min_icir: float = 0.70
    max_drawdown_limit: float = 0.15

    # Statistical Governance
    min_dsr_confidence: float = 0.95        # Deflated Sharpe Ratio >= 95%
    max_pbo_probability: float = 0.20       # Probability of Backtest Overfitting <= 20%
    max_fdr_qvalue: float = 0.05            # Benjamini-Hochberg FDR <= 5%
    max_spa_pvalue: float = 0.05            # Hansen Superior Predictive Ability p <= 0.05

    # Execution & Microstructure
    max_turnover_annual: float = 0.40
    min_capacity_usd_millions: float = 50.0
    max_slippage_bps: float = 25.0

    # Risk & Portfolio
    max_factor_exposure_zscore: float = 0.30
    max_pairwise_alpha_corr: float = 0.40
    min_decay_half_life_days: float = 5.0

    # Cryptographic & Verification
    require_exact_reproduction: bool = True
    require_zero_lookahead_falsification: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_history_days": self.min_history_days,
            "max_missing_pct": self.max_missing_pct,
            "require_pit_clean": self.require_pit_clean,
            "min_oos_sharpe": self.min_oos_sharpe,
            "min_ic": self.min_ic,
            "min_icir": self.min_icir,
            "max_drawdown_limit": self.max_drawdown_limit,
            "min_dsr_confidence": self.min_dsr_confidence,
            "max_pbo_probability": self.max_pbo_probability,
            "max_fdr_qvalue": self.max_fdr_qvalue,
            "max_spa_pvalue": self.max_spa_pvalue,
            "max_turnover_annual": self.max_turnover_annual,
            "min_capacity_usd_millions": self.min_capacity_usd_millions,
            "max_slippage_bps": self.max_slippage_bps,
            "max_factor_exposure_zscore": self.max_factor_exposure_zscore,
            "max_pairwise_alpha_corr": self.max_pairwise_alpha_corr,
            "min_decay_half_life_days": self.min_decay_half_life_days,
            "require_exact_reproduction": self.require_exact_reproduction,
            "require_zero_lookahead_falsification": self.require_zero_lookahead_falsification,
        }
