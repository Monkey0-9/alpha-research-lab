"""
Unit tests for Alpha DSL, Typed AST, Mathematical Canonicalization, and Deduplicating Alpha Registry.
"""
import pytest
from backend.core.alpha_dsl import (
    AlphaParser,
    TypeChecker,
    AlphaRegistry,
    TypeCheckError,
    DuplicateAlphaError,
    DslType,
)


def test_alpha_dsl_parsing_and_canonicalization():
    expr1 = "ADD(open, close)"
    expr2 = "ADD(close, open)"

    ast1 = AlphaParser.parse(expr1)
    ast2 = AlphaParser.parse(expr2)

    # Both must canonicalize to identical sorted representation
    assert ast1.canonical_str() == "ADD(close,open)"
    assert ast2.canonical_str() == "ADD(close,open)"
    assert ast1.ast_hash() == ast2.ast_hash()


def test_alpha_dsl_multiplication_canonicalization():
    expr1 = "MUL(volume, close)"
    expr2 = "MUL(close, volume)"

    ast1 = AlphaParser.parse(expr1)
    ast2 = AlphaParser.parse(expr2)

    assert ast1.canonical_str() == "MUL(close,volume)"
    assert ast2.canonical_str() == "MUL(close,volume)"
    assert ast1.ast_hash() == ast2.ast_hash()


def test_alpha_dsl_nested_transformations():
    expr = "RANK(TS_MEAN(close, 20))"
    ast = AlphaParser.parse(expr)
    assert ast.node_type == DslType.PANEL
    assert ast.complexity() == 4
    assert ast.canonical_str() == "RANK(TS_MEAN(close,20))"


def test_alpha_dsl_type_checking_rejection():
    # GT produces Boolean. Adding Boolean to Panel is illegal!
    illegal_expr = "ADD(close, GT(open, 100))"
    with pytest.raises(TypeCheckError) as exc_info:
        AlphaParser.parse(illegal_expr)
    assert "Boolean" in str(exc_info.value)


def test_alpha_registry_deduplication(tmp_path):
    registry = AlphaRegistry(registry_dir=tmp_path / "alphas")

    # Register initial discovery
    rec1 = registry.register("ADD(open, close)", creator="RESEARCHER_A")
    assert rec1.alpha_id == "ALPHA-000001"
    assert rec1.canonical_expression == "ADD(close,open)"

    # Attempt to register mathematically identical discovery with reversed arguments
    with pytest.raises(DuplicateAlphaError) as exc_info:
        registry.register("ADD(close, open)", creator="RESEARCHER_B")
    assert "Duplicate alpha discovery" in str(exc_info.value)
    assert "ALPHA-000001" in str(exc_info.value)
