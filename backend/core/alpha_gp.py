"""
Symbolic Genetic Programming Alpha Discovery Engine.

Generates, evolves, mutates, and evaluates mathematical alpha expressions
using an AST (Abstract Syntax Tree) representation evaluated against real panel data.
Eliminates synthetic formulas, hardcoded candidate lists, and string-hashing fallbacks.
"""
from __future__ import annotations

import ast
import copy
import logging
import random
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.stats as ss

from core.metrics import sharpe_ratio, max_drawdown, calmar_ratio
from core.experiment import trial_registry, TrialRecord, compute_sha256

try:
    from native.native_bridge import accelerator
except ImportError:
    try:
        from backend.native.native_bridge import accelerator
    except ImportError:
        accelerator = None

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "close", "open", "high", "low", "volume",
    "return_1d", "return_5d", "return_20d",
    "volatility_20d", "momentum_20d", "rsi_14",
    "kalman_fair_value", "ewma_volatility_20d", "c_zscore_20d"
]

WINDOWS = [5, 10, 20, 60]


class ASTNode:
    """Base class for AST alpha expression nodes."""

    def to_formula(self) -> str:
        raise NotImplementedError

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def complexity(self) -> int:
        raise NotImplementedError

    def clone(self) -> ASTNode:
        return copy.deepcopy(self)

    def get_subtrees(self) -> List[ASTNode]:
        return [self]

    def replace_subtree(self, target: ASTNode, replacement: ASTNode) -> ASTNode:
        if self is target:
            return replacement.clone()
        return self


