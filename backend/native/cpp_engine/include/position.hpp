#pragma once
#include <string>
#include <cmath>

namespace quantalpha {

struct Position {
    std::string symbol;
    double shares{0.0};
    double cost_basis{0.0};
    double realized_pnl{0.0};
    double cumulative_borrow_fees{0.0};

    bool is_short() const {
        return shares < -1e-6;
    }
    bool is_long() const {
        return shares > 1e-6;
    }
    bool is_flat() const {
        return std::abs(shares) <= 1e-6;
    }
    double market_value(double current_price) const {
        return shares * current_price;
    }
    double unrealized_pnl(double current_price) const {
        if (is_flat()) return 0.0;
        return (current_price - cost_basis) * shares;
    }
};

} // namespace quantalpha
