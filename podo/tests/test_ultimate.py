"""Ultimate (C6): carga por daño causado (+0.6 %), recibido (+0.9 %) y
orbes (+15 %); a 100 % dispara, se vacía, y el release hace daño ×2
(kind aoe: todos los enemigos en alcance — en 1v1, el activo).
"""
from combatcore.core import CombatCore
from combatcore.frames import InputFrame

from conftest import run_ticks


def _basic(t):
    return InputFrame(frame=t, basic=True)


def _ult(t):
    return InputFrame(frame=t, ultimate=True)


def _basic(t):
    return InputFrame(frame=t, basic=True)


def _ult(t):
    return InputFrame(frame=t, ultimate=True)


def test_ultimate_rejected_when_not_charged(kits, matrix, rules, arena):
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["snorlax"], 750_000, 300_000)],
    ], matrix, rules, arena, max_ticks=5)
    run_ticks(core, 5, lambda t, tm: _ult(t) if tm == 0 and t == 0 else None)
    rej = [r for r in core.rejected if r["action"] == "ultimate"]
    assert rej and rej[0]["reason"] == "not_charged"


def test_orb_gives_charge_and_score(kits, matrix, rules, arena):
    """Pikachu sobre el orb (300_000, 300_000): +15 % y +10 score."""
    core = CombatCore(42, [
        [(kits["pikachu"], 300_000, 300_000)],
        [(kits["snorlax"], 750_000, 300_000)],
    ], matrix, rules, arena, max_ticks=10)
    run_ticks(core, 2)
    assert core.entities[0].charge == 1500
    assert core.score[0] == 10
    assert core.events[0]["ev"] == "orb"
    assert core.orbs[0]["until"] == 1875          # respawn 30 s


def test_charge_from_damage_dealt_and_taken(kits, matrix, rules, arena):
    """3 hits × 2 (electric→grass): causado 6 → +360; recibido 6 → +540."""
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["oddish"], 370_000, 300_000)],     # 1.2 m = range básico
    ], matrix, rules, arena, max_ticks=20)
    run_ticks(core, 20, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    assert core.entities[0].charge == 6 * 60
    assert core.entities[1].charge == 6 * 90


def test_charge_caps_at_max(kits, matrix, rules, arena):
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits["oddish"], 370_000, 300_000)],
    ], matrix, rules, arena, max_ticks=20)
    core.entities[0].charge = 9_900
    run_ticks(core, 20, lambda t, tm: _basic(t) if tm == 0 and t == 0 else None)
    assert core.entities[0].charge == 10_000      # 9900 + 360 → cap


def _release_test(kits, matrix, rules, arena, kit_b):
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000)],
        [(kits[kit_b], 400_000, 300_000)],         # 1.5 m < 2.2 m (aoe)
    ], matrix, rules, arena, max_ticks=40)
    core.entities[0].charge = 10_000
    run_ticks(core, 40, lambda t, tm: _ult(t) if tm == 0 and t == 0 else None)
    evs = [e for e in core.events if e["ev"] == "damage"]
    return core, evs


def test_release_double_damage_normal(kits, matrix, rules, arena):
    """Release a t0: windup 300 ms (19 ticks); 34 normal ×2 = 68.

    C6: "a 100 % dispara, se vacía y recarga" — el daño del release
    recarga (+0.6 % por punto): 68 → 4080."""
    core, evs = _release_test(kits, matrix, rules, arena, "snorlax")
    assert [(e["t"], e["dmg"]) for e in evs] == [(19, 68)]
    assert core.entities[0].charge == 68 * 60


def test_release_type_scaling_grass(kits, matrix, rules, arena):
    """Mismo release vs grass: 34 ×0.5 ×2 = 34 → recarga 2040."""
    core, evs = _release_test(kits, matrix, rules, arena, "oddish")
    assert [(e["t"], e["dmg"]) for e in evs] == [(19, 34)]
    assert core.entities[0].charge == 34 * 60
