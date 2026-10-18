"""Config central de la suite QA PODO (Bloque 6). stdlib-only. Sola fuente de constantes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent      # podo-qa/
REPO = ROOT.parent                          # raíz del repo
PODO_DIR = REPO / "podo"                    # paquete combatcore (31/29)
DATA_DIR = PODO_DIR / "data"                # kits + canónica + reglas (a8)
FIX = ROOT / "fixtures"
RUNS = ROOT / "runs"

# ── Matriz canónica (a8, dueño) ──
CANONICAL_MATRIX = DATA_DIR / "types" / "type_matrix_v1.json"
CANONICAL_VERSION = "1.0.0"
# Cuentas de sanity de a8 (TYPE-MATRIX.md): 51 celdas ×2 · 61 ×0.5 · 204 ×1 · 8 ×0
CANON_COUNTS = {2.0: 51, 0.5: 61, 1.0: 204, 0.0: 8}
# Las 8 inmunidades exactas de la canónica v1.0.0
IMMUNITIES = [
    ("normal", "ghost"), ("ghost", "normal"), ("fighting", "ghost"),
    ("electric", "ground"), ("ground", "flying"), ("poison", "steel"),
    ("psychic", "dark"), ("dragon", "fairy"),
]

# ── Constantes de combate (deben casar con combatcore/constants.py + contract.py) ──
SWITCH_COOLDOWN_S = 4.0
VULNERABLE_S = 1.5
VULN_MULT = 15   # ×1.5 (décimas)
GUARD_MULT = 4   # ×0.4 (décimas)
ULT_MULT = 20    # ×2 (décimas)
MULT_TENTHS = (0, 5, 10, 20)
TYPE_COUNT = 18

# ── Captura (curva por HP + ball; baseline Rattata neutro) ──
BALL_STRENGTH = {"Poké Ball": 1.0, "Great Ball": 1.5, "Ultra Ball": 2.0, "Master Ball": 999.0}

# ── Determinismo / performance / balance ──
TICK_MS = 16
TICK_P99_MAX_MS = 16.0
MATCH_TICKS = 18750               # 5:00
MATCH_HEADLESS_MAX_S = 5.0        # <5 s reales
DETERMINISM_FRAMES = 10000
BALANCE_BAND = 0.10
# Anti-RPG: con word-boundary para no falsos-positivos en "expected"/"express"/"exponent".
ANTI_RPG_PATTERNS = [r"\blevel\b", r"\bxp\b", r"\bexp\b", r"\bstat_growth\b", r"\btree_of_moves\b"]
