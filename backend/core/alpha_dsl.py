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

import numpy as np
import pandas as pd

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
    CS_RANK = "CS_RANK"
    CS_ZSCORE = "CS_ZSCORE"
    CS_NEUTRALIZE = "CS_NEUTRALIZE"
    CS_SCALE = "CS_SCALE"
    CS_DEMEAN = "CS_DEMEAN"
    # Time-Series Operations
    TS_MEAN = "TS_MEAN"
    TS_STD = "TS_STD"
    TS_RANK = "TS_RANK"
    TS_CORR = "TS_CORR"
    TS_COV = "TS_COV"
    DECAY = "DECAY"
    TS_DECAY_LINEAR = "TS_DECAY_LINEAR"
    TS_WMA = "TS_WMA"
    TS_ZSCORE = "TS_ZSCORE"
    TS_SKEW = "TS_SKEW"
    TS_KURT = "TS_KURT"
    TS_MIN = "TS_MIN"
    TS_MAX = "TS_MAX"
    TS_ARGMIN = "TS_ARGMIN"
    TS_ARGMAX = "TS_ARGMAX"
    TS_DELTA = "TS_DELTA"
    TS_DELAY = "TS_DELAY"
    SIGNED_POWER = "SIGNED_POWER"
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
        if node.op in {OpType.RANK, OpType.ZSCORE, OpType.WINSORIZE, OpType.CS_RANK, OpType.CS_ZSCORE, OpType.CS_DEMEAN}:
            if len(arg_types) != 1:
                raise TypeCheckError(f"Operation {node.op.value} requires 1 argument.")
            if arg_types[0] == DslType.BOOLEAN:
                raise TypeCheckError(f"Cannot perform {node.op.value} on Boolean.")
            node.node_type = arg_types[0]
            return node.node_type

        if node.op in {OpType.NEUTRALIZE, OpType.CS_NEUTRALIZE}:
            if len(arg_types) != 2:
                raise TypeCheckError(f"{node.op.value} requires (target, factor).")
            if arg_types[0] == DslType.BOOLEAN or arg_types[1] == DslType.BOOLEAN:
                raise TypeCheckError(f"{node.op.value} operands cannot be Boolean.")
            node.node_type = arg_types[0]
            return node.node_type

        if node.op == OpType.CS_SCALE:
            if len(arg_types) != 2:
                raise TypeCheckError("CS_SCALE requires (expression, target_leverage).")
            if arg_types[1] != DslType.SCALAR:
                raise TypeCheckError("CS_SCALE target_leverage must be Scalar.")
            node.node_type = arg_types[0]
            return node.node_type

        # 3. Time-Series Operators
        if node.op in {
            OpType.TS_MEAN, OpType.TS_STD, OpType.TS_RANK, OpType.DECAY,
            OpType.TS_DECAY_LINEAR, OpType.TS_WMA, OpType.TS_ZSCORE,
            OpType.TS_SKEW, OpType.TS_KURT, OpType.TS_MIN, OpType.TS_MAX,
            OpType.TS_ARGMIN, OpType.TS_ARGMAX, OpType.TS_DELTA, OpType.TS_DELAY,
            OpType.SIGNED_POWER,
        }:
            if len(arg_types) != 2:
                raise TypeCheckError(f"{node.op.value} requires (expression, window/parameter).")
            if arg_types[1] != DslType.SCALAR:
                raise TypeCheckError(f"{node.op.value} parameter must be Scalar.")
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


