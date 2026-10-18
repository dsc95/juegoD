"""Coherencia data/loader de kits (anti-drift) — schema v1.0 de a8
(docs/KIT-DEFINITION.md). Cada data/kits/*.json debe cargar con
combatcore.kits.load_kit y producir un Kit válido; default_teams() (contrato)
debe poder construir el match 1v1 sin tocar nada a mano."""
import config as cfg
from harness import Blocked, cc


def all_kits_cargan():
    kits_mod = cc("combatcore.kits")
    kits = kits_mod.load_kits(cfg.DATA_DIR)
    assert len(kits) >= 3, f"esperaba ≥3 kits, cargué {len(kits)}: {sorted(kits)}"
    for k in kits.values():
        assert k.id and k.name and k.type, f"kit {k.id}: faltan campos"
        assert k.kind in ("fighter", "wild"), f"kit {k.id}: kind inválido {k.kind}"
        assert k.max_hp > 0 and k.speed > 0 and k.weight > 0 and k.dodge_cd > 0, \
            f"kit {k.id}: stats inválidos (hp={k.max_hp} speed={k.speed} w={k.weight} dodge={k.dodge_cd})"
        b = k.basic
        assert b.damage > 0 and b.range > 0, f"kit {k.id}: basic inválido {b}"
        assert b.windup >= 0 and b.cooldown >= 0, f"kit {k.id}: timing inválido {b}"
        assert 1 <= b.hits <= 5, f"kit {k.id}: hits fuera de 1..5: {b.hits}"
        assert b.kind in kits_mod.ABILITY_KINDS, f"kit {k.id}: kind de ability {b.kind!r}"
        if k.kind == "wild":
            assert k.base_catch > 0, f"wild {k.id}: base_catch debe estar en (0,100] (centenas)"
            assert k.ultimate is None, f"wild {k.id} no puede tener ultimate"


def default_teams_funciona():
    """El contrato FIRMADO expone default_teams() (1v1 pikachu vs snorlax): debe poder
    construir el match sin tocar nada a mano."""
    teams = cc("combatcore.contract").default_teams()
    assert len(teams) == 2 and all(len(t) == 1 for t in teams), f"default_teams malformado: {teams}"
    a, x1, y1 = teams[0][0]
    b, x2, y2 = teams[1][0]
    assert a.type == "electric" and b.type == "normal", f"tipos inesperados: {a.type}/{b.type}"
    # Invariante INSENSIBLE a la escala del grid (spec: 2.5 m / 7.5 m / 3.0 m en
    # arena 10×6 m): cuarto / tres-cuartos de ancho, mitad de alto (±1 %).
    # El grid rescaló ×1000 el 2026-10-18 (1u=1/100 m → 1e-5 m): el anchor duro
    # 250/750 se rompió sin que la física cambiara → se afirma en fracciones.
    core_mod = cc("combatcore.core")
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    arena = core_mod.CombatCore(1, teams, matrix).arena
    tol_w, tol_h = arena.w * 0.01, arena.h * 0.01
    assert abs(x1 - arena.w / 4) <= tol_w, f"x1 fuera de ¼ de arena: {x1} (w={arena.w})"
    assert abs(x2 - 3 * arena.w / 4) <= tol_w, f"x2 fuera de ¾ de arena: {x2} (w={arena.w})"
    assert abs(y1 - arena.h / 2) <= tol_h and abs(y2 - arena.h / 2) <= tol_h, \
        f"y fuera de ½ de arena: y1={y1} y2={y2} (h={arena.h})"


def velocidad_doc():
    """Velocidad absoluta documentada: move_speed × base_speed_m (DATA-ARCHITECTURE
    §2.1; match_rules.note: pikachu 1.15×3.6=4.14 m/s, ~2.4 s de cruce de arena).
    Mide el dx real tras N ticks y convierte a m/s con la escala DERIVADA de la
    data (size_m de la arena), sin hardcodear el grid. N=60 ticks (0.96 s ≈
    4.0 m): lo bastante corto para NO tocar la pared (clamp) — a velocidad
    correcta el activo recorrería 39.7 m en 600 ticks y el dx saturaría en la
    distancia al borde (2.5 m → 10 m), falseando la media."""
    import json

    def _j(p):
        return json.loads((cfg.DATA_DIR / p).read_text())

    core_mod = cc("combatcore.core")
    frames_mod = cc("combatcore.frames")
    matrix = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    core = core_mod.CombatCore(1, None, matrix)
    e = core.entities[0]
    x0 = e.x
    n = 60
    for f in range(n):
        core.step({0: frames_mod.InputFrame(frame=f, move_x=1)})
    dx = e.x - x0
    assert dx > 0, "el activo no se movió con move_x=1"
    upm = core.arena.w / _j("arenas/arena_001.json")["size_m"][0]   # pos-u por metro (data)
    kit_js = _j("kits/pikachu.json")["stats"]["move_speed"]
    base_m = _j("config/match_rules.json")["base_speed_m"]
    esperado = kit_js * base_m                                     # m/s (contrato a8)
    medido = dx / upm / (n * cc("combatcore.constants").TICK_MS / 1000)
    assert abs(medido - esperado) / esperado <= 0.05, \
        f"velocidad medida {medido:.4f} m/s ≠ documentada {esperado:.2f} m/s (factor {medido/esperado:.3f})"


CASES = [
    ("all-kits-cargan", all_kits_cargan),
    ("default-teams-funciona", default_teams_funciona),
    ("velocidad-doc", velocidad_doc),
]
