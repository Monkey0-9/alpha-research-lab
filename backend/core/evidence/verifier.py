"""
Evidence Chain Verifier.
Cryptographic inspection engine verifying hashes, parent links, and stage completeness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .artifact import compute_sha256
from .chain import EvidenceChain
from .exceptions import (
    EvidenceChainBrokenException,
    TamperingDetectedException,
    MissingEvidenceException,
)


@dataclass
class EvidenceVerificationReport:
    valid: bool
    chain_id: str
    artifact_count: int
    tip_hash: str
    broken_index: Optional[int] = None
    error_message: Optional[str] = None
    stage_hashes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "chain_id": self.chain_id,
            "artifact_count": self.artifact_count,
            "tip_hash": self.tip_hash,
            "broken_index": self.broken_index,
            "error_message": self.error_message,
            "stage_hashes": self.stage_hashes,
        }


class EvidenceChainVerifier:
    """
    Independent validator for Level-5 Cryptographic Evidence Chains.
    Strictly verifies parent hashes, envelope hashes, and payload hashes.
    """

    @classmethod
    def verify(cls, chain: EvidenceChain, required_stages: Optional[List[str]] = None) -> EvidenceVerificationReport:
        if not chain.artifacts:
            return EvidenceVerificationReport(
                valid=True,
                chain_id=chain.chain_id,
                artifact_count=0,
                tip_hash=chain.root_hash,
            )

        expected_parent = chain.root_hash
        stage_hashes: Dict[str, str] = {}

        for idx, art in enumerate(chain.artifacts):
            # 1. Payload content verification
            if art.payload:
                computed_content = compute_sha256(art.payload)
                if computed_content != art.content_hash:
                    msg = (
                        f"Tampering detected at artifact #{idx} ({art.artifact_type}): "
                        f"content_hash {art.content_hash} != calculated {computed_content}"
                    )
                    return EvidenceVerificationReport(
                        valid=False,
                        chain_id=chain.chain_id,
                        artifact_count=len(chain.artifacts),
                        tip_hash=art.artifact_hash,
                        broken_index=idx,
                        error_message=msg,
                        stage_hashes=stage_hashes,
                    )

            # 2. Envelope hash verification
            computed_envelope = art.compute_artifact_hash()
            if computed_envelope != art.artifact_hash:
                msg = (
                    f"Envelope tampering detected at artifact #{idx} ({art.artifact_type}): "
                    f"artifact_hash {art.artifact_hash} != calculated {computed_envelope}"
                )
                return EvidenceVerificationReport(
                    valid=False,
                    chain_id=chain.chain_id,
                    artifact_count=len(chain.artifacts),
                    tip_hash=art.artifact_hash,
                    broken_index=idx,
                    error_message=msg,
                    stage_hashes=stage_hashes,
                )

            # 3. Parent link verification
            if art.parent_hash != expected_parent:
                msg = (
                    f"Cryptographic link broken at artifact #{idx} ({art.artifact_type}): "
                    f"parent_hash {art.parent_hash} != expected {expected_parent}"
                )
                return EvidenceVerificationReport(
                    valid=False,
                    chain_id=chain.chain_id,
                    artifact_count=len(chain.artifacts),
                    tip_hash=art.artifact_hash,
                    broken_index=idx,
                    error_message=msg,
                    stage_hashes=stage_hashes,
                )

            expected_parent = art.artifact_hash
            stage_hashes[art.artifact_type] = art.artifact_hash

        # 4. Check required stages presence if specified
        if required_stages:
            for req in required_stages:
                if req not in stage_hashes:
                    msg = f"Missing required evidence stage: {req}"
                    return EvidenceVerificationReport(
                        valid=False,
                        chain_id=chain.chain_id,
                        artifact_count=len(chain.artifacts),
                        tip_hash=expected_parent,
                        error_message=msg,
                        stage_hashes=stage_hashes,
                    )

        return EvidenceVerificationReport(
            valid=True,
            chain_id=chain.chain_id,
            artifact_count=len(chain.artifacts),
            tip_hash=expected_parent,
            stage_hashes=stage_hashes,
        )

    @classmethod
    def assert_valid(cls, chain: EvidenceChain, required_stages: Optional[List[str]] = None) -> None:
        """Fail-closed assertion: raises exception immediately if chain is invalid."""
        report = cls.verify(chain, required_stages=required_stages)
        if not report.valid:
            if "Tampering" in (report.error_message or ""):
                raise TamperingDetectedException(report.error_message)
            if "Missing" in (report.error_message or ""):
                raise MissingEvidenceException(report.error_message)
            raise EvidenceChainBrokenException(report.error_message)
