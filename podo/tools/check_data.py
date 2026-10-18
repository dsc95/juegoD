#!/usr/bin/env python3
"""PODO — validador de datos (solo stdlib).

Uso: python3 podo/tools/check_data.py [raiz_proyecto]

Valida:
  1. Todo JSON de data/ fixtures/ parsea.
  2. Matriz 18x18, dominio {0, 0.5, 1, 2}, keys == types.
  3. Kits: invariantes (wild sin ultimate, fighter con wild null, basic presente,
     cooldowns, efectos en enum, kit_id == archivo, ids únicos).
  4. Referencias cruzadas: arena.boss_team -> kits, replay.teams.kits -> kits,
     replay.config.arena -> arenas, match_rules.type_matrix_version == matriz.version.
  5. Medallas: 8 arenas por región, medal_id únicos, m0:true con refs existentes.
  6. Curva de captura: recalcula bounds C4 (>=0.85 y <=0.15).
  7. Fixture smoke: formato, frames_total == duration/tick, actions en enum.

Exit 0 = OK. Exit 1 = errores (se listan).
"""
import json
import sys
from pathlib import Path

if len(sys.argv) > 1:
    _base = Path(sys.argv[1]).resolve()
    RAIZ = _base if (_base / "data").is_dir() else _base / "podo"
else:
    RAIZ = Path(__file__).resolve().parent.parent

TYPES = ["normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost",
         "steel", "fire", "water", "grass", "electric", "psychic", "ice", "dragon",
         "dark", "fairy"]
DOMAIN = {0, 0.5, 1, 2}
ACTIONS = {"basic", "q", "e", "dodge", "guard_on", "guard_off", "ultimate", "switch", "ball"}
EFFECT_TYPES = {"apply_state", "knockback", "pushback", "heal", "shield",
                "reflect", "team_shield", "interrupt"}

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(rel, required=True):
    p = RAIZ / rel
    if not p.exists():
        if required:
            err(f"falta {rel}")
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        err(f"{rel}: JSON inválido: {e}")
        return None


def need(cond, msg):
    if not cond:
        err(msg)


# ---------- 1. Matriz ----------
matrix = load("data/types/type_matrix_v1.json")
matrix_version = None
if matrix:
    matrix_version = matrix.get("version")
    need(isinstance(matrix_version, str), "matriz: version no es string")
    tlist = matrix.get("types", [])
    need(sorted(tlist) == sorted(TYPES), f"matriz: types != los 18 canónicos (diff: {set(TYPES) ^ set(tlist)})")
    m = matrix.get("matrix", {})
    need(set(m) == set(TYPES), "matriz: filas != types")
    for att, row in m.items():
        need(set(row) == set(TYPES), f"matriz: columna {att} != types")
        for dfn, v in row.items():
            need(v in DOMAIN, f"matriz[{att}][{dfn}] = {v!r} fuera de dominio {sorted(DOMAIN)}")
    for a in TYPES:
        for d in TYPES:
            need(m.get(a, {}).get(d) is not None, f"matriz[{a}][{d}] ausente")

# ---------- 2. Config ----------
rules = load("data/config/match_rules.json")
if rules:
    need(rules.get("tick_ms") == 16, "match_rules: tick_ms debe ser 16")
    need(rules.get("type_matrix_version") == matrix_version,
         f"match_rules.type_matrix_version={rules.get('type_matrix_version')!r} != matriz.version={matrix_version!r}")
    need(rules.get("switch", {}).get("cooldown_ms") == 4000, "match_rules.switch.cooldown_ms != 4000 (C3)")

capture = load("data/config/capture.json")
if capture:
    p_cap = capture.get("p_cap", 0)
    exp = capture.get("hp_exp", 1.5)
    balls = capture.get("balls", {})
    need(set(balls) == {"poke_ball", "great_ball", "ultra_ball"}, "capture: faltan balls")
    need(0 < p_cap <= 0.9, "capture: p_cap fuera de (0, 0.9]")

    def p_catch(hp_pct, ball, base):
        return min(p_cap, base * balls[ball] * (1 - hp_pct) ** exp)

    pa = p_catch(0.10, "ultra_ball", 1.0)
    pb = p_catch(0.90, "poke_ball", 1.0)
    need(pa >= 0.85, f"C4 case_a: p(10%HP, ultra) = {pa:.4f} < 0.85")
    need(pb <= 0.15, f"C4 case_b: p(90%HP, poke) = {pb:.4f} > 0.15")

