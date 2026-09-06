"""
Security Master & Corporate Actions Data Models.
Assigns permanent unique security identifiers (security_id) to eliminate ticker collision & survivorship bias.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd


class AssetClass(str, enum.Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    FUTURE = "FUTURE"
    FX = "FX"


class ActionType(str, enum.Enum):
    SPLIT = "SPLIT"
    DIVIDEND = "DIVIDEND"
    SPINOFF = "SPINOFF"
    SYMBOL_CHANGE = "SYMBOL_CHANGE"
    DELISTING = "DELISTING"


class PriceSeriesType(str, enum.Enum):
    RAW_PRICE = "RAW_PRICE"
    SPLIT_ADJUSTED = "SPLIT_ADJUSTED"
    TOTAL_RETURN = "TOTAL_RETURN"
    TRADEABLE_PRICE = "TRADEABLE_PRICE"


@dataclass
class CorporateAction:
    action_id: str
    security_id: str
    action_type: ActionType
    effective_date: str  # YYYY-MM-DD
    ratio: float = 1.0   # For splits (e.g. 4.0 for 4-for-1 split, 0.25 for reverse)
    cash_amount: float = 0.0  # For dividends (e.g. $0.24 per share)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Security:
    security_id: str          # Permanent immutable ID (e.g. SEC-US-AAPL-001)
    ticker: str               # Current primary symbol
    name: str                 # Legal entity name
    exchange: str             # NASDAQ, NYSE, etc.
    figi: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    isin: Optional[str] = None
    country: str = "US"
    currency: str = "USD"
    asset_class: AssetClass = AssetClass.EQUITY
    is_active: bool = True
    delisting_date: Optional[str] = None
    ticker_history: List[Tuple[str, str, Optional[str]]] = field(
        default_factory=list)  # [(ticker, start_date, end_date)]
    corporate_actions: List[CorporateAction] = field(default_factory=list)

    def get_ticker_as_of(self, as_of_date: str) -> str:
        """Resolve ticker as it was known on a specific historical date."""
        target_dt = pd.Timestamp(as_of_date)
        for sym, start, end in self.ticker_history:
            s_dt = pd.Timestamp(start) if start else pd.Timestamp.min
            e_dt = pd.Timestamp(end) if end else pd.Timestamp.max
            if s_dt <= target_dt <= e_dt:
                return sym
        return self.ticker
