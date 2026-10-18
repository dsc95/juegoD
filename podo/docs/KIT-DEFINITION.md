# KitDefinition — spec v1.0

Owner: a8 (Arquitecto de datos). Schema: `data/schema/kit_definition.schema.json`.
Ejemplos: `data/kits/*.json` (5 kits de M0).

## 1. Principio

Un kit es **puro contenido**: un diseñador agrega un kit escribiendo un JSON en `data/kits/`,
sin tocar código. El core (CombatCore) es un intérprete de KitDefinition: aplica reglas
globales (`data/config/match_rules.json`) y lee el contenido del kit. Nada en el kit puede
alterar reglas de serie; si un campo "nuevo" requiere comportamiento nuevo, es cambio de
engine (mayor), no de data.

## 2. Campos

| Campo | Tipo | Notas |
|---|---|---|
| `kit_id` | string `^[a-z][a-z0-9_]*$` | id canónico; debe coincidir con el nombre del archivo |
| `name` | string | nombre de display |
| `kind` | `fighter` \| `wild` | `fighter`: jugable; `wild`: capturable |
| `type` | 18 tipos | debe existir en `data/types/type_matrix_v1.json` (valida el validador) |
| `role` | `carry` \| `defender` \| `support` \| `flex` | etiqueta de balance, no mecánica |
| `stats` | object | `max_hp` (>0), `move_speed` (>0, multiplicador), `weight` (>0, masa para knockback/empuje) |
| `abilities.basic` | ability | obligatorio para todos los kits (wild incluidos) |
| `abilities.q` / `.e` | ability | opcionales; wild M0 tiene `q` y no `e` |
| `abilities.ultimate` | ability | **solo `fighter`**. El schema rechaza `ultimate` en `kind: wild` |
| `cooldowns.dodge_ms` | int ≥ 0 | override del cooldown global de dodge |
| `wild.base_catch` | 0 < x ≤ 1 | factor de la curva de captura (`data/config/capture.json`) |

### Ability

| Campo | Tipo | Notas |
|---|---|---|
| `id`, `name` | string | id único dentro del kit |
| `kind` | `combo`, `strike`, `dash_strike`, `evade_strike`, `control`, `aoe`, `team_aoe`, `ultimate` | categoría de animación/comportamiento del engine |
| `damage` | number ≥ 0 | daño total (en `combo`: por hit) |
| `hits` | int 1..5 | golpes del combo (default 1) |
| `range` | number ≥ 0 | 0 para efectos sin proyectil (ej. `team_shield`) |
| `windup_ms` | int ≥ 0 | anticipación (ventana a esquivar/guardar) |
| `cooldown_ms` | int ≥ 0 | 0 obligatorio solo en `basic` y `ultimate` (ultimate se dispara a 100% de carga y se vacía) |
| `effects` | list de effect | ver abajo |

### Effect

`type` ∈ {`apply_state`, `knockback`, `pushback`, `heal`, `shield`, `reflect`, `team_shield`, `interrupt`}
+ opcionales `state` (`stagger`/`stun`/`slow`), `ms`, `value`, `radius`.
El enum de `effects.type` es la **lista cerrada de comportamiento** que el engine entiende.
Si un kit necesita un efecto fuera del enum → proponer cambio de engine, no parchear data.

## 3. Invariantes (validadas por `tools/check_data.py`)

1. `kit_id` == nombre de archivo.
2. `type` existe en la matriz.
3. `wild` ⇒ tiene `wild.base_catch`, NO tiene `ultimate` ni `e`/`ultimate` con `cooldown_ms=0` implícito.
4. `fighter` ⇒ NO tiene bloque `wild` (o `wild: null`).
5. `basic` siempre presente; `q`/`e` con `cooldown_ms > 0`; `ultimate` con `cooldown_ms = 0`.
6. `effects.type` dentro del enum.
7. Ids de kit únicos en `data/kits/`.
8. Referencias: `boss_team` de arenas y `teams.kits` de replays deben existir como archivos de kit.

## 4. Cero RPG (veto del formulario)

Ningún campo permite: niveles, XP, crecimiento de stats, drops de equipo, rareza progresiva.
`weight` es masa física (knockback), no estadística crecible. Balance = ajustar números en
data + replays de QA; nunca código.

## 5. Balance inicial M0 (datos, tuneables)

| Kit | Tipo/Rol | HP | Vel (×) | Perfil |
|---|---|---|---|---|
| Pikachu | electric / carry | 95 | 1.15 | combo rápido 3×5, Q dash 18 (7s), E evade+stagger 12 (9s), ult AoE 34 |
| Snorlax | normal / defender | 130 | 0.8 | combo 2×10, Q dash+knockback 20 (9s), E reflect 0.5/2.5s +8 (10s), ult AoE 40 |
| Gardevoir | psychic / support | 90 | 1.0 | combo 3×6, Q interrupt 16 (8s), E team_shield 0.4/3s (12s), ult team_aoe 36 |
| Rattata (wild) | normal / flex | 45 | 1.0 | básico 2×4 + Q 8; `base_catch` 1.0 = **baseline de captura** |
| Oddish (wild, stretch) | grass / flex | 50 | 0.85 | básico 2×4 + Q 10 con `slow`; `base_catch` 1.0 |
| Geodude (trío roca) | rock / flex | 60 | 0.9 | jefe arena_001 (Q3): básico 2×5 + Q 9 (6.5s) |
| Graveler (trío roca) | rock / flex | 80 | 0.8 | jefe arena_001 (Q3): básico 2×6 + Q 12 (7s) |
| Onix (trío roca, ancla) | rock / defender | 110 | 0.7 | jefe arena_001 (Q3): básico 2×8 + Q 16 + knockback (8s) |

Trío roca (Q3, aprobada por el cliente 2026-10-18): kits simplificados tipo wild
(básica + 1 habilidad, **sin ultimate**), mismo loader, data only; en M0 no
spawnean como capturables. Regla de corte del cliente: si el checkpoint sem. 2
va en riesgo, jefe = trío neutro (mirror) — flip de un campo en
`data/arenas/arena_001.json` (`boss_team_fallback_neutral`), no re-trabajo.

`stats.move_speed` es **multiplicador** sobre `match_rules.base_speed_m` (3.6 m/s):
velocidad absoluta = `move_speed × base_speed_m` (contrato DATA-ARCHITECTURE §2.1;
pikachu 4.14 m/s, snorlax 2.88 m/s).

Nota de matchup (matriz v1 canónica): los 3 fighters son **mutuamente neutros** (x1 entre sí).
Las ramas de tipo en M0 se ejercitan con los wilds: `electric → grass = 0.5` (Pikachu vs Oddish)
y la inmunidad/neutralidad de `normal`. Ver `TYPE-MATRIX.md` §5.
