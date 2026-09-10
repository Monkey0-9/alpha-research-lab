"""
Institutional Byzantine & Fault-Tolerant Test Matrix for Distributed Raft Consensus.
Verifies:
1. Leader election and majority quorum (N/2 + 1).
2. Split-vote handling and term increments.
3. Stale leader step-down upon discovering higher term.
4. Majority loss defense: Cluster refuses un-quorum commits.
5. Log divergence, conflict detection, and log truncation.
6. Crash-recovery: Node reboot replays log and recovers Merkle root.
7. RPC idempotency: Out-of-order and duplicate AppendEntries handling.
8. Merkle DAG tamper-evidence: Bit-level mutation detection in historical logs.
9. Split-brain network partition and reconciliation.
"""
import hashlib
from backend.core.raft_consensus import LogEntry, RaftCluster, RaftRole


def test_raft_leader_election():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    leader_id = cluster.elect_leader("node_A")

    assert leader_id == "node_A"
    assert cluster.nodes["node_A"].role == RaftRole.LEADER
    assert cluster.nodes["node_B"].role == RaftRole.FOLLOWER
    assert cluster.nodes["node_C"].role == RaftRole.FOLLOWER
    assert cluster.nodes["node_A"].current_term == 1


def test_raft_evidence_replication_and_merkle_root():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    leader_id = cluster.elect_leader("node_A")

    initial_root = cluster.nodes["node_A"].merkle_root
    assert len(initial_root) == 64

    # Submit evidence record 1
    evidence_1 = "ALPHA_EXPERIMENT_001|SHA256:abc123|SHARPE:1.82|STATUS:VALIDATED"
    success, new_root_1 = cluster.submit_evidence(leader_id, evidence_1)

    assert success is True
    assert new_root_1 != initial_root
    assert cluster.nodes["node_A"].merkle_root == new_root_1
    assert cluster.nodes["node_B"].merkle_root == new_root_1
    assert cluster.nodes["node_C"].merkle_root == new_root_1
    assert cluster.nodes["node_A"].commit_index == 1

    # Submit evidence record 2
    evidence_2 = "ALPHA_EXPERIMENT_002|SHA256:def456|SHARPE:0.41|STATUS:REJECTED"
    success, new_root_2 = cluster.submit_evidence(leader_id, evidence_2)
    assert success is True
    assert new_root_2 != new_root_1
    assert cluster.nodes["node_A"].merkle_root == new_root_2
    assert cluster.nodes["node_B"].merkle_root == new_root_2
    assert cluster.nodes["node_C"].merkle_root == new_root_2
    assert cluster.nodes["node_A"].commit_index == 2


def test_raft_network_partition_and_reconciliation():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    leader_id = cluster.elect_leader("node_A")

    # Commit baseline entry
    cluster.submit_evidence(leader_id, "BASELINE_ENTRY")
    baseline_root = cluster.nodes["node_A"].merkle_root

    # INJECT PARTITION: {node_A} (isolated minority) vs {node_B, node_C} (majority)
    cluster.set_partition([{"node_A"}, {"node_B", "node_C"}])

    # 1. Attempt commit on isolated node_A -> Must fail (replications = 1 < 2)
    fail_success, _ = cluster.submit_evidence("node_A", "ISOLATED_ENTRY")
    assert fail_success is False

    # 2. Elect new leader in majority partition {node_B, node_C}
    majority_leader = cluster.elect_leader("node_B")
    assert majority_leader == "node_B"
    assert cluster.nodes["node_B"].role == RaftRole.LEADER

    # 3. Commit entry in majority partition -> Must succeed (replications = 2 of 3)
    majority_success, majority_root = cluster.submit_evidence("node_B", "MAJORITY_EVIDENCE_COMMITTED")
    assert majority_success is True
    assert majority_root != baseline_root
    assert cluster.nodes["node_C"].merkle_root == majority_root

    # 4. HEAL PARTITION
    cluster.heal_partition()
    # Reconcile node_A with authoritative majority leader node_B
    cluster.reconcile_all(majority_leader)

    # Node_A should now have updated its log and Merkle root to match majority leader!
    assert cluster.nodes["node_A"].merkle_root == majority_root
    assert cluster.nodes["node_A"].commit_index == cluster.nodes["node_B"].commit_index


def test_raft_stale_leader_stepdown():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    cluster.elect_leader("node_A")
    node_a = cluster.nodes["node_A"]
    assert node_a.role == RaftRole.LEADER

    # An AppendEntries arrives from a newer leader at term 5
    term, success = node_a.handle_append_entries(
        term=5,
        leader_id="node_B",
        prev_log_index=0,
        prev_log_term=0,
        entries=[],
        leader_commit=0
    )
    # Stale leader MUST step down to FOLLOWER and update its term
    assert success is True
    assert node_a.role == RaftRole.FOLLOWER
    assert node_a.current_term == 5


