"""
Delistings & Survivorship Bias Prevention.
Tracks delisting reasons, final terminal payouts, and involuntary liquidations.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, Any


class DelistingReason(str, enum.Enum):
    BANKRUPTCY = "BANKRUPTCY"
    MERGER_CASH = "MERGER_CASH"
    MERGER_STOCK = "MERGER_STOCK"
    REGULATORY_DELISTING = "REGULATORY_DELISTING"
    PRIVATIZATION = "PRIVATIZATION"
    LIQUIDATION = "LIQUIDATION"


@dataclass
class DelistingEvent:
    event_id: str
    security_id: str
    effective_date: str  # YYYY-MM-DD
    reason: DelistingReason
    final_terminal_price: float = 0.0
    cash_distribution_per_share: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
