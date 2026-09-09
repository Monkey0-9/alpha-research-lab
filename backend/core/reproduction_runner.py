"""
Level-5 Independent Reproduction Runner.
Re-executes or verifies an experiment manifest against reference artifacts across all 17 dimensions.
Emits the authoritative Level-5 Reproduction Certificate.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List

from .evidence.manifest import ExperimentManifest
from .evidence.certificate import ReproductionCertificate, ReproductionCheckItem

logger = logging.getLogger(__name__)


class ReproductionRunner:
    """
    Independent Level-5 reproduction verification engine.
    Verifies bitwise and mathematical identity without trusting the original researcher's code state.
    """

    @classmethod
    def reproduce_experiment(
        cls,
        manifest: ExperimentManifest,
        reproduced_artifacts: Dict[str, Any],
        reference_artifacts: Dict[str, Any],
    ) -> ReproductionCertificate:
        """
        Execute multi-metric comparison between original sealed manifest/artifacts and newly reproduced run.
        """
        items: List[ReproductionCheckItem] = []

        dimensions = [
            ("Dataset", "dataset_id"),
            ("Dataset SHA256", "dataset_sha256"),
            ("Universe", "universe_hash"),
            ("PIT Semantics", "pit_clean"),
            ("Features", "features_hash"),
            ("Alpha AST", "alpha_ast_hash"),
            ("Model", "model_hash"),
            ("Configuration", "config_hash"),
            ("Code SHA", "code_sha"),
            ("Environment", "env_lock_hash"),
            ("Statistical Tests", "statistics_hash"),
            ("Execution", "execution_hash"),
            ("Ledger", "ledger_balanced"),
            ("Risk", "risk_model_hash"),
            ("Equity Curve", "equity_curve_hash"),
            ("Trade Blotter", "trade_blotter_hash"),
            ("Evidence Chain", "evidence_chain_verified"),
        ]

        for display_name, key in dimensions:
            ref_val = reference_artifacts.get(key, manifest.to_dict().get(key))
            rep_val = reproduced_artifacts.get(key)

            # Strict equality requirement for Level-5 exact reproduction
            passed = (ref_val == rep_val) and (ref_val is not None)
            items.append(
                ReproductionCheckItem(
                    name=display_name,
                    passed=passed,
                    reference_value=ref_val,
                    reproduced_value=rep_val,
                    detail="Match" if passed else f"Discrepancy: {ref_val} != {rep_val}",
                )
            )

        cert = ReproductionCertificate(
            experiment_id=manifest.experiment_id,
            environment_hash=reproduced_artifacts.get("env_lock_hash", "CURRENT_ENV"),
            git_sha=reproduced_artifacts.get("code_sha", "CURRENT_GIT"),
            items=items,
        )
        cert.evaluate()
        return cert