class AlphaEvaluator:
    """
    Vectorized Execution Engine for Alpha Expressions across Panel Matrices.
    Supports time-series rolling operations, cross-sectional rankings/neutralizations,
    and mathematical operators across multiple assets and timestamps.
    """

    @classmethod
    def evaluate(cls, expr_or_node: Union[str, ASTNode], data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        if isinstance(expr_or_node, str):
            node = AlphaParser.parse(expr_or_node)
        else:
            node = expr_or_node
        res = cls._eval_node(node, data)
        if isinstance(res, pd.DataFrame):
            return res
        # If scalar, broadcast across the shape of the first dataframe in data
        first_df = next(iter(data.values()))
        return pd.DataFrame(res, index=first_df.index, columns=first_df.columns)

    @classmethod
    def _eval_node(cls, node: ASTNode, data: Dict[str, pd.DataFrame]) -> Union[pd.DataFrame, float]:
        if node.val is not None:
            if isinstance(node.val, (int, float)):
                return float(node.val)
            name = str(node.val).lower()
            for k, v in data.items():
                if k.lower() == name:
                    return v.copy()
            raise KeyError(f"Feature '{node.val}' not found in input data matrices {list(data.keys())}")

        if not node.op:
            raise ValueError("Malformed ASTNode with no operation or value.")

        evaluated_args = [cls._eval_node(arg, data) for arg in node.args]
        op = node.op

        # Unary operations
        if op == OpType.LOG:
            return np.log(np.maximum(1e-7, evaluated_args[0]))
        elif op == OpType.ABS:
            return np.abs(evaluated_args[0])
        elif op == OpType.SIGN:
            return np.sign(evaluated_args[0])

        # Binary Arithmetic
        elif op == OpType.ADD:
            return evaluated_args[0] + evaluated_args[1]
        elif op == OpType.SUB:
            return evaluated_args[0] - evaluated_args[1]
        elif op == OpType.MUL:
            return evaluated_args[0] * evaluated_args[1]
        elif op == OpType.DIV:
            denom = evaluated_args[1]
            if isinstance(denom, pd.DataFrame):
                denom = denom.replace(0, np.nan)
            elif denom == 0:
                denom = np.nan
            return evaluated_args[0] / denom

        # Cross-Sectional Operations
        elif op in {OpType.RANK, OpType.CS_RANK}:
            df = evaluated_args[0]
            return df.rank(axis=1, pct=True) - 0.5
        elif op in {OpType.ZSCORE, OpType.CS_ZSCORE}:
            df = evaluated_args[0]
            mean = df.mean(axis=1)
            std = df.std(axis=1).replace(0, np.nan)
            return df.sub(mean, axis=0).div(std, axis=0).fillna(0.0)
        elif op == OpType.CS_DEMEAN:
            df = evaluated_args[0]
            return df.sub(df.mean(axis=1), axis=0)
        elif op == OpType.WINSORIZE:
            df = evaluated_args[0]
            lower = df.quantile(0.01, axis=1)
            upper = df.quantile(0.99, axis=1)
            return df.clip(lower=lower, upper=upper, axis=0)
        elif op == OpType.CS_SCALE:
            df = evaluated_args[0]
            target = float(evaluated_args[1])
            l1 = df.abs().sum(axis=1).replace(0, np.nan)
            return df.div(l1, axis=0).fillna(0.0) * target
        elif op in {OpType.NEUTRALIZE, OpType.CS_NEUTRALIZE}:
            y = evaluated_args[0]
            x = evaluated_args[1]
            out = y.copy()
            for idx in y.index:
                y_row = y.loc[idx].values
                x_row = x.loc[idx].values
                valid = ~np.isnan(y_row) & ~np.isnan(x_row)
                if np.sum(valid) > 2:
                    xv = x_row[valid]
                    yv = y_row[valid]
                    var_x = float(np.var(xv))
                    if var_x > 1e-9:
                        beta = float(np.cov(xv, yv)[0, 1] / var_x)
                        alpha_val = float(np.mean(yv) - beta * np.mean(xv))
                        res = y_row.copy()
                        res[valid] = yv - (alpha_val + beta * xv)
                        out.loc[idx] = res
            return out

        # Time-Series Operations
        elif op == OpType.TS_MEAN:
            w = int(evaluated_args[1])
            return evaluated_args[0].rolling(window=w, min_periods=max(1, w // 2)).mean()
        elif op == OpType.TS_STD:
            w = int(evaluated_args[1])
            return evaluated_args[0].rolling(window=w, min_periods=max(2, w // 2)).std().fillna(0.0)
        elif op == OpType.TS_MIN:
            w = int(evaluated_args[1])
            return evaluated_args[0].rolling(window=w, min_periods=1).min()
        elif op == OpType.TS_MAX:
            w = int(evaluated_args[1])
            return evaluated_args[0].rolling(window=w, min_periods=1).max()
        elif op == OpType.TS_DELTA:
            w = int(evaluated_args[1])
            return evaluated_args[0].diff(periods=w).fillna(0.0)
        elif op == OpType.TS_DELAY:
            w = int(evaluated_args[1])
            return evaluated_args[0].shift(periods=w)
        elif op == OpType.TS_ZSCORE:
            w = int(evaluated_args[1])
            df = evaluated_args[0]
            rmean = df.rolling(window=w, min_periods=max(2, w // 2)).mean()
            rstd = df.rolling(window=w, min_periods=max(2, w // 2)).std().replace(0, np.nan)
            return ((df - rmean) / rstd).fillna(0.0)
        elif op in {OpType.DECAY, OpType.TS_DECAY_LINEAR}:
            w = int(evaluated_args[1])
            df = evaluated_args[0]
            weights = np.arange(1, w + 1, dtype=np.float64)
            weights /= weights.sum()
            return df.rolling(window=w, min_periods=1).apply(
                lambda x: np.dot(x[-len(weights):], weights[-len(x):]) / np.sum(weights[-len(x):]),
                raw=True
            )
        elif op == OpType.TS_RANK:
            w = int(evaluated_args[1])
            df = evaluated_args[0]
            return df.rolling(window=w, min_periods=max(2, w // 2)).apply(
                lambda x: float(pd.Series(x).rank(pct=True).iloc[-1]),
                raw=False
            )
        elif op == OpType.SIGNED_POWER:
            df = evaluated_args[0]
            power = float(evaluated_args[1])
            return np.sign(df) * (np.abs(df) ** power)
        elif op == OpType.GT:
            return (evaluated_args[0] > evaluated_args[1]).astype(float)
        elif op == OpType.LT:
            return (evaluated_args[0] < evaluated_args[1]).astype(float)
        elif op == OpType.EQ:
            return (evaluated_args[0] == evaluated_args[1]).astype(float)

        raise NotImplementedError(f"Evaluator does not support operator {op.value}")
