"""
Institutional Verification Tests for OMS, EMS, and TCA Engine.
Verifies:
1. Order state machine and terminal state immutability.
2. Pre-trade risk limit enforcement (Notional, ADV %, Price collars).
3. Algorithmic execution slicing (TWAP, VWAP, Almgren-Chriss).
4. Implementation Shortfall TCA decomposition (Delay vs Slippage).
"""
import pytest
from backend.core.oms_ems import (
    ExecutionManagementSystem,
    InvalidOrderStateTransition,
    OrderManagementSystem,
    OrderSide,
    OrderStatus,
    OrderType,
    PreTradeRiskFilter,
    PreTradeRiskViolation,
    TransactionCostAnalysis,
)


def test_oms_order_lifecycle():
    oms = OrderManagementSystem()
    order = oms.create_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1000.0,
        price=150.0
    )
    assert order.status == OrderStatus.NEW
    assert order.leaves_quantity == 1000.0

    # Valid transitions
    oms.transition(order.order_id, OrderStatus.PENDING_NEW)
    oms.transition(order.order_id, OrderStatus.SUBMITTED)

    # 1st Partial Fill: 400 shares @ $150.10
    oms.apply_fill(order.order_id, fill_qty=400.0, fill_price=150.10)
    assert order.status == OrderStatus.PARTIALLY_FILLED
    assert order.filled_quantity == 400.0
    assert order.leaves_quantity == 600.0
    assert round(order.avg_fill_price, 2) == 150.10

    # 2nd Fill: remaining 600 shares @ $150.30
    oms.apply_fill(order.order_id, fill_qty=600.0, fill_price=150.30)
    assert order.status == OrderStatus.FILLED
    assert order.filled_quantity == 1000.0
    assert order.leaves_quantity == 0.0
    # Expected VWAP: (400*150.10 + 600*150.30) / 1000 = 150.22
    assert round(order.avg_fill_price, 2) == 150.22

    # Terminal state rejection: Cannot transition filled order to NEW or CANCELLED
    with pytest.raises(InvalidOrderStateTransition):
        oms.transition(order.order_id, OrderStatus.CANCELLED)


def test_oms_illegal_fill_transitions():
    oms = OrderManagementSystem()
    order = oms.create_order("MSFT", OrderSide.SELL, OrderType.MARKET, quantity=500.0)

    # Attempting to fill in NEW status directly must fail
    with pytest.raises(InvalidOrderStateTransition):
        oms.apply_fill(order.order_id, 100.0, 300.0)

    # Transition to rejected
    oms.transition(order.order_id, OrderStatus.REJECTED, reason="Pre-trade risk failed")
    with pytest.raises(InvalidOrderStateTransition):
        oms.transition(order.order_id, OrderStatus.SUBMITTED)


def test_pre_trade_risk_limits():
    risk = PreTradeRiskFilter(
        max_order_notional=500_000.0,
        max_adv_pct=0.05,  # 5% max ADV
        price_collar_pct=0.03  # 3% max price deviation
    )
    oms = OrderManagementSystem()

    # 1. Notional limit violation
    large_order = oms.create_order("NVDA", OrderSide.BUY, OrderType.LIMIT, quantity=5000.0, price=120.0)
    # Notional = 5000 * 120 = $600,000 > $500,000
    with pytest.raises(PreTradeRiskViolation, match="exceeds max allowed"):
        risk.validate(large_order, reference_price=120.0, adv=1_000_000.0)

    # 2. ADV participation violation
    illiquid_order = oms.create_order("SMALL", OrderSide.BUY, OrderType.MARKET, quantity=10_000.0)
    # ADV = 100,000 -> 10,000 is 10% > 5% allowed
    with pytest.raises(PreTradeRiskViolation, match="exceeding 5.0%"):
        risk.validate(illiquid_order, reference_price=10.0, adv=100_000.0)

    # 3. Fat-finger price collar violation
    collar_order = oms.create_order("TSLA", OrderSide.BUY, OrderType.LIMIT, quantity=100.0, price=220.0)
    # Reference is $200.0, price is $220.0 (+10% deviation > 3% collar)
    with pytest.raises(PreTradeRiskViolation, match="exceeding collar threshold"):
        risk.validate(collar_order, reference_price=200.0, adv=500_000.0)


