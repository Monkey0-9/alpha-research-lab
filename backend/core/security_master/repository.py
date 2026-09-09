"""
Institutional Security Master Repository.
Unified store supporting temporal as-of queries across securities, corporate actions, and universes.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .entities import SecurityEntity
from .identifiers import SymbologyResolver
from .listings import ListingEvent
from .delistings import DelistingEvent
from .universe import PointInTimeUniverseEngine

logger = logging.getLogger(__name__)


class SecurityMasterRepository:
    """
    Central repository for permanent security identities, identifiers,
    historical corporate actions, listings, delistings, and PIT universe memberships.
    """

    def __init__(self):
        self.entities: Dict[str, SecurityEntity] = {}
        self.resolver = SymbologyResolver()
        self.universes: Dict[str, PointInTimeUniverseEngine] = {}
        self.listings: List[ListingEvent] = []
        self.delistings: List[DelistingEvent] = []
        self._bootstrap_default_universe()

    def _bootstrap_default_universe(self) -> None:
        """Seed representative SP500 constituents with permanent IDs."""
        sp500 = PointInTimeUniverseEngine(universe_id="SP500")
        seeds = [
            ("SEC-US-AAPL-001", "AAPL", "Apple Inc.", "1980-12-12", None),
            ("SEC-US-MSFT-001", "MSFT", "Microsoft Corp.", "1986-03-13", None),
            ("SEC-US-GOOGL-001", "GOOGL", "Alphabet Inc.", "2004-08-19", None),
            ("SEC-US-AMZN-001", "AMZN", "Amazon.com Inc.", "1997-05-15", None),
            ("SEC-US-NVDA-001", "NVDA", "NVIDIA Corp.", "1999-01-22", None),
            ("SEC-US-XRX-001", "XRX", "Xerox Holdings Corp", "1960-01-01", "2021-03-22"),
        ]
        for sid, sym, name, l_date, d_date in seeds:
            entity = SecurityEntity(
                security_id=sid,
                ticker=sym,
                listing_date=l_date,
                delisting_date=d_date,
                is_active=d_date is None,
                metadata={"name": name},
            )
            self.register_entity(entity)
            sp500.add_membership(security_id=sid, effective_from=l_date, effective_to=d_date)

        self.universes["SP500"] = sp500

    def register_entity(self, entity: SecurityEntity) -> None:
        self.entities[entity.security_id] = entity
        self.resolver.register(entity)

    def get_entity(self, security_id: str) -> Optional[SecurityEntity]:
        return self.entities.get(security_id)

    def resolve_identifier(self, identifier: str) -> Optional[SecurityEntity]:
        sid = self.resolver.resolve(identifier)
        return self.entities.get(sid) if sid else None

    def get_universe(self, universe_id: str = "SP500") -> PointInTimeUniverseEngine:
        if universe_id not in self.universes:
            self.universes[universe_id] = PointInTimeUniverseEngine(universe_id=universe_id)
        return self.universes[universe_id]