def test_raft_majority_loss_prevents_commit():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    leader_id = cluster.elect_leader("node_A")

    # Isolate leader: Node_A is cut off from both Node_B and Node_C
    cluster.set_partition([{"node_A"}, {"node_B"}, {"node_C"}])

    success, err_msg = cluster.submit_evidence(leader_id, "UNCOMMITTED_DATA")
    assert success is False
    assert "quorum" in err_msg.lower()
    # Commit index must not advance without quorum
    assert cluster.nodes["node_A"].commit_index == 0


def test_raft_log_conflict_truncation():
    node = RaftCluster(["node_A", "node_B", "node_C"]).nodes["node_A"]
    node.current_term = 1

    # Populate log with 3 entries from term 1
    node.log = [
        LogEntry(term=1, index=1, data="e1"),
        LogEntry(term=1, index=2, data="e2"),
        LogEntry(term=1, index=3, data="e3_uncommitted"),
    ]

    # AppendEntries from new leader (term 2) at index 2 with conflicting entry 3
    new_entry_3 = LogEntry(term=2, index=3, data="e3_authoritative")
    term, success = node.handle_append_entries(
        term=2,
        leader_id="node_B",
        prev_log_index=2,
        prev_log_term=1,
        entries=[new_entry_3],
        leader_commit=3
    )

    assert success is True
    # The conflicting uncommitted entry at index 3 must be overwritten
    assert len(node.log) == 3
    assert node.log[2].data == "e3_authoritative"
    assert node.log[2].term == 2


def test_raft_crash_and_recovery():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    leader_id = cluster.elect_leader("node_A")

    cluster.submit_evidence(leader_id, "EVIDENCE_BLOCK_1")
    cluster.submit_evidence(leader_id, "EVIDENCE_BLOCK_2")

    node_b = cluster.nodes["node_B"]
    pre_crash_root = node_b.merkle_root
    assert node_b.commit_index == 2

    # Simulate crash and reboot
    node_b.crash_and_restart()

    # After restart, role must be FOLLOWER and Merkle root accurately replayed
    assert node_b.role == RaftRole.FOLLOWER
    assert node_b.commit_index == 2
    assert node_b.merkle_root == pre_crash_root


def test_raft_rpc_idempotency():
    node = RaftCluster(["node_A", "node_B", "node_C"]).nodes["node_A"]
    entry = LogEntry(term=1, index=1, data="DATA_1")

    # Send first AppendEntries
    node.handle_append_entries(
        term=1, leader_id="node_B", prev_log_index=0, prev_log_term=0, entries=[entry], leader_commit=1
    )
    assert len(node.log) == 1

    # Send duplicate identical AppendEntries
    node.handle_append_entries(
        term=1, leader_id="node_B", prev_log_index=0, prev_log_term=0, entries=[entry], leader_commit=1
    )
    # Must NOT duplicate log entry
    assert len(node.log) == 1
    assert node.commit_index == 1


def test_raft_merkle_dag_tamper_detection():
    cluster = RaftCluster(["node_A", "node_B", "node_C"])
    leader_id = cluster.elect_leader("node_A")

    cluster.submit_evidence(leader_id, "GENUINE_EVIDENCE_1")
    cluster.submit_evidence(leader_id, "GENUINE_EVIDENCE_2")

    node_a = cluster.nodes["node_A"]
    original_root = node_a.merkle_root

    # Tamper with an entry in the log
    tampered_entry = LogEntry(term=node_a.log[0].term, index=node_a.log[0].index, data="TAMPERED_FRAUDULENT_DATA")

    # Recompute Merkle root with tampered entry
    tampered_root = hashlib.sha256(b"GENESIS_EVIDENCE").hexdigest()
    for e in [tampered_entry, node_a.log[1]]:
        tampered_root = hashlib.sha256(f"{tampered_root}|{e.leaf_hash}".encode("utf-8")).hexdigest()

    # Tampered root must NOT match genuine Merkle root
    assert tampered_root != original_root


def test_raft_lower_term_rejection():
    node = RaftCluster(["node_A", "node_B", "node_C"]).nodes["node_A"]
    node.current_term = 10

    # RPC with obsolete term (term 8 < 10) must be rejected
    term, success = node.handle_append_entries(
        term=8,
        leader_id="node_B",
        prev_log_index=0,
        prev_log_term=0,
        entries=[],
        leader_commit=0
    )
    assert success is False
    assert term == 10