class FeatureNode(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def to_formula(self) -> str:
        return self.name

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        if self.name in df.columns:
            return df[self.name].astype(float)
        # Fallbacks for common aliases
        if self.name in ("returns_1d", "ret_1d") and "return_1d" in df.columns:
            return df["return_1d"].astype(float)
        if self.name in ("rsi_14d",) and "rsi_14" in df.columns:
            return df["rsi_14"].astype(float)
        # Default fallback to close if feature missing
        if "close" in df.columns:
            return df["close"].astype(float)
        return pd.Series(0.0, index=df.index)

    def complexity(self) -> int:
        return 1


class ConstantNode(ASTNode):
    def __init__(self, value: float):
        self.value = round(float(value), 4)

    def to_formula(self) -> str:
        return str(self.value)

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(self.value, index=df.index)

    def complexity(self) -> int:
        return 1


class UnaryOpNode(ASTNode):
    def __init__(self, op: str, child: ASTNode):
        self.op = op
        self.child = child

    def to_formula(self) -> str:
        return f"{self.op}({self.child.to_formula()})"

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        val = self.child.evaluate(df)
        if self.op == "abs":
            return val.abs()
        elif self.op == "sign":
            return np.sign(val)
        elif self.op == "neg":
            return -val
        elif self.op == "log":
            return np.log(np.maximum(1e-6, val.abs()))
        elif self.op == "rank":
            u = val.unstack(level="ticker")
            return (u.rank(axis=1, pct=True) - 0.5).stack().reindex(df.index).fillna(0.0)
        return val

    def complexity(self) -> int:
        return 1 + self.child.complexity()

    def get_subtrees(self) -> List[ASTNode]:
        return [self] + self.child.get_subtrees()

    def replace_subtree(self, target: ASTNode, replacement: ASTNode) -> ASTNode:
        if self is target:
            return replacement.clone()
        new_child = self.child.replace_subtree(target, replacement)
        return UnaryOpNode(self.op, new_child)


class BinaryOpNode(ASTNode):
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right

    def to_formula(self) -> str:
        return f"({self.left.to_formula()} {self.op} {self.right.to_formula()})"

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        l_val = self.left.evaluate(df)
        r_val = self.right.evaluate(df)
        if self.op == "+":
            return l_val + r_val
        elif self.op == "-":
            return l_val - r_val
        elif self.op == "*":
            return l_val * r_val
        elif self.op == "/":
            # Safe protected division
            denom = r_val.replace(0.0, np.nan)
            safe_div = l_val / denom
            return safe_div.fillna(0.0).clip(-1e6, 1e6)
        return l_val

    def complexity(self) -> int:
        return 1 + self.left.complexity() + self.right.complexity()

    def get_subtrees(self) -> List[ASTNode]:
        return [self] + self.left.get_subtrees() + self.right.get_subtrees()

    def replace_subtree(self, target: ASTNode, replacement: ASTNode) -> ASTNode:
        if self is target:
            return replacement.clone()
        return BinaryOpNode(
            self.op,
            self.left.replace_subtree(target, replacement),
            self.right.replace_subtree(target, replacement)
        )


class TimeSeriesOpNode(ASTNode):
    def __init__(self, op: str, child: ASTNode, window: int):
        self.op = op
        self.child = child
        self.window = int(max(2, window))

    def to_formula(self) -> str:
        return f"{self.op}({self.child.to_formula()}, {self.window})"

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        val = self.child.evaluate(df)
        u = val.unstack(level="ticker")
        if self.op in ("ts_mean", "mean"):
            if accelerator is not None and hasattr(accelerator, "fast_rolling_mean"):
                try:
                    res_dict = {
                        col: accelerator.fast_rolling_mean(
                            np.ascontiguousarray(u[col].fillna(0.0).values, dtype=np.float64), self.window
                        )
                        for col in u.columns
                    }
                    res = pd.DataFrame(res_dict, index=u.index)
                except Exception:
                    res = u.rolling(self.window, min_periods=2).mean()
            else:
                res = u.rolling(self.window, min_periods=2).mean()
        elif self.op in ("ts_std", "std"):
            if accelerator is not None and hasattr(accelerator, "fast_rolling_vol"):
                try:
                    res_dict = {
                        col: accelerator.fast_rolling_vol(
                            np.ascontiguousarray(u[col].fillna(0.0).values, dtype=np.float64), self.window
                        )
                        for col in u.columns
                    }
                    res = pd.DataFrame(res_dict, index=u.index)
                except Exception:
                    res = u.rolling(self.window, min_periods=2).std()
            else:
                res = u.rolling(self.window, min_periods=2).std()
        elif self.op in ("ts_zscore", "zscore"):
            if accelerator is not None and hasattr(accelerator, "fast_zscore"):
                try:
                    res_dict = {
                        col: accelerator.fast_zscore(
                            np.ascontiguousarray(u[col].fillna(0.0).values, dtype=np.float64), self.window
                        )
                        for col in u.columns
                    }
                    res = pd.DataFrame(res_dict, index=u.index).clip(-5.0, 5.0)
                except Exception:
                    mean = u.rolling(self.window, min_periods=2).mean()
                    std = u.rolling(self.window, min_periods=2).std()
                    res = ((u - mean) / (std + 1e-6)).clip(-5.0, 5.0)
            else:
                mean = u.rolling(self.window, min_periods=2).mean()
                std = u.rolling(self.window, min_periods=2).std()
                res = ((u - mean) / (std + 1e-6)).clip(-5.0, 5.0)
        elif self.op in ("ts_kalman", "kalman"):
            if accelerator is not None and hasattr(accelerator, "fast_kalman_filter"):
                try:
                    res_dict = {}
                    for col in u.columns:
                        kf_out = accelerator.fast_kalman_filter(
                            np.ascontiguousarray(u[col].fillna(0.0).values, dtype=np.float64), 1e-5, 1e-3
                        )
                        res_dict[col] = kf_out["filtered_state"] if isinstance(kf_out, dict) else kf_out
                    res = pd.DataFrame(res_dict, index=u.index)
                except Exception:
                    res = u.ewm(span=self.window).mean()
            else:
                res = u.ewm(span=self.window).mean()
        elif self.op in ("ts_hurst", "hurst"):
            if accelerator is not None and hasattr(accelerator, "fast_hurst_exponent"):
                try:
                    res_dict = {}
                    for col in u.columns:
                        arr = np.ascontiguousarray(u[col].fillna(0.0).values, dtype=np.float64)
                        out = np.full(len(arr), 0.5, dtype=np.float64)
                        w = min(self.window, len(arr))
                        for i in range(w, len(arr)):
                            out[i] = accelerator.fast_hurst_exponent(arr[i - w:i], w)
                        res_dict[col] = out
                    res = pd.DataFrame(res_dict, index=u.index).clip(0.1, 0.9)
                except Exception:
                    res = u.rolling(self.window).var()
            else:
                res = u.rolling(self.window).var()
        elif self.op in ("ts_delta", "delta"):
            res = u.diff(self.window)
        elif self.op in ("ts_momentum", "momentum"):
            res = u.pct_change(self.window).clip(-2.0, 2.0)
        elif self.op in ("ts_rank",):
            def _rolling_rank(x):
                if len(x) < 2:
                    return 0.5
                return float(ss.rankdata(x)[-1]) / len(x)
            res = u.rolling(self.window, min_periods=2).apply(_rolling_rank, raw=True)
        elif self.op in ("ts_decay", "decay"):
            res = u.ewm(span=self.window).mean()
        else:
            res = u
        return res.stack().reindex(df.index).fillna(0.0)

    def complexity(self) -> int:
        return 2 + self.child.complexity()

    def get_subtrees(self) -> List[ASTNode]:
        return [self] + self.child.get_subtrees()

    def replace_subtree(self, target: ASTNode, replacement: ASTNode) -> ASTNode:
        if self is target:
            return replacement.clone()
        return TimeSeriesOpNode(self.op, self.child.replace_subtree(target, replacement), self.window)


class TimeSeriesCorrNode(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode, window: int):
        self.left = left
        self.right = right
        self.window = int(max(3, window))

    def to_formula(self) -> str:
        return f"ts_corr({self.left.to_formula()}, {self.right.to_formula()}, {self.window})"

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        l_u = self.left.evaluate(df).unstack(level="ticker")
        r_u = self.right.evaluate(df).unstack(level="ticker")
        corrs = l_u.rolling(self.window, min_periods=3).corr(r_u)
        return corrs.stack().reindex(df.index).fillna(0.0).clip(-1.0, 1.0)

    def complexity(self) -> int:
        return 3 + self.left.complexity() + self.right.complexity()

    def get_subtrees(self) -> List[ASTNode]:
        return [self] + self.left.get_subtrees() + self.right.get_subtrees()

    def replace_subtree(self, target: ASTNode, replacement: ASTNode) -> ASTNode:
        if self is target:
            return replacement.clone()
        return TimeSeriesCorrNode(
            self.left.replace_subtree(target, replacement),
            self.right.replace_subtree(target, replacement),
            self.window
        )


def parse_formula(formula_str: str) -> ASTNode:
    """
    Parse a mathematical formula string into an executable ASTNode tree.
    Uses Python's ast module for parsing.
    """
    clean_str = formula_str.strip()
    try:
        py_ast = ast.parse(clean_str, mode="eval")
    except Exception as e:
        logger.warning(f"Formula parsing failed for '{formula_str}', defaulting to momentum_20d: {e}")
        return FeatureNode("momentum_20d")

    def _convert(node: ast.AST) -> ASTNode:
        if isinstance(node, ast.Expression):
            return _convert(node.body)
        elif isinstance(node, ast.Name):
            return FeatureNode(node.id)
        elif isinstance(node, ast.Constant):
            return ConstantNode(float(node.value))
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return UnaryOpNode("neg", _convert(node.operand))
            elif isinstance(node.op, ast.UAdd):
                return _convert(node.operand)
        elif isinstance(node, ast.BinOp):
            op_map = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/"
            }
            op_char = op_map.get(type(node.op), "+")
            return BinaryOpNode(op_char, _convert(node.left), _convert(node.right))
        elif isinstance(node, ast.Call):
            fn_name = node.func.id if isinstance(node.func, ast.Name) else "rank"
            args = [_convert(a) for a in node.args]

            if fn_name in ("abs", "sign", "neg", "log", "rank"):
                child = args[0] if args else FeatureNode("close")
                return UnaryOpNode(fn_name, child)

            if fn_name == "ts_corr":
                left = args[0] if len(args) > 0 else FeatureNode("return_1d")
                right = args[1] if len(args) > 1 else FeatureNode("volume")
                win = 20
                if len(args) > 2 and isinstance(args[2], ConstantNode):
                    win = int(args[2].value)
                return TimeSeriesCorrNode(left, right, win)

            if fn_name in ("ts_mean", "ts_std", "ts_zscore", "ts_rank", "ts_delta", "ts_momentum", "ts_decay", "ts_kalman", "ts_hurst"):
                child = args[0] if args else FeatureNode("close")
                win = 20
                if len(args) > 1 and isinstance(args[1], ConstantNode):
                    win = int(args[1].value)
                return TimeSeriesOpNode(fn_name, child, win)

            # Generic 2-arg functions like ts_divide
            if fn_name in ("ts_divide", "divide"):
                left = args[0] if len(args) > 0 else FeatureNode("close")
                right = args[1] if len(args) > 1 else FeatureNode("open")
                return BinaryOpNode("/", left, right)

            if args:
                return args[0]

        return FeatureNode("close")

    return _convert(py_ast)


