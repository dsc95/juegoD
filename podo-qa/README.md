# PODO M0 — Suite QA (Bloque 6, 7f)

Puerta formal "listo para pruebas": **0 FAIL y 0 BLOCKED**. Sin falso verde:
lo no verificable es BLOCKED (nunca PASS); un fallo del arnés es FAIL visible.

## Ejecución (stdlib + pytest, sin pygame en el gate)

```
python3 run_all.py                 # toda la suite
python3 run_all.py --family tipos dano
python3 run_all.py --case tb-angulo
python3 run_all.py --json          # + runs/run_result.json
```

Exit: 0 = puerta abierta · 1 = hay FAIL · 2 = solo BLOCKED.

## Semántica

| Estado  | Significado                                                        |
|---------|--------------------------------------------------------------------|
| PASS    | Verificado contra el contrato/canónica.                            |
| FAIL    | Defecto real (evidencia en el motivo) o fallo del arnés (prefijo `ARNES`). |
| BLOCKED | No verificable aún (dependencia no cableada / sem > 1).            |

## Familias (suites/test_*.py)

| Familia             | Cubre (Bloque 6)                                                                  |
|---------------------|-----------------------------------------------------------------------------------|
| `test_dano`         | `compute_damage` (única fuente de verdad): orden tipo→vulnerable→guardia→ult, fixed-point, ×0/0.5/1/2, barrido de combinaciones. |
| `test_tipos`        | Matriz canónica `data/types/type_matrix_v1.json` **v1.0.0 pinneada**: 18×18, conteo 51×2/61×0.5/204×1/8×0, 8 inmunidades exactas, diagonal, C1 corregido (electric→normal ×1), rama Oddish (electric→grass 0.5), dual-type spec, loader engine→décimas, default del engine. |
| `test_cooldowns`    | `can_switch` (4.0 s) y `vulnerable_window` [0, 1.5) del contrato.                |
| `test_direccionado` | Aim lock `_lock_target` (Q1.4): círculo de range, tie-break dist²→ángulo→eid, banco no es objetivo. Blanco (fuerza 2 activos): el modelo 1-activo/team no ejerce el tie-break en partida. |
| `test_kits_data`    | Anti-drift data↔loader: los 5 kits de a8 cargan; `default_teams()` funciona.    |
| `test_determinismo` | VETO: 10 000 frames, 2 runs, state_hash/digest/events byte-iguales; round-trip de replay; capa de contrato `apply_input_frame`/`advance`. |
| `test_performance`  | 5:00 headless < 5 s (3 partidas); tick p99 < 16 ms.                           |
| `test_orbs`         | Pickup de orbs para AMBOS teams (score_orb).                                    |
| `test_captura`      | Modelo de referencia (anclas C4, monotonía HP/ball). `capture` real = sem 3.   |
| `test_antic_rpg`    | VETO: 0 mecánicas RPG en código runtime (escáner de código, no de prosa) + schemas de kit/JSON sin campos de crecimiento. |

## Estado de hallazgos (2026-10-18 ~11:30, árbol estable)

**0 FAIL de engine.** Cerrados y verificados en árbol estable: tie-break de ángulo
invertido en `_lock_target` y `_pending` sin init en la capa de contrato
(fix `core.py:99`). **Corrección de acta**: el FAIL `orb-team-b` anterior era del
ARNES (el test teletransportaba BENCH del team a; el engine solo evalúa al activo
por team — correcto; el `break` de `_collect_orbs` `core.py:545` está dentro del
if = 1 orb 1 pickup, orden tm). Retracción enviada al canal.

Falsos positivos investigados y retractados (con medición): sospecha de velocidad
×1000 tras el rescale del grid (el grid es MILLI-U: 1u=1/100 m con resto sub-u en
la posición; speed 4.14 m/s = doc) — mi ventana de prueba chocababa la pared del
arena (clamp). Guard agregado: `velocidad-doc` (ventana 60 ticks, escala derivada
de `size_m`, ±5 %); el anchor de spawn es en fracciones de arena (invariante a la
escala del grid).

## Pendientes

- **Commit estable de 29** (quedan 2 errores de colección dev: `test_attack.py`,
  `verify` de `replay.py`) → gate final contra el commit (regla de ab: ningún gate
  sobre árbol mid-write) → confirm de 7f a 31/ab.
- `combatcore_capture` — sem 3 (usa `CombatCore.rng` sembrado; `rng.getstate()`
  va en el digest).
- e2e Bloque 2.11 (C1–C8) + hub TTY — sem 2/3.
- Balance ±10 % — sem 2 (partidas completas con kits finales de a8).
- Cuando a8 anuncie la remoción de `data/types.json` → apagar/re-apuntar
  `engine-default-matrix` a la canónica.
