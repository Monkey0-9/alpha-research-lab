"""
Historical Universe Membership Engine.
Manages point-in-time constituent membership to eliminate survivorship bias.
Never uses static current-day ticker lists for historical backtesting.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Set
import pandas as pd
from core.security_master.master import security_master

logger = logging.getLogger(__name__)


@dataclass
class UniverseMembership:
    universe_id: str         # "SP500", "NASDAQ100", "RUSSELL2000"
    security_id: str         # Permanent security identifier
    effective_from: str      # YYYY-MM-DD
    effective_to: Optional[str] = None  # None if currently active
    source: str = "Standard & Poor's Indices"


class UniverseEngine:
    """Manages historical universe constituent timelines."""

    def __init__(self):
        self._memberships: List[UniverseMembership] = []
        self._bootstrap_sp500_history()

    def _bootstrap_sp500_history(self) -> None:
        """Seed universe with historical additions, removals, and delistings."""
        # Core continuous members
        continuous_secs = [
            "SEC-US-AAPL-001", "SEC-US-MSFT-001", "SEC-US-AMZN-001",
            "SEC-US-NVDA-001", "SEC-US-JPM-001", "SEC-US-XOM-001", "SEC-US-UNH-001"
        ]
        for sid in continuous_secs:
            self._memberships.append(UniverseMembership(
                universe_id="SP500",
                security_id=sid,
                effective_from="2010-01-01",
                effective_to=None
            ))

        # Alphabet added 2006-04-03
        self._memberships.append(UniverseMembership(
            universe_id="SP500",
            security_id="SEC-US-GOOGL-001",
            effective_from="2006-04-03",
            effective_to=None
        ))

        # Meta (Facebook) added 2013-12-23
        self._memberships.append(UniverseMembership(
            universe_id="SP500",
            security_id="SEC-US-META-001",
            effective_from="2013-12-23",
            effective_to=None
        ))

        # Tesla added 2020-12-21
        self._memberships.append(UniverseMembership(
            universe_id="SP500",
            security_id="SEC-US-TSLA-001",
            effective_from="2020-12-21",
            effective_to=None
        ))

        # Xerox (XRX) removed from S&P 500 on 2021-03-22
        self._memberships.append(UniverseMembership(
            universe_id="SP500",
            security_id="SEC-US-XRX-001",
            effective_from="2010-01-01",
            effective_to="2021-03-22"
        ))

    def add_membership(self, membership: UniverseMembership) -> None:
        self._memberships.append(membership)

    def get_members(self, universe_id: str, as_of_date: str) -> List[str]:
        """
        Return permanent security_ids that were members of universe_id strictly on as_of_date.
        """
        target_dt = pd.Timestamp(as_of_date)
        active_ids: Set[str] = set()

        for m in self._memberships:
            if m.universe_id != universe_id:
                continue
            s_dt = pd.Timestamp(m.effective_from)
            e_dt = pd.Timestamp(m.effective_to) if m.effective_to else pd.Timestamp.max

            if s_dt <= target_dt <= e_dt:
                active_ids.add(m.security_id)

        return sorted(list(active_ids))

    def get_active_tickers(self, universe_id: str, as_of_date: str) -> List[str]:
        """
        Return the historical tickers corresponding to active members on as_of_date.
        """
        sec_ids = self.get_members(universe_id, as_of_date)
        tickers = []
        for sid in sec_ids:
            sec = security_master.get_security(sid)
            if sec:
                tickers.append(sec.get_ticker_as_of(as_of_date))
        return sorted(tickers)


universe_engine = UniverseEngine()
