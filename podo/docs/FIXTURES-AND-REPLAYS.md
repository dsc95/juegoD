# Formato de input frames / replays / fixtures — PODO

**Esquema:** `podo/data/schema/replay.schema.json` · **Ejemplo:** `podo/fixtures/sample_smoke.json`
**Versión de formato:** `podo.replay.v1` (`format_version: 1`)

> Un **replay** de un partido **ES** la secuencia de input frames (doble uso: feature +
> debugging + fixture de QA, por diseño del cliente — Bloque 2.10 y 6.21).

## 1. Modelo de determinismo

- La simulación corre en **ticks lógicos de `tick_ms`** (16 ms → 62.5 ticks/s). Un "frame"
  es un índice de tick entero, 0-based.
- **Un frame de input** = el estado de control de UNO asiento `(side, seat)` EN UN tick.
- Contrato de determinismo: mismo archivo (o misma secuencia) + mismo `seed` + misma
  versión de engine/matriz/config ⇒ logs byte-iguales. La verificación es el
  `final_state_hash` (sha256 del estado final canónico) + diff de logs.

## 2. Semántica de la secuencia (CRÍTICO para el harness de QA)

- **Event-sparse con hold:** cada registro `inputs[i]` es el **estado completo** de input
  para su `(side, seat)` **a partir de su tick `t`**, vigente hasta el próximo registro del
  mismo `(side, seat)`. Antes del primer registro de un asiento, el estado es **neutro**
  (sin movimiento, sin acciones).
- `move`: vector 2D con componentes enteros `x, y ∈ {-1, 0, 1}` (8 direcciones + idle;
  normalización la hace CombatCore). `{"x":0,"y":0}` o ausente = quieto.
- `aim`: opcional, `{x, y}` unitario (mouse/aimada; Q1b stretch). En TTY-puro (Q1a) se
  omite: la básica apunta al objetivo más cercano según facing.
- `actions`: lista de **edges** (presiones) en ese tick, del conjunto:
  `basic · q · e · dodge · guard_on · guard_off · ultimate · switch · ball`
  - `guard_on`/`guard_off` modelan el guardado como estado (clic derecho mantener).
  - `switch`: cambiar al siguiente Pokémon de la party (Tab) — sujeto a cooldown global
    (`match_rules.switch.cooldown_ms` = 4000 ms).
  - **Input inválido** (p. ej. switch dentro del cooldown): CombatCore lo **descarta y lo
    loguea** (`rejected_inputs[]` en el tail), nunca rompe la partida (Bloque 5.25).
- Orden de los registros: no importa para la semántica (se resuelve por `t`), pero el
  runner debe **serializar ordenado por (t, side, seat)** para diff byte-a-byte.

## 3. Anclaje de versiones (self-contained)

El fixture/replay pinnea todo lo que toca la simulación:

| campo | qué ancla |
|---|---|
| `engine.version` | versión de CombatCore que lo generó/valida |
| `matrix_version` | versión de `data/types/type_matrix_vX.json` usada |
| `config.arena` | id de arena → kits del jefe, orbes, duración |
| `config.teams.a.kits` / `.b.kits` | ids de kit (3 por lado, orden de party) |
| `seed` | PRNG de captura y cualquier aleatoriedad del core |

El runner **debe** verificar existencia de todos los referenciados antes de correr.

## 4. Fixture vs. replay

- **Replay**: `{format, engine, matrix_version, seed, config, inputs, tail}`.
- **Fixture**: replay **+ bloque `expected`** con las aserciones de QA (outcome, winner,
  reason, scores, hp final, medallas, `rejected_inputs`). La fixture de determinismo de
  10.000 frames (Bloque 6.27c) no necesita `expected` más allá de
  `final_state_hash` estable entre runs.

## 5. Tail y outcome

```json
"tail": {
  "frames_total": 18750,            // = match_duration_ms / tick_ms
  "final_state_hash": "sha256:...", // hash del estado final canónico
  "rejected_inputs": [ {"t": 50, "side": "a", "seat": 0, "action": "switch", "reason": "cooldown"} ],
  "outcome": { "winner": "a", "reason": "ko|timeout_score|forfeit", "score": [32, 21] }
}
```

- `outcome.reason`: `"ko"` (equipo rival fuera), `"timeout_score"` (se agotaron los 5:00 y
  decide el score: golpes + KOs + orbes).
- `score` = `[score_a, score_b]` según pesos de `match_rules.score`.

## 6. Reglas de extensión del formato

- Cambio de campos/semántica ⇒ bump de `format_version` + nota acá.
- Los fixtures viven en `podo/fixtures/` (los de QA los genera su harness; este repo solo
  fija el formato y el ejemplo).
- **Nada de PII/credenciales** en fixtures ni logs (Bloque 7) — datos de juego únicamente.
