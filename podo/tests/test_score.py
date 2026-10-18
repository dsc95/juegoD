"""Score (C5): hit=1, ko=30, orb=10; al timeout decide el score."""
from combatcore.core import CombatCore

from conftest import run_ticks


def test_orb_score_decides_timeout(kits, matrix, rules, arena):
    """Team a sobre un orb (+10) vs team b sin score → timeout_score a."""
    core = CombatCore(42, [
        [(kits["pikachu"], 300_000, 300_000)],
        [(kits["snorlax"], 750_000, 300_000)],
    ], matrix, rules, arena, max_ticks=500)
    run_ticks(core, 500)
    assert core.winner == 0
    assert core.outcome() == {"winner": "a", "reason": "timeout_score",
                              "score": [10, 0]}


def test_orb_no_double_pickup_in_window(kits, matrix, rules, arena):
    """El orb no se re-colecciona durante la ventana de respawn."""
    core = CombatCore(42, [
        [(kits["pikachu"], 300_000, 300_000)],
        [(kits["snorlax"], 750_000, 300_000)],
    ], matrix, rules, arena, max_ticks=1800)
    run_ticks(core, 1800)
    assert core.score[0] == 10                    # 1 pickup (ventana 1875)
    assert core.entities[0].charge == 1500


def test_orb_respawns_and_recollects(kits, matrix, rules, arena):
    """A t1875 el orb respawna: un segundo pickup suma de nuevo."""
    core = CombatCore(42, [
        [(kits["pikachu"], 300_000, 300_000)],
        [(kits["snorlax"], 750_000, 300_000)],
    ], matrix, rules, arena, max_ticks=2000)
    run_ticks(core, 2000)
    assert core.score[0] == 20                    # 2 pickups (t0 + t1875)
    assert core.entities[0].charge == 3000
