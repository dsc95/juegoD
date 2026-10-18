"""Matriz canónica 18×18 — validada contra data/types/type_matrix_v1.json (a8, v1.0.0).
Fuente única: el archivo canónico (decimales {0, 0.5, 1, 2}); NO el placeholder.
Pineado: version "1.0.0" + conteo de celdas 51×2/61×0.5/204×1/8×0 + las 8 inmunidades.
C1 del formulario corregido (electric->normal = ×1). Regla dual-type = spec (§2).
El loader del engine (décimas) se valida contra la canónica; el default del
engine (contract.default_matrix, que carga la canónica directo tras la
migración de 31) debe CASAR con ella."""
import json

import config as cfg
from harness import Blocked, cc


def _canon():
    return json.loads(cfg.CANONICAL_MATRIX.read_text(encoding="utf-8"))


def version_pinned():
    assert _canon()["version"] == cfg.CANONICAL_VERSION, \
        f"version de la canónica = {_canon().get('version')!r} (esperado {cfg.CANONICAL_VERSION!r})"


def shape_18x18():
    d = _canon()
    assert len(d["types"]) == cfg.TYPE_COUNT, f"tipos={len(d['types'])}"
    m = d["matrix"]
    assert set(m) == set(d["types"]), "filas != types"
    for att, row in m.items():
        assert set(row) == set(d["types"]), f"columna {att} != types"
        for v in row.values():
            assert v in (0, 0.5, 1, 2), f"{att} mult inválido: {v}"
    assert sum(len(r) for r in m.values()) == 324


def count_vector():
    """Conteo de celdas por multiplicador (sanity de a8): 51 ×2 · 61 ×0.5 · 204 ×1 · 8 ×0."""
    from collections import Counter
    d = _canon()
    c = Counter(v for row in d["matrix"].values() for v in row.values())
    assert c == {2: 51, 0.5: 61, 1: 204, 0: 8}, \
        f"conteo de celdas difiere de la canónica v1.0.0: {dict(c)}"


def inmunidades_exactas():
    """Las 8 inmunidades listadas por a8, y NINGUNA otra celda ×0."""
    d = _canon()
    m = d["matrix"]
    for att, dfn in cfg.IMMUNITIES:
        assert m[att][dfn] == 0.0, f"{att}->{dfn} debe ser inmune (×0), es {m[att][dfn]}"
    zeros = {(a, dfn) for a, row in m.items() for dfn, v in row.items() if v == 0.0}
    assert zeros == set(cfg.IMMUNITIES), \
        f"celdas ×0 distintas a las 8 canónicas: {sorted(zeros ^ set(cfg.IMMUNITIES))}"


def diagonal():
    """Diagonal de la canónica: 7 ×1, 9 ×0.5 (auto-resistencia), 2 ×2 (ghost, dragon)."""
    d = _canon()
    m = d["matrix"]
    diag = {t: m[t][t] for t in d["types"]}
    assert sum(1 for v in diag.values() if v == 1.0) == 7, \
        f"diagonales ×1: {sum(1 for v in diag.values() if v == 1.0)}"
    assert sum(1 for v in diag.values() if v == 0.5) == 9, \
        f"diagonales ×0.5: {sum(1 for v in diag.values() if v == 0.5)}"
    assert {t for t, v in diag.items() if v == 2.0} == {"ghost", "dragon"}, \
        f"diagonales ×2 inesperadas: {sorted(t for t, v in diag.items() if v == 2.0)}"


def c1_corregido():
    """C1 del formulario decía Pikachu(Electric)->Snorlax(Normal)=×2; la canónica
    dice ×1 (a8, TYPE-MATRIX.md §5). El fixture valida contra la canónica."""
    d = _canon()
    assert d["matrix"]["electric"]["normal"] == 1.0, "electric->normal debe ser ×1 (C1 corregido)"


def oddish_rama_0_5():
    """Rama 0.5× de Oddish (Planta, stretch): electric->grass = ×0.5 (31)."""
    d = _canon()
    assert d["matrix"]["electric"]["grass"] == 0.5, "electric->grass debe ser ×0.5 (rama de Oddish)"


def dual_type_spec():
    """Regla dual-type (TYPE-MATRIX.md §2): producto de los dos pares con clamp
    (4 -> 2, 0.25 -> 0.5); la inmunidad (×0) manda. Modelo de referencia (el engine
    la cablea cuando existan defensores dual; M0 = single type)."""
    d = _canon()

    def dual(att, d1, d2):
        v = d["matrix"][att][d1] * d["matrix"][att][d2]
        if v == 0.0:
            return 0.0
        return max(0.5, min(2.0, v))

    assert dual("electric", "water", "flying") == 2.0, "electric: 2×2 = 4 → clamp 2"
    assert dual("ice", "fire", "ice") == 0.5, "ice: 0.5×0.5 = 0.25 → clamp 0.5"
    assert dual("electric", "water", "ground") == 0.0, "inmunidad no se clampa: ×0 manda"
    assert dual("normal", "fire", "grass") == 1.0, "neutro doble = ×1"


def engine_load_canonical():
    """El loader del engine debe poder leer la canónica (decimales → décimas)."""
    tm = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    assert tm.version == cfg.CANONICAL_VERSION
    assert tm.mult("electric", "water") == 20, "electric->water debe ser ×2 (20 décimas)"
    assert tm.mult("electric", "ground") == 0, "electric->ground debe ser inmune"
    assert tm.mult("bug", "fire") == 5, "bug->fire debe ser ×0.5 (5 décimas)"


def engine_default_matrix():
    """El default del engine (contract.default_matrix) debe cargar y CASAR con la
    canónica celda a celda. Tras la migración de 31 apunta a type_matrix_v1.json
    directo (data/types.json ELIMINADO del árbol el 2026-10-18, luz de ab) — este
    caso queda como guard de la vía de carga + encoding del contrato (≡ canónica)."""
    contract = cc("combatcore.contract")
    m = contract.default_matrix()
    canon = _canon()["matrix"]
    for att, row in canon.items():
        for dfn, v in row.items():
            assert m.mult(att, dfn) == int(round(v * 10)), \
                f"default_matrix {att}->{dfn}={m.mult(att, dfn)} != canónica ×{v}"


CASES = [
    ("version-pinned", version_pinned),
    ("shape-18x18", shape_18x18),
    ("count-vector", count_vector),
    ("inmunidades-exactas", inmunidades_exactas),
    ("diagonal", diagonal),
    ("c1-corregido", c1_corregido),
    ("oddish-rama-0-5", oddish_rama_0_5),
    ("dual-type-spec", dual_type_spec),
    ("engine-load-canonical", engine_load_canonical),
    ("engine-default-matrix", engine_default_matrix),
]
