"""Esquiva: i-frames (160 ms = 10 ticks), distancia exacta 1.8 m en 13
ticks (secuencia divmod, suma exacta), CD por kit (94 / snorlax 113).
"""
from combatcore.core import CombatCore
from combatcore.frames import InputFrame

from conftest import run_ticks


def _core(kits, matrix, rules, arena, pos_a, pos_b, max_ticks=30):
    return CombatCore(42, [
        [(kits["snorlax"], *pos_a)],
        [(kits["pikachu"], *pos_b)],
    ], matrix, rules, arena, max_ticks=max_ticks)


def test_iframes_block_hits(kits, matrix, rules, arena):
    """Dodge en t10: el hit de t11 cae en state_ticks 1 < 10 → bloqueado."""
    core = _core(kits, matrix, rules, arena, (250_000, 300_000),
                 (350_000, 300_000))

    def frames(t, tm):
        if tm == 0 and t == 0:
            return InputFrame(frame=t, basic=True)      # snorlax: hit t11, t12
        if tm == 1 and t == 10:
            return InputFrame(frame=t, dodge=True)
        return None

    run_ticks(core, 30, frames)
    blocked = [e for e in core.events if e["ev"] == "dodge_blocked"]
    assert [e["t"] for e in blocked] == [11, 12]        # los 2 hits del combo
    assert not [e for e in core.events if e["ev"] == "damage"]
    assert core.entities[1].hp == 95


def test_hits_land_after_iframes(kits, matrix, rules, arena):
    """Dodge en t0: a t11 (state_ticks 11 ≥ 10) el hit SÍ cae."""
    core = _core(kits, matrix, rules, arena, (250_000, 300_000),
                 (350_000, 300_000))

    def frames(t, tm):
        if t == 0:
            return InputFrame(frame=t, basic=True) if tm == 0 \
                else InputFrame(frame=t, dodge=True)
        return None

    run_ticks(core, 30, frames)
    evs = [e for e in core.events if e["ev"] == "damage"]
    assert [e["dmg"] for e in evs] == [10, 10]
    assert core.entities[1].hp == 95 - 20


def test_dodge_distance_exact(kits, matrix, rules, arena):
    """13847+13847+11×13846 = 180_000 milli-u exactos, luego IDLE.

    El pikachu (team 1) mira a la izq. → esquiva hacia -x."""
    core = _core(kits, matrix, rules, arena, (750_000, 300_000),
                 (250_000, 300_000), max_ticks=20)
    e = core.entities[1]
    run_ticks(core, 20, lambda t, tm:
              InputFrame(frame=t, dodge=True) if tm == 1 and t == 0
              else None)
    assert e.x == 250_000 - 180_000
    assert e.y == 300_000
    assert e.state == "idle"


def test_dodge_uses_facing_when_no_direction(kits, matrix, rules, arena):
    """Sin dirección explícita: esquiva en el facing del entity."""
    core = _core(kits, matrix, rules, arena, (750_000, 300_000),
                 (250_000, 300_000))
    run_ticks(core, 5, lambda t, tm:
              InputFrame(frame=t, dodge=True) if tm == 1 and t == 0
              else None)
    ev = core.events[0]
    assert ev["ev"] == "dodge"
    assert (ev["dx"], ev["dy"]) == (-1, 0)      # team b mira a la izq.


def test_dodge_cd_per_kit(kits, matrix, rules, arena):
    assert kits["pikachu"].dodge_cd == 94
    assert kits["snorlax"].dodge_cd == 113
    core = _core(kits, matrix, rules, arena, (750_000, 300_000),
                 (250_000, 300_000), max_ticks=300)
    run_ticks(core, 300, lambda t, tm:
              InputFrame(frame=t, dodge=True)
              if tm == 1 and t in (0, 50, 94) else None)
    rej = [r for r in core.rejected if r["action"] == "dodge"]
    assert [r["t"] for r in rej] == [50]         # 50 < 94 → cooldown
    dodges = [e for e in core.events if e["ev"] == "dodge"]
    assert [e["t"] for e in dodges] == [0, 94]   # 94 = CD liberado
