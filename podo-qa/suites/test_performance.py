"""Performance (Bloque 6.27f) — partida 5:00 headless < 5 s reales (3 partidas consecutivas)
y tick p99 < 16 ms. Headless puro: sin pygame, sin I/O, solo CombatCore.
Kits inline (no depende de data/kits/*.json — ver test_kits_data)."""
import time

import config as cfg
from harness import Blocked, cc, inline_kits


def _match(seed=7):
    core_mod = cc("combatcore.core")
    kits = inline_kits()
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    teams = [[(kits["pikachu"], 250, 300)], [(kits["snorlax"], 750, 300)]]
    return core_mod.CombatCore(seed, teams, matrix)


def partida_5min_headless():
    for seed in (1, 2, 3):  # "3 partidas consecutivas"
        core = _match(seed)
        t0 = time.perf_counter()
        while not core.is_over():
            core.step()
        dt = time.perf_counter() - t0
        assert core.is_over(), f"partida seed={seed} no terminó"
        assert dt < cfg.MATCH_HEADLESS_MAX_S, \
            f"partida 5:00 seed={seed} tardó {dt:.3f}s (> {cfg.MATCH_HEADLESS_MAX_S}s)"


def tick_p99():
    core = _match()
    ts = []
    for _ in range(3000):
        if core.is_over():
            break
        t0 = time.perf_counter()
        core.step()
        ts.append(time.perf_counter() - t0)
    ts.sort()
    p99 = ts[int(0.99 * len(ts))] * 1000
    assert p99 < cfg.TICK_P99_MAX_MS, f"tick p99 = {p99:.3f}ms (> {cfg.TICK_P99_MAX_MS}ms)"


CASES = [
    ("partida-5min-headless", partida_5min_headless),
    ("tick-p99", tick_p99),
]
