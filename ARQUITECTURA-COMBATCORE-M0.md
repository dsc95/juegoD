# ARQUITECTURA — CombatCore · M0 · Pokémon Odisea (PODO)

**Rol:** Arquitecto de software (`reflexion-agente-31`) · **Estado:** esqueleto validado (34/34 tests, 2 vetos OK) + **contrato con QA (7f) FIRMADO** · doc reconciliado con la implementación de 29 · pendiente: aprobación final del Jefe
**Fecha:** 2026-10-17 · **Fuente de verdad:** `FORMULARIO-PROYECTO.md` (Bloques 4 y 6) + GDD v2 + `plataforma-juego-pc.md` §2
**Stack M0:** Python 3.12, **stdlib + pytest como máximo**, headless + TTY. Sin LLM, sin red, sin RNG sin semilla.

> **Dos vetos absolutos (Bloque 6) que gobiernan toda la decisión de diseño:**
> 1. **Determinismo** — mismos inputs → mismo resultado, verificable.
> 2. **Anti-RPG** — imposible por *diseño*, no solo no implementado.

---

## 1. Objetivo del M0 y no-objetivos

**Meta:** vertical slice del combate 3v3 en tiempo real (1 arena, 5:00, KO o score) sobre una **simulación determinista** en Python, **jugable en TTY** y **verificable por QA**. Valida el *feel* del control directo y todos los controles.

**No-objetivos M0 (se diseñan, no se construyen):** online/netcode (M2), 5v5, roster completo, 10 regiones, monetización. **Vetos:** cualquier nivel/XP/crecimiento de stats.

**Decisión clave de stack (Bloque 4.18):** el cliente acepta y solicita Python 3 + `.venv` para M0 (CombatCore puro, headless + consola), NO prototipo HTML/mockup (rechazado). La producción meta sigue siendo UE5/C++ (plataforma §1); esta arquitectura de **capas + núcleo determinista** es directamente mapeable a ese stack (el `CombatCore` es el mismo módulo, en C++).

---

## 2. Principio rector: el contrato de determinismo

Toda la arquitectura existe para que esto sea **una función pura**:

```
state_{n+1} = Step( state_n , input_frame_n )
final_state = Fold( Step , input_frames[0..N] , state_0 )
state_0     = Init( config , seed )
```

**Mismo `(config, seed, secuencia de input frames)` → misma secuencia de estados → mismo resultado.** El **replay** de una partida = `config + seed + secuencia de input frames`, y **es la fixture de QA** (Bloque 6.21, caso C7).

### Reglas duras del core (lo que NUNCA entra en la simulación)
| # | Prohibición | Motivo |
|---|-------------|--------|
| 1 | Reloj de pared (`time.time()`, `datetime.now()`) | El core cuenta en **ticks lógicos**; el reloj real solo decide *cuántos* ticks corren |
| 2 | RNG sin semilla / `random` global | Solo un **PRNG sembrado** cuyo estado vive en `MatchState` |
| 3 | `hash()` / `id()` de Python | `hash()` de str está **salado por proceso** (`PYTHONHASHSEED`) → no determinista entre runs. IDs de entidad son **enteros explícitos** |
| 4 | Orden de iteración de `set` no controlado | Se **ordena** explícitamente (`sorted(...)`) donde importa |
| 5 | Floats sin cuantizar en el core | Matriz y modificadores en **entero (porcentaje)**; movimiento en tiles enteros (esqueleto) / fixed-point (M0 full) |
| 6 | I/O, hilos, excepciones dependientes del entorno | El core es puro; el I/O vive en el adapter/runner |

### Cuantización de entradas en el BORDE
Las entradas continuas (mouse, sticks) se **cuantizan en el adapter** a señales discretas (una de 8 direcciones + flags). **El core nunca ve un float crudo** — solo un `InputFrame` discreto. Esto es lo que hace posible el lockstep/rollback en M2.

---

## 3. Capas y módulos (Python, stdlib-only)

```
        ┌─────────────────────────────────────────────┐
        │  PRESENTACIÓN (pluggable)                    │  ← I/O, render, captura de input
        │  TTYAdapter (default) · [PygameAdapter (Q1)] │
        └───────────────┬─────────────────────────────┘
                        │ InputFrame ↓  ·  MatchState render ↑
        ┌───────────────┴─────────────────────────────┐
        │  RUNNER (headless)  ── QA / replays / demo    │  ← run(config, seed, frames) → state
        └───────────────┬─────────────────────────────┘
                        │
        ┌───────────────┴─────────────────────────────┐
        │  COMBATCORE  (puro, determinista, sin I/O)   │  ← Step, damage, cooldowns, i-frames
        │  tick loop · input frames · state machines   │
        └───────────────┬─────────────────────────────┘
                        │ carga (read-only)
        ┌───────────────┴─────────────────────────────┐
        │  DATOS (data-driven, dueño: a8)              │  ← KitDefinition · matriz 18×18 · arena
        └─────────────────────────────────────────────┘
```

