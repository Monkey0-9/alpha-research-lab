"""
Gate 0: Manifest Commit Consistency & Adversarial Mutation Verification Suite.
Validates:
1. Real committed manifests (STATUS.json, RUN_MANIFEST.json) have zero provenance contradictions.
2. Complete detection & rejection (raise IntegrityViolationError / EvidenceTamperedError) on:
   - Tampered commit hashes
   - Stale / fabricated dirty flags
   - Inflated / fabricated test counts
   - Inaccurate prerendered route counts
   - Corrupted SHA-256 evidence package digests
"""
import copy
import json
from pathlib import Path
import tempfile
import pytest

from backend.core.evidence_integrity import (
    EvidenceIntegrityVerifier,
    EvidenceTamperedError,
    IntegrityViolationError,
)


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def verifier(repo_root):
    return EvidenceIntegrityVerifier(repo_root)


def test_real_manifests_are_pristine_and_consistent(verifier, repo_root):
    """Verify live STATUS.json and RUN_MANIFEST.json against ground truth."""
    status_path = repo_root / "STATUS.json"
    assert status_path.exists(), "STATUS.json must exist in repo root"

    with open(status_path, "r", encoding="utf-8") as f:
        status = json.load(f)

    # 1. Cleanliness assertions
    assert status.get("git", {}).get("dirty") is False, "STATUS.json must certify clean working tree"
    if "provenance" in status:
        assert status["provenance"]["git_dirty_at_measurement"] is False

    # 2. Arithmetic assertions
    v = status["verification"]
    assert v["total_tests"] == v["backend_tests"] + v["frontend_tests"]
    assert v["frontend_tests"] == 26
    assert v["nextjs_prerendered_routes_count"] == 17
    assert len(status["routes"]) == 17

    # 3. Live verification against git and pytest discovery
    verified_status = verifier.verify_status_manifest(
        str(status_path),
        enforce_git_commit=True,
        enforce_clean_working_tree=False
    )
    assert verified_status["verification"]["total_tests"] >= 400

    # 4. RUN_MANIFEST.json validation
    run_manifest_path = repo_root / "RUN_MANIFEST.json"
    if run_manifest_path.exists():
        with open(run_manifest_path, "r", encoding="utf-8") as f:
            rm = json.load(f)
        assert rm.get("git_dirty") is False
        if "provenance" in rm:
            assert rm["provenance"]["git_dirty_at_measurement"] is False
        verifier.verify_run_manifest(
            str(run_manifest_path),
            enforce_git_commit=True,
            enforce_clean_working_tree=False
        )


def test_manifest_mutation_detects_tampered_commit(verifier, repo_root):
    """Mutating commit SHA to a rogue hash must trigger IntegrityViolationError."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "STATUS.json"
        with open(repo_root / "STATUS.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        tampered = copy.deepcopy(data)
        tampered["git"]["commit"] = "000000000000000000000000000000000000dead"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(tampered, f)

        with pytest.raises(IntegrityViolationError, match="Git commit hash mismatch"):
            verifier.verify_status_manifest(str(tmp_path), enforce_git_commit=True)


def test_manifest_mutation_detects_dirty_working_tree(verifier, repo_root):
    """Recording dirty: true in manifest must fail closed when clean state is enforced."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "STATUS.json"
        with open(repo_root / "STATUS.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        tampered = copy.deepcopy(data)
        tampered["git"]["dirty"] = True
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(tampered, f)

        with pytest.raises(IntegrityViolationError, match="dirty: true"):
            verifier.verify_status_manifest(
                str(tmp_path),
                enforce_git_commit=False,
                enforce_clean_working_tree=True
            )


def test_manifest_mutation_detects_inflated_test_counts(verifier, repo_root):
    """Falsifying or inflating test numbers must trigger IntegrityViolationError."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "STATUS.json"
        with open(repo_root / "STATUS.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Case A: Arithmetic lie
        tampered_a = copy.deepcopy(data)
        tampered_a["verification"]["total_tests"] = 999
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(tampered_a, f)
        with pytest.raises(IntegrityViolationError, match="Arithmetic mismatch"):
            verifier.verify_status_manifest(str(tmp_path), enforce_git_commit=False)

        # Case B: Backend inflation
        tampered_b = copy.deepcopy(data)
        tampered_b["verification"]["backend_tests"] = 900
        tampered_b["verification"]["total_tests"] = 926
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(tampered_b, f)
        with pytest.raises(IntegrityViolationError, match="Backend test count mismatch"):
            verifier.verify_status_manifest(str(tmp_path), enforce_git_commit=False)


def test_manifest_mutation_detects_route_discrepancy(verifier, repo_root):
    """Reporting inaccurate route counts must trigger IntegrityViolationError."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "STATUS.json"
        with open(repo_root / "STATUS.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        tampered = copy.deepcopy(data)
        tampered["verification"]["nextjs_prerendered_routes_count"] = 14
        tampered["routes"] = tampered["routes"][:14]
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(tampered, f)

        with pytest.raises(IntegrityViolationError, match="Prerendered routes count mismatch"):
            verifier.verify_status_manifest(str(tmp_path), enforce_git_commit=False)


def test_evidence_package_detects_corrupted_digest(repo_root):
    """Tampering with an evidence file referenced in SHA256SUMS must raise EvidenceTamperedError."""
    with tempfile.TemporaryDirectory() as tmp:
        ev_dir = Path(tmp) / "audit_evidence"
        ev_dir.mkdir()

        # Create authentic file and compute checksum
        f1 = ev_dir / "report.json"
        f1.write_text('{"status": "PASS"}', encoding="utf-8")

        verifier = EvidenceIntegrityVerifier(Path(tmp))
        checksums_file = ev_dir / "SHA256SUMS"
        import hashlib
        h1 = hashlib.sha256(f1.read_bytes()).hexdigest()
        checksums_file.write_text(f"{h1}  report.json\n", encoding="utf-8")

        # Pristine check passes
        assert verifier.verify_sha256sums(ev_dir) == 1

        # Corrupt 1 byte in report.json
        f1.write_text('{"status": "FAIL"}', encoding="utf-8")
        with pytest.raises(EvidenceTamperedError, match="Cryptographic hash mismatch"):
            verifier.verify_sha256sums(ev_dir)
