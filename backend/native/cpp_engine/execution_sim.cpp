/**
 * C++ Ultra-Fast Execution & Market Impact Engine
 * Implements Almgren-Chriss optimal liquidation trajectory & TWAP/VWAP simulator.
 */

#include <cmath>
#include <vector>
#include <algorithm>
#include <numeric>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

extern "C" {

/**
 * Almgren-Chriss optimal trajectory computation.
 * Total shares X over T intervals, risk aversion lambda, volatility sigma,
 * temporary impact eta, permanent impact gamma.
 * returns array of share trade sizes tau_k in out_trades.
 */
EXPORT void cpp_almgren_chriss_trajectory(
    double total_shares,
    int intervals,
    double risk_aversion, // lambda
    double volatility,    // sigma
    double temp_impact,   // eta
    double perm_impact,   // gamma
    double* out_holdings, // length intervals + 1
    double* out_trades,   // length intervals
    double* out_expected_cost
) {
    if (intervals <= 0) return;

    double tau = 1.0; // unit time step
    double kappa2 = (risk_aversion * volatility * volatility) / (temp_impact * (1.0 - 0.5 * perm_impact * tau));
    double kappa = std::sqrt(std::max(1e-9, kappa2));

    double cosh_kappa_T = std::cosh(kappa * intervals * tau);
    double sinh_kappa_T = std::sinh(kappa * intervals * tau);

    out_holdings[0] = total_shares;
    double expected_cost = 0.5 * perm_impact * total_shares * total_shares;

    for (int j = 1; j <= intervals; ++j) {
        double t_j = j * tau;
        double remaining_time = (intervals - j) * tau;
        double xj = total_shares * std::sinh(kappa * remaining_time) / (sinh_kappa_T + 1e-12);
        out_holdings[j] = xj;
        double trade = out_holdings[j - 1] - xj;
        out_trades[j - 1] = trade;

        // Add temporary impact cost
        expected_cost += temp_impact * (trade / tau) * (trade / tau) * tau;
    }

    *out_expected_cost = expected_cost;
}

/**
 * Fast TWAP Execution Simulator.
 * Simulates order fill across intervals with slippage and volume constraint.
 */
EXPORT void cpp_simulate_twap(
    double total_shares,
    int n_bars,
    const double* bar_prices,
    const double* bar_volumes,
    double max_participation_rate,
    double spread_bps,
    double* out_executed_prices,
    double* out_executed_shares,
    double* out_total_slippage_bps
) {
    if (n_bars <= 0 || total_shares <= 0.0) return;

    double target_per_bar = total_shares / n_bars;
    double remaining = total_shares;
    double total_dollar_spent = 0.0;
    double benchmark_dollar = total_shares * bar_prices[0];

    for (int i = 0; i < n_bars; ++i) {
        double vol_cap = bar_volumes[i] * max_participation_rate;
        double execution_size = std::min(remaining, std::min(target_per_bar * 1.25, vol_cap));
        if (i == n_bars - 1) {
            execution_size = remaining; // force fill
        }

        // Half spread + linear impact
        double impact_bps = (spread_bps * 0.5) + (execution_size / (bar_volumes[i] + 1e-9)) * 50.0;
        double fill_price = bar_prices[i] * (1.0 + impact_bps / 10000.0);

        out_executed_shares[i] = execution_size;
        out_executed_prices[i] = fill_price;

        total_dollar_spent += execution_size * fill_price;
        remaining -= execution_size;
        if (remaining <= 0.0) {
            for (int k = i + 1; k < n_bars; ++k) {
                out_executed_shares[k] = 0.0;
                out_executed_prices[k] = bar_prices[k];
            }
            break;
        }
    }

    double avg_fill = total_shares > 0 ? (total_dollar_spent / total_shares) : bar_prices[0];
    *out_total_slippage_bps = ((avg_fill / bar_prices[0]) - 1.0) * 10000.0;
}

}