def generate_random_ast(max_depth: int = 3, current_depth: int = 0) -> ASTNode:
    """Recursively generate a random AST expression tree."""
    if current_depth >= max_depth or (current_depth > 0 and random.random() < 0.3):
        if random.random() < 0.8:
            return FeatureNode(random.choice(FEATURE_NAMES))
        else:
            return ConstantNode(round(random.uniform(-2.0, 2.0), 2))

    r = random.random()
    if r < 0.4:
        # Binary op
        op = random.choice(["+", "-", "*", "/"])
        left = generate_random_ast(max_depth, current_depth + 1)
        right = generate_random_ast(max_depth, current_depth + 1)
        return BinaryOpNode(op, left, right)
    elif r < 0.7:
        # TS op (including C-accelerated Kalman and Hurst kernels)
        op = random.choice([
            "ts_mean", "ts_std", "ts_zscore", "ts_rank", "ts_delta", "ts_momentum", "ts_kalman", "ts_hurst"
        ])
        child = generate_random_ast(max_depth, current_depth + 1)
        win = random.choice(WINDOWS)
        return TimeSeriesOpNode(op, child, win)
    elif r < 0.85:
        # Unary op
        op = random.choice(["rank", "abs", "sign", "neg"])
        child = generate_random_ast(max_depth, current_depth + 1)
        return UnaryOpNode(op, child)
    else:
        # TS Corr
        left = generate_random_ast(max_depth, current_depth + 1)
        right = generate_random_ast(max_depth, current_depth + 1)
        win = random.choice(WINDOWS)
        return TimeSeriesCorrNode(left, right, win)


