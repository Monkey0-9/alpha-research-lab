"""
Historical Listings & Primary Exchange Transitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ListingEvent:
    event_id: str
    security_id: str
    ticker: str
    exchange: str
    effective_date: str  # YYYY-MM-DD
    details: Dict[str, Any] = field(default_factory=dict)