**Regla de dependencias:** `core` no depende de nada (ni de `present`, ni de `data` en runtime — los datos se le *inyectan*). `present` y `runner` dependen de `core`. `core` es portable a C++/UE5 1:1.

### Estructura de directorios
```
podo/
  combatcore/     # CombatCore puro (lo que se mapea a C++)
    constants.py  # tick 16 ms, arena, 5:00, fixed-point
    frames.py     # InputFrame + serialización canónica + InputStream
    kits.py       # KitDefinition (frozen, data-driven — anti-RPG)
    types.py      # TypeMatrix 18×18 (décimas: 0/5/10/20)
    entities.py   # máquina de estados, movimiento int, arc/alcance
    contract.py   # CAPA DE CONTRATO (QA 7f): compute_damage,
                  #   type_effectiveness, can_switch, vulnerable_window, defaults
    core.py       # CombatCore: step/run, aim, daño, KO, fin, digest
    replay.py     # save/load/verify (podo-replay/1)
    adapters/
      headless.py # runner sin UI (QA, replays, benchmarks)
      tty.py      # adapter TTY (teclado) — puerta M0 (Q1)
  data/           # data-driven (dueño: a8)
    types.json    # matriz 18×18 (PLACEHOLDER ×1; a8 publica la canónica)
    kits/*.json   # 5 kits provisionales (3 jugadores + 2 salvajes)
  tests/          # pytest
    test_frames.py  test_movement.py  test_attack.py
    test_determinism.py  test_replay.py  test_contract.py
```

---

## 4. CombatCore (diseño detallado)

### 4.1 Tick loop fijo (16 ms lógicos)
- `TICK_MS = 16` → ~62.5 tick/s lógicos. El **runner** avanza ticks lógicos en un bucle; el reloj real solo limita la tasa (never enters state). 
- Una partida de 5:00 = `MATCH_TICKS = 300000 // 16 = 18750` ticks.
- **Performance (Bloque 6.22/29):** 18.750 ticks headless < 5 s reales; tick p99 < 16 ms. Con sim simple esto sobra con mucho margen (ver `test_determinism` incluye un check de perf).

### 4.2 InputFrame (serializable)
- `PlayerInput`: `move` (8-dir cuantizado), `aim` (dirección), y flags `basic, q, e, guard, dodge, ultimate, switch_to, ball`. Todo **discreto**.
- `InputFrame(tick, players[])`: una por tick, una entrada por jugador local.
- Serialización **canónica** (`json`, `sort_keys=True`) → byte-estable → el replay.

### 4.3 Máquinas de estados
- **MatchState** (partida): `running → victory | defeat | timeout`.
- **EntityState** (entidad): `idle → moving | attacking | dodging | guarding | stun → ko`. Transiciones discretas, serializables.

### 4.4 Modelo de entidad + stats inmutables (ver §6 anti-RPG)
`Entity` = estado **mutable de combate** (pos, hp, cooldowns, estado) + `FrozenStats` (poder, **inmutable**, fijado al inicio desde el `KitDefinition`).

### 4.5 Daño (entero, determinista — fórmula única en `contract.py`)
```
dmg = compute_damage(base, tipo_src, tipo_dst, matrix,
                     guarding, perfect_guard, vulnerable, is_ultimate)
      = base × matriz[tipo] (décimas: 0/5/10/20)
      → ×1.5 si vulnerable (recién entrado, post-switch)
      → ×0.4 si guardando   |   → 0 si perfect_guard
      → ×ULT_MULT (×2) si ultimate
      // 10        (todo entero, fixed-point)
```
- **Multiplicativo puro**: sin resta de `defense` (el set cerrado anti-RPG no trae ese stat) y sin piso `max(1,…)` — la inmunidad ×0 **debe** dar 0. (Corrección de este doc: el esbozo anterior traía `max(1, base - defense)`, que inventaba un stat inexistente y rompía el ×0.)
- **Fuente de verdad única:** `core._resolve_attacks` llama a `contract.compute_damage`; la sim y las fixtures de QA comparten la fórmula.
- **La matriz se carga de `data/types.json` (a8), nunca hardcodeada** (regla del caso C1: las pruebas validan el archivo, no la memoria).

### 4.6 Sistemas de combate (semanas 2-4, ya arquitectados)
- **Cooldowns** en ticks lógicos (`*_cd_until`), **i-frames** de esquiva, **guardia/perfect guard** (ventana de timing), **switch** (cooldown 4 s + ventana vulnerable 1.5 s), **KO** → siguiente del equipo, **score** (golpes/KOs/orbes), **captura** (usa el PRNG sembrado → misma seed, mismo resultado), **medallas/desbloqueos** (ver §6).

