"""
Independent Reference Oracle: Point-In-Time Temporal Causality.
Written from first principles to cross-validate production PITDataFabric.
No production imports permitted.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


class OracleTemporalViolation(Exception):
    """Raised by Oracle when causality or lookahead occurs."""
    pass


@dataclass(frozen=True)
class OraclePITEvent:
    entity: str
    feature: str
    value: float
    event_time: datetime
    published_at: datetime
    available_at: datetime
    source: str


class OraclePITValidator:
    """Independent reference validator for point-in-time timeline lookups."""

    @staticmethod
    def validate_ingestion_causality(event: OraclePITEvent) -> None:
        """Rule: event_time <= published_at <= available_at."""
        if event.published_at < event.event_time:
            raise OracleTemporalViolation("Oracle Error: published_at precedes event_time")
        if event.available_at < event.published_at:
            raise OracleTemporalViolation("Oracle Error: available_at precedes published_at")

    @classmethod
    def reference_as_of_lookup(
        cls,
        history: List[OraclePITEvent],
        entity: str,
        feature: str,
        event_time: datetime,
        decision_time: datetime
    ) -> Optional[OraclePITEvent]:
        """
        Pure reference timeline selection:
        1. Filters records matching (entity, feature, event_time).
        2. Filters for available_at <= decision_time.
        3. Returns the latest available record.
        4. If future records exist that were not available, raises OracleTemporalViolation.
        """
        if decision_time.tzinfo is None:
            decision_time = decision_time.replace(tzinfo=timezone.utc)
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)

        matches = [e for e in history if e.entity == entity and e.feature == feature and e.event_time == event_time]
        if not matches:
            return None

        # Check for future lookahead
        available = [e for e in matches if e.available_at <= decision_time]
        if not available:
            if any(e.available_at > decision_time for e in matches):
                raise OracleTemporalViolation(
                    f"Oracle: Attempted to query data for {entity} at {decision_time} "
                    f"before it became available at {matches[0].available_at}"
                )
            return None

        # Return latest available event
        return sorted(available, key=lambda x: x.available_at)[-1]
