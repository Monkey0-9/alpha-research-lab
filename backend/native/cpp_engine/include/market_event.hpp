#pragma once
#include <string>
#include <cstdint>

namespace quantalpha {

struct MarketEvent {
    int64_t timestamp_ns;
    std::string symbol;
    double bid_price;
    double ask_price;
    double last_price;
    double volume;

    double spread_bps() const {
        if (last_price <= 0.0) return 0.0;
        return ((ask_price - bid_price) / last_price) * 10000.0;
    }
};

} // namespace quantalpha
