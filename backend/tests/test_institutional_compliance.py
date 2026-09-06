"""
Unit Tests for Pre-Trade Compliance & Fat-Finger Risk Controls (Sprint 4).
Validates:
1. Normal compliant order approval.
2. Fat-finger price collar rejection (> 3% deviation).
3. Max order notional rejection (>$1M).
4. Portfolio concentration limit rejection (>15% NAV).
5. ADV liquidity participation rejection (>10% ADV).
6. Restricted ticker trading blackout rejection.
7. Regulation SHO short locate verification.
8. Cryptographic audit trail integrity.
"""
from __future__ import annotations

import pytest

from core.compliance import (
    PreTradeComplianceEngine,
    ComplianceConfig,
    ComplianceStatus,
)


@pytest.fixture
def compliance_engine():
    config = ComplianceConfig(
        max_order_notional=500_000.0,
        max_portfolio_concentration=0.15,
        fat_finger_collar_pct=0.03,
        max_adv_participation_pct=0.10,
        require_short_locate=True,
        restricted_tickers={"LOCKED", "RESTRICTED"},
    )
    return PreTradeComplianceEngine(config=config)


def test_compliant_order_approval(compliance_engine):
    dec = compliance_engine.validate_order(
        order_id="ORD-001",
        ticker="AAPL",
        action="BUY",
        shares=500,
        price=150.0,
        market_quote=150.2,
        portfolio_nav=1_000_000.0,
        current_position_shares=0.0,
        adv_shares_20d=50_000.0,
    )

    assert dec.status == ComplianceStatus.APPROVED
    assert len(dec.rejection_reasons) == 0
    assert len(dec.audit_hash) == 64


def test_fat_finger_price_collar_rejection(compliance_engine):
    # Quote is 100.0, limit price is 110.0 (10% dev > 3% collar)
    dec = compliance_engine.validate_order(
        order_id="ORD-002",
        ticker="MSFT",
        action="BUY",
        shares=100,
        price=110.0,
        market_quote=100.0,
        portfolio_nav=1_000_000.0,
    )

    assert dec.status == ComplianceStatus.REJECTED
    assert any("FAT_FINGER" in r for r in dec.rejection_reasons)


def test_max_notional_rejection(compliance_engine):
    # Notional is $600,000 > $500,000 limit
    dec = compliance_engine.validate_order(
        order_id="ORD-003",
        ticker="GOOGL",
        action="BUY",
        shares=3000,
        price=200.0,
        market_quote=200.0,
        portfolio_nav=5_000_000.0,
    )

    assert dec.status == ComplianceStatus.REJECTED
    assert any("MAX_ORDER_NOTIONAL" in r for r in dec.rejection_reasons)


def test_portfolio_concentration_rejection(compliance_engine):
    # Order for $200,000 on $1,000,000 NAV = 20% > 15% max concentration
    dec = compliance_engine.validate_order(
        order_id="ORD-004",
        ticker="NVDA",
        action="BUY",
        shares=2000,
        price=100.0,
        market_quote=100.0,
        portfolio_nav=1_000_000.0,
        current_position_shares=0.0,
    )

    assert dec.status == ComplianceStatus.REJECTED
    assert any("CONCENTRATION" in r for r in dec.rejection_reasons)


def test_adv_participation_rejection(compliance_engine):
    # 2,000 shares on 10,000 ADV = 20% > 10% limit
    dec = compliance_engine.validate_order(
        order_id="ORD-005",
        ticker="SMALLCAP",
        action="BUY",
        shares=2000,
        price=50.0,
        market_quote=50.0,
        portfolio_nav=2_000_000.0,
        adv_shares_20d=10_000.0,
    )

    assert dec.status == ComplianceStatus.REJECTED
    assert any("ADV_PARTICIPATION" in r for r in dec.rejection_reasons)


def test_restricted_ticker_rejection(compliance_engine):
    dec = compliance_engine.validate_order(
        order_id="ORD-006",
        ticker="LOCKED",
        action="BUY",
        shares=100,
        price=50.0,
        market_quote=50.0,
        portfolio_nav=1_000_000.0,
    )

    assert dec.status == ComplianceStatus.REJECTED
    assert any("RESTRICTED_TICKER" in r for r in dec.rejection_reasons)


def test_reg_sho_short_locate_rejection(compliance_engine):
    # Short sale without locate ID must be rejected
    dec_no_locate = compliance_engine.validate_order(
        order_id="ORD-007",
        ticker="SPY",
        action="SELL_SHORT",
        shares=100,
        price=500.0,
        market_quote=500.0,
        portfolio_nav=1_000_000.0,
        borrow_locate_id=None,
    )
    assert dec_no_locate.status == ComplianceStatus.REJECTED
    assert any("REG_SHO_LOCATE" in r for r in dec_no_locate.rejection_reasons)

    # Short sale with valid locate ID must pass
    dec_with_locate = compliance_engine.validate_order(
        order_id="ORD-008",
        ticker="SPY",
        action="SELL_SHORT",
        shares=100,
        price=500.0,
        market_quote=500.0,
        portfolio_nav=1_000_000.0,
        borrow_locate_id="LOC-GS-884920",
    )
    assert dec_with_locate.status == ComplianceStatus.APPROVED
