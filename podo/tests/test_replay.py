"""Replay podo.replay v1: save/verify — el oráculo de determinismo del
replay (31): re-jugar los frames debe dar el MISMO state_hash (+ outcome
+ rejected_inputs).
"""
import json

import pytest

from combatcore.adapters.headless import core_factory, demo_frames
from combatcore.frames import InputFrame
from combatcore.replay import FORMAT, load_replay, save_replay, verify_replay

TEAMS = [["pikachu", "snorlax", "gardevoir"],
         ["snorlax", "pikachu", "gardevoir"]]


def _run_demo(ticks=500, seed=42):
    core = core_factory(seed, TEAMS)
    s0 = demo_frames(ticks, 0)
    s1 = demo_frames(ticks, 1)
    dense = {0: [], 1: []}
    for t in range(ticks):
        # el stream denso no lleva Nones (canon: 1 frame por tick por side)
        fa = s0.get(t) or InputFrame(frame=t)
        fb = s1.get(t) or InputFrame(frame=t)
        dense[0].append(fa)
        dense[1].append(fb)
        core.step({0: fa, 1: fb})
    return core, dense


def _forfeit(core):
    return {"winner": "draw", "reason": "forfeit", "score": list(core.score)}


def test_demo_forfeit_verify(tmp_path):
    core, dense = _run_demo(1500)   # en curso + rejected (ultimate sin carga)
    assert core.winner is None                    # partido en curso
    path = tmp_path / "forfeit.json"
    doc = save_replay(path, core, dense, outcome=_forfeit(core))
    assert doc["format"] == FORMAT
    assert doc["version"] == 1
    assert doc["tail"]["frames_total"] == core.tick
    assert doc["config"]["match_duration_ms"] == 300_000
    assert len(core.rejected) >= 1                # el demo tiene inválidos
    assert doc["tail"]["rejected_inputs"] == core.rejected
    assert verify_replay(path) is True


def test_full_match_ko_verify(tmp_path):
    """Partido completo (KO): outcome real de la sim, no forfeit."""
    core = core_factory(42, [["pikachu"], ["rattata"]])
    dense = {0: [], 1: []}
    while not core.is_over():
        t = core.tick
        fa = (InputFrame(frame=t, move_x=1) if t < 65
              else InputFrame(frame=t, basic=True))
        fb = InputFrame(frame=t)                     # team b: idle
        dense[0].append(fa)
        dense[1].append(fb)
        core.step({0: fa, 1: fb})
    assert core.outcome()["reason"] == "ko"
    path = tmp_path / "full.json"
    save_replay(path, core, dense)
    assert verify_replay(path) is True
    doc = load_replay(path)
    assert doc["tail"]["outcome"]["winner"] == "a"
    assert doc["tail"]["frames_total"] == core.tick


def test_tampered_input_fails_verify(tmp_path):
    core, dense = _run_demo(500)
    path = tmp_path / "orig.json"
    save_replay(path, core, dense, outcome=_forfeit(core))
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["inputs"][0]["input"]["actions"] = ["ultimate"]   # 0 % → inválido
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")
    assert verify_replay(bad) is False


def test_tampered_hash_fails_verify(tmp_path):
    core, dense = _run_demo(500)
    path = tmp_path / "orig.json"
    save_replay(path, core, dense, outcome=_forfeit(core))
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["tail"]["final_state_hash"] = "sha256:" + "0" * 64
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")
    assert verify_replay(bad) is False


def test_bad_format_rejected(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"format": "otro.formato", "version": 1}',
                 encoding="utf-8")
    with pytest.raises(ValueError):
        load_replay(p)
