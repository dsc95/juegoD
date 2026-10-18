"""Movimiento fixed-point en milli-u (cierre 31/a8/29 2026-10-18).

speed = round(move_speed × base_speed_m × 100) u/s; delta/tick =
speed × TICK_MS milli-u EXACTO (sin truncamiento: el resto sub-u vive en
la posición). base_speed_m = 3.6 (match_rules.json).
"""
from combatcore.frames import InputFrame

from conftest import run_ticks


def _active(core, tm=0):
    return core._by_eid[core._teams[tm][core._active[tm]]]


def test_pikachu_speed_exact(make_core):
    """414 u/s × 16 ms = 6624 milli-u/tick; 10 ticks = 66 240."""
    core = make_core([["pikachu"], ["snorlax"]])
    e = _active(core, 0)
    x0 = e.x
    run_ticks(core, 10, lambda t, tm:
              InputFrame(frame=t, move_x=1) if tm == 0 else None)
    assert e.x - x0 == 66_240


def test_snorlax_speed(make_core):
    """288 u/s → 4608 milli-u/tick; 10 ticks = 46 080 (hacia la izq.)."""
    core = make_core([["pikachu"], ["snorlax"]])
    e = _active(core, 1)
    x0 = e.x
    run_ticks(core, 10, lambda t, tm:
              InputFrame(frame=t, move_x=-1) if tm == 1 else None)
    assert x0 - e.x == 46_080


def test_kits_run_at_different_rates(make_core):
    """El multiplicador move_speed debe importar (pikachu > snorlax)."""
    core = make_core([["pikachu"], ["snorlax"]])
    pa, ps = _active(core, 0), _active(core, 1)
    xa, xb = pa.x, ps.x
    run_ticks(core, 100, lambda t, tm:
              InputFrame(frame=t, move_x=1) if tm == 0 else
              InputFrame(frame=t, move_x=-1))
    dist_a = pa.x - xa      # 6624 × 100
    dist_b = xb - ps.x      # 4608 × 100
    assert dist_a == 662_400
    assert dist_b == 460_800
    assert dist_a > dist_b


def test_diagonal_scaled_707(make_core):
    """Diagonal: (6624 × 707)//1000 = 4683 milli-u por eje/tick."""
    core = make_core([["pikachu"], ["snorlax"]])
    e = _active(core, 0)
    x0, y0 = e.x, e.y
    run_ticks(core, 10, lambda t, tm:
              InputFrame(frame=t, move_x=1, move_y=1) if tm == 0 else None)
    assert (e.x - x0) == 46_830
    assert (e.y - y0) == 46_830


def test_slow_halves_delta(make_core):
    """apply_state slow: delta // 2 (3312 milli-u/tick para pikachu)."""
    core = make_core([["pikachu"], ["oddish"]])
    e = _active(core, 0)
    e.slowed_until = 10_000
    x0 = e.x
    run_ticks(core, 10, lambda t, tm:
              InputFrame(frame=t, move_x=1) if tm == 0 else None)
    assert e.x - x0 == 33_120


def test_clamp_to_arena(make_core):
    """Clamp a las paredes (0 y ARENA_W/H)."""
    from combatcore.constants import ARENA_H, ARENA_W
    core = make_core([["pikachu"], ["snorlax"]])
    e = _active(core, 0)
    e.x, e.y = 0, 0
    run_ticks(core, 50, lambda t, tm:
              InputFrame(frame=t, move_x=-1, move_y=-1) if tm == 0 else None)
    assert (e.x, e.y) == (0, 0)
    e.x, e.y = ARENA_W, ARENA_H
    run_ticks(core, 50, lambda t, tm:
              InputFrame(frame=t, move_x=1, move_y=1) if tm == 0 else None)
    assert (e.x, e.y) == (ARENA_W, ARENA_H)


def test_facing_updates_with_movement(make_core):
    core = make_core([["pikachu"], ["snorlax"]])
    e = _active(core, 0)
    run_ticks(core, 5, lambda t, tm:
              InputFrame(frame=t, move_x=0, move_y=1) if tm == 0 else None)
    assert (e.facing_x, e.facing_y) == (0, 1)
