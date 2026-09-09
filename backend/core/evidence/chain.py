"""
Cryptographic Evidence Chain.
Maintains a verifiable, tamper-evident Merkle/blockchain-style linked chain of
research artifacts where each stage's artifact contains the hash of its parent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .artifact import ResearchArtifact
from .exceptions import EvidenceChainBrokenException

logger = logging.getLogger(__name__)

GENESIS_PARENT_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


@dataclass
class EvidenceChain:
    """
    Cryptographic Evidence Chain linking research stages.
    DATASET -> FEATURES -> ALPHA -> VALIDATION -> EXECUTION -> PORTFOLIO -> FINAL EVIDENCE.
    """
    chain_id: str
    experiment_id: str
    artifacts: List[ResearchArtifact] = field(default_factory=list)
    root_hash: str = GENESIS_PARENT_HASH

    def append(self, artifact: ResearchArtifact) -> None:
        """
        Append a research artifact to the chain.
        Verifies that artifact.parent_hash matches the current chain tip.
        """
        artifact.verify_integrity()

        expected_parent = self.artifacts[-1].artifact_hash if self.artifacts else self.root_hash
        if artifact.parent_hash != expected_parent:
            raise EvidenceChainBrokenException(
                f"Cannot append artifact {artifact.artifact_id} ({artifact.artifact_type}): "
                f"expected parent_hash {expected_parent}, but artifact has {artifact.parent_hash}"
            )

        self.artifacts.append(artifact)

    def verify_chain(self) -> bool:
        """
        Verify the complete cryptographic integrity of the entire chain from root to tip.
        Raises EvidenceChainBrokenException or TamperingDetectedException if any anomaly is found.
        """
        if not self.artifacts:
            return True

        expected_parent = self.root_hash
        for idx, art in enumerate(self.artifacts):
            # 1. Verify internal integrity (content & envelope)
            art.verify_integrity()

            # 2. Verify parent linkage
            if art.parent_hash != expected_parent:
                raise EvidenceChainBrokenException(
                    f"Evidence chain broken at index {idx} ({art.artifact_type} / {art.artifact_id}): "
                    f"expected parent {expected_parent}, got {art.parent_hash}"
                )

            expected_parent = art.artifact_hash

        return True

    def get_head(self) -> Optional[ResearchArtifact]:
        return self.artifacts[-1] if self.artifacts else None

    def get_by_type(self, artifact_type: str) -> Optional[ResearchArtifact]:
        for art in self.artifacts:
            if art.artifact_type == artifact_type:
                return art
        return None

    def get_all_by_type(self, artifact_type: str) -> List[ResearchArtifact]:
        return [art for art in self.artifacts if art.artifact_type == artifact_type]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "experiment_id": self.experiment_id,
            "root_hash": self.root_hash,
            "tip_hash": self.get_head().artifact_hash if self.get_head() else self.root_hash,
            "artifact_count": len(self.artifacts),
            "artifacts": [art.to_dict() for art in self.artifacts],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceChain:
        chain = cls(
            chain_id=data["chain_id"],
            experiment_id=data["experiment_id"],
            root_hash=data.get("root_hash", GENESIS_PARENT_HASH),
        )
        for art_data in data.get("artifacts", []):
            art = ResearchArtifact.from_dict(art_data)
            chain.append(art)
        return chain
