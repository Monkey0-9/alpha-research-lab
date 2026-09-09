"""
Point-In-Time Historical Universe Engine.
Prevents survivorship bias by strictly tracking index/universe membership intervals.
Guarantees that 2026 constituents cannot be backtested in 2015 without having been in the index then.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Set, Optional


@dataclass
class UniverseMembership:
    """Historical membership interval for a single security in an investment universe."""
    universe_id: str
    security_id: str
    effective_from: str  # YYYY-MM-DD
    effective_to: Optional[str] = None  # None if currently active
    source: str = "OFFICIAL_INDEX_COMMITTEE"

    def is_member_on(self, as_of_date: str) -> bool:
        if as_of_date < self.effective_from:
            return False
        if self.effective_to and as_of_date > self.effective_to:
            return False
        return True


class PointInTimeUniverseEngine:
    """
    Point-in-Time Universe Engine.
    Filters universes dynamically as of historical dates to completely eliminate survivorship contamination.
    """

    def __init__(self, universe_id: str = "SP500"):
        self.universe_id = universe_id
        self._memberships: List[UniverseMembership] = []

    def add_membership(
        self,
        security_id: str,
        effective_from: str,
        effective_to: Optional[str] = None,
        source: str = "OFFICIAL_INDEX_COMMITTEE",
    ) -> None:
        self._memberships.append(
            UniverseMembership(
                universe_id=self.universe_id,
                security_id=security_id,
                effective_from=effective_from,
                effective_to=effective_to,
                source=source,
            )
        )

    def get_constituents_as_of(self, as_of_date: str) -> List[str]:
        """Return list of permanent security_ids active in universe on as_of_date."""
        active: Set[str] = set()
        for m in self._memberships:
            if m.is_member_on(as_of_date):
                active.add(m.security_id)
        return sorted(list(active))

    def compute_membership_hash(self, as_of_date: str) -> str:
        """Compute cryptographic hash of universe constituents on as_of_date."""
        constituents = self.get_constituents_as_of(as_of_date)
        content = f"{self.universe_id}|{as_of_date}|{','.join(constituents)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
