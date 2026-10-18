"""VETO de determinismo — fixture de 10.000 input frames; 2 runs; state_hash/
digest/events byte-iguales (Bloque 6.27.c / criterio 7). Misma seed + mismos
frames ⇒ misma sim. API de entrada: step({team: InputFrame}) (frame de t se
consume en el tick t; team sin frame = idle)."""
import config as cfg
from harness import Blocked, cc, inline_kits


def _frames(n):
    InputFrame = cc("combatcore.frames").InputFrame
    return [InputFrame(frame=t, move_x=1, move_y=0,
                       basic=(t % 64 == 0), dodge=(t % 257 == 0)) for t in range(n)]


def _match():
    core_mod = cc("combatcore.core")
    kits = inline_kits()
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    teams = [[(kits["pikachu"], 250, 300)], [(kits["snorlax"], 750, 300)]]
    return core_mod.CombatCore(42, teams, matrix)


def _run(n, seed=42):
    core_mod = cc("combatcore.core")
    kits = inline_kits()
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    teams = [[(kits["pikachu"], 250, 300)], [(kits["snorlax"], 750, 300)]]
    core = core_mod.CombatCore(seed, teams, matrix)
    for f in _frames(n):
        core.step({0: f})
    return core


def determinismo_10k():
    a = _run(cfg.DETERMINISM_FRAMES)
    b = _run(cfg.DETERMINISM_FRAMES)
    assert a.state_hash() == b.state_hash(), "state_hash difiere entre 2 runs ⇒ determinismo ROTO (VETO)"
    assert a.digest_json() == b.digest_json(), "digest byte-difiere entre 2 runs idénticas"
    assert a.events_json() == b.events_json(), "log de eventos byte-difiere entre 2 runs idénticas"


def contract_apply_advance():
    """Capa de contrato firmada (31): apply_input_frame(frame, team) + advance(n).
    HOY FALLA (rewrite sem 2 de 29): apply_input_frame escribe a self._pending
    pero __init__ nunca lo inicializa → AttributeError. O se re-inicializa
    _pending = {} en __init__ o se elimina la capa del contrato."""
    core = _match()
    core.apply_input_frame(cc("combatcore.frames").InputFrame(frame=0), team=0)
    core.advance(1)
    assert core.tick == 1, f"tick={core.tick} (esperado 1)"


def replay_roundtrip():
    """El fixture de inputs ES el formato de replay: serialize → deserialize
    ⇒ frames idénticos."""
    fm = cc("combatcore.frames")
    frames = _frames(1000)
    back = fm.deserialize_frames(fm.serialize_frames(frames))
    assert len(back) == len(frames), f"round-trip cambió longitud ({len(back)} != {len(frames)})"
    assert [fm.frame_to_tuple(f) for f in back] == [fm.frame_to_tuple(f) for f in frames], \
        "round-trip de replay corrompe los frames"


CASES = [
    ("determinismo-10k", determinismo_10k),
    ("contract-apply-advance", contract_apply_advance),
    ("replay-roundtrip", replay_roundtrip),
]
