"""Ataques: combos (hits), aim (spec Q1 v1.1), matriz de tipos, KO, score.

Posiciones en milli-u. Ranges: pikachu basic 120_000 (1.2 m), snorlax
basic 100_000, gardevoir basic 160_000.
"""
from combatcore.core import WIN_DRAW
from combatcore.entities import IDLE
from combatcore.frames import InputFrame

from conftest import run_ticks


def _basic(t):
    return InputFrame(frame=t, basic=True)


def _dmg_events(core, dst=None):
    return [e for e in core.events if e["ev"] == "damage"
            and (dst is None or e["dst"] == dst)]


def _on_field(core, eid):
    """Pone un miembro bench en el campo (bench → IDLE) para ejercitar el
    tie-break de aim, que en 1v1 real tiene un solo candidato."""
    e = core._by_eid[eid]
    e.state = IDLE


def test_basic_combo_3_hits(make_core, kits, matrix, rules, arena):
    """pikachu basic = 3 hits de 5 en los 3 primeros ticks ACTIVE (t6-8)."""
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["snorlax"], 370_000, 300_000)],
    ], matrix, rules, arena, max_ticks=100)
    run_ticks(core, 30, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    evs = _dmg_events(core)
    assert [e["dmg"] for e in evs] == [5, 5, 5]
    assert [e["t"] for e in evs] == [6, 7, 8]      # windup 6 + hits
    assert core.entities[1].hp == 130 - 15


def test_no_damage_out_of_range(make_core, kits, matrix, rules, arena):
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["snorlax"], 500_000, 300_000)],      # 2.5 m > 1.2 m
    ], matrix, rules, arena, max_ticks=40)
    run_ticks(core, 30, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    assert _dmg_events(core) == []
    assert core.entities[1].hp == 130


def test_type_matrix_half(make_core, kits, matrix, rules, arena):
    """electric vs grass = ×0.5 → 5 se vuelve 2 por hit."""
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["oddish"], 370_000, 300_000)],       # 1.2 m = range básico
    ], matrix, rules, arena, max_ticks=40)
    run_ticks(core, 20, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    evs = _dmg_events(core)
    assert len(evs) == 3
    assert all(e["dmg"] == 2 and e["mult"] == 5 for e in evs)
    assert core.entities[1].hp == 50 - 6


def test_aim_nearest_wins(make_core, kits, matrix, rules, arena):
    """Tie-break (1): menor dist² gana (ambos candidatos en el campo)."""
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["gardevoir"], 250_000, 300_000)],
        [(kits["snorlax"], 380_000, 300_000),
         (kits["snorlax"], 410_000, 300_000)],
    ], matrix, rules, arena, max_ticks=40)
    _on_field(core, 2)
    run_ticks(core, 20, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    evs = _dmg_events(core)
    assert evs, "debió golpear al más cercano"
    assert all(e["dst"] == 1 for e in evs)          # 130_000 < 160_000


def test_aim_angle_tiebreak(make_core, kits, matrix, rules, arena):
    """Tie-break (2): misma distancia → menor ángulo con el facing.

    Triángulo 9-12-15 (×1000): ambos a 150_000; el de mayor proyección
    sobre el facing (dot 120_000) debe ganarle al de dot 90_000 — aunque
    tenga mayor eid (descarta el tie-break 3).
    """
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["gardevoir"], 250_000, 300_000)],
        [(kits["snorlax"], 340_000, 420_000),        # dot 90_000
         (kits["snorlax"], 370_000, 390_000)],       # dot 120_000
    ], matrix, rules, arena, max_ticks=40)
    _on_field(core, 2)
    run_ticks(core, 20, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    evs = _dmg_events(core)
    assert evs
    assert all(e["dst"] == 2 for e in evs)


def test_aim_eid_tiebreak(make_core, kits, matrix, rules, arena):
    """Tie-break (3): misma distancia Y mismo ángulo → menor eid."""
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["gardevoir"], 250_000, 300_000)],
        [(kits["snorlax"], 350_000, 400_000),        # simétricos (100,±100)
         (kits["snorlax"], 350_000, 200_000)],
    ], matrix, rules, arena, max_ticks=40)
    _on_field(core, 2)
    run_ticks(core, 20, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    evs = _dmg_events(core)
    assert evs
    assert all(e["dst"] == 1 for e in evs)


def test_ko_ends_match_and_scores(make_core, kits, matrix, rules, arena):
    """pikachu (15/swing) vs rattata (45 hp): KO en el 3.º swing."""
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["rattata"], 330_000, 300_000)],       # 0.8 m < 1.2 m
    ], matrix, rules, arena, max_ticks=10_000)
    t = 0
    while not core.is_over():
        run_ticks(core, 1, lambda tt, tm: _basic(t) if tm == 0 else None)
        t = core.tick
    assert core.winner == 0
    assert core.outcome()["reason"] == "ko"
    hits = len(_dmg_events(core))
    assert hits == 9                                # 3 swings × 3 hits
    assert core.score[0] == 9 * 1 + 30              # C5: hit=1, ko=30


def test_timeout_draw(make_core, kits, matrix, rules, arena):
    """Sin acciones, 100 ticks → timeout; score 0:0 → draw."""
    from combatcore.core import CombatCore
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["snorlax"], 750_000, 300_000)],
    ], matrix, rules, arena, max_ticks=100)
    run_ticks(core, 100)
    assert core.winner == WIN_DRAW
    assert core.outcome() == {"winner": "draw", "reason": "timeout_score",
                              "score": [0, 0]}
