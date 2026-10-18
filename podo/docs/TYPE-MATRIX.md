# Matriz canónica de tipos 18×18 — PODO

**Archivo canónico (fuente única de verdad):** `podo/data/types/type_matrix_v1.json`
**Versión:** 1.0.0 · **Generada/verificada:** 2026-10-17 · **Dueño:** a8 (Arquitecto de datos)

> El caso C1 del formulario (`FORMULARIO-PROYECTO.md`) es **ilustrativo** y puede chocar con
> la matriz (así lo advirtió el cliente). La suite de QA (7f) valida a CombatCore **contra
> este archivo**, no contra el formulario. Ejemplo real de choque: C1 dice "Pikachu (Eléctrico)
> a Snorlax (Normal) → ×2"; la canónica dice **×1** (eléctrico no es súper efectivo contra
> normal; lo es contra agua y volador).

## 1. Formato

```json
{
  "version": "1.0.0",
  "types": ["normal", "fighting", ..., "fairy"],   // 18 ids, orden canónico
  "matrix": { "<atacante>": { "<defensor>": 0|0.5|1|2 } }   // 18 × 18 = 324 celdas
}
```

- Multiplicadores permitidos por par: **0, 0.5, 1, 2** (dominio cerrado).
- Cuentas de v1: **51 celdas 2× · 61 celdas 0.5× · 204 celdas 1× · 8 celdas 0×** (las 8
  inmunidades: normal→ghost, ghost→normal, fighting→ghost, electric→ground, ground→flying,
  poison→steel, psychic→dark, dragon→fairy).
- Consumidores: `matrix[atacante][defensor]`. La clave `version` va en el top-level (QA la
  pinnea en sus fixtures).
- **Interfaz engine (decisión 2026-10-18, acordado con 31)**: el engine lee
  **`type_matrix_v1.json` DIRECTO** (fracciones {0, 0.5, 1, 2} + `version` top-level) y
  convierte internamente a décimas (`round(v*10)`): **fuente única, sin archivos derivados**.
  El derivado `data/types.json` (encoding ×10), `tools/gen_types_engine.py` y el
  placeholder `data/gen_types_placeholder.py` quedaron **APROBADOS PARA BORRAR en el
  commit 1** (decisión del Jefe, 2026-10-18; 29 ejecuta el borrado): el trigger se
  cumplió — el engine y la suite de 7f ya validan contra la canónica directo y
  `contract.default_matrix()` apunta a la matriz v1.0.0.

## 2. Regla de tipo doble (defensor con 2 tipos)

Producto de los dos pares, con clamp al dominio:

| producto | resultado |
|---|---|
| 0 × cualquiera | **0** |
| 0.5 × 0.5 = 0.25 | **0.5** |
| 2 × 2 = 4 | **2** |
| resto | producto directo |

Decisión de diseño M0 (el juego real de Pokémon conserva 4×/0.25×; acá el dominio está
cerrado a {0, 0.5, 1, 2} por decisión del cliente). Documentar en GDD cuando se agreguen
especies de 2 tipos.

## 3. Verificación contra fuente oficial (obligación del kickoff)

**Fuentes usadas (2026-10-17):**
1. `https://bulbapedia.bulbagarden.net/wiki/Type` — tabla "Type chart (Generation VI onward)",
   HTML renderizado vía API de MediaWiki.
2. Las **18 páginas de tipo** (`<Type> (type)`) — templates `{{TypeProperties prop=Off/Def}}`.

**Cheques (todos pasaron):**
- 324/324 celdas idénticas entre la extracción de la tabla y la de las 18 páginas.
- **Simetría transpuesta**: para toda pareja (X→Y), `Off(X)` contiene Y en {se, nve, immune}
  ⇔ `Def(Y)` contiene X en la misma categoría. **0 inconsistencias en las 324 parejas × 3
  categorías**. Esto descarta errores de un solo lado de una celda.

**Fuentes descartadas (documentado por trazabilidad):**
- Serebii: 404 en todas las rutas probadas desde la red del equipo.
- PokeAPI (`api.pokeapi.co`): DNS no resuelve (red restringida).
- Wikipedia EN: el artículo `Pokémon type` no existe (404 en la API).
- **Pokémon Showdown** (`data/typechart.ts` en master): **no confiable** — varios bloques son
  incoherentes con el chart oficial y con Bulbapedia (p. ej. su fila de acero omite 6
  resistencias). No se usó para nada. Si se reintenten fuentes, repetir el doble cheque
  (extracción doble + transpuesta) antes de firmar.

