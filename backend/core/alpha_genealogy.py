"""
Alpha Genealogy & Research Search Budget Subsystem.
Tracks lineage DAG across genetic programming mutations, crossovers, and AST simplifications.
Maintains exact empirical trial registry count (N_trials) to eliminate multiple-testing selection bias.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set


@dataclass
class AlphaNode:
    """
    Node representing a single alpha candidate in the genealogical DAG.
    """
    alpha_id: str
    parent_ids: List[str]
    expression: str
    ast_hash: str
    generation: int
    complexity: int
    trial_number: int
    dataset_id: str
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    correlation_with_parents: Dict[str, float] = field(default_factory=dict)
    promotion_state: str = "DISCOVERED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha_id": self.alpha_id,
            "parent_ids": self.parent_ids,
            "expression": self.expression,
            "ast_hash": self.ast_hash,
            "generation": self.generation,
            "complexity": self.complexity,
            "trial_number": self.trial_number,
            "dataset_id": self.dataset_id,
            "performance_metrics": self.performance_metrics,
            "correlation_with_parents": self.correlation_with_parents,
            "promotion_state": self.promotion_state,
            "created_at": self.created_at,
        }


@dataclass
class TrialRecord:
    trial_id: str
    candidate_id: str
    generation: int
    parameters: Dict[str, Any]
    dataset: str
    training_period: str
    validation_period: str
    score: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResearchSearchBudget:
    """
    Authoritative Research Trial Registry.
    Accurately records total candidate evaluations (N_trials) conducted during alpha exploration.
    Feeds authoritative trial budgets directly into DSR, PBO, and Hansen SPA statistical tests.
    """

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.trials: List[TrialRecord] = []
        self._nodes: Dict[str, AlphaNode] = {}
        self._ast_hash_registry: Set[str] = set()

    @property
    def total_trials_count(self) -> int:
        """Authoritative N_trials count."""
        return len(self.trials)

    def record_trial(
        self,
        candidate_id: str,
        generation: int,
        parameters: Dict[str, Any],
        dataset: str,
        training_period: str,
        validation_period: str,
        score: float,
    ) -> TrialRecord:
        """Record an evaluated candidate in the trial registry."""
        trial_id = f"TRL-{len(self.trials) + 1:06d}"
        rec = TrialRecord(
            trial_id=trial_id,
            candidate_id=candidate_id,
            generation=generation,
            parameters=parameters,
            dataset=dataset,
            training_period=training_period,
            validation_period=validation_period,
            score=score,
        )
        self.trials.append(rec)
        return rec

    def register_alpha_node(
        self,
        alpha_id: str,
        parent_ids: List[str],
        expression: str,
        generation: int,
        complexity: int,
        dataset_id: str,
        performance_metrics: Optional[Dict[str, float]] = None,
    ) -> AlphaNode:
        """Register an evolved, mutated, or simplified alpha into the genealogy graph."""
        ast_hash = hashlib.sha256(expression.encode("utf-8")).hexdigest()
        self._ast_hash_registry.add(ast_hash)

        node = AlphaNode(
            alpha_id=alpha_id,
            parent_ids=parent_ids,
            expression=expression,
            ast_hash=ast_hash,
            generation=generation,
            complexity=complexity,
            trial_number=len(self.trials),
            dataset_id=dataset_id,
            performance_metrics=performance_metrics or {},
        )
        self._nodes[alpha_id] = node
        return node

    def get_ancestors(self, alpha_id: str) -> List[str]:
        """Retrieve full ancestral lineage for an alpha candidate."""
        ancestors: List[str] = []
        queue = list(self._nodes.get(alpha_id, AlphaNode("", [], "", "", 0, 0, 0, "")).parent_ids)
        visited = set(queue)

        while queue:
            curr = queue.pop(0)
            ancestors.append(curr)
            parent_node = self._nodes.get(curr)
            if parent_node:
                for p in parent_node.parent_ids:
                    if p not in visited:
                        visited.add(p)
                        queue.append(p)
        return ancestors

    def trials_prior_to_discovery(self, alpha_id: str) -> int:
        """Answer: How many strategies did we try before finding this one?"""
        node = self._nodes.get(alpha_id)
        if node:
            return node.trial_number
        return self.total_trials_count

    def compute_manifest_hash(self) -> str:
        payload = f"{self.experiment_id}|{self.total_trials_count}|{len(self._nodes)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
