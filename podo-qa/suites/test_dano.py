"""Fórmula de daño — valida la ÚNICA fuente de verdad (combatcore.contract.compute_damage).
Aritmética entera (fixed-point en décimas). Orden del contrato: tipo → vulnerable(×1.5)
→ guardia(×0.4) → ultimate(×2); perfect_guard → 0. Usa una matriz sintética controlada
(0/5/10/20) para probar el manejo de multiplicadores sin depender de la canónica de a8."""
import config as cfg
from harness import Blocked, cc

_C = None
def _contract():
    global _C
    if _C is None:
        _C = cc("combatcore.contract")
    return _C


def _synth():
    return cc("combatcore.types").TypeMatrix(
        ["a", "b"],
        {"a": {"a": 1.0, "b": 2.0},    # a→a ×1, a→b ×2
         "b": {"a": 0.5, "b": 0.0}},   # b→a ×0.5, b→b ×0 (inmune)
        "qa-synth")


def _d(base, att, df, **kw):
    return _contract().compute_damage(base, att, df, matrix=_synth(), **kw)


def ref(base, mult, *, guarding=False, perfect_guard=False, vulnerable=False, is_ultimate=False):
    """Referencia independiente re-derivada del contrato documentado (orden + floor en décimas)."""
    v = int(base) * mult
    if vulnerable:
        v = v * cfg.VULN_MULT // 10
    if perfect_guard:
        v = 0
    elif guarding:
        v = v * cfg.GUARD_MULT // 10
    if is_ultimate:
        v = v * cfg.ULT_MULT // 10
    return max(0, v // 10)


def dano_neutro():     assert _d(100, "a", "a") == 100
def dano_doble():      assert _d(100, "a", "b") == 200
def dano_mitad():      assert _d(100, "b", "a") == 50
def dano_inmune():     assert _d(100, "b", "b") == 0
def dano_vulnerable():  assert _d(100, "a", "b", vulnerable=True) == 300
def dano_guardia():     assert _d(100, "a", "a", guarding=True) == 40
def dano_vuln_guardia():assert _d(100, "a", "a", vulnerable=True, guarding=True) == 60
def dano_ultimate():    assert _d(100, "a", "a", is_ultimate=True) == 200
def dano_ult_doble():   assert _d(100, "a", "b", is_ultimate=True) == 400
def dano_perfect():     assert _d(100, "a", "b", perfect_guard=True) == 0
def dano_perfect_prio():assert _d(100, "a", "b", perfect_guard=True, guarding=True) == 0
def dano_fixedpoint():  assert _d(101, "a", "a", guarding=True) == 40   # 1010*4//10=404//10=40


def dano_explora_combinaciones():
    # barrido base × matchup × flags contra la referencia del contrato (orden + floor exacto)
    for base in (1, 40, 100, 101, 250):
        for att, df, m in (("a", "a", 10), ("a", "b", 20), ("b", "a", 5), ("b", "b", 0)):
            for vuln, guard, perf, ult in (
                    (False, False, False, False), (True, False, False, False),
                    (False, True, False, False), (True, True, False, False),
                    (False, False, True, False), (False, False, False, True),
                    (True, True, True, True)):
                got = _d(base, att, df, vulnerable=vuln, guarding=guard,
                         perfect_guard=perf, is_ultimate=ult)
                exp = ref(base, m, vulnerable=vuln, guarding=guard,
                          perfect_guard=perf, is_ultimate=ult)
                assert got == exp, (f"base={base} {att}->{df}(×{m/10}) v={vuln} g={guard} "
                                    f"p={perf} u={ult}: got {got} != exp {exp}")


def dano_determinista():
    assert _d(40, "a", "b", vulnerable=True) == _d(40, "a", "b", vulnerable=True)


def dano_con_canonica():
    """La canónica real (v1.0.0) a través de la única fuente de verdad del daño.
    base = daño real del kit de a8 (Pikachu: 5). C1 corregido: electric→normal = ×1."""
    m = cc("combatcore.types").TypeMatrix.load(cfg.CANONICAL_MATRIX)
    assert _contract().compute_damage(5, "electric", "normal", matrix=m) == 5, "C1: electric→normal ×1"
    assert _contract().compute_damage(5, "electric", "water", matrix=m) == 10, "electric→water ×2"
    assert _contract().compute_damage(5, "electric", "ground", matrix=m) == 0, "electric→ground inmune"
    assert _contract().compute_damage(10, "bug", "fire", matrix=m) == 5, "bug→fire ×0.5"


CASES = [
    ("dano-neutro", dano_neutro), ("dano-doble", dano_doble), ("dano-mitad", dano_mitad),
    ("dano-inmune", dano_inmune), ("dano-vulnerable", dano_vulnerable),
    ("dano-guardia", dano_guardia), ("dano-vuln-guardia", dano_vuln_guardia),
    ("dano-ultimate", dano_ultimate), ("dano-ult-doble", dano_ult_doble),
    ("dano-perfect", dano_perfect), ("dano-perfect-prio", dano_perfect_prio),
    ("dano-fixedpoint", dano_fixedpoint), ("dano-explora-combos", dano_explora_combinaciones),
    ("dano-determinista", dano_determinista), ("dano-con-canonica", dano_con_canonica),
]
