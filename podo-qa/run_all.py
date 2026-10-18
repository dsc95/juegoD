#!/usr/bin/env python3
"""Corre la suite QA PODO (Bloque 6). Stdlib-only (sin pytest; las funciones son pytest-runnable).

  python3 run_all.py                          # toda la suite descubierta (suites/test_*.py)
  python3 run_all.py --family tipos dano      # solo estas familias
  python3 run_all.py --case comp-doble        # solo este id de caso
  python3 run_all.py --json                   # + runs/run_result.json

Semántica: PASS(0) / FAIL(1) / BLOCKED(2). Puerta "listo para pruebas": 0 FAIL y 0 BLOCKED."""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))          # config / harness
sys.path.insert(0, str(ROOT.parent))   # podo.* (CombatCore, de 31/29)
import harness  # noqa: E402

ICON = {"PASS": "✓", "FAIL": "✗", "BLOCKED": "⊘"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    fams = harness.discover()
    ap.add_argument("--family", nargs="*", choices=sorted(fams), help="familias a correr")
    ap.add_argument("--case", nargs="*", help="solo estos ids de caso")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    todo = a.family or fams
    allres = {}
    n = {"PASS": 0, "FAIL": 0, "BLOCKED": 0}
    for fam in todo:
        try:
            res = harness.run_suite(fam, only=a.case)
        except FileNotFoundError:
            res = [{"name": "<suite ausente>", "status": "BLOCKED", "reason": f"{fam}.py no existe", "ms": 0}]
        allres[fam] = res
        print(f"\n== {fam} ==")
        for r in res:
            n[r["status"]] += 1
            line = f"  {ICON[r['status']]} {r['name']}  ({r['ms']}ms)"
            if r["reason"]:
                line += f"  — {r['reason'].splitlines()[0][:120]}"
            print(line)

    total = sum(n.values())
    ready = n["FAIL"] == 0 and n["BLOCKED"] == 0
    puerta = ("✅ PUERTA ABIERTA (0 FAIL, 0 BLOCKED)" if ready
              else f"⛔ NO LISTO PARA PRUEBAS — {n['FAIL']} FAIL · {n['BLOCKED']} BLOCKED")
    print(f"\n── TOTAL {total} · PASS {n['PASS']} · FAIL {n['FAIL']} · BLOCKED {n['BLOCKED']} ──")
    print(puerta)

    if a.json:
        out = ROOT / "runs" / "run_result.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(
            {"families": allres, "totals": n, "ready": ready,
             "generated": time.strftime("%Y-%m-%d %H:%M:%S")},
            indent=2, ensure_ascii=False))
        print(f"\n[json] {out}")

    sys.exit(0 if ready else (1 if n["FAIL"] else 2))


if __name__ == "__main__":
    main()
