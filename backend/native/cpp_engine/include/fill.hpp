#pragma once
#include <string>
#include <cstdint>

namespace quantalpha {

struct Fill {
    int64_t fill_id;
    int64_t order_id;
    std::string symbol;
    double price;
    double shares;
    double commission;
    double slippage_bps;
    int64_t timestamp_ns;
};

} // namespace quantalpha
