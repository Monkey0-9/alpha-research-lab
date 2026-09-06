#pragma once
#include <cmath>

namespace quantalpha {

struct CostSchedule {
    double commission_bps{5.0};
    double borrow_cost_annual_bps{150.0}; // 1.5% annual borrow for short positions
    double sec_fee_bps{0.22};              // SEC transaction fee on sales
    double financing_rate_annual_bps{300.0};// 3.0% margin financing rate on debit cash

    double compute_daily_borrow_drag(double short_notional) const {
        return short_notional * (borrow_cost_annual_bps / 10000.0) / 252.0;
    }

    double compute_daily_margin_financing(double cash_balance) const {
        if (cash_balance >= 0.0) return 0.0;
        return std::abs(cash_balance) * (financing_rate_annual_bps / 10000.0) / 252.0;
    }
};

} // namespace quantalpha
