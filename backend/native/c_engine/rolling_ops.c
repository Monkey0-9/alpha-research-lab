/*
 * C High-Performance Vectorized Quantitative Kernel Engine
 * Compiled as shared library (.dll / .so) for Python CTypes integration.
 * Implements microsecond-level rolling operations, Kalman state-space filtering,
 * Order Flow Imbalance (OFI), microprice estimation, and EWMA risk modeling.
 */

#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

EXPORT void c_rolling_mean(const double* in, double* out, int n, int window) {
    if (n <= 0 || window <= 0) return;
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += in[i];
        if (i >= window) {
            sum -= in[i - window];
        }
        if (i >= window - 1) {
            out[i] = sum / (double)window;
        } else {
            out[i] = 0.0;
        }
    }
}

EXPORT void c_rolling_std(const double* in, double* out, int n, int window) {
    if (n <= 0 || window <= 1) return;
    double sum = 0.0;
    double sum_sq = 0.0;

    for (int i = 0; i < n; i++) {
        sum += in[i];
        sum_sq += in[i] * in[i];

        if (i >= window) {
            sum -= in[i - window];
            sum_sq -= in[i - window] * in[i - window];
        }

        if (i >= window - 1) {
            double mean = sum / (double)window;
            double variance = (sum_sq - (sum * sum) / (double)window) / (double)(window - 1);
            out[i] = variance > 0.0 ? sqrt(variance) : 0.0;
        } else {
            out[i] = 0.0;
        }
    }
}

EXPORT void c_rolling_ema(const double* in, double* out, int n, double alpha) {
    if (n <= 0 || alpha <= 0.0 || alpha > 1.0) return;
    out[0] = in[0];
    for (int i = 1; i < n; i++) {
        out[i] = alpha * in[i] + (1.0 - alpha) * out[i - 1];
    }
}

EXPORT void c_rolling_rsi(const double* in, double* out, int n, int period) {
    if (n <= period || period <= 0) return;
    double avg_gain = 0.0;
    double avg_loss = 0.0;

    out[0] = 50.0;
    for (int i = 1; i <= period; i++) {
        double diff = in[i] - in[i - 1];
        if (diff > 0.0) avg_gain += diff;
        else avg_loss -= diff;
        out[i] = 50.0;
    }

    avg_gain /= (double)period;
    avg_loss /= (double)period;

    for (int i = period + 1; i < n; i++) {
        double diff = in[i] - in[i - 1];
        double gain = diff > 0.0 ? diff : 0.0;
        double loss = diff < 0.0 ? -diff : 0.0;

        avg_gain = (avg_gain * (period - 1) + gain) / (double)period;
        avg_loss = (avg_loss * (period - 1) + loss) / (double)period;

        if (avg_loss == 0.0) {
            out[i] = 100.0;
        } else {
            double rs = avg_gain / avg_loss;
            out[i] = 100.0 - (100.0 / (1.0 + rs));
        }
    }
}

EXPORT void c_simulate_pnl(
    const double* daily_returns,
    const double* positions,
    double* out_pnl,
    int n,
    double fee_bps
) {
    if (n <= 0) return;
    double fee_rate = fee_bps / 10000.0;
    double prev_pos = 0.0;

    for (int i = 0; i < n; i++) {
        double pos = positions[i];
        double delta_pos = fabs(pos - prev_pos);
        double cost = delta_pos * fee_rate;
        double ret = pos * daily_returns[i] - cost;
        out_pnl[i] = ret;
        prev_pos = pos;
    }
}

EXPORT void c_rolling_zscore(const double* in, double* out, int n, int window) {
    if (n <= 0 || window <= 1) return;
    double sum = 0.0;
    double sum_sq = 0.0;

    for (int i = 0; i < n; i++) {
        sum += in[i];
        sum_sq += in[i] * in[i];

        if (i >= window) {
            sum -= in[i - window];
            sum_sq -= in[i - window] * in[i - window];
        }

        if (i >= window - 1) {
            double mean = sum / (double)window;
            double variance = (sum_sq - (sum * sum) / (double)window) / (double)(window - 1);
            double std = variance > 1e-12 ? sqrt(variance) : 1e-6;
            out[i] = (in[i] - mean) / std;
        } else {
            out[i] = 0.0;
        }
    }
}

/*
 * C-Accelerated 1D State-Space Kalman Filter
 * Ideal for tracking latent true fair-value and high-speed online noise attenuation.
 */
EXPORT void c_kalman_filter(
    const double* observations,
    double* out_state,
    double* out_cov,
    int n,
    double q_process_noise,
    double r_measurement_noise,
    double initial_state,
    double initial_cov
) {
    if (n <= 0) return;

    double x_est = initial_state;
    double p_est = initial_cov;

    for (int i = 0; i < n; i++) {
        // 1. Time Update (Predict)
        double x_pred = x_est;
        double p_pred = p_est + q_process_noise;

        // 2. Measurement Update (Correct)
        double z = observations[i];
        double innovation = z - x_pred;
        double innovation_cov = p_pred + r_measurement_noise;
        double k_gain = p_pred / (innovation_cov > 1e-12 ? innovation_cov : 1e-12);

        x_est = x_pred + k_gain * innovation;
        p_est = (1.0 - k_gain) * p_pred;

        out_state[i] = x_est;
        out_cov[i] = p_est;
    }
}

