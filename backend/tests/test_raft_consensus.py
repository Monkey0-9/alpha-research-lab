"""
Institutional Verification Tests for Distributed Raft Consensus Evidence Engine.
Verifies:
1. Leader Election across a 3-node cluster with majority quorum.
2. AppendEntries replication and deterministic Merkle root updates.
3. Network split-brain partition tolerance (minority rejection vs majority commit).
4. Partition healing and log reconciliation.
"""
from backend.core.raft_consensus import RaftCluster, RaftRole


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
    # All 3 nodes must agree on the new Merkle root
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
