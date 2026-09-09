"""
Artifact Identity Subsystem.
Level-5 Cryptographic Identity encapsulating 6 canonical hashes:
1. Content SHA-256
2. Schema hash
3. Parent envelope hash
4. Code / Git commit SHA
5. Python environment lock hash
6. Configuration / parameter hash
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any

GENESIS_PARENT_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


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


@dataclass(frozen=True)
class ArtifactIdentity:
    """
    Immutable cryptographic identity for an artifact.
    Completely binds code, environment, inputs, parameters, parent linkage, and content.
    """
    artifact_id: str
    artifact_type: str
    content_hash: str
    schema_hash: str
    parent_hash: str
    code_sha: str
    environment_hash: str
    configuration_hash: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_composite_hash(self) -> str:
        """Compute the unforgeable envelope digest over all 6 identity dimensions."""
        header = {
            "artifact_id": self.artifact_id,
            "artifact_type": str(self.artifact_type),
            "content_hash": self.content_hash,
            "schema_hash": self.schema_hash,
            "parent_hash": self.parent_hash,
            "code_sha": self.code_sha,
            "environment_hash": self.environment_hash,
            "configuration_hash": self.configuration_hash,
            "created_at": self.created_at,
        }
        return compute_sha256(header)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "content_hash": self.content_hash,
            "schema_hash": self.schema_hash,
            "parent_hash": self.parent_hash,
            "code_sha": self.code_sha,
            "environment_hash": self.environment_hash,
            "configuration_hash": self.configuration_hash,
            "created_at": self.created_at,
        }
