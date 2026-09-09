"""
10-Stage Canonical Evidence Graph.
Enforces the mandatory research DAG invariant:
DATA -> FEATURE -> ALPHA -> TRIAL -> VALIDATION -> STATISTICS -> EXECUTION -> RISK -> REPRODUCTION -> DECISION
"""
from __future__ import annotations

import enum
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from .artifact import ResearchArtifact
from .exceptions import MissingEvidenceException, EvidenceChainBrokenException

logger = logging.getLogger(__name__)


class EvidenceStage(str, enum.Enum):
    DATA = "DATA"
    FEATURE = "FEATURE"
    ALPHA = "ALPHA"
    TRIAL = "TRIAL"
    VALIDATION = "VALIDATION"
    STATISTICS = "STATISTICS"
    EXECUTION = "EXECUTION"
    RISK = "RISK"
    REPRODUCTION = "REPRODUCTION"
    DECISION = "DECISION"


CANONICAL_STAGE_ORDER: List[EvidenceStage] = [
    EvidenceStage.DATA,
    EvidenceStage.FEATURE,
    EvidenceStage.ALPHA,
    EvidenceStage.TRIAL,
    EvidenceStage.VALIDATION,
    EvidenceStage.STATISTICS,
    EvidenceStage.EXECUTION,
    EvidenceStage.RISK,
    EvidenceStage.REPRODUCTION,
    EvidenceStage.DECISION,
]


@dataclass
class StageNode:
    stage: EvidenceStage
    artifact: ResearchArtifact
    verified: bool = False
    parent_stage: Optional[EvidenceStage] = None


class EvidenceGraph:
    """
    Strict 10-Stage Directed Acyclic Graph enforcing that every research claim
    is backed by cryptographically linked artifacts through the complete pipeline.
    """

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self._nodes: Dict[EvidenceStage, StageNode] = {}

    def attach_stage(
        self,
        stage: EvidenceStage,
        artifact: ResearchArtifact,
        verify_linkage: bool = True,
    ) -> None:
        """
        Attach a research artifact to a specific stage.
        Verifies that all prerequisite previous stages exist and that parent_hash matches.
        """
        stage_idx = CANONICAL_STAGE_ORDER.index(stage)

        # 1. Prerequisite check: all preceding stages must already be attached
        for prev_idx in range(stage_idx):
            prev_stage = CANONICAL_STAGE_ORDER[prev_idx]
            if prev_stage not in self._nodes:
                raise MissingEvidenceException(
                    f"Cannot attach stage '{stage.value}' for experiment '{self.experiment_id}': "
                    f"prerequisite stage '{prev_stage.value}' is missing."
                )

        # 2. Cryptographic parent linkage check
        if stage_idx > 0 and verify_linkage:
            parent_stage = CANONICAL_STAGE_ORDER[stage_idx - 1]
            parent_node = self._nodes[parent_stage]
            if artifact.parent_hash != parent_node.artifact.artifact_hash:
                raise EvidenceChainBrokenException(
                    f"Stage linkage broken between '{parent_stage.value}' and '{stage.value}': "
                    f"expected parent_hash {parent_node.artifact.artifact_hash}, "
                    f"got {artifact.parent_hash}"
                )

        # 3. Internal artifact integrity check
        artifact.verify_integrity()

        self._nodes[stage] = StageNode(
            stage=stage,
            artifact=artifact,
            verified=True,
            parent_stage=CANONICAL_STAGE_ORDER[stage_idx - 1] if stage_idx > 0 else None,
        )
        logger.debug("Attached verified evidence for stage %s (hash: %s)", stage.value, artifact.artifact_hash)

    def is_stage_complete(self, stage: EvidenceStage) -> bool:
        return stage in self._nodes and self._nodes[stage].verified

    def get_stage_artifact(self, stage: EvidenceStage) -> Optional[ResearchArtifact]:
        node = self._nodes.get(stage)
        return node.artifact if node else None

    def verify_complete_graph(self) -> bool:
        """
        Verifies that all 10 canonical stages are present, non-empty, and cryptographically linked.
        """
        for stage in CANONICAL_STAGE_ORDER:
            if stage not in self._nodes:
                raise MissingEvidenceException(
                    f"Evidence graph incomplete for '{self.experiment_id}': stage '{stage.value}' is missing."
                )
            self._nodes[stage].artifact.verify_integrity()

        # Verify parent chain across all nodes
        for idx in range(1, len(CANONICAL_STAGE_ORDER)):
            curr_stage = CANONICAL_STAGE_ORDER[idx]
            prev_stage = CANONICAL_STAGE_ORDER[idx - 1]
            curr_art = self._nodes[curr_stage].artifact
            prev_art = self._nodes[prev_stage].artifact

            if curr_art.parent_hash != prev_art.artifact_hash:
                raise EvidenceChainBrokenException(
                    f"Graph parent hash mismatch between {prev_stage.value} and {curr_stage.value}: "
                    f"{curr_art.parent_hash} != {prev_art.artifact_hash}"
                )

        return True

    def get_completed_stages(self) -> List[str]:
        return [s.value for s in CANONICAL_STAGE_ORDER if s in self._nodes]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "completed_stages": self.get_completed_stages(),
            "total_stages": len(CANONICAL_STAGE_ORDER),
            "is_fully_certified": len(self._nodes) == len(CANONICAL_STAGE_ORDER),
            "stages": {
                s.value: {
                    "artifact_id": node.artifact.artifact_id,
                    "artifact_hash": node.artifact.artifact_hash,
                    "parent_hash": node.artifact.parent_hash,
                    "created_at": node.artifact.created_at,
                }
                for s, node in self._nodes.items()
            }
        }
