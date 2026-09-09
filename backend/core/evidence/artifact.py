"""
Immutable Research Artifact Model.
Forms the fundamental node in the Level-5 Cryptographic Evidence Chain.
"""
from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any

from .exceptions import TamperingDetectedException


class ArtifactType(str, enum.Enum):
    RESEARCH_QUESTION = "RESEARCH_QUESTION"
    HYPOTHESIS = "HYPOTHESIS"
    DATASET_MANIFEST = "DATASET_MANIFEST"
    PIT_DATA = "PIT_DATA"
    FEATURE_MANIFEST = "FEATURE_MANIFEST"
    ALPHA_AST = "ALPHA_AST"
    TRIAL_REGISTRY = "TRIAL_REGISTRY"
    VALIDATION_RESULT = "VALIDATION_RESULT"
    STATISTICAL_TESTS = "STATISTICAL_TESTS"
    FALSIFICATION = "FALSIFICATION"
    EXECUTION_RESULT = "EXECUTION_RESULT"
    PORTFOLIO_RESULT = "PORTFOLIO_RESULT"
    RISK_RESULT = "RISK_RESULT"
    REPRODUCTION_RECORD = "REPRODUCTION_RECORD"
    FINAL_EVIDENCE = "FINAL_EVIDENCE"


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize object to canonically sorted UTF-8 JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def compute_sha256(payload: Any) -> str:
    """Compute deterministic SHA-256 over canonically serialized payload."""
    if isinstance(payload, bytes):
        return hashlib.sha256(payload).hexdigest()
    if isinstance(payload, str):
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


@dataclass
class ResearchArtifact:
    """
    Cryptographically sealed Level-5 Research Artifact.
    Every artifact is uniquely identified, content-hashed, schema-hashed,
    and bound to its parent artifact's cryptographic hash.
    """
    artifact_id: str
    artifact_type: str
    content_hash: str
    schema_hash: str
    parent_hash: str
    producer: str
    code_sha: str
    environment_hash: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    artifact_hash: str = ""

    def __post_init__(self):
        if not self.content_hash and self.payload:
            self.content_hash = compute_sha256(self.payload)
        if not self.artifact_hash:
            self.artifact_hash = self.compute_artifact_hash()

    def compute_artifact_hash(self) -> str:
        """Compute the definitive envelope hash linking content, schema, provenance and parent."""
        header = {
            "artifact_id": self.artifact_id,
            "artifact_type": str(self.artifact_type),
            "content_hash": self.content_hash,
            "schema_hash": self.schema_hash,
            "parent_hash": self.parent_hash,
            "producer": self.producer,
            "code_sha": self.code_sha,
            "environment_hash": self.environment_hash,
            "created_at": self.created_at,
        }
        return compute_sha256(header)

    def verify_integrity(self) -> bool:
        """Verify that content matches content_hash and envelope matches artifact_hash."""
        if self.payload:
            calculated_content_hash = compute_sha256(self.payload)
            if calculated_content_hash != self.content_hash:
                raise TamperingDetectedException(
                    f"Artifact content tampered: expected {self.content_hash}, got {calculated_content_hash}"
                )
        calculated_artifact_hash = self.compute_artifact_hash()
        if calculated_artifact_hash != self.artifact_hash:
            raise TamperingDetectedException(
                f"Artifact envelope tampered: expected {self.artifact_hash}, got {calculated_artifact_hash}"
            )
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": str(self.artifact_type),
            "content_hash": self.content_hash,
            "schema_hash": self.schema_hash,
            "parent_hash": self.parent_hash,
            "producer": self.producer,
            "code_sha": self.code_sha,
            "environment_hash": self.environment_hash,
            "created_at": self.created_at,
            "payload": self.payload,
            "artifact_hash": self.artifact_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResearchArtifact:
        return cls(
            artifact_id=data["artifact_id"],
            artifact_type=data["artifact_type"],
            content_hash=data["content_hash"],
            schema_hash=data["schema_hash"],
            parent_hash=data.get("parent_hash", "GENESIS"),
            producer=data.get("producer", "QUANTALPHA_SYSTEM"),
            code_sha=data.get("code_sha", "UNKNOWN_GIT_SHA"),
            environment_hash=data.get("environment_hash", "DEFAULT_ENV_HASH"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            payload=data.get("payload", {}),
            artifact_hash=data.get("artifact_hash", ""),
        )