# ---------- 3. Kits ----------
kits = {}
kits_dir = RAIZ / "data" / "kits"
if kits_dir.is_dir():
    for p in sorted(kits_dir.glob("*.json")):
        k = load(p.relative_to(RAIZ))
        if not k:
            continue
        kid = k.get("kit_id")
        need(kid == p.stem, f"{p.name}: kit_id ({kid!r}) != nombre de archivo")
        need(kid not in kits, f"kit_id duplicado: {kid}")
        kits[kid] = k
        need(k.get("type") in TYPES, f"{kid}: type inválido {k.get('type')!r}")
        kind = k.get("kind")
        need(kind in ("fighter", "wild"), f"{kid}: kind inválido")
        ab = k.get("abilities", {})
        need("basic" in ab, f"{kid}: falta basic")
        for slot, ab_ in ab.items():
            need(isinstance(ab_, dict), f"{kid}.{slot}: no es object")
            for fld in ("id", "name", "kind", "damage", "range", "windup_ms", "cooldown_ms"):
                need(fld in ab_, f"{kid}.{slot}: falta {fld}")
            for eff in ab_.get("effects", []):
                need(eff.get("type") in EFFECT_TYPES,
                     f"{kid}.{slot}: effect.type {eff.get('type')!r} no está en el enum del engine")
        if kind == "wild":
            need("ultimate" not in ab, f"{kid}: wild no puede tener ultimate")
            w = k.get("wild")
            need(isinstance(w, dict) and 0 < w.get("base_catch", 0) <= 1,
                 f"{kid}: wild requiere wild.base_catch en (0, 1]")
        else:
            need(k.get("wild") in (None, {}), f"{kid}: fighter no debe tener bloque wild")
            for slot in ("q", "e"):
                if slot in ab:
                    need(ab[slot].get("cooldown_ms", 0) > 0, f"{kid}.{slot}: cooldown_ms debe ser > 0")
            if "ultimate" in ab:
                need(ab["ultimate"].get("cooldown_ms") == 0, f"{kid}.ultimate: cooldown_ms debe ser 0")

for kid in ("pikachu", "snorlax", "gardevoir", "rattata", "oddish"):
    need(kid in kits, f"kit de M0 ausente: {kid}")

# ---------- 4. Arenas + medallas ----------
arenas = {}
arenas_dir = RAIZ / "data" / "arenas"
if arenas_dir.is_dir():
    for p in sorted(arenas_dir.glob("*.json")):
        a = load(p.relative_to(RAIZ))
        if not a:
            continue
        arenas[a["arena_id"]] = a
        for ref in a.get("boss_team", []):
            need(ref in kits, f"{a['arena_id']}: boss_team referencia kit inexistente {ref!r}")
        for ref in a.get("boss_team_fallback_neutral", []):
            need(ref in kits, f"{a['arena_id']}: boss_team_fallback_neutral referencia kit inexistente {ref!r}")

need("arena_001" in arenas, "falta arena_001 (M0)")

medals_dir = RAIZ / "data" / "medals"
if medals_dir.is_dir():
    for p in sorted(medals_dir.glob("*.json")):
        r = load(p.relative_to(RAIZ))
        if not r:
            continue
        ar = r.get("arenas", [])
        need(len(ar) == 8, f"{p.name}: región debe tener 8 arenas (tiene {len(ar)})")
        seen = set()
        for e in ar:
            mid = e.get("medal_id")
            need(mid not in seen, f"{p.name}: medal_id duplicado {mid}")
            seen.add(mid)
            need(e.get("gym_type") in TYPES, f"{p.name}: gym_type inválido {e.get('gym_type')!r}")
            need("m0" in e, f"{p.name}: arenaEntry sin flag m0")
            if e.get("m0"):
                need(e.get("arena_id") in arenas,
                     f"{p.name}: m0:true en {e.get('arena_id')} sin archivo de arena")
        need("championship" in r and "unlock" in r["championship"], f"{p.name}: falta championship")

# ---------- 5. Fixtures ----------
fx_dir = RAIZ / "fixtures"
if fx_dir.is_dir():
    for p in sorted(fx_dir.glob("*.json")):
        f = load(p.relative_to(RAIZ))
        if not f:
            continue
        need(f.get("format") == "podo.replay", f"{p.name}: format != podo.replay")
        need(f.get("format_version") == 1, f"{p.name}: format_version != 1")
        need(f.get("matrix_version") == matrix_version,
             f"{p.name}: matrix_version pin != matriz canónica")
        cfg = f.get("config", {})
        need(cfg.get("tick_ms") == 16, f"{p.name}: tick_ms != 16")
        frames = cfg.get("match_duration_ms", 0) / cfg.get("tick_ms", 16)
        tail = f.get("tail", {})
        need(tail.get("frames_total") == frames,
             f"{p.name}: tail.frames_total ({tail.get('frames_total')}) != duration/tick ({frames})")
        for team in ("a", "b"):
            for ref in cfg.get("teams", {}).get(team, {}).get("kits", []):
                need(ref in kits, f"{p.name}: team {team} referencia kit inexistente {ref!r}")
        need(cfg.get("arena") in arenas, f"{p.name}: arena {cfg.get('arena')!r} no existe")
        prev = {}
        for fr in f.get("inputs", []):
            for fld in ("t", "side", "seat", "input"):
                need(fld in fr, f"{p.name}: frame sin campo {fld}")
            need(fr["side"] in ("a", "b"), f"{p.name}: side inválido")
            need(0 <= fr["seat"] <= 2, f"{p.name}: seat inválido")
            for act in fr["input"].get("actions", []):
                need(act in ACTIONS, f"{p.name}: action inválida {act!r}")
            key = (fr["side"], fr["seat"])
            need(prev.get(key, -1) <= fr["t"], f"{p.name}: inputs no ordenados para {key}")
            prev[key] = fr["t"]
        need(str(tail.get("final_state_hash", "")).startswith("sha256:"),
             f"{p.name}: final_state_hash debe ser sha256:...")

# ---------- report ----------
for w in warnings:
    print(f"WARN  {w}")
if errors:
    for e in errors:
        print(f"ERROR {e}")
    print(f"\nFAIL: {len(errors)} error(es)")
    sys.exit(1)
print(f"OK: matriz v{matrix_version} ({324 if matrix else '?'} celdas) | {len(kits)} kits | "
      f"{len(arenas)} arena(s) | validador PODO sin errores")
