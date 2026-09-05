"""
Alpha DSL, Typed AST Engine, Canonicalization & Registry.
Enforces institutional alpha standards:
1. Strict Type System: Scalar, TimeSeries, CrossSection, Panel, Boolean.
2. Compile-Time Type Checking: Rejects invalid type operations (e.g. CrossSection + Boolean).
3. Mathematical AST Canonicalization: (A + B) == (B + A), commutative sorting.
4. Cryptographic AST Hashing: SHA-256 fingerprint prevents duplicate discoveries in the registry.
"""
from __future__ import annotations

import enum
import hashlib
import json
import logging
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set

logger = logging.getLogger(__name__)

REGISTRY_DIR = Path(__file__).resolve().parents[2] / "data" / "alpha_registry"
REGISTRY_DIR.mkdir(parents=True, exist_ok=True)


class DslType(str, enum.Enum):
    SCALAR = "Scalar"
    TIMESERIES = "TimeSeries"
    CROSSSECTION = "CrossSection"
    PANEL = "Panel"
    BOOLEAN = "Boolean"


class OpType(str, enum.Enum):
    # Commutative Binary Arithmetic
    ADD = "ADD"
    MUL = "MUL"
    # Non-commutative Binary Arithmetic
    SUB = "SUB"
    DIV = "DIV"
    # Unary Math
    LOG = "LOG"
    ABS = "ABS"
    SIGN = "SIGN"
    # Cross-Sectional Operations
    RANK = "RANK"
    ZSCORE = "ZSCORE"
    WINSORIZE = "WINSORIZE"
    NEUTRALIZE = "NEUTRALIZE"
    # Time-Series Operations
    TS_MEAN = "TS_MEAN"
    TS_STD = "TS_STD"
    TS_RANK = "TS_RANK"
    TS_CORR = "TS_CORR"
    TS_COV = "TS_COV"
    DECAY = "DECAY"
    # Comparison & Logical
    GT = "GT"
    LT = "LT"
    EQ = "EQ"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


COMMUTATIVE_OPS: Set[OpType] = {OpType.ADD, OpType.MUL, OpType.AND, OpType.OR, OpType.EQ}


class TypeCheckError(Exception):
    """Raised when an expression attempts an illegal operation across types."""
    pass


class DuplicateAlphaError(Exception):
    """Raised when an alpha AST hash matches an already registered discovery."""
    pass


@dataclass
class ASTNode:
    op: Optional[OpType] = None
    args: List[ASTNode] = field(default_factory=list)
    val: Optional[Union[str, float, int]] = None
    node_type: DslType = DslType.PANEL

    def canonical_str(self) -> str:
        """
        Generate mathematically canonical representation.
        Commutative operations (A + B, A * B) sort children alphabetically.
        """
        if self.val is not None:
            if isinstance(self.val, float):
                return f"{self.val:.6g}"
            return str(self.val)

        if not self.op:
            return ""

        child_strs = [arg.canonical_str() for arg in self.args]

        # Canonicalize commutative operations by sorting arguments
        if self.op in COMMUTATIVE_OPS and len(child_strs) >= 2:
            child_strs = sorted(child_strs)

        args_formatted = ",".join(child_strs)
        return f"{self.op.value}({args_formatted})"

    def ast_hash(self) -> str:
        """Compute SHA-256 fingerprint of the canonical representation."""
        c_str = self.canonical_str()
        return hashlib.sha256(c_str.encode("utf-8")).hexdigest()

    def complexity(self) -> int:
        """Compute structural complexity (number of operators + operands)."""
        c = 1
        for arg in self.args:
            c += arg.complexity()
        return c


