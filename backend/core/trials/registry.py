"""
Authoritative Trial Registry Subsystem.
Implements append-only audit trail for every candidate evaluation to solve the multiple-testing / file-drawer problem.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrialRecord:
    """
    Immutable record of a single research trial or parameter evaluation.
    """
    trial_id: str
    experiment_id: str
    candidate_id: str
    generation: int
    parameters: Dict[str, Any]
    dataset_id: str
    score: float
    training_period: str
    validation_period: str
    status: str = "COMPLETED"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "experiment_id": self.experiment_id,
            "candidate_id": self.candidate_id,
            "generation": self.generation,
            "parameters": self.parameters,
            "dataset_id": self.dataset_id,
            "score": self.score,
            "training_period": self.training_period,
            "validation_period": self.validation_period,
            "status": self.status,
            "timestamp": self.timestamp,
        }


class TrialRegistry:
    """
    Append-only repository of evaluated research trials.
    Enforces honest accounting of search space exploration without cherry-picking.
    """

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self._trials: List[TrialRecord] = []
        self._by_id: Dict[str, TrialRecord] = {}

    @property
    def total_trials_count(self) -> int:
        """The authoritative N_trials used for Deflated Sharpe Ratio (DSR) & PBO calculations."""
        return len(self._trials)

    def record_trial(
        self,
        candidate_id: str,
        parameters: Dict[str, Any],
        dataset_id: str,
        score: float,
        training_period: str = "",
        validation_period: str = "",
        generation: int = 0,
        status: str = "COMPLETED",
    ) -> TrialRecord:
        """Register a new evaluated parameterization."""
        trial_id = f"TRL-{self.experiment_id}-{len(self._trials) + 1:06d}"
        record = TrialRecord(
            trial_id=trial_id,
            experiment_id=self.experiment_id,
            candidate_id=candidate_id,
            generation=generation,
            parameters=parameters,
            dataset_id=dataset_id,
            score=score,
            training_period=training_period,
            validation_period=validation_period,
            status=status,
        )
        self._trials.append(record)
        self._by_id[trial_id] = record
        return record

    def get_trial(self, trial_id: str) -> Optional[TrialRecord]:
        return self._by_id.get(trial_id)

    def list_trials(self) -> List[TrialRecord]:
        return list(self._trials)

    def get_max_score(self) -> float:
        if not self._trials:
            return 0.0
        return max(t.score for t in self._trials)

    def get_scores(self) -> List[float]:
        return [t.score for t in self._trials]
