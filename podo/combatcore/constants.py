"""Constantes fijas del CombatCore (PODO M0).

Fixed-point (cierre 31/a8/29 2026-10-18): la POSICIÓN vive en MILLI-U
(1 u = 1/100 m; 1 milli-u = 1/1000 u = 1/100 000 m). Toda la geometría
(clamp, rango, colisión) opera en milli-u exactos; a la u entera solo se
redondea para render. La única unidad de tiempo es el tick lógico de
TICK_MS milisegundos.

NOTA sem 2: las REGLAS GLOBALES (switch, dodge, guardia, ultimate, score)
viven en data/config/match_rules.json (dueño: a8) — se cargan en rules.py.
Aquí solo quedan constantes de engine (no de balance).
"""

TICK_MS = 16                      # 1 tick lógico (≈ 60 fps de presentación)


def ticks_from_ms(ms: int) -> int:
    """ms → ticks lógicos (entero, redondeo medio hacia arriba). Determinista."""
    return (ms + TICK_MS // 2) // TICK_MS


MATCH_DURATION_MS = 300_000       # 5:00 (fallback; la fuente es match_rules/arena)
MAX_TICKS = ticks_from_ms(MATCH_DURATION_MS)   # 18 750 ticks

# Arena M0: 10 m × 6 m en MILLI-U (10 m = 1000 u = 1 000 000 milli-u).
# Las coords de a8 (metros, origen al centro) se mapean con ARENA_CENTER.
ARENA_W = 1_000_000
ARENA_H = 600_000
ARENA_CENTER = (ARENA_W // 2, ARENA_H // 2)

# Velocidad (cierre 31/a8 2026-10-18): move_speed del kit es MULTIPLICADOR
# adimensional sobre base_speed_m (m/s, global en match_rules.json, 3.6).
# speed = round(move_speed * base_speed_m * 100) u/s; por tick (TICK_MS ms)
# avanza speed*TICK_MS milli-u EXACTO (414 u/s × 16 ms = 6624 milli-u/tick):
# sin truncamiento, el resto sub-u vive en la posición (estado de sim).
# Se resuelve UNA vez en el loader kits.py; la sim solo multiplica enteros.

# Ticks con hitbox activa de un swing (el schema de kits no define active_ms;
# es parámetro de engine, no de contenido).
ACTIVE_TICKS = 6

# 1/sqrt(2) * 1000, aproximación entera para normalizar diagonal (8 dir.).
DIAG_SCALE = 707

# Carga de ultimate en centi-porcentaje (10000 = 100%). Los % de a8
# (0.6 / 0.9 / 15) se convierten a entero en rules.py: ×100 exacto.
CHARGE_FULL = 10000
