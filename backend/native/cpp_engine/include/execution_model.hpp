#pragma once
#include <algorithm>
#include <cmath>
#include "order.hpp"
#include "market_event.hpp"
#include "fill.hpp"

namespace quantalpha {

class ExecutionModel {
public:
    double max_adv_participation{0.15}; // max 15% of bar volume
    double half_spread_bps{5.0};
    double impact_coefficient{0.35};    // non-linear Almgren-Chriss impact

    Fill execute_order(
        int64_t fill_id,
        Order& order,
        const MarketEvent& event,
        double commission_bps = 5.0
    ) const {
        double max_shares = event.volume * max_adv_participation;
        double requested = order.remaining_quantity();
        double fill_shares = std::min(requested, std::max(0.0, max_shares));
        if (order.type == OrderType::MARKET && fill_shares <= 0.0 && event.volume > 0.0) {
            fill_shares = std::min(requested, event.volume * 0.01);
        }

        // Almgren-Chriss non-linear square-root market impact:
        // Impact = half_spread + gamma * sqrt(order_volume / bar_volume)
        double participation = (event.volume > 0.0) ? (fill_shares / event.volume) : 0.0;
        double impact_bps = half_spread_bps + (impact_coefficient * std::sqrt(participation) * 10000.0);

        double base_price = (event.last_price > 0.0) ? event.last_price : ((event.bid_price + event.ask_price) * 0.5);
        double fill_price = (order.side == OrderSide::BUY) 
            ? (base_price * (1.0 + impact_bps / 10000.0))
            : (base_price * (1.0 - impact_bps / 10000.0));

        double trade_notional = fill_shares * fill_price;
        double commission = trade_notional * (commission_bps / 10000.0);

        order.filled_quantity += fill_shares;
        if (order.remaining_quantity() <= 1e-6) {
            order.status = OrderStatus::FILLED;
        } else {
            order.status = OrderStatus::PARTIALLY_FILLED;
        }

        return Fill{
            fill_id,
            order.order_id,
            order.symbol,
            fill_price,
            fill_shares,
            commission,
            impact_bps,
            event.timestamp_ns
        };
    }
};

} // namespace quantalpha
