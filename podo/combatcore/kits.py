"""Loader de KitDefinition — schema v1.0 de a8 (docs/KIT-DEFINITION.md).

El kit es CONTENIDO PURO: CombatCore es su intérprete. Las reglas globales
NO están en el kit (viven en match_rules.json → rules.py).

Conversión float → entero de una sola vez (la sim solo ve enteros):
- move_speed (MULTIPLICADOR adimensional sobre base_speed_m global, en
  match_rules.json; cierre 31/a8 2026-10-18) → unidades/1000ms:
  round(move_speed * base_speed_m * 100). NUNCA con /1000 (typo de la doc
  de a8: congela el engine).
- range (metros) → milli-u: round(range * 100) * 1000
- knockback/pushback value (metros) → milli-u: round(v * 100) * 1000
- windup_ms / cooldown_ms / dodge_ms → ticks vía ticks_from_ms
- weight → centenas (1.0 → 100): kits pesados empujan menos
- base_catch → centenas (1.0 → 100), solo wilds (semana 3)

Los effects usan un enum CERRADO (KIT-DEFINITION.md): si aparece uno nuevo,
el loader falla (no se inventa interpretación).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .constants import ticks_from_ms

EFFECT_TYPES = (
    "apply_state", "knockback", "pushback", "heal",
    "shield", "reflect", "team_shield", "interrupt",
)
STATE_IDS = {"stagger": 1, "stun": 2, "slow": 3}
ABILITY_KINDS = (
    "combo", "strike", "dash_strike", "evade_strike",
    "control", "aoe", "team_aoe",
)


@dataclass(frozen=True)
class Effect:
    type: str          # enum cerrado (EFFECT_TYPES)
    state: int         # 0=n/a, 1=stagger, 2=stun, 3=slow (solo apply_state)
    ms: int            # duración en ms (entero, del JSON)
    value: int         # entero fijo: knockback/pushback = unidades (m×100);
                       # reflect/shield/team_shield = centenas (0.5 → 50)


def _effect(d: dict) -> Effect:
    t = d["type"]
    if t not in EFFECT_TYPES:
        raise ValueError(f"effect desconocido (enum cerrado): {t!r}")
    v = float(d.get("value", 0))
    value = 0
    if t in ("knockback", "pushback"):
        value = int(round(v * 100)) * 1000   # metros → milli-u
    elif t in ("reflect", "shield", "team_shield"):
        value = int(round(v * 100))
    elif t == "heal":
        value = int(round(v))
    state = STATE_IDS.get(d.get("state", ""), 0)
    if t == "apply_state" and state == 0:
        raise ValueError(f"apply_state sin estado válido: {d.get('state')!r}")
    return Effect(t, state, int(d.get("ms", 0)), value)


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    kind: str          # combo|strike|dash_strike|evade_strike|control|aoe|team_aoe
    damage: int
    hits: int          # 1..5; un combo golpea en los N primeros ticks ACTIVE
    range: int         # milli-u (m × 100 × 1000)
    windup: int        # ticks
    cooldown: int      # ticks (0 = sin CD, p.ej. basic)
    effects: tuple     # (Effect, ...)


def _ability(d: dict) -> Ability:
    kind = d["kind"]
    if kind not in ABILITY_KINDS:
        raise ValueError(f"kind de ability desconocido: {kind!r}")
    hits = int(d.get("hits", 1))
    if not 1 <= hits <= 5:
        raise ValueError(f"hits fuera de 1..5: {hits}")
    return Ability(
        id=d["id"],
        name=d["name"],
        kind=kind,
        damage=int(d["damage"]),
        hits=hits,
        range=int(round(float(d["range"]) * 100)) * 1000,
        windup=ticks_from_ms(int(d["windup_ms"])),
        cooldown=ticks_from_ms(int(d.get("cooldown_ms", 0))),
        effects=tuple(_effect(x) for x in d.get("effects", [])),
    )


@dataclass(frozen=True)
class Kit:
    kit_id: str
    name: str
    kind: str          # fighter | wild
    type: str          # tipos de la matriz (M0: single)
    role: str
    max_hp: int
    speed: int         # u/s (ya resuelto: move_speed × base_speed_m × 100)
    weight: int        # centenas (masa para knockback)
    basic: Ability
    q: Ability | None
    e: Ability | None
    ultimate: Ability | None
    dodge_cd: int      # ticks (kit sobreescribe el global)
    base_catch: int    # centenas, solo wild

    @property
    def id(self) -> str:  # compat con código existente (31/contract)
        return self.kit_id


def load_kit(path, base_speed_m: float) -> Kit:
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    if d["kit_id"] != p.stem:
        raise ValueError(f"kit_id {d['kit_id']!r} != nombre de archivo {p.stem!r}")
    if d.get("schema_version", "1.0") not in ("1.0", 1.0):
        raise ValueError(f"schema_version de kit no soportado: {d.get('schema_version')}")
    st, ab = d["stats"], d["abilities"]
    wild = d.get("wild") or {}
    if d["kind"] == "wild" and "ultimate" in ab:
        raise ValueError(f"kit wild con ultimate: {d['kit_id']}")
    if d["kind"] not in ("fighter", "wild"):
        raise ValueError(f"kind de kit inválido: {d['kind']!r}")
    return Kit(
        kit_id=d["kit_id"],
        name=d["name"],
        kind=d["kind"],
        type=d["type"],
        role=d["role"],
        max_hp=int(st["max_hp"]),
        speed=int(round(float(st["move_speed"]) * float(base_speed_m) * 100)),
        weight=int(round(float(st["weight"]) * 100)),
        basic=_ability(ab["basic"]),
        q=_ability(ab["q"]) if "q" in ab else None,
        e=_ability(ab["e"]) if "e" in ab else None,
        ultimate=_ability(ab["ultimate"]) if "ultimate" in ab else None,
        dodge_cd=ticks_from_ms(int(d.get("cooldowns", {}).get("dodge_ms", 1500))),
        base_catch=int(round(float(wild.get("base_catch", 0)) * 100)),
    )


def load_kits(data_dir, base_speed_m: float = None) -> dict:
    """{kit_id: Kit} para todos los data/kits/*.json (orden alfabético).

    `base_speed_m` (m/s, serie) viene de data/config/match_rules.json;
    se lee una vez aquí (fuente canónica de a8) salvo override en tests.
    """
    if base_speed_m is None:
        try:
            d = json.loads(
                (Path(data_dir) / "config" / "match_rules.json")
                .read_text(encoding="utf-8"))
            base_speed_m = float(d["base_speed_m"])
        except (OSError, KeyError, ValueError):
            base_speed_m = 3.6
    kits = {}
    for p in sorted(Path(data_dir).glob("kits/*.json")):
        k = load_kit(p, base_speed_m)
        if k.kit_id in kits:
            raise ValueError(f"kit duplicado: {k.kit_id}")
        kits[k.kit_id] = k
    return kits
