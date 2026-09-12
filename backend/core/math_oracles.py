"""
QuantAlpha Independent Mathematical Oracles (Phase 2).
Provides standalone, clean-room, reference mathematical implementations
for statistical risk metrics, volatility models, bootstrap intervals,
and multiple-testing corrections to cross-validate primary platform calculations.
"""
import math
import random
from typing import Any, Dict, List, Tuple


class IndependentMathOracle:
    """Independent mathematical reference implementations with explicit closed-form formulas."""

    @staticmethod
    def mean(data: List[float]) -> float:
        if not data:
            raise ValueError("Data series cannot be empty")
        return sum(data) / len(data)

    @staticmethod
    def variance(data: List[float], ddof: int = 1) -> float:
        n = len(data)
        if n <= ddof:
            raise ValueError(f"Sample size {n} must be greater than ddof {ddof}")
        m = IndependentMathOracle.mean(data)
        return sum((x - m) ** 2 for x in data) / (n - ddof)

    @staticmethod
    def std_dev(data: List[float], ddof: int = 1) -> float:
        return math.sqrt(IndependentMathOracle.variance(data, ddof=ddof))

    @staticmethod
    def skewness(data: List[float]) -> float:
        n = len(data)
        if n < 3:
            return 0.0
        m = IndependentMathOracle.mean(data)
        s = IndependentMathOracle.std_dev(data, ddof=1)
        if s == 0:
            return 0.0
        m3 = sum((x - m) ** 3 for x in data) / n
        return (m3 / (s ** 3)) * (math.sqrt(n * (n - 1)) / (n - 2))

    @staticmethod
    def kurtosis(data: List[float]) -> float:
        """Excess kurtosis (normal distribution = 0.0)."""
        n = len(data)
        if n < 4:
            return 0.0
        m = IndependentMathOracle.mean(data)
        s = IndependentMathOracle.std_dev(data, ddof=1)
        if s == 0:
            return 0.0
        m4 = sum((x - m) ** 4 for x in data) / n
        raw_kurt = m4 / (s ** 4)
        # Sample excess kurtosis adjustment
        factor1 = (n - 1) / ((n - 2) * (n - 3))
        adj_kurt = factor1 * ((n + 1) * raw_kurt - 3 * (n - 1))
        return adj_kurt

    @staticmethod
    def sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.0,
        annualization_factor: float = 252.0
    ) -> float:
        """
        Exact Sharpe ratio: (Mean(R) - Rf/annualization) / StdDev(R) * sqrt(annualization)
        """
        if not returns or len(returns) < 2:
            return 0.0
        daily_rf = risk_free_rate / annualization_factor if risk_free_rate > 0 else 0.0
        excess_returns = [r - daily_rf for r in returns]
        mean_excess = sum(excess_returns) / len(excess_returns)
        s = IndependentMathOracle.std_dev(returns, ddof=1)
        if s <= 1e-12:
            return 0.0
        return (mean_excess / s) * math.sqrt(annualization_factor)

    @staticmethod
    def sortino_ratio(
        returns: List[float],
        target_return: float = 0.0,
        annualization_factor: float = 252.0
    ) -> float:
        """
        Exact Sortino ratio using downside semi-deviation below target return.
        Downside deviation = sqrt( 1/N * sum( min(r - target, 0)^2 ) )
        """
        if not returns or len(returns) < 2:
            return 0.0
        mean_r = sum(returns) / len(returns)
        downside_sq_sum = sum(min(r - target_return, 0.0) ** 2 for r in returns)
        downside_dev = math.sqrt(downside_sq_sum / len(returns))
        if downside_dev <= 1e-12:
            return 0.0
        return ((mean_r - target_return) / downside_dev) * math.sqrt(annualization_factor)

    @staticmethod
    def max_drawdown(equity_curve_or_returns: List[float], is_returns: bool = True) -> Tuple[float, int, int]:
        """
        Computes maximum peak-to-trough percentage drawdown.
        Returns: (max_dd_fraction, peak_index, trough_index)
        """
        if not equity_curve_or_returns:
            return 0.0, 0, 0

        if is_returns:
            equity = [1.0]
            for r in equity_curve_or_returns:
                equity.append(equity[-1] * (1.0 + r))
        else:
            equity = equity_curve_or_returns

        peak = equity[0]
        peak_idx = 0
        max_dd = 0.0
        best_peak_idx = 0
        trough_idx = 0

        for i, val in enumerate(equity):
            if val > peak:
                peak = val
                peak_idx = i
            else:
                dd = (peak - val) / peak if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd
                    best_peak_idx = peak_idx
                    trough_idx = i

        return max_dd, best_peak_idx, trough_idx

    @staticmethod
    def omega_ratio(returns: List[float], threshold: float = 0.0) -> float:
        """
        Omega ratio = sum(max(R - threshold, 0)) / sum(max(threshold - R, 0))
        """
        if not returns:
            return 0.0
        gains = sum(max(r - threshold, 0.0) for r in returns)
        losses = sum(max(threshold - r, 0.0) for r in returns)
        if losses <= 1e-12:
            return float("inf") if gains > 0 else 1.0
        return gains / losses

    @staticmethod
    def realized_volatility(
        returns: List[float],
        annualization_factor: float = 252.0
    ) -> float:
        if not returns or len(returns) < 2:
            return 0.0
        return IndependentMathOracle.std_dev(returns, ddof=1) * math.sqrt(annualization_factor)

    @staticmethod
    def parkinson_volatility(
        highs: List[float],
        lows: List[float],
        annualization_factor: float = 252.0
    ) -> float:
        """
        Parkinson high-low volatility:
        sigma = sqrt( 1 / (4 * ln(2) * N) * sum( (ln(H_i / L_i))^2 ) ) * sqrt(annualization)
        """
        n = min(len(highs), len(lows))
        if n < 1:
            return 0.0
        sq_sum = 0.0
        for h, l in zip(highs[:n], lows[:n]):
            if h > 0 and l > 0 and h >= l:
                sq_sum += (math.log(h / l)) ** 2
        var = sq_sum / (4.0 * math.log(2.0) * n)
        return math.sqrt(var) * math.sqrt(annualization_factor)

    @staticmethod
    def garman_klass_volatility(
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        annualization_factor: float = 252.0
    ) -> float:
        """
        Garman-Klass volatility incorporating OHLC:
        sigma^2 = 1/N * sum( 0.5*(ln(H/L))^2 - (2*ln(2)-1)*(ln(C/O))^2 )
        """
        n = min(len(opens), len(highs), len(lows), len(closes))
        if n < 1:
            return 0.0
        term_sum = 0.0
        c1 = 2.0 * math.log(2.0) - 1.0
        for o, h, l, c in zip(opens[:n], highs[:n], lows[:n], closes[:n]):
            if o > 0 and h > 0 and l > 0 and c > 0:
                hl = math.log(h / l)
                co = math.log(c / o)
                term_sum += 0.5 * (hl ** 2) - c1 * (co ** 2)
        var = max(0.0, term_sum / n)
        return math.sqrt(var) * math.sqrt(annualization_factor)

    @staticmethod
    def historical_var_cvar(
        returns: List[float],
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculates Empirical Historical Value-at-Risk (VaR) and Conditional VaR (CVaR).
        Returns positive loss fractions (e.g. VaR=0.021 means 2.1% loss).
        """
        if not returns:
            return 0.0, 0.0
        sorted_r = sorted(returns)
        n = len(sorted_r)
        alpha = 1.0 - confidence_level
        cutoff_idx = max(0, int(math.floor(alpha * n)))
        var_val = -sorted_r[cutoff_idx]

        tail_returns = sorted_r[: cutoff_idx + 1]
        cvar_val = -(sum(tail_returns) / len(tail_returns)) if tail_returns else var_val
        return max(0.0, var_val), max(0.0, cvar_val)

    @staticmethod
    def cornish_fisher_var(
        returns: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """
        Cornish-Fisher expansion VaR adjusting standard normal quantile for skewness & kurtosis.
        """
        if not returns or len(returns) < 4:
            return 0.0
        m = IndependentMathOracle.mean(returns)
        s = IndependentMathOracle.std_dev(returns, ddof=1)
        skew = IndependentMathOracle.skewness(returns)
        kurt = IndependentMathOracle.kurtosis(returns)

        # Approximate inverse standard normal CDF for confidence level (e.g., 0.95 -> ~1.644853)
        # Using Acklam's high-precision approximation for standard normal quantile
        alpha = 1.0 - confidence_level
        z = IndependentMathOracle._norm_ppf(alpha)

        # Cornish-Fisher adjusted quantile
        z_cf = (
            z
            + (z ** 2 - 1.0) * (skew / 6.0)
            + (z ** 3 - 3.0 * z) * (kurt / 24.0)
            - (2.0 * z ** 3 - 5.0 * z) * (skew ** 2 / 36.0)
        )
        # VaR as positive loss
        cf_var = -(m + z_cf * s)
        return max(0.0, cf_var)

    @staticmethod
    def _norm_ppf(p: float) -> float:
        """Acklam's algorithm for inverse standard normal cumulative distribution function."""
        if p <= 0.0 or p >= 1.0:
            raise ValueError("p must be in (0, 1)")

        a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
             1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
        b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
             6.680131188771972e01, -1.328068155288572e01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
             -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
             3.754408661907416e00]

        p_low = 0.02425
        p_high = 1.0 - p_low

        if p < p_low:
            q = math.sqrt(-2.0 * math.log(p))
            return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                   ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
                   (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
        else:
            q = math.sqrt(-2.0 * math.log(1.0 - p))
            return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                    ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)

    @staticmethod
    def circular_block_bootstrap_ci(
        returns: List[float],
        metric_func,
        block_size: int = 10,
        n_bootstraps: int = 500,
        alpha: float = 0.05,
        seed: int = 42
    ) -> Tuple[float, float, float]:
        """
        Circular Block Bootstrap confidence intervals for dependent time-series returns.
        Returns: (point_estimate, lower_ci, upper_ci)
        """
        if not returns:
            return 0.0, 0.0, 0.0
        rng = random.Random(seed)
        n = len(returns)
        point_est = metric_func(returns)
        if n < block_size or n_bootstraps < 10:
            return point_est, point_est, point_est

        boot_stats = []
        for _ in range(n_bootstraps):
            sample = []
            while len(sample) < n:
                start = rng.randint(0, n - 1)
                for b in range(block_size):
                    sample.append(returns[(start + b) % n])
                    if len(sample) == n:
                        break
            boot_stats.append(metric_func(sample))

        boot_stats.sort()
        low_idx = int(math.floor(alpha / 2.0 * n_bootstraps))
        high_idx = int(math.ceil((1.0 - alpha / 2.0) * n_bootstraps)) - 1
        return point_est, boot_stats[max(0, low_idx)], boot_stats[min(n_bootstraps - 1, high_idx)]

    @staticmethod
    def multiple_testing_corrections(
        p_values: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Independent reference implementation of Multiple Hypothesis Testing corrections:
        1. Bonferroni Family-Wise Error Rate (FWER)
        2. Holm-Bonferroni Step-Down FWER
        3. Benjamini-Hochberg False Discovery Rate (FDR)
        """
        m = len(p_values)
        if m == 0:
            return {}

        indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])

        # 1. Bonferroni
        bonf_threshold = alpha / m
        bonf_rejected = [p <= bonf_threshold for p in p_values]
        bonf_adjusted = [min(1.0, p * m) for p in p_values]

        # 2. Holm-Bonferroni
        holm_rejected = [False] * m
        holm_adjusted = [0.0] * m
        for rank, (orig_idx, p_val) in enumerate(indexed_p):
            k = m - rank
            threshold = alpha / k
            if p_val <= threshold:
                holm_rejected[orig_idx] = True
            else:
                # Once one fails, all subsequent ranked hypotheses fail
                break

        running_max = 0.0
        for rank, (orig_idx, p_val) in enumerate(indexed_p):
            k = m - rank
            adj = min(1.0, p_val * k)
            running_max = max(running_max, adj)
            holm_adjusted[orig_idx] = running_max

        # 3. Benjamini-Hochberg (FDR)
        bh_rejected = [False] * m
        max_valid_rank = -1
        for rank, (orig_idx, p_val) in enumerate(indexed_p):
            rank_1based = rank + 1
            threshold = (rank_1based / m) * alpha
            if p_val <= threshold:
                max_valid_rank = rank

        if max_valid_rank >= 0:
            for rank in range(max_valid_rank + 1):
                bh_rejected[indexed_p[rank][0]] = True

        # Calculate BH adjusted p-values (q-values)
        bh_adjusted = [0.0] * m
        running_min = 1.0
        for rank in range(m - 1, -1, -1):
            orig_idx, p_val = indexed_p[rank]
            rank_1based = rank + 1
            adj = min(1.0, (p_val * m) / rank_1based)
            running_min = min(running_min, adj)
            bh_adjusted[orig_idx] = running_min

        return {
            "total_hypotheses": m,
            "nominal_alpha": alpha,
            "bonferroni": {
                "rejected_count": sum(bonf_rejected),
                "rejected_mask": bonf_rejected,
                "adjusted_p": bonf_adjusted,
            },
            "holm_bonferroni": {
                "rejected_count": sum(holm_rejected),
                "rejected_mask": holm_rejected,
                "adjusted_p": holm_adjusted,
            },
            "benjamini_hochberg_fdr": {
                "rejected_count": sum(bh_rejected),
                "rejected_mask": bh_rejected,
                "adjusted_p": bh_adjusted,
            },
        }
