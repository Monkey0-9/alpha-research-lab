"""
QuantAlpha Level-5 Cryptographic Evidence Subsystem.
Integrity-first research operating system evidence chain, deterministic manifests,
fail-closed verification, and Level-5 reproduction certificates.
"""
from .base import Evidence, EvidenceBundle, EvidenceStatus, compute_canonical_hash
from .data import DataValidationEvidence
from .leakage import LeakageAuditEvidence
from .validation import OOSValidationEvidence, CPCVEvidence
from .statistics import DSREvidence, PBOEvidence, HansenSPAEvidence
from .execution import ExecutionCostEvidence, CapacityEvidence
from .risk import FactorAttributionEvidence, StressTestEvidence
from .falsification import FalsificationEvidence
from .promotion import AlphaStage, ClaimCeiling, QualityGatePolicy, GateDecision

# Level-5 Cryptographic Extensions
from .exceptions import (
    EvidenceException,
    EvidenceChainBrokenException,
    TamperingDetectedException,
    MissingEvidenceException,
    LedgerCorruptionException,
    OptimizationFailedException,
    RiskModelUnavailableException,
    ReproductionFailedException,
)
from .artifact import ArtifactType, ResearchArtifact, compute_sha256
from .manifest import ExperimentManifest, HypothesisManifest, DatasetManifest, UniverseManifest
from .chain import EvidenceChain, GENESIS_PARENT_HASH
from .evidence import EvidenceResult, StageEvidenceStatus
from .certificate import ReproductionCertificate, ReproductionCheckItem, AlphaEvidenceCard
from .verifier import EvidenceChainVerifier, EvidenceVerificationReport
from .graph import EvidenceGraph, EvidenceStage, CANONICAL_STAGE_ORDER

__all__ = [
    # Base & Stages
    "Evidence",
    "EvidenceBundle",
    "EvidenceStatus",
    "compute_canonical_hash",
    "DataValidationEvidence",
    "LeakageAuditEvidence",
    "OOSValidationEvidence",
    "CPCVEvidence",
    "DSREvidence",
    "PBOEvidence",
    "HansenSPAEvidence",
    "ExecutionCostEvidence",
    "CapacityEvidence",
    "FactorAttributionEvidence",
    "StressTestEvidence",
    "FalsificationEvidence",
    "AlphaStage",
    "ClaimCeiling",
    "QualityGatePolicy",
    "GateDecision",
    # Level-5 Cryptographic Elements
    "EvidenceException",
    "EvidenceChainBrokenException",
    "TamperingDetectedException",
    "MissingEvidenceException",
    "LedgerCorruptionException",
    "OptimizationFailedException",
    "RiskModelUnavailableException",
    "ReproductionFailedException",
    "ArtifactType",
    "ResearchArtifact",
    "compute_sha256",
    "ExperimentManifest",
    "HypothesisManifest",
    "DatasetManifest",
    "UniverseManifest",
    "EvidenceChain",
    "GENESIS_PARENT_HASH",
    "EvidenceResult",
    "StageEvidenceStatus",
    "ReproductionCertificate",
    "ReproductionCheckItem",
    "AlphaEvidenceCard",
    "EvidenceChainVerifier",
    "EvidenceVerificationReport",
    "EvidenceGraph",
    "EvidenceStage",
    "CANONICAL_STAGE_ORDER",
]
