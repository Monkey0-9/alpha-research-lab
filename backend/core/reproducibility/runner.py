"""
Independent Level-5 Reproduction Engine.
Orchestrates multi-metric comparison and issues immutable reproduction certificates.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

from .comparator import MultiMetricReproductionComparator
from ..evidence.manifest import ExperimentManifest
from ..evidence.certificate import ReproductionCertificate, ReproductionCheckItem

logger = logging.getLogger(__name__)


class Level5ReproductionEngine:
    """
    Independent Level-5 reproduction engine.
    Verifies experiment outputs across all 14 empirical dimensions without manufacturing evidence.
    """

    @classmethod
    def verify_and_certify(
        cls,
        manifest: ExperimentManifest,
        reference_metrics: Dict[str, Any],
        reproduced_metrics: Dict[str, Any],
        fail_closed: bool = True,
    ) -> ReproductionCertificate:
        """
        Evaluate full multi-metric reproduction and emit authoritative certificate.
        """
        report = MultiMetricReproductionComparator.compare(
            experiment_id=manifest.experiment_id,
            reference=reference_metrics,
            reproduced=reproduced_metrics,
            fail_closed=fail_closed,
        )

        items = [
            ReproductionCheckItem(
                name=r.metric_name,
                passed=r.passed,
                reference_value=r.reference_value,
                reproduced_value=r.reproduced_value,
                detail=r.discrepancy,
            )
            for r in report.results
        ]

        cert = ReproductionCertificate(
            experiment_id=manifest.experiment_id,
            environment_hash=manifest.environment_lock_hash,
            git_sha=manifest.code_sha,
            items=items,
        )
        cert.evaluate()
        return cert