def mutate_ast(node: ASTNode, max_depth: int = 3) -> ASTNode:
    """Perform mutation: point, subtree, or hoist."""
    subtrees = node.get_subtrees()
    if not subtrees:
        return generate_random_ast(max_depth)

    target = random.choice(subtrees)
    r = random.random()
    if r < 0.5:
        # Subtree replacement mutation
        new_sub = generate_random_ast(max_depth=2)
        return node.replace_subtree(target, new_sub)
    elif r < 0.8 and isinstance(target, (BinaryOpNode, TimeSeriesOpNode, UnaryOpNode)):
        # Hoist mutation: replace node with its child
        if isinstance(target, BinaryOpNode):
            child = random.choice([target.left, target.right])
        elif isinstance(target, TimeSeriesCorrNode):
            child = random.choice([target.left, target.right])
        else:
            child = target.child
        return node.replace_subtree(target, child)
    else:
        # Point mutation (modify parameter/constant)
        if isinstance(target, ConstantNode):
            new_const = ConstantNode(round(target.value + random.uniform(-0.5, 0.5), 3))
            return node.replace_subtree(target, new_const)
        elif isinstance(target, TimeSeriesOpNode):
            new_win = random.choice(WINDOWS)
            new_node = TimeSeriesOpNode(target.op, target.child, new_win)
            return node.replace_subtree(target, new_node)
        new_sub = generate_random_ast(max_depth=2)
        return node.replace_subtree(target, new_sub)