class TypeChecker:
    """Validates structural correctness and type consistency of Alpha AST expressions."""

    @classmethod
    def infer_and_validate(cls, node: ASTNode) -> DslType:
        if node.val is not None:
            if isinstance(node.val, (int, float)):
                node.node_type = DslType.SCALAR
                return DslType.SCALAR
            # Ticker/feature identifier defaults to Panel or TimeSeries
            node.node_type = DslType.PANEL
            return DslType.PANEL

        if not node.op:
            return node.node_type

        # Recursively check and infer children
        arg_types = [cls.infer_and_validate(arg) for arg in node.args]

        # 1. Commutative and Arithmetic Binary Ops
        if node.op in {OpType.ADD, OpType.SUB, OpType.MUL, OpType.DIV}:
            if len(arg_types) != 2:
                raise TypeCheckError(f"Operation {node.op.value} requires exactly 2 arguments, got {len(arg_types)}.")
            t1, t2 = arg_types[0], arg_types[1]
            if t1 == DslType.BOOLEAN or t2 == DslType.BOOLEAN:
                raise TypeCheckError(f"Cannot perform arithmetic {node.op.value} with Boolean type ({t1}, {t2}).")
            # Panel + Panel -> Panel, Panel + Scalar -> Panel, etc.
            if t1 == DslType.PANEL or t2 == DslType.PANEL:
                node.node_type = DslType.PANEL
            elif t1 == DslType.CROSSSECTION or t2 == DslType.CROSSSECTION:
                node.node_type = DslType.CROSSSECTION
            elif t1 == DslType.TIMESERIES or t2 == DslType.TIMESERIES:
                node.node_type = DslType.TIMESERIES
            else:
                node.node_type = DslType.SCALAR
            return node.node_type

        # 2. Cross-Sectional Transformations
        if node.op in {OpType.RANK, OpType.ZSCORE, OpType.WINSORIZE}:
            if len(arg_types) != 1:
                raise TypeCheckError(f"Operation {node.op.value} requires 1 argument.")
            if arg_types[0] == DslType.BOOLEAN:
                raise TypeCheckError(f"Cannot perform {node.op.value} on Boolean.")
            node.node_type = arg_types[0]
            return node.node_type

        if node.op == OpType.NEUTRALIZE:
            if len(arg_types) != 2:
                raise TypeCheckError("NEUTRALIZE requires (target, factor).")
            if arg_types[0] == DslType.BOOLEAN or arg_types[1] == DslType.BOOLEAN:
                raise TypeCheckError("NEUTRALIZE operands cannot be Boolean.")
            node.node_type = arg_types[0]
            return node.node_type

        # 3. Time-Series Operators
        if node.op in {OpType.TS_MEAN, OpType.TS_STD, OpType.TS_RANK, OpType.DECAY}:
            if len(arg_types) != 2:
                raise TypeCheckError(f"{node.op.value} requires (expression, window).")
            if arg_types[1] != DslType.SCALAR:
                raise TypeCheckError(f"{node.op.value} lookback window must be Scalar.")
            if arg_types[0] == DslType.BOOLEAN:
                raise TypeCheckError(f"Cannot apply {node.op.value} to Boolean.")
            node.node_type = arg_types[0]
            return node.node_type

        if node.op in {OpType.TS_CORR, OpType.TS_COV}:
            if len(arg_types) != 3:
                raise TypeCheckError(f"{node.op.value} requires (x, y, window).")
            if arg_types[2] != DslType.SCALAR:
                raise TypeCheckError(f"{node.op.value} window must be Scalar.")
            node.node_type = arg_types[0]
            return node.node_type

        # 4. Comparisons
        if node.op in {OpType.GT, OpType.LT, OpType.EQ}:
            if len(arg_types) != 2:
                raise TypeCheckError(f"{node.op.value} requires 2 arguments.")
            node.node_type = DslType.BOOLEAN
            return DslType.BOOLEAN

        # 5. Unary
        if node.op in {OpType.LOG, OpType.ABS, OpType.SIGN}:
            if len(arg_types) != 1:
                raise TypeCheckError(f"{node.op.value} requires 1 argument.")
            if arg_types[0] == DslType.BOOLEAN:
                raise TypeCheckError(f"Cannot perform {node.op.value} on Boolean.")
            node.node_type = arg_types[0]
            return node.node_type

        return DslType.PANEL