def test_ems_algorithmic_slicing():
    oms = OrderManagementSystem()
    order = oms.create_order("AAPL", OrderSide.BUY, OrderType.TWAP, quantity=10_000.0)

    # 1. TWAP: 5 equal slices
    twap_slices = ExecutionManagementSystem.slice_twap(order, num_slices=5)
    assert len(twap_slices) == 5
    assert all(s == 2000.0 for s in twap_slices)
    assert sum(twap_slices) == 10_000.0

    # 2. VWAP: U-shaped intraday profile
    profile = [0.30, 0.15, 0.10, 0.15, 0.30]
    vwap_slices = ExecutionManagementSystem.slice_vwap(order, profile)
    assert len(vwap_slices) == 5
    assert round(sum(vwap_slices), 4) == 10_000.0
    assert vwap_slices[0] == 3000.0
    assert vwap_slices[2] == 1000.0

    # 3. Almgren-Chriss: Optimal trajectory
    ac_slices = ExecutionManagementSystem.slice_almgren_chriss(
        total_quantity=10_000.0,
        num_intervals=5,
        daily_volatility=0.02,
        daily_volume=1_000_000.0,
        risk_aversion=1e-4
    )
    assert len(ac_slices) == 5
    assert round(sum(ac_slices), 4) == 10_000.0
    # Almgren-Chriss should execute more aggressively upfront to reduce variance risk
    assert ac_slices[0] > ac_slices[-1]


def test_transaction_cost_analysis_implementation_shortfall():
    # Target decided at $100.00
    # Reached market at $100.20 (Delay = +20 bps)
    # Executed in 2 tranches:
    # 500 @ $100.30, 500 @ $100.50 -> VWAP = $100.40 (Trading cost = +20 bps)
    tca = TransactionCostAnalysis.compute(
        side=OrderSide.BUY,
        decision_price=100.00,
        arrival_price=100.20,
        fills=[(500.0, 100.30), (500.0, 100.50)]
    )

    assert tca.execution_vwap == 100.40
    # Delay cost = (100.20 - 100.00)/100.00 * 10000 = +20.0 bps
    assert tca.delay_cost_bps == 20.0
    # Trading cost = (100.40 - 100.20)/100.00 * 10000 = +20.0 bps
    assert tca.trading_cost_bps == 20.0
    # Total IS = 40.0 bps
    assert tca.total_is_bps == 40.0


def test_oms_exhaustive_invalid_state_transitions():
    oms = OrderManagementSystem()
    order = oms.create_order("AAPL", OrderSide.BUY, OrderType.MARKET, quantity=100.0)

    # 1. From NEW, cannot transition directly to FILLED, PARTIALLY_FILLED, CANCELLED, EXPIRED
    for invalid_target in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED,
                           OrderStatus.CANCELLED, OrderStatus.EXPIRED]:
        with pytest.raises(InvalidOrderStateTransition):
            oms.transition(order.order_id, invalid_target)

    # 2. Advance to terminal state REJECTED
    oms.transition(order.order_id, OrderStatus.REJECTED)

    # Terminal state cannot transition anywhere
    for any_state in OrderStatus:
        with pytest.raises(InvalidOrderStateTransition):
            oms.transition(order.order_id, any_state)