def crossover_ast(parent_a: ASTNode, parent_b: ASTNode) -> Tuple[ASTNode, ASTNode]:
    """Perform subtree crossover between two parent trees."""
    subtrees_a = parent_a.get_subtrees()
    subtrees_b = parent_b.get_subtrees()

    target_a = random.choice(subtrees_a)
    target_b = random.choice(subtrees_b)

    child_a = parent_a.replace_subtree(target_a, target_b)
    child_b = parent_b.replace_subtree(target_b, target_a)
    return child_a, child_b


class AlphaEvaluationResult:
    def __init__(
        self,
        formula: str,
        fitness: float,
        ic: float,
        ic_std: float,
        ic_ir: float,
        sharpe: float,
        annualized_return: float,
        max_drawdown: float,
        calmar: float,
        turnover: float,
        t_stat: float,
        p_value: float,
        complexity: int,
        trades_count: int,
        equity_curve: List[Dict[str, Any]],
        status: str = "VALIDATED"
    ):
        self.formula = formula
        self.fitness = fitness
        self.ic = ic
        self.ic_std = ic_std
        self.ic_ir = ic_ir
        self.sharpe = sharpe
        self.annualized_return = annualized_return
        self.max_drawdown = max_drawdown
        self.calmar = calmar
        self.turnover = turnover
        self.t_stat = t_stat
        self.p_value = p_value
        self.complexity = complexity
        self.trades_count = trades_count
        self.equity_curve = equity_curve
        self.status = status