class AlphaParser:
    """Parses functional Alpha DSL expressions into typed canonical AST trees."""

    @classmethod
    def parse(cls, expr: str) -> ASTNode:
        expr = expr.strip()
        # Check if scalar number
        try:
            val = float(expr)
            if val.is_integer():
                return ASTNode(val=int(val), node_type=DslType.SCALAR)
            return ASTNode(val=val, node_type=DslType.SCALAR)
        except ValueError:
            pass

        # Check function call syntax: OP(arg1, arg2, ...)
        match = re.match(r"^([A-Z_]+)\((.*)\)$", expr)
        if match:
            op_str, inner_args = match.groups()
            try:
                op = OpType(op_str)
            except ValueError:
                raise ValueError(f"Unknown DSL operator '{op_str}' in expression: {expr}")

            # Split arguments respecting nested parentheses
            args_raw = cls._split_args(inner_args)
            child_nodes = [cls.parse(arg) for arg in args_raw]
            node = ASTNode(op=op, args=child_nodes)
            TypeChecker.infer_and_validate(node)
            return node

        # Plain identifier (feature name)
        if re.match(r"^[a-zA-Z0-9_]+$", expr):
            return ASTNode(val=expr, node_type=DslType.PANEL)

        raise ValueError(f"Unable to parse expression: {expr}")

    @staticmethod
    def _split_args(s: str) -> List[str]:
        args = []
        depth = 0
        cur = []
        for char in s:
            if char == "(":
                depth += 1
                cur.append(char)
            elif char == ")":
                depth -= 1
                cur.append(char)
            elif char == "," and depth == 0:
                args.append("".join(cur).strip())
                cur = []
            else:
                cur.append(char)
        if cur:
            args.append("".join(cur).strip())
        return args


@dataclass
class AlphaRecord:
    alpha_id: str
    expression: str
    canonical_expression: str
    ast_hash: str
    complexity: int
    creator: str = "GP_ORCHESTRATOR"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "DISCOVERED"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlphaRegistry:
    """Registry maintaining canonical unique alphas and rejecting duplicate AST discoveries."""

    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or REGISTRY_DIR
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.registry_dir / "alpha_manifest.json"
        self._alphas: Dict[str, AlphaRecord] = self._load()

    def _load(self) -> Dict[str, AlphaRecord]:
        if not self.manifest_file.exists():
            return {}
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return {k: AlphaRecord(**v) for k, v in raw.items()}
        except Exception as e:
            logger.warning(f"Failed to load alpha registry: {e}")
            return {}

    def _save(self) -> None:
        raw = {k: v.to_dict() for k, v in self._alphas.items()}
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    def register(
        self,
        expression: str,
        creator: str = "GP_ORCHESTRATOR",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlphaRecord:
        """Parse, validate, canonicalize, and register alpha if not a duplicate."""
        ast = AlphaParser.parse(expression)
        ast_hash = ast.ast_hash()
        canon_expr = ast.canonical_str()

        # Check for existing discovery with identical AST hash
        for rec in self._alphas.values():
            if rec.ast_hash == ast_hash:
                raise DuplicateAlphaError(
                    f"Duplicate alpha discovery! Expression '{expression}' canonicalizes to "
                    f"'{canon_expr}' (hash={ast_hash[:12]}), matching existing {rec.alpha_id}."
                )

        idx = len(self._alphas) + 1
        alpha_id = f"ALPHA-{idx:06d}"

        record = AlphaRecord(
            alpha_id=alpha_id,
            expression=expression,
            canonical_expression=canon_expr,
            ast_hash=ast_hash,
            complexity=ast.complexity(),
            creator=creator,
            metadata=metadata or {},
        )

        self._alphas[alpha_id] = record
        self._save()
        logger.info(f"Registered {alpha_id}: {canon_expr} (hash={ast_hash[:12]})")
        return record

    def get_by_id(self, alpha_id: str) -> Optional[AlphaRecord]:
        return self._alphas.get(alpha_id)

    def get_by_hash(self, ast_hash: str) -> Optional[AlphaRecord]:
        for rec in self._alphas.values():
            if rec.ast_hash == ast_hash:
                return rec
        return None

    def list_alphas(self) -> List[AlphaRecord]:
        return list(self._alphas.values())


alpha_registry = AlphaRegistry()
