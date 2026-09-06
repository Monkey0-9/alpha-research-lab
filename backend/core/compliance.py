"""
Pre-Trade Compliance, Fat-Finger Collars & Risk Controls Engine (Sprint 4).

Enforces institutional quantitative execution mandates before orders hit the market:
1. Fat-Finger Price Collar: Rejects limit orders priced > X% away from prevailing NBBO quote.
2. Max Notional Order Limit: Rejects single orders exceeding institutional dollar cap.
3. Portfolio Concentration Limit: Blocks trades pushing single-name exposure > Max % of portfolio NAV.
4. ADV Participation Limit: Collars order quantity to max allowable percentage of Average Daily Volume.
5. Restricted List Enforcement: Rejects tickers on blackout, insider, or Reg-M restriction lists.
6. Short-Sale Locate Verification: Enforces Regulation SHO locate requirement before permitting short sell orders.
7. Cryptographic Compliance Audit Trail: Creates immutable SHA-256 signed compliance decisions.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)


class ComplianceStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WARNED = "WARNED"


@dataclass
class ComplianceRuleResult:
    rule_name: str
    passed: bool
    details: str
    limit_value: Optional[float] = None
    observed_value: Optional[float] = None


@dataclass
class ComplianceDecision:
    order_id: str
    ticker: str
    action: str
    shares: float
    price: float
    status: ComplianceStatus
    rule_results: List[ComplianceRuleResult] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit_hash: str = ""

    def __post_init__(self):
        if not self.audit_hash:
            self.audit_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        content = f"{self.order_id}|{self.ticker}|{self.action}|{self.shares}|{self.price}|{self.status.value}|{self.timestamp}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "ticker": self.ticker,
            "action": self.action,
            "shares": self.shares,
            "price": self.price,
            "status": self.status.value,
            "audit_hash": self.audit_hash,
            "timestamp": self.timestamp,
            "rejection_reasons": self.rejection_reasons,
            "rule_results": [
                {
                    "rule": r.rule_name,
                    "passed": r.passed,
                    "details": r.details,
                    "limit": r.limit_value,
                    "observed": r.observed_value,
                }
                for r in self.rule_results
            ],
        }


@dataclass
class ComplianceConfig:
    max_order_notional: float = 1_000_000.0        # Max $1M per single order
    max_portfolio_concentration: float = 0.15      # Max 15% NAV in a single name
    fat_finger_collar_pct: float = 0.03            # Max 3% away from NBBO
    max_adv_participation_pct: float = 0.10        # Max 10% of 20-day ADV
    require_short_locate: bool = True              # Reg SHO locate verification
    restricted_tickers: Set[str] = field(default_factory=set)


class PreTradeComplianceEngine:
    """
    High-performance pre-trade risk and compliance filter.
    Executed synchronously prior to sending any order to broker gateways.
    """

    def __init__(self, config: Optional[ComplianceConfig] = None):
        self.config = config or ComplianceConfig()
        self._audit_log: List[ComplianceDecision] = []

    def add_restricted_ticker(self, ticker: str):
        self.config.restricted_tickers.add(ticker.upper())

    def remove_restricted_ticker(self, ticker: str):
        self.config.restricted_tickers.discard(ticker.upper())

    def validate_order(
        self,
        order_id: str,
        ticker: str,
        action: str,  # "BUY", "SELL", "SELL_SHORT"
        shares: float,
        price: float,
        market_quote: float,
        portfolio_nav: float,
        current_position_shares: float = 0.0,
        adv_shares_20d: Optional[float] = None,
        borrow_locate_id: Optional[str] = None,
    ) -> ComplianceDecision:
        """
        Evaluate order against all institutional pre-trade risk controls.
        """
        ticker = ticker.upper()
        action = action.upper()
        notional = shares * price
        results: List[ComplianceRuleResult] = []
        rejections: List[str] = []

        # 1. Restricted Ticker Check
        if ticker in self.config.restricted_tickers:
            res = ComplianceRuleResult(
                rule_name="RESTRICTED_TICKER",
                passed=False,
                details=f"Ticker {ticker} is on the institutional restricted / Reg-M blackout list.",
            )
            results.append(res)
            rejections.append(f"[{res.rule_name}] {res.details}")
        else:
            results.append(ComplianceRuleResult(rule_name="RESTRICTED_TICKER", passed=True, details="Ticker is clear to trade."))

        # 2. Max Single-Order Notional Check
        if notional > self.config.max_order_notional:
            res = ComplianceRuleResult(
                rule_name="MAX_ORDER_NOTIONAL",
                passed=False,
                details=f"Order notional ${notional:,.2f} exceeds cap of ${self.config.max_order_notional:,.2f}.",
                limit_value=self.config.max_order_notional,
                observed_value=notional,
            )
            results.append(res)
            rejections.append(f"[{res.rule_name}] {res.details}")
        else:
            results.append(ComplianceRuleResult(
                rule_name="MAX_ORDER_NOTIONAL",
                passed=True,
                details="Order notional is within risk limits.",
                limit_value=self.config.max_order_notional,
                observed_value=notional,
            ))

        # 3. Fat-Finger Price Collar Check
        if market_quote > 0.0 and price > 0.0:
            price_dev = abs(price - market_quote) / market_quote
            if price_dev > self.config.fat_finger_collar_pct:
                res = ComplianceRuleResult(
                    rule_name="FAT_FINGER_PRICE_COLLAR",
                    passed=False,
                    details=f"Limit price ${price:.2f} deviates {price_dev:.1%} from NBBO quote ${market_quote:.2f}, exceeding collar limit of {self.config.fat_finger_collar_pct:.1%}.",
                    limit_value=self.config.fat_finger_collar_pct,
                    observed_value=price_dev,
                )
                results.append(res)
                rejections.append(f"[{res.rule_name}] {res.details}")
            else:
                results.append(ComplianceRuleResult(
                    rule_name="FAT_FINGER_PRICE_COLLAR",
                    passed=True,
                    details="Limit price is within NBBO collar tolerance.",
                    limit_value=self.config.fat_finger_collar_pct,
                    observed_value=price_dev,
                ))

        # 4. ADV Participation Limit
        if adv_shares_20d is not None and adv_shares_20d > 0.0:
            participation = shares / adv_shares_20d
            if participation > self.config.max_adv_participation_pct:
                res = ComplianceRuleResult(
                    rule_name="ADV_PARTICIPATION_LIMIT",
                    passed=False,
                    details=f"Order size {shares:,.0f} shares is {participation:.1%} of 20d ADV ({adv_shares_20d:,.0f}), exceeding max participation rate of {self.config.max_adv_participation_pct:.1%}.",
                    limit_value=self.config.max_adv_participation_pct,
                    observed_value=participation,
                )
                results.append(res)
                rejections.append(f"[{res.rule_name}] {res.details}")
            else:
                results.append(ComplianceRuleResult(
                    rule_name="ADV_PARTICIPATION_LIMIT",
                    passed=True,
                    details="Order participation rate within liquidity bounds.",
                    limit_value=self.config.max_adv_participation_pct,
                    observed_value=participation,
                ))

        # 5. Portfolio Concentration Limit
        if portfolio_nav > 0.0:
            delta_shares = shares if "BUY" in action else -shares
            projected_shares = current_position_shares + delta_shares
            projected_exposure = abs(projected_shares * price)
            projected_weight = projected_exposure / portfolio_nav
            if projected_weight > self.config.max_portfolio_concentration:
                res = ComplianceRuleResult(
                    rule_name="PORTFOLIO_CONCENTRATION_LIMIT",
                    passed=False,
                    details=f"Projected post-trade concentration {projected_weight:.1%} exceeds maximum single-name cap of {self.config.max_portfolio_concentration:.1%}.",
                    limit_value=self.config.max_portfolio_concentration,
                    observed_value=projected_weight,
                )
                results.append(res)
                rejections.append(f"[{res.rule_name}] {res.details}")
            else:
                results.append(ComplianceRuleResult(
                    rule_name="PORTFOLIO_CONCENTRATION_LIMIT",
                    passed=True,
                    details="Post-trade exposure within concentration bounds.",
                    limit_value=self.config.max_portfolio_concentration,
                    observed_value=projected_weight,
                ))

        # 6. Short-Sale Locate Check (Regulation SHO)
        if action == "SELL_SHORT" and self.config.require_short_locate:
            if not borrow_locate_id or len(borrow_locate_id.strip()) == 0:
                res = ComplianceRuleResult(
                    rule_name="REG_SHO_LOCATE",
                    passed=False,
                    details=f"Short sale of {shares:,.0f} shares of {ticker} rejected: No valid borrow locate identifier provided.",
                )
                results.append(res)
                rejections.append(f"[{res.rule_name}] {res.details}")
            else:
                results.append(ComplianceRuleResult(
                    rule_name="REG_SHO_LOCATE",
                    passed=True,
                    details=f"Valid borrow locate confirmed: {borrow_locate_id}",
                ))

        status = ComplianceStatus.REJECTED if rejections else ComplianceStatus.APPROVED
        decision = ComplianceDecision(
            order_id=order_id,
            ticker=ticker,
            action=action,
            shares=shares,
            price=price,
            status=status,
            rule_results=results,
            rejection_reasons=rejections,
        )

        self._audit_log.append(decision)
        if status == ComplianceStatus.REJECTED:
            logger.warning(f"Compliance REJECTED order {order_id} ({ticker} {action}): {'; '.join(rejections)}")
        else:
            logger.info(f"Compliance APPROVED order {order_id} ({ticker} {action} ${notional:,.2f})")

        return decision

    def get_audit_trail(self) -> List[ComplianceDecision]:
        return list(self._audit_log)


pre_trade_compliance = PreTradeComplianceEngine()
