"""
Institutional Security Master Entities.
Defines permanent security entities, identifier schemes, and 6-dimension universal temporal model.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class AssetClass(str, enum.Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    FUTURE = "FUTURE"
    FX = "FX"


@dataclass
class UniversalTemporalStamp:
    """
    6-Dimension Temporal Model.
    Prevents lookahead, revision, and availability leakage.
    """
    event_time: str          # Time transaction/event physically took place
    effective_time: str      # Time corporate/accounting event takes financial effect
    publication_time: str    # Time data vendor or filing was published
    available_time: str      # Earliest time data was accessible to quant models
    revision_time: str       # Time record was revised or restated
    ingestion_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, str]:
        return {
            "event_time": self.event_time,
            "effective_time": self.effective_time,
            "publication_time": self.publication_time,
            "available_time": self.available_time,
            "revision_time": self.revision_time,
            "ingestion_time": self.ingestion_time,
        }


@dataclass
class SecurityEntity:
    """
    Permanent Institutional Security Entity.
    Identifies a company or instrument across corporate changes, renames, and delistings.
    """
    security_id: str             # Permanent internal ID (e.g. SEC-US-AAPL-001)
    figi: Optional[str] = None   # Financial Instrument Global Identifier
    isin: Optional[str] = None   # International Securities Identification Number
    cusip: Optional[str] = None  # Committee on Uniform Securities Identification Procedures
    permno: Optional[str] = None  # CRSP Permanent Identifier
    ticker: str = ""             # Current primary ticker
    exchange: str = "US"
    currency: str = "USD"
    asset_class: AssetClass = AssetClass.EQUITY
    listing_date: Optional[str] = None    # YYYY-MM-DD
    delisting_date: Optional[str] = None  # YYYY-MM-DD
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_listed_on(self, as_of_date: str) -> bool:
        """Check whether the security was legally listed and trading on as_of_date."""
        if self.listing_date and as_of_date < self.listing_date:
            return False
        if self.delisting_date and as_of_date > self.delisting_date:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        ac_str = self.asset_class.value if isinstance(self.asset_class, AssetClass) else str(self.asset_class)
        return {
            "security_id": self.security_id,
            "figi": self.figi,
            "isin": self.isin,
            "cusip": self.cusip,
            "permno": self.permno,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "currency": self.currency,
            "asset_class": ac_str,
            "listing_date": self.listing_date,
            "delisting_date": self.delisting_date,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }
