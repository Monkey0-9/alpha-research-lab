"""
Symbology & Identifier Resolution Engine.
Resolves cross-vendor identifiers (FIGI, ISIN, CUSIP, PERMNO, Tickers) to permanent security_ids.
"""
from __future__ import annotations

from typing import Dict, Optional
from .entities import SecurityEntity


class SymbologyResolver:
    """Multi-identifier bidirectional mapping registry."""

    def __init__(self):
        self._figi_map: Dict[str, str] = {}
        self._isin_map: Dict[str, str] = {}
        self._cusip_map: Dict[str, str] = {}
        self._permno_map: Dict[str, str] = {}
        self._ticker_map: Dict[str, str] = {}

    def register(self, entity: SecurityEntity) -> None:
        sid = entity.security_id
        if entity.figi:
            self._figi_map[entity.figi] = sid
        if entity.isin:
            self._isin_map[entity.isin] = sid
        if entity.cusip:
            self._cusip_map[entity.cusip] = sid
        if entity.permno:
            self._permno_map[entity.permno] = sid
        if entity.ticker:
            self._ticker_map[entity.ticker] = sid

    def resolve(self, identifier: str) -> Optional[str]:
        """Resolve arbitrary vendor identifier to permanent security_id."""
        if identifier in self._figi_map:
            return self._figi_map[identifier]
        if identifier in self._isin_map:
            return self._isin_map[identifier]
        if identifier in self._cusip_map:
            return self._cusip_map[identifier]
        if identifier in self._permno_map:
            return self._permno_map[identifier]
        if identifier in self._ticker_map:
            return self._ticker_map[identifier]
        return None
