"""
Search Budget Accounting Subsystem.
Tracks trial budgets and selection bias penalties (Bailey & Lopez de Prado 2014).
"""
from __future__ import annotations

import math
from typing import Optional
from .registry import TrialRegistry


class BudgetExhaustedException(Exception):
    """Raised when research trial count exceeds maximum approved exploratory search budget."""


class SearchBudgetTracker:
    """
    Manages empirical search budgets and calculates the expected maximum Sharpe under null hypothesis of no skill:
    E[max_N] ≈ (1 - gamma)*Z^{-1}(1 - 1/N) + gamma*Z^{-1}(1 - 1/(N*e))
    """

    def __init__(self, experiment_id: str, max_allocated_trials: int = 1000):
        self.experiment_id = experiment_id
        self.max_allocated_trials = max_allocated_trials
        self.registry = TrialRegistry(experiment_id)

    @property
    def trials_used(self) -> int:
        return self.registry.total_trials_count

    @property
    def budget_remaining(self) -> int:
        return max(0, self.max_allocated_trials - self.trials_used)

    def check_budget_available(self) -> bool:
        if self.trials_used >= self.max_allocated_trials:
            raise BudgetExhaustedException(
                f"Search budget exhausted for experiment {self.experiment_id}: "
                f"used {self.trials_used} / {self.max_allocated_trials} trials."
            )
        return True

    def expected_maximum_sr(self, n_trials: Optional[int] = None) -> float:
        """
        Approximate analytical expectation of the maximum Sharpe ratio from N independent null trials.
        Euler-Mascheroni constant gamma ≈ 0.5772156649
        """
        n = n_trials if n_trials is not None else max(self.trials_used, 1)
        if n <= 1:
            return 0.0

        # Approximation using extreme value theory for standard normal
        # E[max_N] ≈ sqrt(2 * ln(N)) + gamma / sqrt(2 * ln(N))
        gamma = 0.5772156649
        term = 2.0 * math.log(n)
        if term <= 0:
            return 0.0
        sqrt_term = math.sqrt(term)
        return float(sqrt_term + (gamma / sqrt_term))
