"""Runner stdlib-only de la suite QA PODO (Bloque 6). Semántica PASS(0)/FAIL(1)/BLOCKED(2).

Sin falso verde:
  * BLOCKED = no se pudo verificar (falta dependencia o dato) — NO es PASS.
  * Un fallo del propio ARNEZ (bug del test) = FAIL visible, nunca se traga.
  * La puerta "listo para pruebas" = 0 FAIL y 0 BLOCKED.
Estructurado para ser también pytest-runnable (funciones con assert), pero corre solo con stdlib."""
import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import config as cfg

ROOT = Path(__file__).resolve().parent
for _p in (str(cfg.REPO), str(cfg.PODO_DIR)):   # para `import combatcore` y `import podo.*`
    if _p not in sys.path:
        sys.path.insert(0, _p)


class Blocked(Exception):
    """Caso no verificable ahora (dependencia o dato no disponible). Se reporta BLOCKED."""


def cc(name: str):
    """Importa un submódulo (p. ej. 'combatcore.contract'); si falta, Bloquea."""
    try:
        return importlib.import_module(name)
    except Exception as e:
        raise Blocked(f"{name} no disponible ({type(e).__name__}: {e})")


def discover():
    """Familias disponibles: uno por suites/test_*.py (descubrimiento automático)."""
    return sorted(p.stem for p in (ROOT / "suites").glob("test_*.py"))


def _load_suite(suite: str):
    path = ROOT / "suites" / f"{suite}.py"
    if not path.exists():
        raise FileNotFoundError(suite)
    spec = importlib.util.spec_from_file_location(f"podo_qa_{suite}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_one(name, fn):
    t0 = time.perf_counter()
    try:
        fn()
        st, reason = "PASS", ""
    except Blocked as b:
        st, reason = "BLOCKED", str(b)
    except AssertionError as a:
        st, reason = "FAIL", (str(a) or "assert falló")
    except Exception as e:
        st, reason = "FAIL", f"ARNES {type(e).__name__}: {e}"
    return {"name": name, "status": st, "reason": reason, "ms": round((time.perf_counter() - t0) * 1000, 2)}


def inline_kits():
    """Kits M0 inline con el schema v1.0 de a8 (Kit/Ability), espejo de data/kits.
    Para pruebas de COMPORTAMIENTO que no dependen de data/kits/*.json.
    Valores = los kits reales de a8 (hp/damage/range/windup según data/kits)."""
    kits_mod = cc("combatcore.kits")
    K, AB = kits_mod.Kit, kits_mod.Ability

    def _ab(kid, name, kind, dmg, hits, rng, wu, cd):
        return AB(id=f"{kid}_basic", name=name, kind=kind, damage=dmg, hits=hits,
                  range=rng, windup=wu, cooldown=cd, effects=())

    def _kit(kid, name, kind, t, role, hp, speed, weight, ab, dodge_cd=94):
        return K(kit_id=kid, name=name, kind=kind, type=t, role=role, max_hp=hp,
                 speed=speed, weight=weight, basic=ab, q=None, e=None,
                 ultimate=None, dodge_cd=dodge_cd, base_catch=0)

    return {
        "pikachu": _kit("pikachu", "Pikachu", "fighter", "electric", "carry",
                        95, 1800, 100, _ab("pikachu", "Chispa", "combo", 5, 3, 120, 6, 0)),
        "rattata": _kit("rattata", "Rattata", "fighter", "normal", "fighter",
                        45, 1800, 100, _ab("rattata", "Mordisco", "strike", 4, 1, 90, 6, 0)),
        "snorlax": _kit("snorlax", "Snorlax", "fighter", "normal", "defender",
                        130, 1200, 150, _ab("snorlax", "Barrido", "strike", 10, 1, 100, 11, 0)),
    }


def run_suite(suite: str, only=None):
    mod = _load_suite(suite)
    return [_run_one(n, f) for n, f in mod.CASES if only is None or n in only]


def read_json(path):
    return json.loads(Path(path).read_text())
