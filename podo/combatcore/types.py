"""Matriz de matchup de tipos.

Fuente de verdad: data/types/type_matrix_v1.json (v1.0.0, 18×18, verificada
contra Bulbapedia por a8 — dueña de la matriz). Los multiplicadores en el
archivo son {0, 0.5, 1, 2}; el core los mantiene en DÉCIMAS enteras
(0/5/10/20) para la aritmética determinista (la conversión round(v*10) se
hace una vez en el loader).
"""
from __future__ import annotations

import json
from pathlib import Path

TENTHS_VALID = (0, 5, 10, 20)


class TypeMatrix:
    def __init__(self, types, matrix, version):
        self.types = list(types)
        self.version = str(version)
        self._m = {}
        for atk, row in matrix.items():
            if atk not in self.types:
                raise ValueError(f"tipo atacante desconocido: {atk!r}")
            for d, v in row.items():
                if d not in self.types:
                    raise ValueError(f"tipo defensor desconocido: {d!r}")
                tenths = int(round(float(v) * 10))
                if tenths not in TENTHS_VALID:
                    raise ValueError(
                        f"multiplicador inválido para {atk}->{d}: {v} "
                        f"(dominio: {{0, 0.5, 1, 2}})")
                self._m[(atk, d)] = tenths
        for a in self.types:
            for d in self.types:
                if (a, d) not in self._m:
                    raise ValueError(f"falta par en la matriz: {a}->{d}")

    @classmethod
    def load(cls, path) -> "TypeMatrix":
        """Carga la matriz desde JSON. La canónica en disco es
        type_matrix_v1.json (fracciones {0, 0.5, 1, 2}, a8). El loader
        además acepta la escala histórica en décimas {0, 5, 10, 20}
        (fuente histórica eliminada 2026-10-18): se auto-detecta, los
        dos dominios son disjuntos salvo el 0."""
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        vals = {v for row in d["matrix"].values() for v in row.values()}
        if vals <= {0, 0.5, 1, 2}:
            matrix = {a: {dd: float(v) for dd, v in row.items()}
                      for a, row in d["matrix"].items()}
        elif vals <= {0, 5, 10, 20}:
            matrix = {a: {dd: float(v) / 10.0 for dd, v in row.items()}
                      for a, row in d["matrix"].items()}
        else:
            raise ValueError(
                f"escala de multiplicadores no reconocida: {sorted(vals)[:6]}…")
        return cls(d["types"], matrix, d["version"])

    def mult(self, attacker: str, defender: str) -> int:
        """Multiplicador en décimas (10 = ×1, 20 = ×2, 5 = ×0.5, 0 = ×0)."""
        return self._m[(attacker, defender)]
