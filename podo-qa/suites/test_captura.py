"""Curva de captura por HP + ball — baseline Rattata (neutro ×1, formulario C4).
Semana 1: propiedades del MODELO DE REFERENCIA (verde, no depende de CombatCore).
CombatCore.capture (usa CombatCore.rng sembrado) = sem.3 → BLOCKED hasta que 31/29 lo cableen."""
import config as cfg
from harness import Blocked, cc, read_json

K = 0.5  # pendiente del modelo de referencia (la curva exacta la fija 31/a8 en sem.3)


def _p(hp, ball):
    return max(0.0, min(1.0, K * cfg.BALL_STRENGTH[ball] * (1.0 - hp)))


def _fx():
    return read_json(cfg.FIX / "captura.json")


def spec_anchors():
    for a in _fx()["anchors"]:
        p = _p(a["hp"], a["ball"])
        if "p_min" in a:
            assert p >= a["p_min"], f"ancla C4 (hp={a['hp']}, {a['ball']}): p={p} < p_min={a['p_min']}"
        if "p_max" in a:
            assert p <= a["p_max"], f"ancla C4 (hp={a['hp']}, {a['ball']}): p={p} > p_max={a['p_max']}"


def spec_monotonic_hp():
    f = _fx()
    ball = f["probe_balls"][1]
    ps = [_p(h, ball) for h in f["probe_hp"]]
    assert all(ps[i] >= ps[i + 1] for i in range(len(ps) - 1)), f"p no debe crecer con HP: {ps}"


def spec_monotonic_ball():
    f = _fx()
    ps = [_p(0.5, b) for b in f["probe_balls"]]
    assert all(ps[i] <= ps[i + 1] for i in range(len(ps) - 1)), f"p no debe crecer con mejor ball: {ps}"


def combatcore_capture():
    core_mod = cc("combatcore.core")
    if not hasattr(core_mod.CombatCore, "capture_probability"):
        raise Blocked("captura = sem.3 (usa CombatCore.rng sembrado); aún no cableada en CombatCore")
    # Cuando 31/29 la cableen: validar anclas C4 + monotonía contra la implementación real.


CASES = [
    ("spec-anchors", spec_anchors),
    ("spec-monotonic-hp", spec_monotonic_hp),
    ("spec-monotonic-ball", spec_monotonic_ball),
    ("combatcore-capture", combatcore_capture),
]
