"""Fixtures del suite CombatCore (sem 2: 3v3 sobre data canónica de a8)."""
import sys
from pathlib import Path

import pytest

PODO = Path(__file__).resolve().parents[1]
if str(PODO) not in sys.path:
    sys.path.insert(0, str(PODO))

from combatcore.core import CombatCore            # noqa: E402
from combatcore.kits import load_kits             # noqa: E402
from combatcore.rules import load_arena, load_rules  # noqa: E402
from combatcore.types import TypeMatrix           # noqa: E402

DATA = PODO / "data"
SPAWN = {0: (250_000, 300_000), 1: (750_000, 300_000)}   # milli-u


@pytest.fixture(scope="session")
def kits():
    return load_kits(DATA)


@pytest.fixture(scope="session")
def matrix():
    return TypeMatrix.load(DATA / "types" / "type_matrix_v1.json")


@pytest.fixture(scope="session")
def rules():
    return load_rules(DATA / "config" / "match_rules.json")


@pytest.fixture(scope="session")
def arena():
    return load_arena(DATA / "arenas" / "arena_001.json")


@pytest.fixture
def make_core(kits, matrix, rules, arena):
    """Fábrica: teams = [(kit_id, ...), (kit_id, ...)] → CombatCore.

    Los miembros de un equipo se apilan desde el spawn (±120 u) para no
    superponerse; el miembro 0 es el activo.
    """
    def make(teams, seed=42, max_ticks=10_000):
        out = []
        for tm, ids in enumerate(teams):
            x0, y0 = SPAWN[tm]
            step = 120_000 if tm == 0 else -120_000
            out.append([(kits[i], x0 + step * j, y0)
                        for j, i in enumerate(ids)])
        return CombatCore(seed, out, matrix, rules, arena,
                          max_ticks=max_ticks)
    return make


def run_ticks(core, n, frames_fn=None):
    """Corre n ticks; frames_fn(tick, team) → InputFrame|None (opcional)."""
    from combatcore.frames import InputFrame
    for t in range(n):
        frames = {}
        if frames_fn is not None:
            for tm in (0, 1):
                f = frames_fn(t, tm)
                if f is not None:
                    frames[tm] = f
        core.step(frames)
    return core
