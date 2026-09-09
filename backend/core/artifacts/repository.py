"""
Immutable Content-Addressed Artifact Repository.
Rejects in-place mutation and enforces append-only storage indexed by artifact hash.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, List

from .envelope import ArtifactEnvelope

logger = logging.getLogger(__name__)


class DuplicateArtifactException(Exception):
    """Raised when an attempt is made to overwrite an existing artifact with differing content."""


class ArtifactRepository:
    """
    Immutable content-addressed store for sealed Research Artifacts.
    """

    def __init__(self):
        self._by_hash: Dict[str, ArtifactEnvelope] = {}
        self._by_id: Dict[str, List[ArtifactEnvelope]] = {}

    def store(self, envelope: ArtifactEnvelope) -> str:
        """
        Store a verified artifact envelope.
        Returns the envelope_hash.
        """
        envelope.verify()
        h = envelope.envelope_hash

        if h in self._by_hash:
            # Idempotent re-storage of identical artifact is permitted
            return h

        art_id = envelope.identity.artifact_id
        self._by_hash[h] = envelope
        if art_id not in self._by_id:
            self._by_id[art_id] = []
        self._by_id[art_id].append(envelope)

        logger.debug("Stored artifact %s (%s) with hash %s", art_id, envelope.identity.artifact_type, h)
        return h

    def get_by_hash(self, envelope_hash: str) -> Optional[ArtifactEnvelope]:
        """Retrieve artifact envelope by its composite hash and verify its integrity."""
        env = self._by_hash.get(envelope_hash)
        if env:
            env.verify()
        return env

    def get_latest_by_id(self, artifact_id: str) -> Optional[ArtifactEnvelope]:
        """Retrieve latest version of artifact by ID."""
        versions = self._by_id.get(artifact_id, [])
        if not versions:
            return None
        env = versions[-1]
        env.verify()
        return env

    def count(self) -> int:
        return len(self._by_hash)

    def clear(self) -> None:
        """Testing utility to clear in-memory store."""
        self._by_hash.clear()
        self._by_id.clear()
