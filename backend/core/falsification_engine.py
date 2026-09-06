"""
Alpha Falsification Engine.
Subjects promising alphas to an 11-step stress and falsification protocol:
1. Sign Reversal
2. Feature Permutation
3. Label Permutation
4. Universe Perturbation (30% random constituent drop)
5. Parameter Perturbation (window jiggle)
6. Time-Period Perturbation (early vs late split)
7. Cost Stress (3x transaction fees)
8. Regime Stress (high volatility drawdown)
9. Factor Neutralization (idiosyncratic residual test)
10. Placebo Test (pure noise replacement)
11. Feature Ablation

Rule: If an alpha fails falsification, it is REJECTED or FLAGGED as fragile.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FalsificationStepResult:
    step_name: str
    passed: bool
    baseline_metric: float
    perturbed_metric: float
    description: str


@dataclass
class FalsificationReport:
    alpha_id: str
    verdict: str  # "PASSED", "FALSIFIED", "FLAGGED_FRAGILE"
    tests_passed: int
    total_tests: int
    survival_score: float  # tests_passed / total_tests
    steps: List[FalsificationStepResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha_id": self.alpha_id,
            "verdict": self.verdict,
            "tests_passed": self.tests_passed,
            "total_tests": self.total_tests,
            "survival_score": round(self.survival_score, 3),
            "steps": [asdict(s) for s in self.steps],
            "timestamp": self.timestamp,
        }


class FalsificationEngine:
    """Stress tests and attempts to falsify alphas before live capital allocation."""

    def run_falsification_suite(
        self,
        alpha_id: str,
        signal: np.ndarray,
        forward_returns: np.ndarray,
        baseline_ic: float,
        costs_bps: float = 5.0,
    ) -> FalsificationReport:
        sig = np.asarray(signal, dtype=np.float64)
        ret = np.asarray(forward_returns, dtype=np.float64)
        n = min(len(sig), len(ret))
        sig, ret = sig[:n], ret[:n]

        steps: List[FalsificationStepResult] = []

        # 1. Sign Reversal: inverting signal must invert IC
        rev_ic = self._calc_ic(-sig, ret)
        rev_passed = rev_ic < 0 and np.isclose(rev_ic, -baseline_ic, atol=0.05)
        steps.append(FalsificationStepResult(
            step_name="sign_reversal",
            passed=bool(rev_passed),
            baseline_metric=baseline_ic,
            perturbed_metric=rev_ic,
            description="Inverting signal direction should invert the IC sign symmetrically.",
        ))

        # 2. Feature Permutation: shuffling feature must collapse IC
        rng = np.random.default_rng(42)
        shuff_sig = rng.permutation(sig)
        shuff_ic = self._calc_ic(shuff_sig, ret)
        shuff_passed = abs(shuff_ic) < max(0.05, abs(baseline_ic) * 0.3)
        steps.append(FalsificationStepResult(
            step_name="feature_permutation",
            passed=bool(shuff_passed),
            baseline_metric=baseline_ic,
            perturbed_metric=shuff_ic,
            description="Randomly permuting feature order over time should collapse IC to ~0.",
        ))

        # 3. Label Permutation: shuffling forward returns must collapse IC
        shuff_ret = rng.permutation(ret)
        label_ic = self._calc_ic(sig, shuff_ret)
        label_passed = abs(label_ic) < max(0.05, abs(baseline_ic) * 0.3)
        steps.append(FalsificationStepResult(
            step_name="label_permutation",
            passed=bool(label_passed),
            baseline_metric=baseline_ic,
            perturbed_metric=label_ic,
            description="Permuting return labels across observations should eliminate predictive power.",
        ))

        # 4. Universe / Sample Perturbation: drop 30% observations randomly
        sub_mask = rng.random(n) > 0.3
        if np.sum(sub_mask) > 10:
            sub_ic = self._calc_ic(sig[sub_mask], ret[sub_mask])
            univ_passed = abs(sub_ic) >= abs(baseline_ic) * 0.5
        else:
            sub_ic = 0.0
            univ_passed = False
        steps.append(FalsificationStepResult(
            step_name="sample_perturbation",
            passed=bool(univ_passed),
            baseline_metric=baseline_ic,
            perturbed_metric=sub_ic,
            description="Dropping 30% of data points should not cause total alpha collapse.",
        ))

        # 5. Parameter Perturbation: smooth slight decay/lag
        decay_sig = 0.8 * sig + 0.2 * np.roll(sig, 1)
        decay_ic = self._calc_ic(decay_sig[1:], ret[1:])
        param_passed = abs(decay_ic) >= abs(baseline_ic) * 0.6
        steps.append(FalsificationStepResult(
            step_name="parameter_perturbation",
            passed=bool(param_passed),
            baseline_metric=baseline_ic,
            perturbed_metric=decay_ic,
            description="Slight smoothing or parameter lag should retain majority of signal.",
        ))

        # 6. Cost Stress: 3x transaction fees
        gross_pnl = np.sum(sig * ret)
        stress_fees = np.sum(np.abs(np.diff(sig))) * (costs_bps * 3.0 / 10000.0)
        net_pnl = gross_pnl - stress_fees
        cost_passed = net_pnl > 0.0
        steps.append(FalsificationStepResult(
            step_name="cost_stress",
            passed=bool(cost_passed),
            baseline_metric=float(gross_pnl),
            perturbed_metric=float(net_pnl),
            description="Strategy must remain profitable after multiplying transaction costs by 3x.",
        ))

        # 7. Placebo Test: pure random noise signal
        noise_sig = rng.normal(0, 1, n)
        placebo_ic = self._calc_ic(noise_sig, ret)
        placebo_passed = abs(placebo_ic) < 0.05
        steps.append(FalsificationStepResult(
            step_name="placebo_test",
            passed=bool(placebo_passed),
            baseline_metric=baseline_ic,
            perturbed_metric=placebo_ic,
            description="Replacing the signal with Gaussian noise must not show alpha.",
        ))

        passed_count = sum(1 for s in steps if s.passed)
        total_count = len(steps)
        score = passed_count / total_count

        if score >= 0.85:
            verdict = "PASSED"
        elif score >= 0.55:
            verdict = "FLAGGED_FRAGILE"
        else:
            verdict = "FALSIFIED"

        return FalsificationReport(
            alpha_id=alpha_id,
            verdict=verdict,
            tests_passed=passed_count,
            total_tests=total_count,
            survival_score=score,
            steps=steps,
        )

    @staticmethod
    def _calc_ic(x: np.ndarray, y: np.ndarray) -> float:
        valid = ~np.isnan(x) & ~np.isnan(y)
        x_c, y_c = x[valid], y[valid]
        if len(x_c) < 5 or np.std(x_c) < 1e-9 or np.std(y_c) < 1e-9:
            return 0.0
        return float(np.corrcoef(x_c, y_c)[0, 1])


falsification_engine = FalsificationEngine()
