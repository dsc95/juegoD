"""Capa de contrato CombatCore (QA 7f + Dev 29).

Oráculos de reglas y funciones puras con **firmas estables** para que QA
escriba fixtures contra el contrato sin tocar la simulación. Aquí viven las
REGLAS (no el estado de sim): la sim (`core.py`) las consume.

Contrato de determinismo: cada función es pura (misma entrada → misma
salida); la sim usa aritmética entera (fixed-point) y la matriz canónica de
`data/types/type_matrix_v1.json` (v1.0.0). El daño de la sim y
`compute_damage` comparten la ÚNICA fórmula (fuente de verdad única).
"""
from __future__ import annotations

from pathlib import Path

from .constants import ARENA_H, ARENA_W, ticks_from_ms
from .kits import load_kits
from .types import TypeMatrix

# ---------------------------------------------------------------- constantes
# Valores del plan (Bloque 6 / GDD v2). Tunes finales de a8 (balance, sem 2).
SWITCH_COOLDOWN_S = 4.0      # cooldown del switch (Tab/1-3), en segundos
VULNERABLE_S = 1.5           # ventana vulnerable del recién entrado, en segundos
ULT_MULT = 20                # multiplicador de ultimate en décimas (×2)
GUARD_MULT = 4               # guardia: ×0.4 (−60 %), en décimas
VULN_MULT = 15               # ventana vulnerable: ×1.5 (+50 %), en décimas

# La SIM es tick-based. Los valores en TICKS se DERIVAN de los segundos vía
# ticks_from_ms (UNA sola fuente de verdad — regla del Jefe 2026-10-17: nunca
# hardcodear 250/94). La sim compara ticks contra estos, no contra los segundos.
SWITCH_COOLDOWN_TICKS = ticks_from_ms(int(SWITCH_COOLDOWN_S * 1000))   # 4.0 s → 250
VULNERABLE_TICKS = ticks_from_ms(int(VULNERABLE_S * 1000))            # 1.5 s → 94

# ------------------------------------------------------------------ defaults
_DATA = Path(__file__).resolve().parent.parent / "data"
_default_matrix_cache = None
_default_kits_cache = None


def default_matrix() -> TypeMatrix:
    """Matriz canónica de `data/types/type_matrix_v1.json` (v1.0.0, a8;
    cacheada; read-only). La matriz histórica en décimas fue eliminada
    2026-10-18: type_matrix_v1.json es la única matriz en disco."""
    global _default_matrix_cache
    if _default_matrix_cache is None:
        _default_matrix_cache = TypeMatrix.load(
            _DATA / "types" / "type_matrix_v1.json")
    return _default_matrix_cache


def _default_kits():
    global _default_kits_cache
    if _default_kits_cache is None:
        _default_kits_cache = load_kits(_DATA)
    return _default_kits_cache


def default_teams() -> list:
    """1v1 estándar (igual que el factory de tests): pikachu vs snorlax.

    Coords en milli-u (2026-10-18, fixed-point cierre 31/a8/29)."""
    kits = _default_kits()
    return [
        [(kits["pikachu"], ARENA_W // 4, ARENA_H // 2)],
        [(kits["snorlax"], 3 * ARENA_W // 4, ARENA_H // 2)],
    ]


# ------------------------------------------------------------- oráculos QA
def type_effectiveness(attacker: str, defender: str,
                       matrix: TypeMatrix | None = None) -> float:
    """Multiplicador de tipo (×0, ×0.5, ×1, ×2) como float — oráculo de QA.

    El core usa la misma matriz en décimas enteras (`matrix.mult`) para el
    daño determinista; esto es la versión float para las 324 tests de matriz.
    """
    m = matrix if matrix is not None else default_matrix()
    return m.mult(attacker, defender) / 10.0


def compute_damage(base, attacker: str, defender: str, *,
                   matrix: TypeMatrix | None = None,
                   guarding: bool = False, perfect_guard: bool = False,
                   vulnerable: bool = False, is_ultimate: bool = False) -> int:
    """Fórmula canónica de daño — ÚNICA fuente de verdad (la sim la usa).

    Aritmética entera (fixed-point) en décimas. Orden de aplicación:
    tipo → vulnerable → guardia → ultimate. `base` = daño base del ataque
    (`AttackSpec.damage`). Returns: daño entero (≥0); ×0 (inmunidad) → 0.
    """
    base = int(base)
    m = matrix if matrix is not None else default_matrix()
    v = base * m.mult(attacker, defender)      # × tipo (décimas)
    if vulnerable:
        v = v * VULN_MULT // 10                # ×1.5
    if perfect_guard:
        v = 0                                  # perfect guard: 0 daño
    elif guarding:
        v = v * GUARD_MULT // 10               # ×0.4 (−60 %)
    if is_ultimate:
        v = v * ULT_MULT // 10                 # ×2
    return max(0, v // 10)


def can_switch(elapsed_s: float) -> bool:
    """¿El switch ya está disponible? (cooldown de 4 s desde el último)."""
    return elapsed_s >= SWITCH_COOLDOWN_S


def vulnerable_window(t_s: float) -> bool:
    """¿`t_s` está dentro de la ventana vulnerable post-switch [0, 1.5 s)?"""
    return 0.0 <= t_s < VULNERABLE_S