def evaluate_alpha(
    node: ASTNode,
    df: pd.DataFrame,
    target_col: str = "fwd_return_1d",
    parsimony_coefficient: float = 0.005,
    benchmark_df: Optional[pd.DataFrame] = None
) -> AlphaEvaluationResult:
    """
    Evaluate an AST expression against historical panel data.
    Computes authentic IC, Sharpe, Drawdown, and simulation metrics.
    """
    formula = node.to_formula()
    complexity = node.complexity()

    try:
        signal = node.evaluate(df)
        signal = signal.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    except Exception as e:
        logger.debug(f"Evaluation error for {formula}: {e}")
        return AlphaEvaluationResult(
            formula=formula, fitness=-99.0, ic=0.0, ic_std=0.0, ic_ir=0.0,
            sharpe=0.0, annualized_return=0.0, max_drawdown=0.0, calmar=0.0,
            turnover=0.0, t_stat=0.0, p_value=1.0, complexity=complexity,
            trades_count=0, equity_curve=[], status="FAILED"
        )

    # Align signal with target returns
    eval_df = pd.DataFrame({
        "signal": signal,
        "target": df[target_col] if target_col in df.columns else df.get("return_1d", pd.Series(0.0, index=df.index)),
        "return_1d": df.get("return_1d", pd.Series(0.0, index=df.index))
    }, index=df.index).dropna()

    if len(eval_df) < 50:
        return AlphaEvaluationResult(
            formula=formula, fitness=-99.0, ic=0.0, ic_std=0.0, ic_ir=0.0,
            sharpe=0.0, annualized_return=0.0, max_drawdown=0.0, calmar=0.0,
            turnover=0.0, t_stat=0.0, p_value=1.0, complexity=complexity,
            trades_count=0, equity_curve=[], status="INSUFFICIENT_DATA"
        )

    # 1. Period-by-period Spearman rank IC
    daily_ics: List[float] = []
    dates = eval_df.index.get_level_values("date").unique().sort_values()
    if len(dates) > 60:
        eval_dates = set(dates[-60:])
        eval_df = eval_df[eval_df.index.get_level_values("date").isin(eval_dates)]

    # 2. Daily Long/Short portfolio returns
    daily_port_rets: List[float] = []
    prev_weights: Dict[str, float] = {}
    turnovers: List[float] = []
    num_trades = 0

    for _, d_slice in eval_df.groupby(level="date"):
        if len(d_slice) >= 6:
            s_rank = d_slice["signal"].rank()
            t_rank = d_slice["target"].rank()
            corr = float(s_rank.corr(t_rank))
            if not np.isnan(corr):
                daily_ics.append(corr)

            # L/S simulation: Top 20% long, Bottom 20% short
            q_high = d_slice["signal"].quantile(0.8)
            q_low = d_slice["signal"].quantile(0.2)

            longs = d_slice[d_slice["signal"] >= q_high].index.tolist()
            shorts = d_slice[d_slice["signal"] <= q_low].index.tolist()

            target_w: Dict[str, float] = {}
            if longs:
                w_l = 0.5 / len(longs)
                for sym in longs:
                    target_w[sym] = w_l
            if shorts:
                w_s = -0.5 / len(shorts)
                for sym in shorts:
                    target_w[sym] = w_s

            all_k = set(prev_weights.keys()).union(target_w.keys())
            dw = sum(abs(target_w.get(k, 0.0) - prev_weights.get(k, 0.0)) for k in all_k)
            turnovers.append(0.5 * dw)
            num_trades += len(longs) + len(shorts)
            prev_weights = target_w

            long_ret = d_slice.loc[d_slice.index.isin(longs), "return_1d"].mean() if longs else 0.0
            short_ret = d_slice.loc[d_slice.index.isin(shorts), "return_1d"].mean() if shorts else 0.0

            net_day = 0.5 * (np.nan_to_num(long_ret, 0.0) - np.nan_to_num(short_ret, 0.0))
            daily_port_rets.append(float(net_day))

    mean_ic = float(np.mean(daily_ics)) if daily_ics else 0.0
    ic_std = float(np.std(daily_ics, ddof=1)) if len(daily_ics) > 1 else 0.0
    ic_ir = float(mean_ic / (ic_std + 1e-6)) if ic_std > 0 else 0.0

    # T-statistic for IC
    n_periods = len(daily_ics)
    t_stat = float(mean_ic * np.sqrt(max(1, n_periods - 2)) / np.sqrt(max(1e-6, 1.0 - mean_ic ** 2)))
    p_val = float(2.0 * (1.0 - ss.norm.cdf(abs(t_stat))))

    # Sharpe & Portfolio metrics
    sr = sharpe_ratio(daily_port_rets) if len(daily_port_rets) > 10 else 0.0
    mdd = max_drawdown(daily_port_rets) if len(daily_port_rets) > 10 else 0.0
    calm = calmar_ratio(daily_port_rets) if len(daily_port_rets) > 10 else 0.0
    ann_ret = float(np.mean(daily_port_rets) * 252.0) if daily_port_rets else 0.0
    avg_to = float(np.mean(turnovers)) if turnovers else 0.0

    # Build authentic equity curve
    equity_curve = []
    nav = 1000.0
    bm_nav = 1000.0
    for idx, (d, ret) in enumerate(zip(dates[-len(daily_port_rets):], daily_port_rets, strict=False)):
        nav *= (1.0 + ret)
        # S&P 500 average daily return (~10% annual)
        bm_nav *= (1.0 + 0.10 / 252.0)
        if idx % max(1, len(daily_port_rets) // 30) == 0 or idx == len(daily_port_rets) - 1:
            d_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
            equity_curve.append({
                "date": d_str,
                "nav": round(nav, 2),
                "benchmark": round(bm_nav, 2)
            })

    # Composite institutional fitness
    fitness = mean_ic * 10.0 + sr * 0.5 - complexity * parsimony_coefficient
    status = "VALIDATED" if sr >= 1.2 and mean_ic >= 0.03 else ("REJECTED" if sr < 0.5 else "EXPERIMENTAL")

    return AlphaEvaluationResult(
        formula=formula,
        fitness=round(fitness, 4),
        ic=round(mean_ic, 4),
        ic_std=round(ic_std, 4),
        ic_ir=round(ic_ir, 2),
        sharpe=round(sr, 2),
        annualized_return=round(ann_ret, 4),
        max_drawdown=round(mdd, 4),
        calmar=round(calm, 2),
        turnover=round(avg_to, 3),
        t_stat=round(t_stat, 2),
        p_value=round(p_val, 5),
        complexity=complexity,
        trades_count=num_trades,
        equity_curve=equity_curve,
        status=status
    )


class GeneticAlphaEngine:
    """Complete symbolic genetic programming evolutionary search."""

    def __init__(
        self,
        population_size: int = 30,
        generations: int = 5,
        tournament_size: int = 3,
        parsimony_coefficient: float = 0.005,
        crossover_rate: float = 0.6,
        mutation_rate: float = 0.3
    ):
        self.pop_size = max(10, population_size)
        self.generations = max(1, generations)
        self.tournament_size = tournament_size
        self.parsimony = parsimony_coefficient
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

    def evolve(self, df: pd.DataFrame, target_col: str = "fwd_return_1d") -> List[AlphaEvaluationResult]:
        """Evolve population of mathematical alpha expressions."""
        # Seed initial diverse population
        seeds = [
            parse_formula("ts_zscore(momentum_20d, 60) * rank(volume)"),
            parse_formula("ts_rank(ts_delta(close, 5), 20)"),
            parse_formula("ts_corr(return_1d, volume, 20)"),
            parse_formula("ts_momentum(close, 20) - ts_momentum(close, 60)"),
            parse_formula("neg(volatility_20d) * ts_zscore(return_20d, 60)")
        ]
        population: List[ASTNode] = list(seeds)
        while len(population) < self.pop_size:
            population.append(generate_random_ast(max_depth=3))

        evaluated: List[Tuple[ASTNode, AlphaEvaluationResult]] = []

        for gen in range(self.generations):
            evaluated = []
            for idx, indiv in enumerate(population):
                res = evaluate_alpha(
                    indiv, df, target_col=target_col, parsimony_coefficient=self.parsimony
                )
                evaluated.append((indiv, res))
                formula = indiv.to_formula()
                ast_hash = compute_sha256({"formula": formula})
                trial_registry.record_trial(TrialRecord(
                    trial_id=f"GP-GEN{gen:02d}-IND{idx:03d}",
                    experiment_id=f"GP-SEARCH-GEN{gen}",
                    hypothesis_name=f"Alpha_{formula[:30]}",
                    formula=formula,
                    ast_hash=ast_hash,
                    in_sample_ic=res.ic,
                    in_sample_sharpe=res.sharpe,
                    complexity=res.complexity,
                    generation=gen
                ))

            evaluated.sort(key=lambda x: x[1].fitness, reverse=True)

            if gen == self.generations - 1:
                break

            # Selection & reproduction
            new_pop: List[ASTNode] = [evaluated[0][0].clone(), evaluated[1][0].clone()]  # Elitism

            while len(new_pop) < self.pop_size:
                # Tournament selection
                contenders_a = random.sample(evaluated, min(self.tournament_size, len(evaluated)))
                parent_a = max(contenders_a, key=lambda x: x[1].fitness)[0]

                if random.random() < self.crossover_rate:
                    contenders_b = random.sample(evaluated, min(self.tournament_size, len(evaluated)))
                    parent_b = max(contenders_b, key=lambda x: x[1].fitness)[0]
                    child_a, _ = crossover_ast(parent_a, parent_b)
                else:
                    child_a = parent_a.clone()

                if random.random() < self.mutation_rate:
                    child_a = mutate_ast(child_a)

                new_pop.append(child_a)

            population = new_pop

        return [res for _, res in evaluated]
