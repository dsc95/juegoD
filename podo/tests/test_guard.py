"""Guardia: normal (×0.4) y perfect guard.

La guardia es HOLD (guard_on/guard_off del canon podo.replay): sin frame
de guardia el estado se suelta al tick siguiente. Perfect = ventana de
`perfect_ticks` (120 ms = 8 ticks) desde `guard_started`: 0 daño +
reflect 50 % del daño CRUDO + corte del combo (interrupt → RECOVERY).
"""
from combatcore.core import CombatCore
from combatcore.frames import InputFrame

from conftest import run_ticks


def _core(kits, matrix, rules, arena, max_ticks=30):
    return CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["snorlax"], 370_000, 300_000)],
    ], matrix, rules, arena, max_ticks=max_ticks)


def _hold(t):
    return InputFrame(frame=t, guard=True)


def test_guard_reduces_damage_60pct(kits, matrix, rules, arena):
    """Guardia desde t0, swing en t10 → hit t16 (16 > 8): 5 → 2 por hit."""
    core = _core(kits, matrix, rules, arena)

    def frames(t, tm):
        if tm == 1:
            return _hold(t)
        if t == 10:
            return InputFrame(frame=t, basic=True)
        return None

    run_ticks(core, 30, frames)
    evs = [e for e in core.events if e["ev"] == "damage"]
    assert [e["t"] for e in evs] == [16, 17, 18]
    assert [e["dmg"] for e in evs] == [2, 2, 2]
    assert core.entities[1].hp == 130 - 6


def test_perfect_guard_reflects_and_cuts_combo(kits, matrix, rules, arena):
    """Guardia desde t0; swing en t0 → hit t6 (6 ≤ 8) → perfect."""
    core = _core(kits, matrix, rules, arena)

    def frames(t, tm):
        if tm == 1:
            return _hold(t)
        if t == 0:
            return InputFrame(frame=t, basic=True)
        return None

    run_ticks(core, 30, frames)
    to_def = [e for e in core.events
              if e["ev"] == "damage" and e["dst"] == 1]
    assert to_def == []                              # 0 daño al defensor
    refl = [e for e in core.events
            if e["ev"] == "damage" and e["dst"] == 0]
    assert len(refl) == 1                            # el combo se cortó
    assert refl[0]["dmg"] == 2                       # 50 % de 5 (crudo)
    assert refl[0]["t"] == 6
    assert any(e["ev"] == "interrupt" and e["dst"] == 0
               for e in core.events)
    assert core.entities[0].hp == 95 - 2
    assert core.entities[1].hp == 130


def test_perfect_window_boundary(kits, matrix, rules, arena):
    """Guardia desde t0: hit en t8 → 8-0 = 8 ≤ 8 → perfect;
    hit en t9 → 9 > 8 → guardia normal (2 por hit)."""
    def run(basic_at):
        core = _core(kits, matrix, rules, arena)

        def frames(t, tm):
            if tm == 1:
                return _hold(t)
            if t == basic_at:
                return InputFrame(frame=t, basic=True)
            return None

        run_ticks(core, 30, frames)
        return core

    core = run(2)                                   # hit en t8
    assert not [e for e in core.events
                if e["ev"] == "damage" and e["dst"] == 1]
    core = run(3)                                   # hit en t9
    evs = [e for e in core.events
           if e["ev"] == "damage" and e["dst"] == 1]
    assert len(evs) == 3 and all(e["dmg"] == 2 for e in evs)
