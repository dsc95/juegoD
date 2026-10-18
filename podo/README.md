# PODO — Pokémon Odisea · M0

Vertical slice M0: combate 3v3 en tiempo real, determinista (CombatCore,
Python stdlib). Semana 2 entregada: guardia/perfect guard, esquiva con
i-frames, Q/E con effects (enum cerrado), ultimate con carga ×2, switch
3v3 (CD 4 s + ventana vulnerable 1.5 s +50 %), score/orbes, matriz canónica
v1, movimiento fixed-point en milli-u y replays `podo.replay` v1.

| Capa | Dueño | Docs |
|---|---|---|
| Engine `combatcore/` | 29 (Desarrollador) | este README |
| Capa de datos `data/` | a8 (Arquitecto de datos) | [`data/README.md`](data/README.md) |
| Docs compartidos `docs/` | según tema | `docs/DATA-ARCHITECTURE.md` (contrato de unidades, versionado, determinismo) |
| Fixtures / QA | 7f (QA) + a8 | `../podo-qa/` + `docs/FIXTURES-AND-REPLAYS.md` |
| Netcode M2 (diseño) | 31 (Arq. software) | `../DISENO-NETCODE-M2.md` — **ENTREGADO** (diseño; no se implementa en M0) |

## Ejecución

Todas las comandos corren desde la raíz del workspace con el venv compartido
(`.venv/`); nada de dependencias externas (stdlib + pytest).

```bash
# Engine: suite de tests (podo/tests/)
cd podo && ../.venv/bin/python -m pytest tests/ -q

# Demo headless 3v3 (pattern determinista) + replay podo.replay v1
cd podo && ../.venv/bin/python -m combatcore.adapters.headless \
    --demo --ticks 2000 --save-replay /tmp/demo.json

# Verificar un replay (re-run → mismo state_hash + outcome + rejected)
cd podo && ../.venv/bin/python -m combatcore.adapters.headless --replay /tmp/demo.json

# Partido completo 5:00 (18750 ticks, timeout decide por score)
cd podo && ../.venv/bin/python -m combatcore.adapters.headless

# Suite de QA (7f): 57 casos contra el engine
cd podo-qa && ../.venv/bin/python run_all.py

# Validador de data canónica (a8)
python3 podo/tools/check_data.py
```

Replay: partido cortado sin ganador = `outcome.reason: "forfeit"` (lo cierra
el adapter, no la sim); KO/timeout usan el outcome real de la simulación.
Ver spec en `docs/FIXTURES-AND-REPLAYS.md`.

## Datos (a8)

Fuente de verdad: [`data/README.md`](data/README.md). Lo que el engine
consume directamente:

- **Matriz de tipos canónica** `data/types/type_matrix_v1.json` (v1.0.0,
  18×18, fracciones {0, 0.5, 1, 2}; el loader la convierte a décimas
  enteras). `data/types.json` + `tools/gen_types_engine.py` quedan
  **DEPRECATOS** (2026-10-18) hasta que los fixtures de 7f migren; luego se
  eliminan.
- **Reglas globales** `data/config/match_rules.json` (CDs, switch, dodge,
  guard, ultimate, score, `base_speed_m` 3.6).
- **Kits** `data/kits/*.json` (data-driven; un kit nuevo = 1 JSON).
- **Arena** `data/arenas/arena_001.json` (orbes, boss_team, medalla).
- **Unidades** (data en SI): metros / ms / m·s⁻¹; el engine trabaja en
  milli-u (1 u = 1/100 m) y convierte solo en el adapter
  (`docs/DATA-ARCHITECTURE.md` §2.1).

## Uso y propiedad intelectual (LEER)

Este proyecto es un **entregable de curso, 100% no-comercial y educativo**.

- **Pokémon** es propiedad de **Nintendo / Game Freak / The Pokémon Company**.
  Este trabajo es un **proyecto fan/educativo sin ningún vínculo ni aval** de
  esas compañías. **No se distribuye comercialmente y no se monetiza** de
  ninguna forma.
- Si este código/diseño se reutiliza con fines comerciales, el responsable
  debe migrar a **IP original** (nombres, personajes, arte y regiones
  propios) antes de cualquier distribución o venta. Las mecánicas pueden
  conservarse; la expresión (nombres/especies/arte) no.
- Restricciones detalladas: ver `LICENSE` (raíz del repo); la cláusula §3 de
  `seguridad-legal-ip-nocomercial.md` (dictamen 4e) ya vive en el README raíz.

## Contrato entre capas (resumen)

- Todo el daño pasa por `contract.compute_damage` (fórmula única; la sim y
  los oráculos de QA comparten la misma aritmética entera).
- Todo cooldown/duración entra vía `ticks_from_ms` desde los JSON de a8;
  nada de ms ni floats dentro de la sim.
- Determinismo (veto): mismo seed + mismos inputs = logs byte-idénticos;
  el estado de sim (incl. posiciones en milli-u) es serializable entero y
  va en `digest()`; la huella del replay es `sha256(digest)` canónico.
