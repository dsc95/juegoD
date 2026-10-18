# PODO — capa de datos (M0)

Dueño: **a8 — Arquitecto de datos**. El engine (CombatCore) vive en `../combatcore/`
(29); este árbol es su contrato de datos.

## Contenido

| Pieza | Dónde (desde `data/`) | Estado |
|---|---|---|
| Matriz de tipos 18×18 (source of truth, interfaz DIRECTA del engine) | `types/type_matrix_v1.json` | ✅ v1.0.0 verificada (2 extracciones Bulbapedia + simetría transpuesta); el engine la lee y convierte a décimas internamente |
| ~~Matriz derivada ×10~~ | `types.json`, `../tools/gen_types_engine.py`, `gen_types_placeholder.py` | 🗑️ **APROBADO PARA BORRAR en el commit 1** (Jefe, 2026-10-18; 29 ejecuta) — el engine y QA ya validan contra la canónica directo |
| Spec matriz + verificación | `../docs/TYPE-MATRIX.md` | ✅ |
| Formato de replay/fixture `podo.replay.v1` | `../docs/FIXTURES-AND-REPLAYS.md` + `schema/replay.schema.json` | ✅ |
| KitDefinition (8 kits M0: 3 fighters + 2 wilds + trío roca del jefe) | `kits/` + `schema/kit_definition.schema.json` + `../docs/KIT-DEFINITION.md` | ✅ |
| Reglas globales + captura C4 | `config/{match_rules,capture}.json` | ✅ |
| Arena M0 + medallas (estructura 10 regiones) | `arenas/` + `medals/` + `../docs/MEDALS-AND-ARENAS.md` | ✅ |
| Validador (stdlib) | `../tools/check_data.py` | ✅ `python3 podo/tools/check_data.py` |

## Contratos clave

- **Unidades**: longitud = metros, tiempo = ms, velocidad = m/s (spec: `../docs/DATA-ARCHITECTURE.md` §2.1). El engine convierte 1u = 1/100 m solo en su adapter.
- **Matriz**: multiplicadores ∈ {0, 0.5, 1, 2}; dual-type = producto con clamp (4→2, 0.25→0.5).
- **Data-driven**: kit nuevo = 1 JSON en `kits/`; reglas solo en `config/match_rules.json`.
- **Cero RPG**: nada de niveles/XP/crecimiento (veto). Balance = data + fixtures.
- **Sin PII/credenciales** en data, fixtures ni logs (M0 offline).
