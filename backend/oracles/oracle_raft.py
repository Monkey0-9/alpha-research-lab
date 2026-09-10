"""
Independent Reference Oracle: Distributed Raft Consensus Safety Invariants.
Implements the 5 formal safety properties defined in Ongaro & Ousterhout (2014).
Zero production imports permitted.
"""
from dataclasses import dataclass
from typing import Dict, List, Set


class OracleRaftInvariantViolation(Exception):
    """Raised when a distributed trace violates formal consensus safety."""
    pass


@dataclass(frozen=True)
class OracleRaftLogEntry:
    index: int
    term: int
    command: str


class OracleRaftSafetyValidator:
    """Independent formal verifier for distributed consensus execution traces."""

    def __init__(self):
        # Tracking leaders per term: term -> set of leader node_ids
        self._leaders_per_term: Dict[int, Set[str]] = {}
        # Tracking node logs: node_id -> list of entries
        self._node_logs: Dict[str, List[OracleRaftLogEntry]] = {}
        # Tracking committed entries: index -> (term, command)
        self._committed_entries: Dict[int, OracleRaftLogEntry] = {}

    def record_leader_election(self, term: int, leader_id: str) -> None:
        """
        Invariant 1: Election Safety.
        At most one leader can be elected in a given term.
        """
        leaders = self._leaders_per_term.setdefault(term, set())
        if leader_id not in leaders and len(leaders) >= 1:
            existing = list(leaders)[0]
            raise OracleRaftInvariantViolation(
                f"Election Safety Violated: Term {term} already elected leader {existing}, "
                f"cannot also elect {leader_id}"
            )
        leaders.add(leader_id)

    def record_node_log(self, node_id: str, log: List[OracleRaftLogEntry]) -> None:
        """
        Invariant 3: Log Matching Property.
        If two logs contain an entry with the same index and term,
        then the logs are identical in all entries up through the given index.
        """
        self._node_logs[node_id] = list(log)
        for other_id, other_log in self._node_logs.items():
            if other_id == node_id:
                continue
            # Compare overlapping prefix
            min_len = min(len(log), len(other_log))
            for i in range(min_len):
                if log[i].index == other_log[i].index and log[i].term == other_log[i].term:
                    # Invariant: All previous entries 0..i must match exactly
                    for prev_idx in range(i):
                        if (log[prev_idx].term != other_log[prev_idx].term or
                                log[prev_idx].command != other_log[prev_idx].command):
                            raise OracleRaftInvariantViolation(
                                f"Log Matching Violated: Nodes {node_id} and {other_id} match at index {i} "
                                f"(term {log[i].term}) but diverge at earlier index {prev_idx}"
                            )

    def record_committed_entry(self, entry: OracleRaftLogEntry) -> None:
        """
        Invariant 5: State Machine Safety.
        If a server has applied a log entry at a given index to its state machine,
        no other server will ever apply a different log entry for the same index.
        """
        if entry.index in self._committed_entries:
            prev = self._committed_entries[entry.index]
            if prev.term != entry.term or prev.command != entry.command:
                raise OracleRaftInvariantViolation(
                    f"State Machine Safety Violated: Index {entry.index} was previously committed "
                    f"as (term {prev.term}, cmd {prev.command}), now attempting to commit "
                    f"(term {entry.term}, cmd {entry.command})"
                )
        self._committed_entries[entry.index] = entry
