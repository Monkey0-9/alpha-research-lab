#pragma once
#include <vector>
#include <string>
#include <unordered_map>
#include "market_event.hpp"
#include "order.hpp"
#include "fill.hpp"
#include "portfolio.hpp"
#include "execution_model.hpp"
#include "transaction_cost.hpp"

namespace quantalpha {

class BacktestEngine {
public:
    Portfolio portfolio;
    ExecutionModel execution_model;
    CostSchedule costs;
    std::vector<Fill> all_fills;
    int64_t next_order_id{1};
    int64_t next_fill_id{1};

    BacktestEngine(double initial_cash = 100000.0) {
        portfolio.cash = initial_cash;
    }

    Fill process_order(
        const std::string& symbol,
        OrderSide side,
        double quantity,
        const MarketEvent& event
    ) {
        Order ord{
            next_order_id++,
            symbol,
            side,
            OrderType::MARKET,
            quantity,
            0.0,
            0.0,
            OrderStatus::PENDING,
            event.timestamp_ns
        };

        Fill fill = execution_model.execute_order(next_fill_id++, ord, event, costs.commission_bps);

        // Update portfolio cash & position
        double trade_dollar = fill.shares * fill.price;
        if (side == OrderSide::BUY) {
            portfolio.cash -= (trade_dollar + fill.commission);
            Position& pos = portfolio.positions[symbol];
            pos.symbol = symbol;
            double prev_shares = pos.shares;
            pos.shares += fill.shares;
            if (pos.shares > 1e-6) {
                pos.cost_basis = ((prev_shares * pos.cost_basis) + trade_dollar) / pos.shares;
            }
        } else {
            portfolio.cash += (trade_dollar - fill.commission);
            Position& pos = portfolio.positions[symbol];
            pos.symbol = symbol;
            pos.shares -= fill.shares;
        }

        portfolio.cumulative_commissions += fill.commission;
        all_fills.push_back(fill);
        return fill;
    }

    void apply_financing_and_borrow(const std::unordered_map<std::string, double>& current_prices) {
        // Daily borrow fee on short positions
        for (auto& [sym, pos] : portfolio.positions) {
            if (pos.is_short()) {
                auto it = current_prices.find(sym);
                double p = (it != current_prices.end()) ? it->second : pos.cost_basis;
                double short_notional = std::abs(pos.shares * p);
                double fee = costs.compute_daily_borrow_drag(short_notional);
                pos.cumulative_borrow_fees += fee;
                portfolio.cumulative_borrow_costs += fee;
                portfolio.cash -= fee;
            }
        }

        // Daily debit financing on negative cash balance
        if (portfolio.cash < 0.0) {
            double margin_charge = costs.compute_daily_margin_financing(portfolio.cash);
            portfolio.cash -= margin_charge;
        }
    }
};

} // namespace quantalpha
