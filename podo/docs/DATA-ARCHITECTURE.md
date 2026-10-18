# Data Architecture — PODO M0

Owner: a8 (Arquitecto de datos).

## 1. Árbol

```
podo/
├── README.md
├── data/
│   ├── types/type_matrix_v1.json      # MATRIZ CANÓNICA 18x18 (source of truth de tipos)
│   ├── schema/                        # JSON Schema 2020-12
│   │   ├── type_matrix.schema.json
│   │   ├── kit_definition.schema.json
│   │   ├── replay.schema.json
│   │   └── medal_region.schema.json
│   ├── kits/                          # 1 archivo por kit (data-driven)
│   ├── arenas/arena_001.json          # M0: solo arena 1
│   ├── medals/region_01_kanto.json    # estructura 10 regiones (M0 juega 1)
│   └── config/
│       ├── match_rules.json           # reglas globales de serie (switch/dodge/guard/ult/score)
│       └── capture.json               # curva de captura C4 + calibración
├── docs/
│   ├── TYPE-MATRIX.md                 # spec matriz + método de verificación
│   ├── FIXTURES-AND-REPLAYS.md        # spec podo.replay.v1
│   ├── KIT-DEFINITION.md
│   ├── MEDALS-AND-ARENAS.md
│   └── DATA-ARCHITECTURE.md           # este archivo
├── fixtures/sample_smoke.json         # fixture de formato (parsing + switch aceptado/rechazado)
└── tools/
    └── check_data.py                  # validador stdlib (JSON, schemas ligeros, referencias, C4)
```

## 2. Source of truth

| Dato | Archivo canónico |
|---|---|
| Tipos y multiplicadores | `data/types/type_matrix_v1.json` — **interfaz directa del engine** (decisión 2026-10-18): el core la lee y convierte internamente a décimas; `data/types.json` (derivado ×10) y `tools/gen_types_engine.py` quedan DEPRECADOS hasta migrar el loader viejo, luego se eliminan |
| Reglas de serie | `data/config/match_rules.json` (cualquier regla que cambie va acá, nunca en kits) |
| Curva de captura | `data/config/capture.json` |
| Kits | `data/kits/<kit_id>.json` |
| Arenas/medallas | `data/arenas/` + `data/medals/` |

### 2.1 Contrato de unidades (fijado 2026-10-17, acordado con 31/Arq. software)

| Magnitud | Unidad en la capa de DATOS | Ejemplo |
|---|---|---|
| Longitud (range, knockback, dodge, spawn, tamaño de arena) | **metros** (float) | `range: 2.4` = 2.4 m |
| Tiempo (duraciones, cooldowns, tick) | **ms** (int) | `cooldown_ms: 4000` |
| Velocidad base (regla global) | **m/s** | `match_rules.base_speed_m = 3.6` |
| `stats.move_speed` | **multiplicador adimensional** sobre `base_speed_m` | `1.15` → 4.14 m/s |

- Cierre 31/a8 (2026-10-18): `move_speed` **NO es m/s absoluto** — es un multiplicador
  de balance sobre la velocidad base global (regla de serie, tuneable en data).
  Velocidad absoluta de un kit = `move_speed × base_speed_m`. Calibración M0:
  pikachu 4.14 m/s (cruce de arena ~2.4 s), gardevoir 3.6, snorlax 2.88; el dodge
  (1.8 m / 200 ms = 9 m/s de ráfaga) queda ~2× la velocidad de carrera, como corresponde.
- El engine de 29/31 simula en unidades propias (**1u = 1/100 m**, i.e. 100 u/m) y
  convierte **solo en el adapter determinista**; la data nunca lleva escalas de sim.
  Conversión de velocidad (cierre de typo 31/a8, 2026-10-18):
  - `u_por_s = round(move_speed × base_speed_m × 100)` → pikachu `round(1.15×3.6×100) = 414 u/s`.
    (El `/1000` de la versión anterior era un typo: `×100/1000` da 0.414 → round 0.)
  - **Determinismo por tick (fijado)**: avanzar en fixed-point de 1/1000 u,
    `delta_milli_u_por_tick = u_por_s × tick_ms` (= 414×16 = 6624 milli-u/tick = 6.624 u/tick).
    **No redondear a u entero por tick**: truncar a 6 u/tick bajaría pikachu a 3.75 m/s
    (−9%) y rompería la calibración. El engine acumula exacto y proyecta a u entero.
  - **Implementado y verificado (29/31, 2026-10-18)**: toda la geometría de sim
    (clamp de arena, rangos, colisiones, knockback, orbes, spawns) opera en
    **milli-u**; **u entero SOLO para render**. La posición fixed-point entra en el
    `digest()` del estado (flag de determinismo cubierto; smoke: 2 runs = hash
    idéntico; pikachu x = 250_000 + 100×6624 = 912_400 milli-u tras 100 ticks).
  - Cruce de arena (1000 u): 1000/414 ≈ 2.42 s con el avance exacto.
  Arena M0: `size_m: [10, 6]` = 1000×600u, origen en el centro (x ∈ [−5, 5], y ∈ [−3, 3]).
- La conversión debe ser exacta y determinista (aritmética fija/entera en el sim;
  responsabilidad de 31 en el adapter).
- Cambio de este contrato = **major** de data (rompe todos los fixtures).

## 3. Versionado

- Cada archivo con contenido canónico lleva `version` semver (o `arena_id`/`kit_id` como id estable).
- **Regla mayor**: cualquier cambio que altere el resultado de un replay existente
  (multiplicador de matriz, regla de daño, fórmula de captura, duraciones) → bump mayor +
  nuevo archivo de matriz con fecha, sin sobrescribir (ej. `type_matrix_v2.json`).
- **Regla menor**: agregar kits/arenas/medallas nuevos, tuneo de balance dentro de la misma regla.
- Los replays pinan `matrix_version`, `engine.version`, `arena`, `teams` → un replay viejo se
  reproduce con la data de su época si se conserva el snapshot.
- Política de compatibilidad: M0 congela `type_matrix 1.0.0` y `match_rules 1.0.0` al cierre
  del slice; cambios de balance M1 no rompen fixtures M0.

## 4. Determinismo (contrato de data)

- Un run está definido por: `(replay inputs, seed, data snapshot)`.
- El core no lee nada más (sin reloj real, sin red, sin RNG sin sembrar).
- `tail.final_state_hash` = sha256 del estado serializado ordenado al final del match →
  dos runs con los mismos inputs+seed+data deben producir el mismo hash (QA 6.x).
- Ningún dato lleva PII, credenciales ni red de producción (M0 offline).

## 5. Orden de carga (para el core/CLI)

1. `config/match_rules.json` + `config/capture.json`
2. `types/type_matrix_v1.json`
3. `kits/*` → tabla de kits
4. `arenas/<arena>.json` del replay → valida `boss_team`/kits contra la tabla
5. `fixtures/*.json` (inputs) → simula → compara con `tail`/`expected`

## 6. Validación

`python3 podo/tools/check_data.py` (solo stdlib): parseo JSON, matriz 18×18 con dominio
{0, 0.5, 1, 2}, invariantes de kits (wild sin ultimate, ids únicos), referencias cruzadas
(arena→kits, replay→kits/arena), versión de matriz pinada en `match_rules` y fixture, y
recalcula los bounds C4 de la curva de captura. Correr antes de cada cierre de semana.
