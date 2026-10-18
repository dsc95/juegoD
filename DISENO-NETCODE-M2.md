# DISEÑO — Netcode M2 · lockstep / rollback · Pokémon Odisea (PODO)

**Rol:** Arquitecto de software (`reflexion-agente-31`) · **Estado:** diseño (NO se implementa en M0)
**Fecha:** 2026-10-18 · **Depende de:** `ARQUITECTURA-COMBATCORE-M0.md` §2 (contrato de determinismo) + `podo/combatcore/` (contrato firmado con QA 7f)
**Stack:** M0 = Python de referencia. M2 producción = C++/UE5 (el MISMO `CombatCore`, portado).

> **Principio:** el netcode M2 **no inventa** determinismo — lo *exige*. Todo lo que sigue es
> consecuencia directa del contrato de determinismo que ya está firmado y probado
> (2 runs, mismos inputs → logs/digest byte-iguales; 10 000 frames verificados). Si el
> contrato de determinismo falla, el netcode no existe. Por eso este doc **no re-discute**
> el determinismo; asume que `podo/combatcore` lo cumple.

---

## 1. Modelo elegido: lockstep determinista (+ rollback opcional)

**Lockstep determinista** (deterministic lockstep) es el modelo nativo de PODO, porque la sim
ya ES una función pura:

```
state_{n+1} = Step( state_n , input_frames_n )
```

Cada cliente corre el **MISMO** `CombatCore`. El cliente `i` avanza al tick `T` cuando tiene
los `InputFrame` del tick `T` de **todos** los jugadores. Como todos parten del mismo
`(config, seed)` y reciben las mismas secuencias de inputs, todos llegan al **mismo** estado
(same seed + same inputs = same result). No hay que transmitir estado, ni posición, ni
resultado: **solo se transmiten input frames** (tiny, fijos, serializables).

**Rollback (GGPO-style)** se suma en M2 para **ocultar latencia de render** (no de autoridad):
especular sobre inputs faltantes, render adelantado, y ante el input tardío rewind + re-sim.
Es opcional por partida; el lockstep puro ya es jugable en red local / casual.

**Por qué NO server-authoritative puro en M2-casual:** el lockstep determinista no necesita un
servidor de simulación (ahorra infra y el "feel" es idéntico en todos los clientes). El
server-authoritative sí se usa en **ranked** (ver §6) para anti-cheat.

---

## 2. Lo que el netcode REQUIERE del core (contrato, no diseño nuevo)

| Requisito | Dónde ya está | Estado |
|---|---|---|
| `state = Step(state, inputs)` puro | `core.step(frames)` / `core.run(streams)` | ✅ |
| Estado **entero / fixed-point** (sin divergencia de float entre máquinas) | `constants`, `entities` | ✅ |
| **Un solo** PRNG sembrado, **estado serializable** | `CombatCore.rng = random.Random(seed)` | ✅ (ver §5 flag) |
| Proceso de entidades **ordenado por `eid`** (sin orden de `set`) | `core.step` | ✅ |
| **Sin reloj de pared** (el tick ES el reloj) | `constants.TICK_MS` | ✅ |
| `InputFrame` serializable + formato canónico | `frames.py` (`FIELD_ORDER`, `serialize_frames`) | ✅ |
| Conversión ms→ticks **única** (`ticks_from_ms`) | `constants` + `contract` | ✅ (regla del Jefe 2026-10-17) |
| Snapshot byte-estable + verify de replay | `digest()` / `digest_json()` / `replay.py` | ✅ |

> **Flag duro (sem 3 → gate de M2):** cuando la captura use `self.rng`, el snapshot **DEBE**
> incluir `rng.getstate()` (29 lo dejó como TODO en `digest()`). **Sin esto, un rollback que
> cruce una captura no es reproducible y el netcode ranked se rompe.** Es gate, no nice-to-have.

---

## 3. Protocolo de exchange de input frames

