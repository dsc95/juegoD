"""Capa de contrato CombatCore (QA 7f + Dev 29).

Firmas estables para las fixtures BLOCKED: daño, tipos, cooldowns.
El core y estos oráculos comparten la ÚNICA fórmula de daño.
"""
from combatcore.contract import (ULT_MULT, VULNERABLE_S, SWITCH_COOLDOWN_S,
                                 can_switch, compute_damage,
                                 type_effectiveness, vulnerable_window)
from combatcore.core import CombatCore
from combatcore.frames import InputFrame
from combatcore.types import TypeMatrix


def _m():
    # API canónica (types.py v1.0.0): fracciones {0, 0.5, 1, 2} + version.
    return TypeMatrix(["a", "b"],
                      {"a": {"a": 1.0, "b": 2.0}, "b": {"a": 1.0, "b": 0.5}},
                      "1.0.0-test")


# ------------------------------------------------------------------- tipos
def test_type_effectiveness_float():
    assert type_effectiveness("fire", "grass") == 2.0   # canónica v1.0.0
    m = _m()
    assert type_effectiveness("a", "b", m) == 2.0       # ×2
    assert type_effectiveness("b", "b", m) == 0.5       # ×0.5
    assert type_effectiveness("a", "a", m) == 1.0       # ×1


# --------------------------------------------------------------------- daño
def test_compute_damage_neutral():
    assert compute_damage(40, "a", "a", matrix=_m()) == 40   # ×1
    assert compute_damage(40, "a", "b", matrix=_m()) == 80   # ×2
    assert compute_damage(40, "b", "b", matrix=_m()) == 20   # ×0.5


def test_compute_damage_modifiers():
    assert compute_damage(100, "a", "a", matrix=_m(),
                          vulnerable=True) == 150            # ×1.5
    assert compute_damage(100, "a", "a", matrix=_m(),
                          guarding=True) == 40               # ×0.4 (−60 %)
    assert compute_damage(100, "a", "a", matrix=_m(),
                          perfect_guard=True) == 0           # perfect guard
    assert compute_damage(100, "a", "a", matrix=_m(),
                          is_ultimate=True) == 100 * ULT_MULT // 10  # ×2


def test_compute_damage_matches_core(make_core):
    """La sim y el oráculo comparten la fórmula (fuente de verdad única).

    Camina hasta entrar en alcance (posiciones en milli-u) y dispara el
    basic: un combo (hits=N) resuelve N hits (1 por tick ACTIVE); cada
    `dmg` del log debe casar con `compute_damage`.
    """
    core = make_core([["pikachu"], ["snorlax"]])
    a = core.entities[0].kit.basic
    e0, e1 = core.entities[0], core.entities[1]
    t = 0
    while e0.dist2(e1) > a.range * a.range and t < 500:
        core.step({0: InputFrame(frame=t, move_x=1)})
        t += 1
    core.step({0: InputFrame(frame=t, basic=True)})
    t += 1
    for _ in range(a.windup + 6 + 6 + 2):   # WINDUP + ACTIVE + RECOVERY
        core.step({0: InputFrame(frame=t)})
        t += 1
    d = [ev for ev in core.events if ev["ev"] == "damage"]
    t0, t1 = e0.kit.type, e1.kit.type
    expected = compute_damage(a.damage, t0, t1, matrix=core.matrix)
    assert len(d) == a.hits
    assert all(ev["dmg"] == expected for ev in d)


# --------------------------------------------------------- cooldowns (QA)
def test_can_switch_and_vulnerable_window():
    assert not can_switch(3.9)
    assert can_switch(SWITCH_COOLDOWN_S)
    assert can_switch(4.1)
    assert vulnerable_window(0.0)
    assert vulnerable_window(1.49)
    assert not vulnerable_window(VULNERABLE_S)
    assert not vulnerable_window(-0.1)


def test_cooldown_ticks_derived_via_ticks_from_ms():
    """La sim usa ticks DERIVADOS de los segundos vía ticks_from_ms (Jefe)."""
    from combatcore.constants import ticks_from_ms
    from combatcore.contract import SWITCH_COOLDOWN_TICKS, VULNERABLE_TICKS
    assert SWITCH_COOLDOWN_TICKS == ticks_from_ms(4000) == 250
    assert VULNERABLE_TICKS == ticks_from_ms(1500) == 94


# ------------------------------------------------- superficie de CombatCore
def test_combatcore_contract_surface():
    core = CombatCore(42)                 # defaults del contrato (1v1)
    assert not core.is_over()
    assert core.final_score(0) == 0
    core.apply_input_frame(InputFrame(frame=0, move_x=1), team=0)
    h0 = core.state_hash()
    core.advance(1)
    assert core.state_hash() != h0        # el estado cambió

    def run():
        c = CombatCore(42, max_ticks=50)
        c.advance(50)
        return c.state_hash(), c.is_over(), c.winner
    assert run() == run()                # determinismo vía state_hash