### 4.7 PRNG determinista
El único PRNG vive en `CombatCore.rng = random.Random(seed)` (Mersenne Twister de CPython — determinista: misma seed → misma secuencia; **serializable** vía `rng.getstate()`/`setstate()`). Aceptado como desvío del esbozo original (xorshift64) porque cumple el contrato y es más simple. **Nota dura para sem 3:** cuando la captura lo use, el digest/snapshot **DEBE incluir `rng.getstate()`** para que el replay y el rollback de M2 sigan siendo reproducibles.

### 4.8 Serialización de estado
- `CombatCore.digest()` → estado serializable (enteros: tick, seed, entidades, winner); `digest_json()` → JSON canónico. **Esta es la huella de determinismo** (2 runs → byte-igual).
- `replay.py` (formato `podo-replay/1`): `{seed, ticks, teams, frames por equipo, events, digest}`; `verify()` re-corre exactamente `ticks` steps y exige eventos+digest byte-iguales. **El replay ES la fixture de QA.**
- **Sem 3:** el snapshot de rollback DEBE incluir `rng.getstate()` (ver §4.7).

### 4.9 Capa de contrato (QA 7f) — `contract.py`
Superficie de **firmas estables** para que QA escriba fixtures sin tocar la sim:
- `compute_damage(base, atk, def, *, matrix, guarding, perfect_guard, vulnerable, is_ultimate) -> int` — fórmula única de daño (la usa el core).
- `type_effectiveness(atk, def, matrix=None) -> float` — oráculo de la matriz (324 combos).
- `can_switch(elapsed_s) -> bool` (≥4 s) · `vulnerable_window(t_s) -> bool` ([0, 1.5) s).
- `CombatCore(seed, teams=None, matrix=None, max_ticks=18750)` + `apply_input_frame(frame, team)`, `advance(n)`, `state_hash()`, `is_over()`, `final_score(team)`; `winner` = atributo.
- **FIRMADO con QA (7f)** el 2026-10-17 — desbloquea fixtures de daño/tipos/cooldowns/dirección. Captura (sem 3) vía `CombatCore.rng` sembrado.

---

## 5. Presentación fina + decisión Q1

**Adaptador pluggable** (`present/adapter.py`): una interfaz `render(state) → str` + `next_input() → InputFrame`. Dos `InputSource`:
- **ScriptedInputSource** — lee una secuencia de `InputFrame` (list/file). Es el camino **headless/QA/replay** (determinista, testeable).
- **InteractiveInputSource** — captura tecla (local, `termios`).

**Q1 (TTY vs pygame) — el cliente decide, NO bloquea:**
- **Por defecto: `TTYAdapter`** (stdlib, respeta "stdlib + pytest"). Ya es jugable en semana 2.
- **Opcional (stretch): `PygameAdapter`** si Q1 = (b) — **1 dependencia chica**, implementa la MISMA interfaz; no toca el core.
- **Recomendación (alineada con el Jefe):** puerta con **(a) TTY**; pygame como stretch. La arquitectura lo permite sin coste: cambiar de superficie = cambiar el adapter, el `CombatCore` no se toca.

---

## 6. Anti-RPG por diseño (veto absoluto)

No basta con "no implementar niveles": el diseño **imposibilita** el crecimiento.

1. **Stats = datos de entrada inmutables.** `FrozenStats` es un `dataclass(frozen=True)` con un **conjunto CERRADO** de campos (`max_hp, move_speed, base_damage, defense, attack_range, basic_cooldown_ms`). **No existe** campo de nivel/experiencia/crecimiento. Se fija **una vez** al iniciar (loadout) y es inmutable: mutarlo lanza error.
2. **No hay API de crecimiento.** El core no expone `subir()`, `ganar_experiencia()`, `evolucionar()` ni ninguna mutación de stats en runtime. Las stats solo se leen.
3. **Progresión = más opciones, no más poder.** La medalla **desbloquea un NUEVO kit** (una `KitDefinition` más en el roster selectable). **Nunca** modifica las stats de un kit existente. Capturar = sumar un luchador con el **mismo poder** que todos.
4. **Triple guarda:**
   - **Estructural:** `FrozenStats` frozen + campos cerrados (no cabe un campo de nivel).
   - **Estática:** test que escanea `core/` y exige **0** apariciones de identificadores de progresión (Bloque 6.27e).
   - **Unitaria:** test que afirma que el conjunto de campos de `FrozenStats` no contiene ningún identificador de nivel/experiencia/crecimiento.

---

## 7. Modelo de datos (coordino con a8)