- **Unidad de red:** el `InputFrame` (11 campos fijos, `FIELD_ORDER` — ver `frames.py`). ~40 bytes
  serializado. Es el **único** dato que se transmite por tick, por jugador.
- **Regla de avance (lockstep):** el cliente avanza al tick `T` cuando ha recibido el
  `InputFrame(T)` de cada uno de los `N` jugadores. El avance máximo está limitado por el
  jugador con más "deuda" de input:

  ```
  advance_to = min( para cada jugador j : último tick de j confirmado )
  ```

- **Retardo de input (teórico, lockstep puro):** `delay = (N − 1) × RTT_max`.
  Para 3v3 (`N = 6`): hasta `5 × RTT`. A 30 ms de RTT → ~150 ms de input delay. Aceptable para
  casual / local-first; para ranked se usa rollback (§4) para **ocultar** el retardo de render.
- **Orden de aplicación = orden de jugadores.** Al re-simular, cada `InputFrame(T)` se aplica en
  orden de `player` (0..N−1) dentro del tick — **determinista**, igual que el proceso por `eid`.
- **Resync / reconnect:** si un cliente se cae o se desincroniza, se hace **full-state resync**:
  el (autoridad o un peer) envía un snapshot `digest` + la ventana de `InputFrame` pendientes, y
  el re-entrante re-simula. No hay "delta" de estado en M2 (los input frames + snapshot bastan).

---

## 4. Rollback (GGPO-style) — opcional, para ocultar latencia

El lockstep puro espera los inputs de todos (seguro, pero con input delay). El rollback permite
**render adelantado** con inputs especulados:

1. **Snapshot** cada `k` ticks (`k ≈ 3–8`): guardar `digest()` (incluye `rng.getstate()` — §5)
   + la ventana de `InputFrame` de los últimos `k` ticks. El `digest` byte-estable ya es la
   snapshot; `replay.py` ya verifica que re-simular da el mismo digest.
2. **Especulación:** si falta el `InputFrame(T)` de un jugador, usar su último frame conocido
   (o un idle) para simular "a ciegas" y render.
3. **Input tardío:** cuando llega el `InputFrame` real, se **rewind** a la última snapshot
   (≤ `k` ticks), se re-simula con los inputs reales, y se fast-forward. Si el estado re-simulado
   difiere del renderizado, se corrige visualmente en ≤ `k` ticks (el "snap").
4. **Coste:** re-simular `k` ticks desde la snapshot. **Baratísimo** para PODO: el benchmark de
   M0 corre 5:00 (18 750 ticks) en < 5 s headless → re-simular 8 ticks es < 1 ms. El rollback no
   es un cuello de botella en esta sim.
5. **Límite:** el rollback oculta el retardo de **render**, no el de **autoridad**. Un input
   sigue tardando `(N−1)×RTT` en ser *válido* para todos; el rollback solo hace que el jugador
   **sienta** su propio input de forma inmediata.

---

## 5. Snapshot (formato, M2)

```
{
  "tick":      int,        // tick de la snapshot
  "seed":      int,        // seed de partida (ya en digest)
  "rng_state": [ ... ],    // rng.getstate() — OBLIGATORIO (ver flag §2)
  "entities":  [ ... ],    // mismos campos que CombatCore.digest() (enteros)
  "winner":    int,
  "inputs":    { player: [InputFrame(t-k+1) .. InputFrame(t)] }   // ventana de k ticks
}
```

- **Byte-estable** (JSON canónico, `sort_keys=True`) — igual criterio que `digest_json()`.
- **Deriva del replay:** `replay.py` (`podo-replay/1`) ya guarda `{seed, ticks, teams, frames,
  events, digest}` y `verify()` re-simula. El snapshot de M2 es "un replay en cualquier tick T".
  QA (7f) re-usa el MISMO `verify()` para confirmar que **todos los clientes** llegaron al mismo
  estado (2 runs → byte-igual = el mismo criterio del veto de determinismo).

---