/*
 * High-Frequency Order Flow Imbalance (OFI) Kernel
 * Quantifies net volume addition/cancellation pressure across consecutive L1/L2 quotes.
 */
EXPORT void c_order_flow_imbalance(
    const double* bid_prices,
    const double* bid_sizes,
    const double* ask_prices,
    const double* ask_sizes,
    double* out_ofi,
    int n
) {
    if (n <= 1) return;
    out_ofi[0] = 0.0;

    for (int i = 1; i < n; i++) {
        double delta_bid_vol = 0.0;
        if (bid_prices[i] > bid_prices[i - 1]) {
            delta_bid_vol = bid_sizes[i];
        } else if (bid_prices[i] == bid_prices[i - 1]) {
            delta_bid_vol = bid_sizes[i] - bid_sizes[i - 1];
        } else {
            delta_bid_vol = -bid_sizes[i - 1];
        }

        double delta_ask_vol = 0.0;
        if (ask_prices[i] < ask_prices[i - 1]) {
            delta_ask_vol = ask_sizes[i];
        } else if (ask_prices[i] == ask_prices[i - 1]) {
            delta_ask_vol = ask_sizes[i] - ask_sizes[i - 1];
        } else {
            delta_ask_vol = -ask_sizes[i - 1];
        }

        out_ofi[i] = delta_bid_vol - delta_ask_vol;
    }
}

/*
 * High-Precision Microprice Kernel
 * Computes depth-weighted equilibrium price incorporating bid/ask queue imbalance.
 */
EXPORT void c_microprice(
    const double* bid_prices,
    const double* bid_sizes,
    const double* ask_prices,
    const double* ask_sizes,
    double* out_microprice,
    int n
) {
    if (n <= 0) return;
    for (int i = 0; i < n; i++) {
        double total_depth = bid_sizes[i] + ask_sizes[i];
        if (total_depth > 1e-12) {
            out_microprice[i] = (bid_sizes[i] * ask_prices[i] + ask_sizes[i] * bid_prices[i]) / total_depth;
        } else {
            out_microprice[i] = 0.5 * (bid_prices[i] + ask_prices[i]);
        }
    }
}

/*
 * Exponentially Weighted Moving Average (EWMA) Volatility Kernel
 * RiskMetrics standard: sigma_t^2 = lambda * sigma_{t-1}^2 + (1 - lambda) * r_t^2
 */
EXPORT void c_ewma_volatility(
    const double* returns,
    double* out_vol,
    int n,
    double lambda_decay
) {
    if (n <= 0) return;
    double var_est = returns[0] * returns[0];
    out_vol[0] = sqrt(var_est > 0.0 ? var_est : 1e-8);

    double one_minus_lambda = 1.0 - lambda_decay;
    for (int i = 1; i < n; i++) {
        double r2 = returns[i] * returns[i];
        var_est = lambda_decay * var_est + one_minus_lambda * r2;
        out_vol[i] = sqrt(var_est > 0.0 ? var_est : 1e-8);
    }
}

/*
 * Rolling Rescaled Range (R/S) Hurst Exponent Kernel
 * Distinguishes mean-reverting (H < 0.5), random walk (H = 0.5), and momentum (H > 0.5) regimes.
 */
EXPORT void c_rescaled_range_hurst(
    const double* prices,
    double* out_hurst,
    int n,
    int window
) {
    if (n <= 0 || window < 10) return;

    for (int i = 0; i < n; i++) {
        if (i < window - 1) {
            out_hurst[i] = 0.5; // neutral prior
            continue;
        }

        int start = i - window + 1;
        // 1. Calculate log returns and their mean
        double sum_r = 0.0;
        double sum_sq_r = 0.0;
        int m = window - 1;

        for (int j = 1; j < window; j++) {
            double p0 = prices[start + j - 1];
            double p1 = prices[start + j];
            double r = (p0 > 1e-6 && p1 > 1e-6) ? log(p1 / p0) : 0.0;
            sum_r += r;
            sum_sq_r += r * r;
        }

        double mean_r = sum_r / (double)m;
        double variance = (sum_sq_r - (sum_r * sum_r) / (double)m) / (double)(m > 1 ? m - 1 : 1);
        double s = variance > 1e-12 ? sqrt(variance) : 1e-6;

        // 2. Compute cumulative deviations from mean
        double cum_dev = 0.0;
        double min_dev = 0.0;
        double max_dev = 0.0;

        for (int j = 1; j < window; j++) {
            double p0 = prices[start + j - 1];
            double p1 = prices[start + j];
            double r = (p0 > 1e-6 && p1 > 1e-6) ? log(p1 / p0) : 0.0;
            cum_dev += (r - mean_r);
            if (cum_dev > max_dev) max_dev = cum_dev;
            if (cum_dev < min_dev) min_dev = cum_dev;
        }

        double range = max_dev - min_dev;
        double rs = range / s;
        if (rs > 0.0 && m > 2) {
            double h = log(rs) / log((double)m);
            // Bound Hurst exponent between 0.01 and 0.99
            if (h < 0.01) h = 0.01;
            if (h > 0.99) h = 0.99;
            out_hurst[i] = h;
        } else {
            out_hurst[i] = 0.5;
        }
    }
}
