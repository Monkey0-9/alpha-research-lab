"""
Multi-Metric Reproduction Comparator.
Verifies reproduction across all 14 mandatory quantitative dimensions:
1. In-Sample Sharpe Ratio
2. Out-of-Sample Sharpe Ratio
3. Mean Information Coefficient (IC)
4. Information Coefficient Information Ratio (ICIR)
5. Annualized Return
6. Annualized Volatility
7. Maximum Drawdown
8. Portfolio Turnover
9. Execution Cost
10. Strategy Capacity
11. Total Trade Count
12. Equity Curve SHA-256
13. Trade Blotter SHA-256
14. Risk Report SHA-256
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Any, List


class ReproductionMismatchException(Exception):
    """Raised when reproduced results diverge from reference baseline beyond rigorous tolerances."""


@dataclass
class MetricComparisonResult:
    metric_name: str
    passed: bool
    reference_value: Any
    reproduced_value: Any
    tolerance_used: str
    discrepancy: str = ""


@dataclass
class MultiMetricReproductionReport:
    experiment_id: str
    all_passed: bool
    metrics_evaluated_count: int
    passed_count: int
    failed_count: int
    results: List[MetricComparisonResult] = field(default_factory=list)

    def summary_table(self) -> str:
        status_str = "PASSED (VERIFIED REPRODUCIBLE)" if self.all_passed else "FAILED (REPRODUCTION MISMATCH)"
        lines = [
            f"=== LEVEL-5 MULTI-METRIC REPRODUCTION REPORT [{self.experiment_id}] ===",
            f"Overall Status: {status_str}",
            f"Passing Dimensions: {self.passed_count} / {self.metrics_evaluated_count}",
            "-" * 80,
            f"{'Metric':<25} | {'Ref Value':<15} | {'Rep Value':<15} | {'Status':<8} | Detail",
            "-" * 80,
        ]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            ref_str = str(r.reference_value)[:14]
            rep_str = str(r.reproduced_value)[:14]
            lines.append(f"{r.metric_name:<25} | {ref_str:<15} | {rep_str:<15} | {status:<8} | {r.discrepancy}")
        lines.append("=" * 80)
        return "\n".join(lines)


class MultiMetricReproductionComparator:
    """
    Independent Level-5 Multi-Metric Quantitative Comparator.
    """

    # Tolerances
    FLOAT_REL_TOL = 1e-4
    FLOAT_ABS_TOL = 1e-4
    TURNOVER_REL_TOL = 1e-3
    CAPACITY_REL_TOL = 1e-3

    REQUIRED_DIMENSIONS = [
        ("sharpe", "float_rel", FLOAT_REL_TOL),
        ("oos_sharpe", "float_rel", FLOAT_REL_TOL),
        ("ic", "float_abs", FLOAT_ABS_TOL),
        ("icir", "float_abs", FLOAT_ABS_TOL),
        ("annualized_return", "float_rel", FLOAT_REL_TOL),
        ("annualized_volatility", "float_rel", FLOAT_REL_TOL),
        ("max_drawdown", "float_rel", FLOAT_REL_TOL),
        ("turnover", "float_rel", TURNOVER_REL_TOL),
        ("total_cost", "float_rel", FLOAT_REL_TOL),
        ("capacity", "float_rel", CAPACITY_REL_TOL),
        ("trade_count", "exact_int", 0),
        ("equity_curve_hash", "exact_str", 0),
        ("trade_blotter_hash", "exact_str", 0),
        ("risk_report_hash", "exact_str", 0),
    ]

    @classmethod
    def compare(
        cls,
        experiment_id: str,
        reference: Dict[str, Any],
        reproduced: Dict[str, Any],
        fail_closed: bool = True,
    ) -> MultiMetricReproductionReport:
        """
        Compare reproduced metrics against reference baseline.
        """
        results: List[MetricComparisonResult] = []

        for metric_name, kind, tol in cls.REQUIRED_DIMENSIONS:
            ref_val = reference.get(metric_name)
            rep_val = reproduced.get(metric_name)

            if ref_val is None or rep_val is None:
                results.append(
                    MetricComparisonResult(
                        metric_name=metric_name,
                        passed=False,
                        reference_value=ref_val,
                        reproduced_value=rep_val,
                        tolerance_used="presence_check",
                        discrepancy=f"MISSING: ref={ref_val}, rep={rep_val}",
                    )
                )
                continue

            passed = False
            discrepancy = "Match"

            if kind == "float_rel":
                try:
                    ref_f = float(ref_val)
                    rep_f = float(rep_val)
                    passed = math.isclose(ref_f, rep_f, rel_tol=float(tol), abs_tol=1e-6)
                    if not passed:
                        diff = abs(ref_f - rep_f)
                        rel_diff = diff / max(abs(ref_f), 1e-9)
                        discrepancy = f"rel_diff {rel_diff:.6e} > {tol}"
                except Exception as e:
                    passed = False
                    discrepancy = f"Conversion error: {e}"

            elif kind == "float_abs":
                try:
                    ref_f = float(ref_val)
                    rep_f = float(rep_val)
                    diff = abs(ref_f - rep_f)
                    passed = diff <= float(tol)
                    if not passed:
                        discrepancy = f"abs_diff {diff:.6e} > {tol}"
                except Exception as e:
                    passed = False
                    discrepancy = f"Conversion error: {e}"

            elif kind == "exact_int":
                try:
                    passed = int(ref_val) == int(rep_val)
                    if not passed:
                        discrepancy = f"Integer mismatch: {ref_val} != {rep_val}"
                except Exception as e:
                    passed = False
                    discrepancy = f"Conversion error: {e}"

            elif kind == "exact_str":
                passed = str(ref_val) == str(rep_val)
                if not passed:
                    discrepancy = f"Hash mismatch: {ref_val} != {rep_val}"

            results.append(
                MetricComparisonResult(
                    metric_name=metric_name,
                    passed=passed,
                    reference_value=ref_val,
                    reproduced_value=rep_val,
                    tolerance_used=f"{kind}({tol})",
                    discrepancy=discrepancy,
                )
            )

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)
        all_passed = failed_count == 0

        report = MultiMetricReproductionReport(
            experiment_id=experiment_id,
            all_passed=all_passed,
            metrics_evaluated_count=len(results),
            passed_count=passed_count,
            failed_count=failed_count,
            results=results,
        )

        if fail_closed and not all_passed:
            failed_names = [r.metric_name for r in results if not r.passed]
            raise ReproductionMismatchException(
                f"REPRODUCTION MISMATCH for experiment '{experiment_id}': "
                f"failed on dimensions: {failed_names}"
            )

        return report
