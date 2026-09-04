/*
 * C High-Performance Vectorized Time-Series Rolling Operations
 * Compiled as shared library (.dll / .so) for Python CTypes integration.
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
            out[i] = 0.0; // or NaN representation
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
