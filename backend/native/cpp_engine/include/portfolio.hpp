#pragma once
#include <string>
#include <unordered_map>
#include "position.hpp"

namespace quantalpha {

struct Portfolio {
    double cash{100000.0};
    double cumulative_commissions{0.0};
    double cumulative_borrow_costs{0.0};
    std::unordered_map<std::string, Position> positions;

    double total_nav(const std::unordered_map<std::string, double>& current_prices) const {
        double pos_val = 0.0;
        for (const auto& [sym, pos] : positions) {
            auto it = current_prices.find(sym);
            double p = (it != current_prices.end()) ? it->second : pos.cost_basis;
            pos_val += pos.market_value(p);
        }
        return cash + pos_val;
    }

    double gross_exposure(const std::unordered_map<std::string, double>& current_prices) const {
        double exp = 0.0;
        for (const auto& [sym, pos] : positions) {
            auto it = current_prices.find(sym);
            double p = (it != current_prices.end()) ? it->second : pos.cost_basis;
            exp += std::abs(pos.market_value(p));
        }
        return exp;
    }
};

} // namespace quantalpha
