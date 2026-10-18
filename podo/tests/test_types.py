"""Matriz canónica v1.0.0 (a8) + oráculos de contrato."""
import pytest

from combatcore.contract import compute_damage, type_effectiveness
from combatcore.types import TypeMatrix


def test_canonical_values(matrix):
    # Bulbapedia: electric
    assert matrix.mult("electric", "grass") == 5       # ×0.5
    assert matrix.mult("electric", "flying") == 20     # ×2
    assert matrix.mult("electric", "ground") == 0      # ×0
    assert matrix.mult("electric", "normal") == 10     # ×1
    # grass
    assert matrix.mult("grass", "water") == 20
    assert matrix.mult("grass", "fire") == 5
    # bug
    assert matrix.mult("bug", "psychic") == 20
    assert matrix.mult("bug", "fire") == 5


def test_matrix_complete_324(matrix):
    assert len(matrix.types) == 18
    n = 0
    for a in matrix.types:
        for d in matrix.types:
            matrix.mult(a, d)
            n += 1
    assert n == 324


def test_version_pin(matrix):
    assert matrix.version == "1.0.0"


def test_load_rejects_unknown_scale(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"types": ["a"], "matrix": {"a": {"a": 3}}, '
                 '"version": "x"}', encoding="utf-8")
    with pytest.raises(ValueError):
        TypeMatrix.load(p)


def test_oracle_matches_matrix(matrix):
    assert type_effectiveness("electric", "grass", matrix) == 0.5
    assert type_effectiveness("electric", "flying", matrix) == 2.0
    assert type_effectiveness("electric", "ground", matrix) == 0.0


def test_compute_damage_type_branch(matrix):
    assert compute_damage(10, "electric", "grass", matrix=matrix) == 5
    assert compute_damage(10, "electric", "flying", matrix=matrix) == 20
    assert compute_damage(10, "electric", "ground", matrix=matrix) == 0
    assert compute_damage(10, "electric", "normal", matrix=matrix) == 10