## 6. Ranked: server-authoritative lockstep

- En **ranked** el servidor es la autoridad. Corre el `CombatCore` y **ordena + re-broadcastea**
  los `InputFrame` (evita que un cliente malicioso elabore el orden).
- **Anti-cheat:** el servidor valida cada `InputFrame` (rango de `move_x/y`, flags válidos,
  `switch` 0..3/99 — la validación ya existe en `frames.validate`). El "feel" sigue siendo
  lockstep determinista; el servidor solo es el ordenador/verificador de inputs.
- **Dominio:** la validación/anti-cheat y la seguridad del protocolo es de **4e (Seguridad)**.
  Este doc (31) define el modelo determinista; 4e define la integridad de la red.

---

## 7. Puntos de integración concretos (lo que M2 consume de M0)

| M2 necesita | M0 ya provee (firmado) |
|---|---|
| Formato de wire del input | `InputFrame` + `serialize_frames` / `deserialize_frames` (`frames.py`) |
| Driver por tick | `CombatCore.step(frames)` (1 tick) / `run(streams)` (a fin) |
| Snapshot + fingerprint | `digest()` / `digest_json()` (`core.py`) |
| Ventana de inputs / replay | `InputStream` (`frames.py`) + `replay.py` (save/verify) |
| Reglas de cooldown en ticks | `SWITCH_COOLDOWN_TICKS` / `VULNERABLE_TICKS` (derivados vía `ticks_from_ms`, `contract.py`) |
| Verificación multi-cliente | `replay.verify()` (2 runs → byte-igual) |

**No hay que tocar `CombatCore` para M2** salvo el flag de `rng.getstate()` en el snapshot (§5).
Eso es lo que "config + 1 capa" (la Jefe) prometió: el netcode se monta **sobre** el contrato,
no dentro del core.

---

## 8. Riesgos / decisiones abiertas (M2)

1. **Port C++/UE5 (el riesgo nº 1):** el `CombatCore` de Python es la **referencia**. El port a
   C++ debe replicar **exacto** la matemática entera (fixed-point, `ticks_from_ms`, tie-break de
   aim, orden por `eid`) y el RNG. Cualquier divergencia rompe el lockstep entre clientes.
   **Mitigación:** el mismo suite de determinismo (10 000 frames → byte-igual) corre contra el
   port; y se genera un **golden set** de replays desde Python que el C++ debe reproducir
   byte-a-byte. (El RNG: o se porta el mismo Mersenne Twister de CPython, o se valida
   cross-lingua — decisión M2 con 29.)
2. **Retardo de input `(N−1)×RTT`:** para 6 jugadores es alto en RTT elevados. Rollback (§4)
   oculta el render; el input delay de autoridad queda. **Decisión M2:** ¿rollback por defecto en
   ranked? ¿ventana `k`? Tunning con 29.
3. **`rng.getstate()` en snapshot (sem 3):** gate duro. Si no se resuelve antes de M2, el
   rollback no es reproducible con captura. Registrado como gate.
4. **Fuera de scope M2 (para más adelante):** compresión/delta de frames (ahora es trivial a 40 B),
   matchmaking, resync parcial (M2 hace full-state), optimización de snapshot.

---

## 9. Resumen (one-liner por sección)

- **Modelo:** lockstep determinista; rollback opcional para ocultar latencia de render.
- **Wire:** solo `InputFrame` por tick por jugador (~40 B); estado/posición/resultados NO se transmiten.
- **Base:** todo depende del contrato de determinismo ya firmado (Python de referencia).
- **Rollback:** snapshot byte-estable cada `k` ticks + rewind + re-sim (baratísimo: 8 ticks < 1 ms).
- **Ranked:** server-authoritative lockstep; validación/anti-cheat de 4e.
- **Dependencia dura:** `rng.getstate()` en el snapshot (sem 3) — gate de M2.
- **Riesgo nº 1:** port C++/UE5 byte-a-byte (golden set de replays como garantía).
