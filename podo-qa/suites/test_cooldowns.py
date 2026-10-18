"""Cooldowns exactos — valida combatcore.contract (can_switch, vulnerable_window, constantes).
   switch: can_switch(e) = e >= 4.0.  ventana vulnerable: vulnerable_window(t) = [0.0, 1.5)."""
import config as cfg
from harness import Blocked, cc

_C = None
def _contract():
    global _C
    if _C is None:
        _C = cc("combatcore.contract")
    return _C

def _cs(): return _contract().can_switch
def _vw(): return _contract().vulnerable_window

def constantes():
    assert _contract().SWITCH_COOLDOWN_S == cfg.SWITCH_COOLDOWN_S
    assert _contract().VULNERABLE_S == cfg.VULNERABLE_S

def switch_3_9():    assert _cs()(3.9) is False
def switch_4_0():    assert _cs()(4.0) is True
def switch_4_1():    assert _cs()(4.1) is True
def switch_10():     assert _cs()(10.0) is True
def vuln_0():        assert _vw()(0.0) is True
def vuln_0_75():     assert _vw()(0.75) is True
def vuln_1_49():     assert _vw()(1.49) is True
def vuln_1_5():      assert _vw()(1.5) is False
def vuln_1_51():     assert _vw()(1.51) is False
def vuln_negativo(): assert _vw()(-0.1) is False

CASES = [
    ("constantes", constantes),
    ("switch-3.9", switch_3_9), ("switch-4.0", switch_4_0),
    ("switch-4.1", switch_4_1), ("switch-10", switch_10),
    ("vuln-0.0", vuln_0), ("vuln-0.75", vuln_0_75), ("vuln-1.49", vuln_1_49),
    ("vuln-1.5", vuln_1_5), ("vuln-1.51", vuln_1_51), ("vuln-negativo", vuln_negativo),
]