## 4. Resumen (v1)

| ataca → | 2× (súper efectivo) | 0.5× (poco efectivo) | 0× (inmune) |
|---|---|---|---|
| normal | — | rock, steel | ghost |
| fighting | normal, rock, steel, ice, dark | flying, poison, bug, psychic, fairy | ghost |
| flying | fighting, bug, grass | rock, steel, electric | — |
| poison | grass, fairy | poison, ground, rock, ghost | steel |
| ground | poison, rock, steel, fire, electric | bug, grass | flying |
| rock | flying, bug, fire, ice | fighting, ground, steel | — |
| bug | grass, psychic, dark | fighting, flying, poison, ghost, steel, fire, fairy | — |
| ghost | ghost, psychic | dark | normal |
| steel | rock, ice, fairy | steel, fire, water, electric | — |
| fire | bug, steel, grass, ice | rock, fire, water, dragon | — |
| water | ground, rock, fire | water, grass, dragon | — |
| grass | ground, rock, water | flying, poison, bug, steel, fire, grass, dragon | — |
| electric | flying, water | grass, electric, dragon | ground |
| psychic | fighting, poison | steel, psychic | dark |
| ice | flying, ground, grass, dragon | steel, fire, water, ice | — |
| dragon | dragon | steel | fairy |
| dark | ghost, psychic | fighting, dark, fairy | — |
| fairy | fighting, dragon, dark | poison, steel, fire | — |

## 5. Notas de contenido para M0

- Los 3 kits (pikachu=electric, snorlax=normal, gardevoir=psychic) son **neutros entre sí**
  (ningún matchup 2×/0.5× dentro del trío). La matriz se ejerce en M0 contra: salvajes
  (oddish=grass: **electric→grass = 0.5×**) y contra kits nuevos en semanas 3-4.
  → El "matchup 18 tipos" se valida por las 324 unitarias de QA, no por el contenido de M0.
- **Oddish (stretch)**: la premisa del kickoff decía "valida la rama de resistencia Psíquico
  ×0,5". **Corrección canónica:** planta **no** resiste psíquico (psychic→grass = **1×**).
  La rama 0.5× que sí valida Oddish es **electric→grass = 0.5×** (básica/Q de Pikachu vs.
  Oddish). La rama psychic 0.5× se valida contra steel y psychic (sin esos kits en M0, queda
  cubierta por las 324 unitarias).
- **Trío roca (Q3, 2026-10-18) — el jefe de arena_001 es Geodude/Graveler/Onix (roca).**
  Matchup REAL contra los 3 kits (verificado en la canónica):
  - normal→rock = **0.5×** ✓ (Snorlax hace medio daño: el "switch forzado" del brief SÍ se ejerce).
  - electric→rock = **1×** y rock→electric = **1×** (NEUTRO en ambos sentidos).
  - psychic→rock = **1×** y rock→psychic = **1×** (NEUTRO).
  - El brief del cliente decía "2× Pikachu→Roca" y "Roca→Pikachu 0,5×": **ambos chocan con el
    chart oficial** (mismo tipo de caso que C1). eléctrico solo hace 2× a flying/water, y roca
    solo hace 0,5× a fighting/ground/steel. Ningún 2× se ejerce dentro de arena M0 contra el
    trío (un 2× contra roca exigiría atacante grass/fighting/ground/water/steel — no hay en el
    trío M0; el único grass disponible es el wild stretch Oddish: grass→rock = 2×).
  - Consecuencia para el diseño: el trío roca funciona como **muro** (castiguea a Snorlax con
    el 0.5× + 130-110 de HP), no como matchup ventajoso/contraventajoso completo. Presentado
    al cliente con la canónica de evidencia.
  - **Decisión final (Jefe, 2026-10-18): opción (c) — trío intacto, documentado como «muro».**
    El 2× era errata del brief (mismo patrón que C1); corregido en plan v1.2 (§2 y §10).
    La canónica mandó: no se altera la matriz ni el trío por un error del brief.
  - **Decisión (Jefe, 2026-10-18): opción (c) — trío intacto, documentado como «muro».** El 2×
    era errata del brief (misma clase que C1); el plan quedó corregido en v1.2 (§2/§10).
    Este registro es la trazabilidad canónica del caso.

## 6. Versionado

- Cambio de un multiplicador = **major** (rompe el balance y las 324 unitarias).
- Cambio de formato/schema = **major**.
- Cada versión queda como archivo (`type_matrix_v1.json`, `v2`, …); la vigente se referencia
  por `version` en fixtures y en `config/match_rules.json`.
