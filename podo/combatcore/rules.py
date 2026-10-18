"""Reglas globales de match y arena — cargadas desde los JSON de a8.

Fuente de verdad: data/config/match_rules.json y data/arenas/*.json
(docs/MEDALS-AND-ARENAS.md). Nada de balance se hardcodea aquí: todo
parámetro que existe en los JSON vive allí y se convierte a enteros
fijos EN ESTE LOADER (la sim solo hace aritmética entera).

Conversiones float → entero (deterministas, redondeo medio):
- multiplicadores de daño → décimas (1.5 → 15)
- reducciones → décimas (reducción 0.6 → multiplicador 4 = ×0.4)
- reflejos/escudos → centenas (0.5 → 50, 0.4 → 40)
- distancias → unidades fixed-point (1.8 m → 180)
- % de carga → centi-porcentaje (0.6 → 60 por 1 de daño; 15 → 1500)
- tiempos → ticks vía ticks_from_ms (NUNCA ms ni floats en la sim)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .constants import (
    ARENA_CENTER,
    ARENA_H,
    ARENA_W,
    CHARGE_FULL,
    ticks_from_ms,
)

_MARGIN = 24_000  # milli-u: nada spawnea pegado al borde


@dataclass(frozen=True)
class MatchRules:
    """Reglas globales en unidades de simulación (ticks / enteros fijos)."""
    tick_ms: int
    max_ticks: int
    party_size: int
    matrix_version: str

    # switch (GDD: CD 4 s + ventana vulnerable 1.5 s, +50 %)
    switch_cd: int            # ticks
    vuln_ticks: int           # ticks
    vuln_mult: int            # décimas (15 = ×1.5)

    # dodge (200 ms, i-frames 160 ms, distancia 1.8 m)
    dodge_distance: int       # unidades (180)
    dodge_ticks: int          # duración total
    iframes_ticks: int        # ticks invulnerables (los primeros)
    dodge_cd: int             # ticks (default; el kit puede sobreescribir)

    # guardia (reducción 0.6 → ×0.4; ventana perfect 120 ms; refleja 50 %)
    guard_mult: int           # décimas (4 = ×0.4)
    perfect_ticks: int        # ventana de perfect guard
    perfect_reflect: int      # centenas (50 = 50 % del daño crudo)

    # ultimate (carga: % de daño causado / recibido / orb; max 100)
    ult_dealt_centi: int      # centi-% por 1 de daño causado (60)
    ult_taken_centi: int      # centi-% por 1 de daño recibido (90)
    ult_orb_centi: int        # centi-% por orb (1500)
    ult_max_centi: int        # carga llena (10000 = 100 %)

    # score
    score_hit: int
    score_ko: int
    score_orb: int


def load_rules(path) -> MatchRules:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    sw, dg = d["switch"], d["dodge"]
    gd, ul, sc = d["guard"], d["ultimate"], d["score"]
    return MatchRules(
        tick_ms=int(d["tick_ms"]),
        max_ticks=ticks_from_ms(int(d["match_duration_ms"])),
        party_size=int(d["party_size"]),
        matrix_version=str(d["type_matrix_version"]),
        switch_cd=ticks_from_ms(int(sw["cooldown_ms"])),
        vuln_ticks=ticks_from_ms(int(sw["vulnerable_ms"])),
        vuln_mult=int(round(float(sw["vulnerable_damage_mult"]) * 10)),
        dodge_distance=int(round(float(dg["distance"]) * 100)) * 1000,
        dodge_ticks=ticks_from_ms(int(dg["duration_ms"])),
        iframes_ticks=ticks_from_ms(int(dg["iframes_ms"])),
        dodge_cd=ticks_from_ms(int(dg["cooldown_ms"])),
        guard_mult=int(round((1.0 - float(gd["damage_reduction"])) * 10)),
        perfect_ticks=ticks_from_ms(int(gd["perfect_window_ms"])),
        perfect_reflect=int(round(float(gd["perfect_reflect_mult"]) * 100)),
        ult_dealt_centi=int(round(float(ul["charge_per_damage_dealt_pct"]) * 100)),
        ult_taken_centi=int(round(float(ul["charge_per_damage_taken_pct"]) * 100)),
        ult_orb_centi=int(round(float(ul["charge_per_orb_pct"]) * 100)),
        ult_max_centi=int(round(float(ul["max"]) * 100)),
        score_hit=int(sc["hit"]),
        score_ko=int(sc["ko"]),
        score_orb=int(sc["orb"]),
    )


@dataclass(frozen=True)
class Arena:
    """Arena en unidades fixed-point (coords 0-origin, esquina sup. izq.)."""
    arena_id: str
    w: int
    h: int
    orbs: tuple           # ((x, y, respawn_ticks), ...)
    boss_kits: tuple      # (kit_id, kit_id, kit_id)
    medal: str

    @property
    def orb_respawn(self) -> int:
        return self.orbs[0][2] if self.orbs else 0


def load_arena(path) -> Arena:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    ox, oy = ARENA_CENTER
    orbs = []
    for mx, my in d["orbs"]["spawn_points"]:
        # coords de a8: metros, origen al centro → milli-u 0-origin
        x = int(round(float(mx) * 100)) * 1000 + ox
        y = int(round(float(my) * 100)) * 1000 + oy
        x = max(_MARGIN, min(ARENA_W - _MARGIN, x))
        y = max(_MARGIN, min(ARENA_H - _MARGIN, y))
        orbs.append((x, y, ticks_from_ms(int(d["orbs"]["respawn_ms"]))))
    return Arena(
        arena_id=str(d["arena_id"]),
        w=ARENA_W,
        h=ARENA_H,
        orbs=tuple(orbs),
        boss_kits=tuple(d["boss_team"]),
        medal=str(d.get("medal_on_win", "")),
    )
