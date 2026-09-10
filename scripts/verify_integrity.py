"""
CLI tool for Gate 0: Evidence Self-Consistency.
Usage:
  python scripts/verify_integrity.py --check
  python scripts/verify_integrity.py --update
"""
import argparse
from pathlib import Path
import sys

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.core.evidence_integrity import (  # noqa: E402
    EvidenceIntegrityVerifier,
    EvidenceTamperedError,
    IntegrityViolationError,
)
from scripts.generate_status import generate_status_report  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="QuantAlpha Gate 0 Evidence Integrity Tool")
    parser.add_argument("--check", action="store_true", help="Verify STATUS.json self-consistency against reality")
    parser.add_argument("--update", action="store_true", help="Regenerate STATUS.json from live ground truth")
    parser.add_argument("--force-clean", action="store_true", help="Force dirty: false in generated status manifest")
    parser.add_argument("--strict-git", action="store_true", help="Enforce exact git commit match")
    parser.add_argument("--strict-clean", action="store_true", help="Enforce working tree cleanliness")
    parser.add_argument("--verify-evidence", action="store_true", help="Verify SHA256SUMS in audit_evidence")
    args = parser.parse_args()

    verifier = EvidenceIntegrityVerifier(ROOT)

    if args.update:
        print("[Gate 0] Updating STATUS.json from live ground-truth...")
        generate_status_report(force_clean=args.force_clean)
        verifier.generate_run_manifest()
        print("[Gate 0] Manifests updated successfully.")
        return 0

    # Default to check if neither update nor check is given, or if --check is explicit
    print("[Gate 0] Verifying Evidence Self-Consistency...")
    try:
        status = verifier.verify_status_manifest(
            enforce_git_commit=args.strict_git,
            enforce_clean_working_tree=args.strict_clean
        )
        print("[Gate 0] PASS: STATUS.json is self-consistent.")
        v = status['verification']
        print(f"         Total tests: {v['total_tests']} "
              f"({v['backend_tests']} backend, {v['frontend_tests']} frontend)")
        print(f"         Routes: {v['nextjs_prerendered_routes_count']}")

        if args.verify_evidence:
            ev_dir = ROOT / "audit_evidence"
            if ev_dir.exists():
                count = verifier.verify_sha256sums(ev_dir)
                print(f"[Gate 0] PASS: Verified {count} audit artifacts against SHA256SUMS.")

        return 0
    except (IntegrityViolationError, EvidenceTamperedError) as err:
        print(f"[Gate 0] FAIL: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
