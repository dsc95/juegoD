"""VETO de determinismo (Bloque 6, criterio 7): mismo seed + mismos
inputs = logs byte-idénticos. Sin tiempo real, sin RNG sin semilla.
"""
import time

from combatcore.adapters.headless import core_factory, demo_frames
from combatcore.frames import InputStream

TEAMS = [["pikachu", "snorlax", "gardevoir"],
         ["snorlax", "pikachu", "gardevoir"]]


def _run(ticks=3000, seed=42):
    core = core_factory(seed, TEAMS)
    s0 = demo_frames(ticks, 0)
    s1 = demo_frames(ticks, 1)
    for t in range(ticks):
        core.step({0: s0.get(t), 1: s1.get(t)})
    return core


def test_two_runs_byte_identical():
    a, b = _run(), _run()
    assert a.events_json() == b.events_json()
    assert a.digest_json() == b.digest_json()
    assert a.state_hash() == b.state_hash()
    assert a.score == b.score


def test_digest_is_all_integers():
    core = _run(500)
    def walk(v):
        if isinstance(v, list):
            for x in v:
                walk(x)
        else:
            assert isinstance(v, (int, str, bool)), type(v)
    walk(core.digest())


def test_full_match_5min_under_5s():
    """Partido completo 5:00 (1v1 idle → timeout) en < 5 s de pared."""
    t0 = time.perf_counter()
    core = core_factory(42, [["pikachu"], ["snorlax"]])
    core.run({0: InputStream(0), 1: InputStream(1)})
    assert core.tick == 18750
    assert core.is_over()                          # timeout a 5:00
    assert core.outcome()["reason"] == "timeout_score"
    assert (time.perf_counter() - t0) * 1000 < 5000
