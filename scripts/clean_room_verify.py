"""
QuantAlpha Clean-Room Verification Engine (Phase 1).
Validates that an independent, isolated environment reproduces the exact
published research baseline without relying on cached or developer-local artifacts.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.core.evidence_integrity import (  # noqa: E402
    EvidenceIntegrityVerifier,
    EvidenceTamperedError,
    IntegrityViolationError,
)


def collect_environment_telemetry() -> Dict[str, Any]:
    """Capture complete clean-room system and dependency environment."""
    telemetry = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    # Node version
    try:
        node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
        telemetry["node_version"] = node_ver
    except Exception:
        telemetry["node_version"] = "unavailable"

    # Git SHA
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        telemetry["git_commit"] = git_sha
    except Exception:
        telemetry["git_commit"] = "unavailable"

    # Installed pip packages
    try:
        pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
        telemetry["pip_packages"] = sorted(pip_freeze.splitlines())
    except Exception:
        telemetry["pip_packages"] = []

    return telemetry


def run_clean_room_verification(strict: bool = True) -> Dict[str, Any]:
    """Execute complete clean-room audit and return structured verification certificate."""
    start_time = time.time()
    verifier = EvidenceIntegrityVerifier(ROOT)
    report: Dict[str, Any] = {
        "verifier": "QuantAlpha Clean-Room Verifier v1.0",
        "environment": collect_environment_telemetry(),
        "checks": {},
        "passed": False,
    }

    # 1. Manifest self-consistency
    print("[Clean-Room] Verifying STATUS.json and RUN_MANIFEST.json...")
    try:
        status_data = verifier.verify_status_manifest(enforce_git_commit=strict, enforce_clean_working_tree=strict)
        manifest_data = verifier.verify_run_manifest(enforce_git_commit=strict, enforce_clean_working_tree=strict)
        report["checks"]["manifest_integrity"] = {
            "status": "PASS",
            "verified_backend_tests": status_data["verification"]["backend_tests"],
            "verified_frontend_tests": status_data["verification"]["frontend_tests"],
            "prerendered_routes": len(manifest_data.get("routes", [])),
        }
        print("  [PASS] Manifest integrity validated.")
    except (IntegrityViolationError, EvidenceTamperedError) as e:
        report["checks"]["manifest_integrity"] = {"status": "FAIL", "error": str(e)}
        print(f"  [FAIL] Manifest integrity failed: {e}", file=sys.stderr)
        return report

    # 2. SHA-256 evidence package checksums if audit_evidence exists
    ev_dir = ROOT / "audit_evidence"
    if ev_dir.exists():
        print("[Clean-Room] Verifying cryptographic evidence digests (SHA256SUMS)...")
        try:
            verified_files = verifier.verify_sha256sums(ev_dir)
            report["checks"]["evidence_checksums"] = {
                "status": "PASS",
                "verified_artifacts": verified_files,
            }
            print(f"  [PASS] Verified {verified_files} audit evidence artifacts against SHA256SUMS.")
        except EvidenceTamperedError as e:
            report["checks"]["evidence_checksums"] = {"status": "FAIL", "error": str(e)}
            print(f"  [FAIL] Evidence digest verification failed: {e}", file=sys.stderr)
            return report
    else:
        report["checks"]["evidence_checksums"] = {"status": "SKIPPED", "reason": "No audit_evidence dir"}

    # 3. Authoritative test suite execution
    print("[Clean-Room] Executing authorative backend test runner (pytest)...")
    try:
        pytest_proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        report["checks"]["backend_pytest"] = {
            "status": "PASS" if pytest_proc.returncode == 0 else "FAIL",
            "exit_code": pytest_proc.returncode,
            "stdout_summary": pytest_proc.stdout.splitlines()[-2:] if pytest_proc.stdout else [],
        }
        if pytest_proc.returncode == 0:
            print("  [PASS] Pytest suite completed with 0 errors.")
        else:
            print(f"  [FAIL] Pytest failed: {pytest_proc.stderr}", file=sys.stderr)
    except Exception as e:
        report["checks"]["backend_pytest"] = {"status": "ERROR", "error": str(e)}

    # 4. Frontend unit and API test execution
    print("[Clean-Room] Executing frontend test runner (npm test)...")
    try:
        npm_proc = subprocess.run(
            ["npm", "test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            shell=os.name == "nt",
            timeout=180,
        )
        report["checks"]["frontend_test"] = {
            "status": "PASS" if npm_proc.returncode == 0 else "FAIL",
            "exit_code": npm_proc.returncode,
        }
        if npm_proc.returncode == 0:
            print("  [PASS] Frontend test suite completed with 0 errors.")
        else:
            print(f"  [FAIL] Frontend test runner failed: {npm_proc.stderr}", file=sys.stderr)
    except Exception as e:
        report["checks"]["frontend_test"] = {"status": "ERROR", "error": str(e)}

    # Final decision
    all_passed = all(
        c.get("status") == "PASS" or c.get("status") == "SKIPPED"
        for c in report["checks"].values()
    )
    report["passed"] = all_passed
    report["elapsed_seconds"] = round(time.time() - start_time, 2)

    return report


def main():
    parser = argparse.ArgumentParser(description="QuantAlpha Clean-Room Reproducibility Auditor")
    parser.add_argument("--strict", action="store_true", default=True, help="Enforce strict git and clean baseline")
    parser.add_argument("--output", type=str, default=None, help="Save clean-room report to JSON file")
    args = parser.parse_args()

    print("=================================================================")
    print("QuantAlpha Clean-Room Independent Verification Suite")
    print("=================================================================")
    result = run_clean_room_verification(strict=args.strict)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"[Clean-Room] Verification certificate saved to {out_path}")

    if result["passed"]:
        print("=================================================================")
        print("RESULT: PASS -- Independent clean environment verified baseline.")
        print("=================================================================")
        return 0
    else:
        print("=================================================================")
        print("RESULT: FAIL -- Discrepancy detected in clean-room verification.")
        print("=================================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())
