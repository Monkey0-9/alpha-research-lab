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

/**
 * Fast VWAP Execution Simulator.
 * Simulates order fill across intervals matching historical volume curve.
 */
EXPORT void cpp_simulate_vwap(
    double total_shares,
    int n_bars,
    const double* bar_prices,
    const double* bar_volumes,
    double spread_bps,
    double* out_executed_prices,
    double* out_executed_shares,
    double* out_total_slippage_bps
) {
    if (n_bars <= 0 || total_shares <= 0.0) return;

    double total_volume = 0.0;
    for (int i = 0; i < n_bars; ++i) {
        total_volume += bar_volumes[i];
    }
    if (total_volume <= 0.0) total_volume = 1.0;

    double remaining = total_shares;
    double total_dollar_spent = 0.0;

    for (int i = 0; i < n_bars; ++i) {
        double vol_weight = bar_volumes[i] / total_volume;
        double target_shares = total_shares * vol_weight;
        double execution_size = std::min(remaining, target_shares);
        if (i == n_bars - 1) {
            execution_size = remaining;
        }

        double impact_bps = (spread_bps * 0.5) + (execution_size / (bar_volumes[i] + 1e-9)) * 35.0;
        double fill_price = bar_prices[i] * (1.0 + impact_bps / 10000.0);

        out_executed_shares[i] = execution_size;
        out_executed_prices[i] = fill_price;

        total_dollar_spent += execution_size * fill_price;
        remaining -= execution_size;
    }

    double avg_fill = total_shares > 0 ? (total_dollar_spent / total_shares) : bar_prices[0];
    *out_total_slippage_bps = ((avg_fill / bar_prices[0]) - 1.0) * 10000.0;
}

/**
 * Event-Driven Discrete Portfolio & Execution Engine.
 * Processes MarketEvent -> OrderEvent -> FillEvent -> Cash/Position Update -> Daily NAV
 * Enforces commission, bid/ask spread, non-linear market impact, and borrow costs.
 */
EXPORT void cpp_event_driven_backtest(
    int n_steps,
    const double* prices,
    const double* volumes,
    const double* target_shares,
    double initial_cash,
    double commission_bps,
    double spread_bps,
    double impact_coeff,
    double borrow_cost_annual_bps,
    double* out_nav,
    double* out_positions,
    double* out_cash,
    double* out_cumulative_fees,
    double* out_step_pnl,
    double* out_summary_metrics // [total_return, sharpe_ratio, max_drawdown, turnover]
) {
    if (n_steps <= 0) return;

    double cash = initial_cash;
    double current_position = 0.0;
    double cumulative_fees = 0.0;
    double prev_nav = initial_cash;
    double peak_nav = initial_cash;
    double max_dd = 0.0;
    double total_traded_volume = 0.0;

    std::vector<double> daily_returns;
    daily_returns.reserve(n_steps);

    for (int t = 0; t < n_steps; ++t) {
        double p = prices[t];
        double v = std::max(1.0, volumes[t]);
        double target = target_shares[t];
        double delta_shares = target - current_position;

        double step_fee = 0.0;

        // Process Order & Fill if position adjustment requested
        if (std::abs(delta_shares) > 1e-6) {
            total_traded_volume += std::abs(delta_shares) * p;
            double participation = std::abs(delta_shares) / v;
            double impact_rate = (spread_bps * 0.5 + impact_coeff * participation * 100.0) / 10000.0;

            double fill_price = (delta_shares > 0) ? (p * (1.0 + impact_rate)) : (p * (1.0 - impact_rate));
            double trade_dollar = delta_shares * fill_price;
            double commission = std::abs(trade_dollar) * (commission_bps / 10000.0);

            step_fee += commission;
            cash -= (trade_dollar + commission);
            current_position += delta_shares;
        }

        // Apply short borrow financing drag
        if (current_position < 0.0) {
            double short_value = std::abs(current_position * p);
            double daily_borrow_fee = short_value * (borrow_cost_annual_bps / 10000.0) / 252.0;
            step_fee += daily_borrow_fee;
            cash -= daily_borrow_fee;
        }

        cumulative_fees += step_fee;
        double nav = cash + current_position * p;
        double step_pnl = nav - prev_nav;

        out_nav[t] = nav;
        out_positions[t] = current_position;
        out_cash[t] = cash;
        out_cumulative_fees[t] = cumulative_fees;
        out_step_pnl[t] = step_pnl;

        // Track drawdown
        if (nav > peak_nav) peak_nav = nav;
        double dd = (peak_nav > 0) ? ((peak_nav - nav) / peak_nav) : 0.0;
        if (dd > max_dd) max_dd = dd;

        // Daily return
        double ret = (prev_nav > 0) ? (step_pnl / prev_nav) : 0.0;
        daily_returns.push_back(ret);

        prev_nav = nav;
    }

    // Compute Summary Metrics
    double total_return = (initial_cash > 0) ? ((out_nav[n_steps - 1] - initial_cash) / initial_cash) : 0.0;
    
    double mean_ret = 0.0;
    for (double r : daily_returns) mean_ret += r;
    mean_ret /= n_steps;

    double var_ret = 0.0;
    for (double r : daily_returns) var_ret += (r - mean_ret) * (r - mean_ret);
    var_ret = (n_steps > 1) ? (var_ret / (n_steps - 1)) : 1e-9;
    double std_ret = std::sqrt(var_ret);

    double sharpe = (std_ret > 1e-8) ? ((mean_ret / std_ret) * std::sqrt(252.0)) : 0.0;
    double turnover = (initial_cash > 0) ? (total_traded_volume / (initial_cash * n_steps)) : 0.0;

    out_summary_metrics[0] = total_return;
    out_summary_metrics[1] = sharpe;
    out_summary_metrics[2] = max_dd;
    out_summary_metrics[3] = turnover;
}

}

