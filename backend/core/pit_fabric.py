"""
QuantAlpha Multi-Timestamp Point-in-Time Data Fabric.
Enforces institutional multi-temporal causality:
  event_time <= published_at <= available_at <= decision_time < effective_to

Guarantees zero publication-delay lookahead, zero wire-delay lookahead,
and strict historical revision auditability.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Dict, List, Optional, Tuple


class TemporalLookaheadError(Exception):
    """Raised when an operation attempts to access data prior to its availability timestamp."""
    pass


@dataclass(frozen=True)
class PITRecord:
    entity_id: str
    feature_name: str
    value: float
    event_time: datetime
    published_at: datetime
    available_at: datetime
    effective_from: datetime
    effective_to: Optional[datetime]
    revision_id: int
    source_id: str
    digest: str

    @staticmethod
    def compute_digest(
        entity_id: str,
        feature_name: str,
        value: float,
        event_time: datetime,
        published_at: datetime,
        available_at: datetime,
        revision_id: int,
        source_id: str
    ) -> str:
        payload = (
            f"{entity_id}|{feature_name}|{value:.8f}|"
            f"{event_time.isoformat()}|{published_at.isoformat()}|{available_at.isoformat()}|"
            f"{revision_id}|{source_id}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PITDataFabric:
    """
    Institutional Point-in-Time Data Store.
    Maintains complete bitemporal revision lineage.
    """

    def __init__(self):
        # Store: (entity_id, feature_name) -> list of PITRecord sorted by available_at
        self._store: Dict[Tuple[str, str], List[PITRecord]] = {}

    def record_observation(
        self,
        entity_id: str,
        feature_name: str,
        value: float,
        event_time: datetime,
        published_at: datetime,
        available_at: datetime,
        source_id: str,
        revision_id: Optional[int] = None
    ) -> PITRecord:
        """
        Record a new data observation or revision.
        Enforces: event_time <= published_at <= available_at.
        Automatically retires previous active revision for the same event_time.
        """
        # Ensure UTC timezone awareness
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        if available_at.tzinfo is None:
            available_at = available_at.replace(tzinfo=timezone.utc)

        if published_at < event_time:
            raise ValueError(
                f"Causality violation: published_at ({published_at}) cannot precede event_time ({event_time})"
            )
        if available_at < published_at:
            raise ValueError(
                f"Causality violation: available_at ({available_at}) cannot precede published_at ({published_at})"
            )

        key = (entity_id, feature_name)
        existing = self._store.setdefault(key, [])

        # Filter existing records for the same event_time to assign revision_id
        same_event_records = [r for r in existing if r.event_time == event_time]
        if revision_id is None:
            revision_id = len(same_event_records)

        effective_from = available_at
        digest = PITRecord.compute_digest(
            entity_id=entity_id,
            feature_name=feature_name,
            value=value,
            event_time=event_time,
            published_at=published_at,
            available_at=available_at,
            revision_id=revision_id,
            source_id=source_id
        )

        # If previous revision exists for this event_time, retire it by setting effective_to
        updated_records = []
        for r in existing:
            if r.event_time == event_time and r.effective_to is None:
                # Retire previous revision
                retired = PITRecord(
                    entity_id=r.entity_id,
                    feature_name=r.feature_name,
                    value=r.value,
                    event_time=r.event_time,
                    published_at=r.published_at,
                    available_at=r.available_at,
                    effective_from=r.effective_from,
                    effective_to=effective_from,
                    revision_id=r.revision_id,
                    source_id=r.source_id,
                    digest=r.digest
                )
                updated_records.append(retired)
            else:
                updated_records.append(r)

        new_record = PITRecord(
            entity_id=entity_id,
            feature_name=feature_name,
            value=value,
            event_time=event_time,
            published_at=published_at,
            available_at=available_at,
            effective_from=effective_from,
            effective_to=None,
            revision_id=revision_id,
            source_id=source_id,
            digest=digest
        )
        updated_records.append(new_record)
        self._store[key] = sorted(updated_records, key=lambda x: (x.event_time, x.available_at))
        return new_record

    def query_as_of(
        self,
        entity_id: str,
        feature_name: str,
        event_time: datetime,
        decision_time: datetime,
        fail_closed: bool = True
    ) -> Optional[PITRecord]:
        """
        Query the active value for a specific event_time as known at decision_time.
        Strict Invariant:
          available_at <= decision_time
          effective_from <= decision_time < effective_to (or effective_to is None)
        """
        if decision_time.tzinfo is None:
            decision_time = decision_time.replace(tzinfo=timezone.utc)
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)

        key = (entity_id, feature_name)
        records = self._store.get(key, [])

        valid_candidates = []
        for r in records:
            if r.event_time != event_time:
                continue
            # Rule: Must have been available by decision_time
            if r.available_at <= decision_time:
                # Check effective window
                if r.effective_from <= decision_time:
                    if r.effective_to is None or decision_time < r.effective_to:
                        valid_candidates.append(r)

        if not valid_candidates:
            if fail_closed:
                # Check if future data exists to provide an informative exception
                future_exists = any(r.event_time == event_time and r.available_at > decision_time for r in records)
                if future_exists:
                    raise TemporalLookaheadError(
                        f"Lookahead violation: Observation for {entity_id}.{feature_name} at {event_time} "
                        f"was not available at decision_time {decision_time}"
                    )
            return None

        # Return the latest revision available at decision_time
        return max(valid_candidates, key=lambda x: x.revision_id)

    def query_history_as_of(
        self,
        entity_id: str,
        feature_name: str,
        start_event_time: datetime,
        end_event_time: datetime,
        decision_time: datetime
    ) -> List[PITRecord]:
        """
        Retrieve complete event-time history between start and end, as strictly known at decision_time.
        """
        if decision_time.tzinfo is None:
            decision_time = decision_time.replace(tzinfo=timezone.utc)
        if start_event_time.tzinfo is None:
            start_event_time = start_event_time.replace(tzinfo=timezone.utc)
        if end_event_time.tzinfo is None:
            end_event_time = end_event_time.replace(tzinfo=timezone.utc)

        key = (entity_id, feature_name)
        records = self._store.get(key, [])

        # Group by event_time
        events = sorted(set(r.event_time for r in records if start_event_time <= r.event_time <= end_event_time))
        history = []
        for ev in events:
            rec = self.query_as_of(entity_id, feature_name, ev, decision_time, fail_closed=False)
            if rec is not None:
                history.append(rec)
        return history

    def get_revision_history(
        self,
        entity_id: str,
        feature_name: str,
        event_time: datetime
    ) -> List[PITRecord]:
        """Audit trail: returns all revisions for an event in chronological order."""
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        key = (entity_id, feature_name)
        records = self._store.get(key, [])
        return [r for r in records if r.event_time == event_time]