def test_oms_overfill_and_negative_fill_defense():
    oms = OrderManagementSystem()
    order = oms.create_order("GOOGL", OrderSide.BUY, OrderType.LIMIT, quantity=100.0, price=150.0)
    oms.transition(order.order_id, OrderStatus.PENDING_NEW)
    oms.transition(order.order_id, OrderStatus.SUBMITTED)

    # Negative fill rejection
    with pytest.raises(ValueError, match="positive"):
        oms.apply_fill(order.order_id, fill_qty=-10.0, fill_price=150.0)

    # Zero fill rejection
    with pytest.raises(ValueError, match="positive"):
        oms.apply_fill(order.order_id, fill_qty=0.0, fill_price=150.0)

    # Overfill rejection (101 shares > 100 shares leaves)
    with pytest.raises(ValueError, match="exceeds leaves quantity"):
        oms.apply_fill(order.order_id, fill_qty=100.01, fill_price=150.0)

    # Valid partial fill
    oms.apply_fill(order.order_id, fill_qty=50.0, fill_price=150.0)

    # Attempting to fill remaining with 51 shares > 50 shares leaves
    with pytest.raises(ValueError, match="exceeds leaves quantity"):
        oms.apply_fill(order.order_id, fill_qty=50.1, fill_price=150.0)


def test_oms_duplicate_client_order_id_defense():
    oms = OrderManagementSystem()
    oms.create_order("MSFT", OrderSide.BUY, OrderType.MARKET, quantity=10.0, client_order_id="CL-UNIQUE-001")
    with pytest.raises(ValueError, match="Duplicate client order ID"):
        oms.create_order("MSFT", OrderSide.SELL, OrderType.MARKET, quantity=5.0, client_order_id="CL-UNIQUE-001")


def test_pre_trade_risk_boundary_precision():
    risk = PreTradeRiskFilter(max_order_notional=100_000.0, max_adv_pct=0.10, price_collar_pct=0.05)
    oms = OrderManagementSystem()

    # Exact threshold: 1,000 shares @ $100.00 = $100,000 (Allowed)
    exact_order = oms.create_order("XYZ", OrderSide.BUY, OrderType.LIMIT, quantity=1000.0, price=100.0)
    risk.validate(exact_order, reference_price=100.0, adv=1_000_000.0)

    # $0.01 over threshold: 1,000 shares @ $100.01 = $100,010 (Breached)
    oms_over = OrderManagementSystem()
    over_order = oms_over.create_order("XYZ", OrderSide.BUY, OrderType.LIMIT, quantity=1000.0, price=100.01)
    with pytest.raises(PreTradeRiskViolation, match="exceeds max allowed"):
        risk.validate(over_order, reference_price=100.0, adv=1_000_000.0)


def test_ems_almgren_chriss_risk_aversion_monotonicity():
    # Risk-neutral (low lambda) should have flatter schedule than high lambda (risk-averse)
    flat_schedule = ExecutionManagementSystem.slice_almgren_chriss(
        total_quantity=10_000.0, num_intervals=10, daily_volatility=0.01,
        daily_volume=1_000_000.0, risk_aversion=1e-8
    )
    front_loaded_schedule = ExecutionManagementSystem.slice_almgren_chriss(
        total_quantity=10_000.0, num_intervals=10, daily_volatility=0.03,
        daily_volume=1_000_000.0, risk_aversion=1e-2
    )
    # Conservation of mass
    assert round(sum(flat_schedule), 2) == 10_000.0
    assert round(sum(front_loaded_schedule), 2) == 10_000.0

    # High risk aversion trades significantly more in the first bucket than low risk aversion
    assert front_loaded_schedule[0] > flat_schedule[0]
    # Ratio of first bucket to last bucket is much higher under high risk aversion
    ratio_high_lambda = front_loaded_schedule[0] / front_loaded_schedule[-1]
    ratio_low_lambda = flat_schedule[0] / flat_schedule[-1]
    assert ratio_high_lambda > ratio_low_lambda


def test_transaction_cost_analysis_sell_side_shortfall():
    # SELL order: Decision at $100.00
    # Market drops before arrival: $99.80 (Delay cost = 20 bps)
    # Market drops further during execution: Executed at $99.50 (Trading cost = 30 bps)
    tca = TransactionCostAnalysis.compute(
        side=OrderSide.SELL,
        decision_price=100.00,
        arrival_price=99.80,
        fills=[(100.0, 99.50)]
    )
    # Both delay and trading costs are positive penalties to alpha
    assert tca.delay_cost_bps == 20.0
    assert tca.trading_cost_bps == 30.0
    assert tca.total_is_bps == 50.0
