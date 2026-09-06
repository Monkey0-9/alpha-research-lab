#pragma once
#include <string>
#include <cstdint>

namespace quantalpha {

enum class OrderSide {
    BUY,
    SELL
};

enum class OrderType {
    MARKET,
    LIMIT
};

enum class OrderStatus {
    PENDING,
    PARTIALLY_FILLED,
    FILLED,
    CANCELLED,
    REJECTED
};

struct Order {
    int64_t order_id;
    std::string symbol;
    OrderSide side;
    OrderType type;
    double quantity;
    double filled_quantity{0.0};
    double limit_price{0.0};
    OrderStatus status{OrderStatus::PENDING};
    int64_t created_time_ns{0};

    bool is_active() const {
        return status == OrderStatus::PENDING || status == OrderStatus::PARTIALLY_FILLED;
    }

    double remaining_quantity() const {
        return quantity - filled_quantity;
    }
};

} // namespace quantalpha
