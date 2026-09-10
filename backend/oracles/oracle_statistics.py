"""
Independent Reference Oracle: Statistical & Econometric Estimators.
Implements reference formulas for:
1. Newey-West (1987) Heteroskedasticity and Autocorrelation Consistent (HAC) Variance.
2. Bailey & Lopez de Prado (2014) Deflated Sharpe Ratio (DSR) analytical asymptotic CDF.
3. Hansen (2005) Superior Predictive Ability (SPA) studentized test statistic.
Zero production imports permitted.
"""
import math
from typing import Sequence, Tuple


class OracleStatistics:
    """Independent reference implementations of quantitative statistical tests."""

    @staticmethod
    def newey_west_hac_variance(returns: Sequence[float], max_lags: int) -> float:
        """
        Pure reference Newey-West (1987) HAC variance estimator with Bartlett kernel.
        Var_HAC = gamma_0 + 2 * sum_{l=1}^L (1 - l / (L + 1)) * gamma_l
        """
        n = len(returns)
        if n <= 1:
            return 0.0

        mean = sum(returns) / n
        demeaned = [r - mean for r in returns]

        # gamma_0: sample variance
        gamma_0 = sum(x * x for x in demeaned) / n

        hac_sum = gamma_0
        for lag in range(1, max_lags + 1):
            gamma_lag = sum(demeaned[t] * demeaned[t - lag] for t in range(lag, n)) / n
            weight = 1.0 - (lag / (max_lags + 1.0))
            hac_sum += 2.0 * weight * gamma_lag

        return max(0.0, hac_sum)

    @staticmethod
    def deflated_sharpe_ratio_oracle(
        estimated_sr: float,
        n_trials: int,
        sample_length: int,
        skewness: float = 0.0,
        kurtosis: float = 3.0
    ) -> Tuple[float, float]:
        """
        Closed-form analytical DSR oracle (Bailey & Lopez de Prado 2014).
        Returns: (expected_max_sr, dsr_pvalue)
        """
        if n_trials <= 1:
            expected_max_sr = 0.0
        else:
            euler_mascheroni = 0.57721566490153286
            two_log_n = 2.0 * math.log(n_trials)
            expected_max_sr = math.sqrt(two_log_n) * (1.0 - (euler_mascheroni / two_log_n))
            # De-annualize expected max SR to sample periodicity if annualized
            expected_max_sr = expected_max_sr / math.sqrt(252.0)

        # Standard error under non-normality (Mertens 2002)
        denom_sq = 1.0 - (skewness * estimated_sr) + (((kurtosis - 1.0) / 4.0) * (estimated_sr ** 2))
        std_err = math.sqrt(max(denom_sq, 1e-8) / max(sample_length - 1, 1))

        z_stat = (estimated_sr - expected_max_sr) / std_err
        # Normal CDF via math.erf
        dsr_pvalue = 0.5 * (1.0 + math.erf(z_stat / math.sqrt(2.0)))
        return expected_max_sr, dsr_pvalue

    @staticmethod
    def hansen_spa_statistic_oracle(
        loss_benchmark: Sequence[float],
        loss_model: Sequence[float]
    ) -> float:
        """
        Computes Hansen's relative performance sample mean:
        d_k = L_benchmark - L_model (positive d_k indicates model outperforms benchmark).
        """
        n = min(len(loss_benchmark), len(loss_model))
        if n == 0:
            return 0.0
        d = [loss_benchmark[i] - loss_model[i] for i in range(n)]
        mean_d = sum(d) / n
        var_d = sum((x - mean_d) ** 2 for x in d) / max(n - 1, 1)
        std_d = math.sqrt(max(var_d, 1e-12))
        # Studentized t-statistic
        return (mean_d * math.sqrt(n)) / std_d
