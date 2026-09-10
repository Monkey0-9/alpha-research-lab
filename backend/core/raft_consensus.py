"""
QuantAlpha Distributed Raft Consensus Evidence Engine.
Implements:
1. Leader Election (Term, Candidate, Majority Quorum N/2 + 1).
2. Log Replication via AppendEntries RPC.
3. Cryptographic Merkle Root state machine commitments.
4. Split-brain and network partition tolerance (Minority rejection, Majority progression).
5. Partition healing and log reconciliation.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Dict, List, Optional, Set, Tuple


class RaftRole(str, Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"


@dataclass
class LogEntry:
    term: int
    index: int
    data: str  # Serialized evidence record
    leaf_hash: str = ""

    def __post_init__(self):
        if not self.leaf_hash:
            self.leaf_hash = hashlib.sha256(f"{self.term}|{self.index}|{self.data}".encode("utf-8")).hexdigest()


class RaftNode:
    """A single Raft consensus node managing replicated state and evidence Merkle roots."""

    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers  # IDs of other nodes in cluster
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []  # 1-indexed (log[0] is dummy sentinel)
        self.commit_index = 0
        self.last_applied = 0
        self.role = RaftRole.FOLLOWER
        self.merkle_root: str = hashlib.sha256(b"GENESIS_EVIDENCE").hexdigest()

        # Leader state: node_id -> next index / match index
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

    @property
    def last_log_index(self) -> int:
        return len(self.log)

    @property
    def last_log_term(self) -> int:
        return self.log[-1].term if self.log else 0

    def start_election(self) -> None:
        """Transition to candidate and request votes."""
        self.role = RaftRole.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id

    def handle_request_vote(
        self,
        term: int,
        candidate_id: str,
        last_log_index: int,
        last_log_term: int
    ) -> Tuple[int, bool]:
        """Process RequestVote RPC."""
        if term > self.current_term:
            self.current_term = term
            self.role = RaftRole.FOLLOWER
            self.voted_for = None

        vote_granted = False
        if term == self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
            # Check log up-to-date invariant
            if (last_log_term > self.last_log_term) or (
                last_log_term == self.last_log_term and last_log_index >= self.last_log_index
            ):
                vote_granted = True
                self.voted_for = candidate_id

        return self.current_term, vote_granted

    def handle_append_entries(
        self,
        term: int,
        leader_id: str,
        prev_log_index: int,
        prev_log_term: int,
        entries: List[LogEntry],
        leader_commit: int
    ) -> Tuple[int, bool]:
        """Process AppendEntries RPC."""
        if term > self.current_term:
            self.current_term = term
            self.role = RaftRole.FOLLOWER
            self.voted_for = None

        if term < self.current_term:
            return self.current_term, False

        # Recognize active leader
        self.role = RaftRole.FOLLOWER

        # Log consistency check
        if prev_log_index > 0:
            if prev_log_index > len(self.log):
                return self.current_term, False
            if self.log[prev_log_index - 1].term != prev_log_term:
                # Conflicting entry: truncate log
                self.log = self.log[:prev_log_index - 1]
                return self.current_term, False

        # Append new entries not already in log
        for e in entries:
            idx = e.index
            if idx <= len(self.log):
                self.log[idx - 1] = e
            else:
                self.log.append(e)

        # Update commit index and Merkle root
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log))
            self._apply_entries_to_merkle()

        return self.current_term, True

    def _apply_entries_to_merkle(self) -> None:
        """Apply newly committed entries to update the deterministic Merkle evidence root."""
        while self.last_applied < self.commit_index:
            entry = self.log[self.last_applied]
            combined = f"{self.merkle_root}|{entry.leaf_hash}".encode("utf-8")
            self.merkle_root = hashlib.sha256(combined).hexdigest()
            self.last_applied += 1


class RaftCluster:
    """Simulated 3-Node Raft Consensus Cluster with programmable partition injection."""

    def __init__(self, node_ids: Optional[List[str]] = None):
        ids = node_ids or ["node_A", "node_B", "node_C"]
        self.nodes: Dict[str, RaftNode] = {nid: RaftNode(nid, [p for p in ids if p != nid]) for nid in ids}
        self.partition_groups: List[Set[str]] = [set(ids)]  # Default: all connected

    def set_partition(self, groups: List[Set[str]]) -> None:
        """Inject network partition (e.g. [{"node_A"}, {"node_B", "node_C"}])."""
        self.partition_groups = groups

    def heal_partition(self) -> None:
        """Heal network partition so all nodes communicate freely."""
        self.partition_groups = [set(self.nodes.keys())]

    def _can_communicate(self, src: str, dst: str) -> bool:
        for grp in self.partition_groups:
            if src in grp and dst in grp:
                return True
        return False

    def elect_leader(self, preferred_node: Optional[str] = None) -> str:
        """Conduct election in the majority partition."""
        cand_id = preferred_node or list(self.nodes.keys())[0]
        candidate = self.nodes[cand_id]
        candidate.start_election()

        votes = 1  # Self-vote
        for peer_id in candidate.peers:
            if self._can_communicate(cand_id, peer_id):
                peer = self.nodes[peer_id]
                t, granted = peer.handle_request_vote(
                    term=candidate.current_term,
                    candidate_id=cand_id,
                    last_log_index=candidate.last_log_index,
                    last_log_term=candidate.last_log_term
                )
                if granted:
                    votes += 1

        quorum = (len(self.nodes) // 2) + 1
        if votes >= quorum:
            candidate.role = RaftRole.LEADER
            for pid in candidate.peers:
                candidate.next_index[pid] = candidate.last_log_index + 1
                candidate.match_index[pid] = 0
            return cand_id
        else:
            raise RuntimeError(f"Election failed for {cand_id}: received {votes}/{quorum} votes.")

    def submit_evidence(self, leader_id: str, evidence_data: str) -> Tuple[bool, str]:
        """
        Submit evidence to leader.
        Replicates via AppendEntries. Commits only if written to majority quorum.
        Returns: (success, merkle_root)
        """
        leader = self.nodes.get(leader_id)
        if not leader or leader.role != RaftRole.LEADER:
            return False, "Not the leader"

        # Append to leader's local log
        new_index = leader.last_log_index + 1
        entry = LogEntry(term=leader.current_term, index=new_index, data=evidence_data)
        leader.log.append(entry)

        replications = 1  # Leader itself
        for peer_id in leader.peers:
            if self._can_communicate(leader_id, peer_id):
                peer = self.nodes[peer_id]
                prev_idx = new_index - 1
                prev_term = leader.log[prev_idx - 1].term if prev_idx > 0 else 0

                term, success = peer.handle_append_entries(
                    term=leader.current_term,
                    leader_id=leader_id,
                    prev_log_index=prev_idx,
                    prev_log_term=prev_term,
                    entries=[entry],
                    leader_commit=leader.commit_index
                )
                if success:
                    replications += 1
                    leader.match_index[peer_id] = new_index
                    leader.next_index[peer_id] = new_index + 1

        quorum = (len(self.nodes) // 2) + 1
        if replications >= quorum:
            # Commit entry
            leader.commit_index = new_index
            leader._apply_entries_to_merkle()
            # Send updated commit to peers in partition
            for peer_id in leader.peers:
                if self._can_communicate(leader_id, peer_id):
                    self.nodes[peer_id].handle_append_entries(
                        term=leader.current_term,
                        leader_id=leader_id,
                        prev_log_index=new_index,
                        prev_log_term=entry.term,
                        entries=[],
                        leader_commit=leader.commit_index
                    )
            return True, leader.merkle_root
        else:
            # Quorum lost! Log entry remains uncommitted
            return False, "Failed to achieve quorum replication"

    def reconcile_all(self, leader_id: str) -> None:
        """Reconcile logs across all connected nodes after partition heal."""
        leader = self.nodes[leader_id]
        for peer_id in leader.peers:
            if self._can_communicate(leader_id, peer_id):
                peer = self.nodes[peer_id]
                peer.handle_append_entries(
                    term=leader.current_term,
                    leader_id=leader_id,
                    prev_log_index=0,
                    prev_log_term=0,
                    entries=leader.log,
                    leader_commit=leader.commit_index
                )
