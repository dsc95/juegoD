"""VETO anti-RPG — 0 mecánicas de nivel/XP/crecimiento de stats en el código runtime.
El escáner apunta a CÓDIGO (identificadores), no a prosa: excluye comentarios (#) y
docstrings, porque el propio docstring que DECLARA el veto ("no hay nivel, XP ni...")
contiene la palabra sin ser una mecánica. El grep crudo con prosa queda reportado a
mano en cada gate (transparencia, no se esconde)."""
import dataclasses
import json
import re

import config as cfg
from harness import Blocked, cc


def _code_lines(path):
    """Líneas de código de un .py: sin comentarios de línea y sin bloques de docstring."""
    out, in_doc = [], None
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if in_doc:
            if in_doc in s:
                in_doc = None
            continue
        if s.startswith("#"):
            continue
        m = re.match(r'^("""|\'\'\')', s)
        if m:
            if s.count(m.group(1)) < 2:   # docstring multi-línea: se cierra adelante
                in_doc = m.group(1)
            continue
        out.append((i, line))
    return out


def runtime_no_rpg():
    core = cfg.PODO_DIR / "combatcore"
    if not core.exists():
        raise Blocked("podo/combatcore/ no existe aún")
    hits = []
    for p in sorted(core.rglob("*.py")):
        for i, line in _code_lines(p):
            for pat in cfg.ANTI_RPG_PATTERNS:
                if re.search(pat, line, re.IGNORECASE):
                    hits.append(f"{p.relative_to(cfg.PODO_DIR)}:{i}: {line.strip()}")
    assert not hits, "mecánica RPG detectada en código runtime (VETO anti-RPG):\n" + "\n".join(hits[:20])


def _flatten_keys(d, prefix=""):
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            keys.add(f"{prefix}{k}")
            keys |= _flatten_keys(v, f"{prefix}{k}.")
    elif isinstance(d, list):
        for v in d:
            keys |= _flatten_keys(v, prefix)
    return keys


def kits_fijos():
    """Anti-RPG estructural: ni el schema del kit (Kit/Ability/Effect) ni los JSON de
    data/kits pueden expresar nivel/XP/crecimiento — los stats son fijos (veto absoluto)."""
    kits_mod = cc("combatcore.kits")
    bad = {"level", "xp", "exp", "stat_growth", "tree_of_moves"}
    for cls in (kits_mod.Kit, kits_mod.Ability, kits_mod.Effect):
        fields = {f.name for f in dataclasses.fields(cls)}
        assert not (fields & bad), f"{cls.__name__} expone campos RPG: {fields & bad}"
    n = 0
    for p in sorted((cfg.DATA_DIR / "kits").glob("*.json")):
        keys = {k.split(".")[-1] for k in _flatten_keys(json.loads(p.read_text(encoding="utf-8")))}
        assert not (keys & bad), f"{p.name} trae campos RPG: {keys & bad}"
        n += 1
    assert n >= 3, f"esperaba ≥3 kits en data/kits, encontré {n}"


CASES = [
    ("runtime-no-rpg", runtime_no_rpg),
    ("kits-fijos", kits_fijos),
]
