"""Básica dirigida — aim lock (spec Q1.4 v1.1): se LOCKEA en WINDUP→ACTIVE
(vía core._lock_target, matemática entera sin floats). Hitbox CIRCULAR de
`range` (los kits de a8 no definen arco; el facing solo interviene en el
tie-break de ángulo). Tie-break spec: (1) menor dist², (2) menor ángulo con
el facing, (3) menor eid.

NOTA de modelo: en el engine actual (1 activo por team, resto en BENCH) solo
hay UN candidato posible → el tie-break Q1.4 no se ejerce en partida real.
Estos casos lo prueban BLANCO: fuerzan 2 enemigos activos (core.entities[i].
state = IDLE) para validar la función contra la spec. El banco NUNCA es
objetivo (caso aparte). Kits inline; atacante = pikachu (300,300) facing +x,
basic range 120."""
import config as cfg
from harness import Blocked, cc, inline_kits


def _lock(team1, force_active=False):
    core_mod = cc("combatcore.core")
    ents = cc("combatcore.entities")
    kits = inline_kits()
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    teams = [[(kits["pikachu"], 300, 300)], [(kits["rattata"], x, y) for (x, y) in team1]]
    core = core_mod.CombatCore(1, teams, matrix)
    if force_active and len(team1) > 1:
        core.entities[2].state = ents.IDLE   # blanco: 2do enemigo activo
    att = core.entities[0]
    att.abl = att.kit.basic
    core._lock_target(att)
    return att._swing_target


def tb_distancia():
    # eid1@(410,300) d2=12100 ; eid2@(400,300) d2=10000 → el más cercano = eid2
    assert _lock([(410, 300), (400, 300)], force_active=True) == 2


def tb_angulo():
    # misma d2=10000; eid1@(360,380) dot=60 (~53°); eid2@(380,360) dot=80 (~37°)
    # spec: menor ángulo = mayor dot = eid2
    assert _lock([(360, 380), (380, 360)], force_active=True) == 2


def tb_eid():
    # misma d2=8000 y mismo dot=80 (380,340 vs 380,260) → menor eid = eid1
    assert _lock([(380, 340), (380, 260)], force_active=True) == 1


def tb_fuera_de_alcance():
    # enemigo a ddx=400 (> range 120 de chispa) → sin objetivo
    assert _lock([(700, 300)]) is None


def tb_banco_no_objetivo():
    # eid2 está en BENCH (350,300) y más cerca (d2=2500) pero NO es candidato:
    # solo el miembro activo del enemigo puede ser lockeado → eid1
    assert _lock([(400, 300), (350, 300)]) == 1


CASES = [
    ("tb-distancia", tb_distancia),
    ("tb-angulo", tb_angulo),
    ("tb-eid", tb_eid),
    ("tb-fuera-alcance", tb_fuera_de_alcance),
    ("tb-banco-no-objetivo", tb_banco_no_objetivo),
]
