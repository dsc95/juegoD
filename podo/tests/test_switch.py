"""Switch 3v3 (C3): CD 4 s (250 ticks), ventana vulnerable +50 % (94
ticks), auto-switch al KO del activo (sin CD), wipe del equipo → KO.
"""
from combatcore.core import CombatCore
from combatcore.frames import InputFrame

from conftest import run_ticks


def _sw(t):
    return InputFrame(frame=t, switch=99)


def _basic(t):
    return InputFrame(frame=t, basic=True)


def test_switch_cd_4s(make_core):
    """3.9 s (t244) → rechazado; 4.1 s (t256) → aceptado."""
    core = make_core([["pikachu", "snorlax", "gardevoir"],
                      ["snorlax", "pikachu", "gardevoir"]], max_ticks=600)

    def frames(t, tm):
        if tm == 0 and t in (0, 244, 256):
            return _sw(t)
        return None

    run_ticks(core, 600, frames)
    evs = [e for e in core.events if e["ev"] == "switch"]
    assert [e["t"] for e in evs] == [0, 256]
    assert [e["to"] for e in evs] == [1, 2]
    assert core._active[0] == 2
    assert core._switch_cd[0] == 256 + 250
    rej = [r for r in core.rejected if r["action"] == "switch"]
    assert [r["t"] for r in rej] == [244]
    assert rej[0]["reason"] == "cooldown"


def test_entrant_vulnerable_50pct(kits, matrix, rules, arena):
    """El entrado recibe +50 % (5 → 7) durante la ventana (94 ticks)."""
    core = CombatCore(42, [
        [(kits["pikachu"], 100_000, 300_000),
         (kits["snorlax"], 200_000, 300_000),
         (kits["gardevoir"], 300_000, 300_000)],
        [(kits["pikachu"], 370_000, 300_000)],
    ], matrix, rules, arena, max_ticks=30)

    def frames(t, tm):
        if tm == 0 and t == 0:
            return _sw(t)
        if tm == 1 and t == 0:
            return _basic(t)
        return None

    run_ticks(core, 30, frames)
    entrant = core.entities[1]                     # snorlax, al spawn de a
    assert (entrant.x, entrant.y) == (250_000, 300_000)
    assert entrant.vulnerable_until == 94
    evs = [e for e in core.events if e["ev"] == "damage" and e["dst"] == 1]
    assert [e["dmg"] for e in evs] == [7, 7, 7]    # 5 × 1.5 → 7 (entero)
    assert entrant.hp == 130 - 21


def test_vulnerable_window_expires(kits, matrix, rules, arena):
    """Después de t94 el entrado vuelve a recibir daño normal."""
    core = CombatCore(42, [
        [(kits["pikachu"], 100_000, 300_000),
         (kits["snorlax"], 200_000, 300_000),
         (kits["gardevoir"], 300_000, 300_000)],
        [(kits["pikachu"], 370_000, 300_000)],
    ], matrix, rules, arena, max_ticks=120)

    def frames(t, tm):
        if tm == 0 and t == 0:
            return _sw(t)
        if tm == 1 and t in (0, 94):
            return _basic(t)                       # hits t6-8 y t100-102
        return None

    run_ticks(core, 120, frames)
    evs = [e for e in core.events if e["ev"] == "damage" and e["dst"] == 1]
    assert [e["dmg"] for e in evs] == [7, 7, 7, 5, 5, 5]
    assert core.entities[1].hp == 130 - 21 - 15


def test_auto_switch_on_ko_no_cd(kits, matrix, rules, arena):
    """KO del activo → entra el siguiente: con ventana vulnerable,
    SIN consumir CD de switch."""
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000),
         (kits["snorlax"], 250_000, 420_000),
         (kits["gardevoir"], 250_000, 540_000)],
        [(kits["snorlax"], 350_000, 300_000)],
    ], matrix, rules, arena, max_ticks=10_000)
    while not any(e["ev"] == "auto_switch" for e in core.events):
        core.step({1: _basic(core.tick)})
        assert core.tick < 500
    ev = next(e for e in core.events if e["ev"] == "auto_switch")
    new = core.entities[1]
    assert core._active[0] == 1
    assert new.vulnerable_until == ev["t"] + 94
    assert core._switch_cd[0] == 0                 # auto: sin CD


def test_team_wipe_is_ko(kits, matrix, rules, arena):
    core = CombatCore(42, [
        [(kits["pikachu"], 250_000, 300_000),
         (kits["snorlax"], 250_000, 420_000)],
        [(kits["snorlax"], 350_000, 300_000)],
    ], matrix, rules, arena, max_ticks=10_000)
    while not core.is_over():
        core.step({1: _basic(core.tick)})
    assert core.winner == 1
    assert core.outcome()["reason"] == "ko"


def test_switch_no_alive_rejected(make_core):
    core = make_core([["pikachu"], ["snorlax"]], max_ticks=10)
    run_ticks(core, 5, lambda t, tm: _sw(t) if tm == 0 and t == 0 else None)
    rej = [r for r in core.rejected if r["action"] == "switch"]
    assert rej and rej[0]["reason"] == "no_alive"
    assert core._active[0] == 0
