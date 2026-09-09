"""
Artifact Envelope Subsystem.
Enforces tamper-proof encapsulation of artifact payloads bound to their 6-dimensional cryptographic identity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

from .identity import ArtifactIdentity, compute_sha256


class ArtifactTamperingException(Exception):
    """Raised when an artifact's payload or identity envelope fails cryptographic verification."""


class ArtifactIntegrityBreachException(Exception):
    """Raised when an artifact has inconsistent hashes or mismatched parent links."""


@dataclass
class ArtifactEnvelope:
    """
    Cryptographically sealed envelope wrapping artifact payload and identity.
    """
    identity: ArtifactIdentity
    payload: Dict[str, Any] = field(default_factory=dict)
    envelope_hash: str = ""

    def __post_init__(self):
        if not self.envelope_hash:
            self.envelope_hash = self.identity.compute_composite_hash()

    @classmethod
    def create(
        cls,
        artifact_id: str,
        artifact_type: str,
        payload: Dict[str, Any],
        parent_hash: str,
        schema_hash: str = "SCHEMA_DEFAULT_V1",
        code_sha: str = "UNKNOWN_GIT_SHA",
        environment_hash: str = "ENV_LOCK_DEFAULT",
        configuration_hash: str = "CONFIG_DEFAULT",
    ) -> ArtifactEnvelope:
        """Construct, seal, and hash a new ArtifactEnvelope."""
        content_hash = compute_sha256(payload)
        ident = ArtifactIdentity(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            content_hash=content_hash,
            schema_hash=schema_hash,
            parent_hash=parent_hash,
            code_sha=code_sha,
            environment_hash=environment_hash,
            configuration_hash=configuration_hash,
        )
        return cls(identity=ident, payload=payload, envelope_hash=ident.compute_composite_hash())

    def verify(self) -> bool:
        """
        Verify that:
        1. Payload actually computes to identity.content_hash.
        2. Identity envelope correctly computes to envelope_hash.
        """
        actual_content_hash = compute_sha256(self.payload)
        if actual_content_hash != self.identity.content_hash:
            raise ArtifactTamperingException(
                f"Artifact content tampered for {self.identity.artifact_id}: "
                f"expected content_hash {self.identity.content_hash}, but payload hashed to {actual_content_hash}"
            )

        expected_env_hash = self.identity.compute_composite_hash()
        if self.envelope_hash != expected_env_hash:
            raise ArtifactIntegrityBreachException(
                f"Artifact envelope hash corrupted for {self.identity.artifact_id}: "
                f"expected {expected_env_hash}, but envelope recorded {self.envelope_hash}"
            )

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "payload": self.payload,
            "envelope_hash": self.envelope_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArtifactEnvelope:
        ident_data = data["identity"]
        ident = ArtifactIdentity(**ident_data)
        env = cls(
            identity=ident,
            payload=data.get("payload", {}),
            envelope_hash=data.get("envelope_hash", ""),
        )
        env.verify()
        return env
