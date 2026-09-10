"""
Gate 0: Evidence Self-Consistency & Tamper Verification Test Suite.
Verifies:
1. Ground-truth detection of test counts and Next.js routes.
2. Immediate fail-closed rejection of fabricated or inflated test numbers.
3. Git commit SHA and working tree cleanliness enforcement.
4. SHA-256 evidence package checksum verification.
"""
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
def temp_repo_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_evidence_verifier_real_system_consistency():
    verifier = EvidenceIntegrityVerifier()
    # Test counting on actual repository
    b_count, breakdown = verifier.count_actual_backend_tests()
    assert b_count > 300
    assert len(breakdown) > 40

    routes = verifier.get_actual_prerendered_routes()
    assert len(routes) == 17
    assert "/" in routes
    assert "/_not-found" in routes
    assert "/alpha-discovery" in routes


def test_evidence_verifier_detects_arithmetic_tampering(temp_repo_dir):
    verifier = EvidenceIntegrityVerifier(root_dir=temp_repo_dir)
    status_file = temp_repo_dir / "STATUS.json"

    # Fabricate inconsistent math: 350 + 26 != 400
    bad_data = {
        "git": {"commit": "abc", "dirty": False},
        "verification": {
            "total_tests": 400,
            "backend_tests": 350,
            "frontend_tests": 26,
            "nextjs_prerendered_routes_count": 1,
        },
        "routes": ["/"]
    }
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    with pytest.raises(IntegrityViolationError, match="Arithmetic mismatch"):
        verifier.verify_status_manifest(str(status_file), enforce_git_commit=False)


def test_evidence_verifier_detects_route_count_tampering(temp_repo_dir):
    verifier = EvidenceIntegrityVerifier(root_dir=temp_repo_dir)
    status_file = temp_repo_dir / "STATUS.json"

    # Claimed 14 routes but route array has only 1
    bad_data = {
        "git": {"commit": "abc", "dirty": False},
        "verification": {
            "total_tests": 376,
            "backend_tests": 350,
            "frontend_tests": 26,
            "nextjs_prerendered_routes_count": 14,
        },
        "routes": ["/"]
    }
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    with pytest.raises(IntegrityViolationError, match="Route count mismatch"):
        verifier.verify_status_manifest(str(status_file), enforce_git_commit=False)


def test_evidence_verifier_detects_git_commit_mismatch(temp_repo_dir):
    verifier = EvidenceIntegrityVerifier(root_dir=temp_repo_dir)
    status_file = temp_repo_dir / "STATUS.json"

    bad_data = {
        "git": {"commit": "FAKE_COMMIT_HASH_0000000000000000000000", "dirty": False},
        "verification": {
            "total_tests": 26,
            "backend_tests": 0,
            "frontend_tests": 26,
            "nextjs_prerendered_routes_count": 1,
        },
        "routes": ["/"]
    }
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    with pytest.raises(IntegrityViolationError, match="Git commit hash mismatch"):
        verifier.verify_status_manifest(str(status_file), enforce_git_commit=True)


def test_evidence_sha256sums_tamper_detection(temp_repo_dir):
    verifier = EvidenceIntegrityVerifier(root_dir=temp_repo_dir)
    ev_dir = temp_repo_dir / "evidence"
    ev_dir.mkdir(parents=True)

    test_file = ev_dir / "artifact.txt"
    test_file.write_text("authentic institutional evidence", encoding="utf-8")

    import hashlib
    h = hashlib.sha256("authentic institutional evidence".encode("utf-8")).hexdigest()
    sums_file = ev_dir / "SHA256SUMS"
    sums_file.write_text(f"{h}  artifact.txt\n", encoding="utf-8")

    # 1. Authentic artifact passes
    assert verifier.verify_sha256sums(ev_dir) == 1

    # 2. Tamper with file contents
    test_file.write_text("tampered corrupted data", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        verifier.verify_sha256sums(ev_dir)


def test_run_manifest_generation(temp_repo_dir):
    verifier = EvidenceIntegrityVerifier()
    out_manifest = temp_repo_dir / "RUN_MANIFEST.json"
    manifest = verifier.generate_run_manifest(output_path=out_manifest)

    assert out_manifest.exists()
    assert "platform" in manifest
    assert "git_commit" in manifest
    assert manifest["prerendered_routes_count"] == 17
    assert manifest["verified_tests"]["frontend"] == 26