| Dato | Formato | Dueño | Nota |
|---|---|---|---|
| `KitDefinition` | JSON por kit | a8 | data-driven; el core la carga, no hardcodea |
| **Matriz 18×18** | `matrix.json` (versionado) | **a8** | **fuente de verdad**; verificada contra fuente oficial (NO de memoria); valores en % entero. El esqueleto trae un **STUB neutro** que a8 reemplaza con las 324 combinaciones |
| Config de arena | `arena.json` | a8 | orbes, timer, loadouts |
| Medallas/desbloqueos | (semana 3) | a8 | árbol; desbloquea kits, no stats |
| Fixtures/replays | secuencia de `InputFrame` JSON | 7f | **el replay ES la fixture** |

> **Caso C1 (trampa consciente):** los `×2`/`×0.5` del formulario son **ilustrativos**. La arquitectura aplica **lo que dice `matrix.json`**; la prueba de balance valida contra ese archivo. El core y yo **no** asumimos multiplicadores de memoria.

---

## 8. Netcode M2 — lockstep / rollback

**Solo doc de diseño (no se implementa en M0).** Ver `DISENO-NETCODE-M2.md`. Resumen:
- **Lockstep determinista:** cada cliente corre el MISMO `CombatCore`; avanza al tick *T* cuando tiene los `InputFrame` de todos los jugadores para *T*. El determinismo (§2) es lo que lo hace posible.
- **Rollback (GGPO):** snapshots de `MatchState` cada *k* ticks + buffer de inputs con especulación. Ante input tardío: rewind al último snapshot, re-simular con el input real, fast-forward. **Requiere** que el estado sea serializable y el core re-ejecutable puro — ya garantizado por §2/§4.8.
- **Server authority (ranked):** el servidor valida inputs (anti-cheat) — posición de `4e`.

---

## 9. Estrategia de prueba (Bloque 6)

| Familia | Qué cubre | Estado esqueleto |
|---|---|---|
| **Determinismo** | fixture ≥10.000 frames → 2 runs → **diff = 0** (byte-identical) | ✅ `test_determinism` |
| **Anti-RPG** | estático (0 hits) + estructural (frozen/cerrado) | ✅ `test_antirpg` |
| **Skeleton** | 1 entidad se mueve y ataca | ✅ `test_skeleton` |
| **Performance** | tick p99 < 16 ms; 5:00 < 5 s headless | ✅ (check incluido) |
| Unitarias (matriz 324, daño, cooldowns, i-frames, captura, score, fin) | Bloque 6.27a | semana 2-4 (7f) |
| E2E (7 escenarios 2.11) | Bloque 6.27b | semana 2-4 (7f) |
| Balance (banda ±10%) | Bloque 6.27d | contra `matrix.json` de a8 |

**Vetos de puerta:** 1 fallo de determinismo **o** de anti-RPG = **no listo**.

---

## 10. Riesgos y decisiones abiertas

- **Q1 (superficie):** resuelta por diseño (pluggable, TTY default) — el cliente elige, no bloquea.
- **Q2 (salvajes/hub en M0):** **CERRADA** (plan v1.1): Rattata obligatorio (baseline ×1) + Oddish (stretch) + hub TTY mínimo. Afecta a `CaptureSystem` y al runner; no bloquea el core.
- **Scope creep RPG:** mitigado por §6 (triple guarda) + revisión de código.
- **Matriz de memoria:** el stub neutro + la validación contra `matrix.json` de a8 lo evitan.

---

## 11. Entregable semana 1 (este esqueleto)

- [x] Arquitectura (este doc) — **reconciliada con la implementación de 29** (naming `podo/combatcore`, fixed-point, daño multiplicativo, `random.Random`). Pendiente: aprobación final del Jefe.
- [x] Esqueleto core **corriendo** (29): tick loop fijo, `InputFrame` serializable, máquina de estados, **1 entidad que se mueve y ataca** (aim spec Q1 v1.1), PRNG sembrado.
- [x] **Contrato de determinismo probado:** 10.000 frames, 2 runs, log byte-idéntico (**34/34 tests en verde**).
- [x] **Anti-RPG probado:** `KitDefinition` frozen/cerrado + escaneo estático = 0 hits de mecánica.
- [x] **Contrato con QA (7f) FIRMADO:** capa `contract.py` + superficie de `CombatCore` (apply_input_frame/advance/state_hash/is_over/final_score). Desbloquea fixtures de daño/tipos/cooldowns/dirección.
- [x] Adapter TTY + runner headless (`python -m combatcore.adapters.headless --demo`).

**Siguiente (con 29, sem 2):** partido 3v3 jugable, Q/E, guardia/perfect guard, esquiva, ultimate, switch (CD 4 s + ventana 1,5 s), KO/timeout→score. Matriz real de a8 cuando la publique.
