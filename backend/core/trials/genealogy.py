"""
Alpha Genealogy DAG Subsystem.
Maintains an immutable directed acyclic graph (DAG) of alpha formulations, mutations, and lineages.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set


@dataclass
class AlphaGenealogyNode:
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
            "promotion_state": self.promotion_state,
            "created_at": self.created_at,
        }


class AlphaGenealogyDAG:
    """
    Directed Acyclic Graph tracking genetic exploration and mutation lineage.
    """

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self._nodes: Dict[str, AlphaGenealogyNode] = {}
        self._ast_hash_registry: Set[str] = set()

    def register_node(
        self,
        alpha_id: str,
        expression: str,
        parent_ids: Optional[List[str]] = None,
        generation: int = 0,
        complexity: int = 1,
        trial_number: int = 1,
        dataset_id: str = "SP500_DAILY",
        performance_metrics: Optional[Dict[str, float]] = None,
    ) -> AlphaGenealogyNode:
        ast_hash = hashlib.sha256(expression.strip().encode("utf-8")).hexdigest()
        self._ast_hash_registry.add(ast_hash)

        node = AlphaGenealogyNode(
            alpha_id=alpha_id,
            parent_ids=parent_ids or [],
            expression=expression,
            ast_hash=ast_hash,
            generation=generation,
            complexity=complexity,
            trial_number=trial_number,
            dataset_id=dataset_id,
            performance_metrics=performance_metrics or {},
        )
        self._nodes[alpha_id] = node
        return node

    def get_node(self, alpha_id: str) -> Optional[AlphaGenealogyNode]:
        return self._nodes.get(alpha_id)

    def is_duplicate_ast(self, expression: str) -> bool:
        h = hashlib.sha256(expression.strip().encode("utf-8")).hexdigest()
        return h in self._ast_hash_registry

    def get_lineage(self, alpha_id: str) -> List[AlphaGenealogyNode]:
        """Trace lineage backwards from node to root ancestors."""
        lineage: List[AlphaGenealogyNode] = []
        curr = self._nodes.get(alpha_id)
        if not curr:
            return lineage

        visited = set()
        queue = [curr]
        while queue:
            node = queue.pop(0)
            if node.alpha_id not in visited:
                visited.add(node.alpha_id)
                lineage.append(node)
                for pid in node.parent_ids:
                    p = self._nodes.get(pid)
                    if p:
                        queue.append(p)
        return lineage
