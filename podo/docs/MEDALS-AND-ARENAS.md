# Medallas y Arenas — PODO

Owner: a8. Schema: `data/schema/medal_region.schema.json`.

## 1. Estructura canónica

- **10 regiones × 8 arenas + 1 campeonato regional** = 90 nodos de progreso.
- 80 medallas = 8 por región (una por arena); el campeonato da un **título** (no medalla) y
  desbloquea la siguiente región.
- Cada medalla tiene UN desbloqueo: `unlock.kind` ∈ {`kit`, `arena`, `region`, `mode`, `cosmetic`}.

## 2. Progresión (flujo)

```
arena N ──gana──> kanto_medal_N ──desbloquea──> unlock (arena N+1 / kit / ...)
arena 8 ──gana──> kanto_medal_08 ──> campeonato kanto
campeonato kanto ──gana──> título kanto_champion ──> región johto (order 2)
```

## 3. Scope M0

- M0 juega **solo `arena_001`** (`m0: true` en `region_01_kanto.json`).
- Las otras 7 arenas de Kanto + 9 regiones completas = **estructura ya versionada, contenido
  M1+**. Los kits de recompensa aún no existen: se marcan `ref: tbd_m1_*` y `m0: false`
  (el validador NO exige que `tbd_m1_*` apunte a un kit real; solo exige que `m0: true`
  apunte a datos existentes).
- La medalla de M0 (`kanto_medal_01`) desbloquea `arena_002` (kind `arena`): la UI puede
  mostrar el siguiente paso sin que M1 exista todavía.

## 4. Arenas

- `data/arenas/<arena_id>.json`: `region_id`, `gym_type` (flavor + criterio de matchup futuro),
  `duration_ms`, `orbs` (cantidad, respawn, spawn points), `boss_team` (3 `kit_id` existentes),
  `medal_on_win`.
- El **boss_team** es data: cambiar el equipo del jefe = editar el JSON, no código.
- En M0 el pool de kits es el mirror de los 3 fighters definidos, por lo que `boss_team`
  siempre es válido contra la tabla de kits.

## 5. Reglas de contenido

1. Una región tiene exactamente 8 arenas + 1 campeonato (validado).
2. `gym_type` debe ser un tipo de la matriz (flavor, pero consistente).
3. `medal_id` único por región; patrón `<region>_medal_NN`.
4. El `unlock.kind: region` solo aparece en el campeonato.
5. No hay pay-to-win: todos los unlocks se ganan jugando (GDD).
6. Placeholder M1: `ref` con prefijo `tbd_m1_` + `m0: false`; al definir el contenido real se
   reemplaza el `ref` y se pone `m0` según el milestone.
