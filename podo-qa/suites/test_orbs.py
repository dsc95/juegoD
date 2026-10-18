"""Orbs del arena (arena_001: 3 orbs; dan score + carga de ultimate —
match_rules.score). Verifica que AMBOS equipos puedan recolectar: el pickup
debe evaluar al miembro activo de cada team."""
import config as cfg
from harness import Blocked, cc


def _match():
    core_mod = cc("combatcore.core")
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    return core_mod.CombatCore(1, None, matrix)  # equipos defaults 3v3 (data de a8)


def _put_on_orb(core, team, orb_i):
    """Mueve al miembro ACTIVO (state IDLE) del team sobre el orb.
    (Fix arnes 2026-10-18: antes usaba core.entities[1], que en 3v3 es BENCH
    del team a — el engine solo evalúa al activo de cada team.)"""
    ents = cc("combatcore.entities")
    x, y, _r = core.arena.orbs[orb_i]
    for e in core.entities:
        if e.team == team and e.state == ents.IDLE:
            e.x, e.y = int(x), int(y)
            return
    raise AssertionError(f"team {team} sin miembro activo (IDLE)")


def orb_team_a_recolecta():
    """Control: el activo del team a sobre un orb gana score_orb."""
    core = _match()
    _put_on_orb(core, 0, 0)
    antes = core.score[0]
    core.step({})
    assert core.score[0] == antes + core.rules.score_orb, \
        f"team a no recolectó: score {core.score[0]} (antes {antes})"


def orb_team_b_recolecta():
    """Paridad de equipos: el activo del team b también recolecta.
    Nota 2026-10-18: el FAIL anterior fue del ARNES (teletransportaba BENCH del
    team a); el `break` de core._collect_orbs está DENTRO del if → 1 orb = 1
    pickup, orden determinista tm=0,1. Engine inocente en este caso."""
    core = _match()
    _put_on_orb(core, 1, 1)
    antes = core.score[1]
    core.step({})
    assert core.score[1] == antes + core.rules.score_orb, \
        f"team b no recolectó: score {core.score[1]} (antes {antes})"


CASES = [
    ("orb-team-a", orb_team_a_recolecta),
    ("orb-team-b", orb_team_b_recolecta),
]
