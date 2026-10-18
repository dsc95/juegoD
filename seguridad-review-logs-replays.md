# REVIEW SEGURIDAD — Arquitectura de Logs / Replays (M0)

**Proyecto:** Pokémon Odisea (PODO) · M0
**Autor:** Seguridad (`4e`) · **Fecha:** 2026-10-17
**Estado:** ✅ **REVIEW EJECUTADA — DISEÑO APROBADO (2026-10-18).** Validado contra `ARQUITECTURA-COMBATCORE-M0.md` + `podo/docs/FIXTURES-AND-REPLAYS.md` + código (`podo/combatcore/replay.py`, `adapters/tty.py`, `adapters/headless.py`). Veredicto en §2.1. 1 gap R6 detectado y cerrado antes del commit 1 (ver §3 H3).

---

## 0. Contexto y objetivo

- M0 es **100% offline**: sin red, sin cuentas, sin PII, sin credenciales (Bloque 7.30–7.31).
- **Replay = log de input frames** con doble uso: *feature* (reproducir la partida) + *fixture de QA* (determinismo, Bloque 6.27c / 29).
- Log estructurado por partida: **inputs, eventos de daño/KO/switch/capture, timer, score**.
- Mi ángulo (Seguridad): verificar que el log/replay **no contenga ni un dato sensible, ni credencial, ni semilla expuesta de forma insegura**, y que el formato **permita** el determinismo que QA exige (logs byte-iguales en 2 runs).

> Nota de alcance: "seguridad" en M0 offline = **higiene de datos + no-introducir superficie de riesgo** para M2, no un modelo de amenazas activo. No hay atacante ni canal de red en M0.

---

## 1. Requisitos de seguridad (checklist)

Cada ítem es verificable y debe aparecer explícito en el diseño de `31`.

### R1 — Solo datos de juego, nada de identidad
- El log/replay contiene **exclusivamente** estado de simulación: input frames, eventos (daño/KO/switch/capture), timer, score, seed, versión de build/config.
- **PROHIBIDO** en el log: usernames, Steam ID, IP, MAC/serial, hostname, ruta de usuario, locale, versión de SO, versión de drivers.
- **Razón:** M0 no tiene cuentas, pero el formato de log se hereda a M2 (online). Si hoy se escribe `player_name` o `hostname`, mañana es PII en producción. Cero cost hoy, caro mañana.

### R2 — Sin credenciales ni secretos, nunca
- **Nunca** se loguean valores de `.env`, API keys, tokens, secretos.
- La regla dura del formulario (7.31): "nunca loguear credenciales".
- El log debe ser **independiente** del entorno de ejecución: mismo log aunque el proceso tenga/un `.env`. Si un error/stacktrace se captura al log, debe estar **saneado** (no imprimir `os.environ`).

### R3 — Semilla: registrada, no expuesta
- La **seed del RNG debe ir en el log** (es obligatoria para determinismo: misma seed + mismos inputs → mismo resultado, Bloque 6.27c).
- **"No expuesta de forma insegura"** = la seed:
  - (a) es un entero/opaque determinístico, **no** derivada ni codifica ningún secreto real;
  - (b) se genera de forma **reproducible** para QA (fija en fixtures) y **aleatoria** en partida real (para que no se pueda predecir captura/drop);
  - (c) en M2 (online) la seed de una partida ranked **no** debe ser derivable de un secreto del servidor ni usarse como oráculo (se revisa en el doc anti-cheat M2).
- En M0 offline esto es **higiene**, no un secreto: la seed puede viajar dentro del replay sin problema, siempre que no encodee nada sensible.

### R4 — Reproducibilidad / determinismo (habilita la prueba de QA)
- **Nada de reloj de pared** en el log: usar **tick count / frame index** (relación 1:1 con los 16 ms lógicos), nunca `wall-clock timestamp`. Un timestamp real haría imposible el diff byte-a-byte.
- **Orden estable**: serializar colecciones en orden determinista (sortear por key o index). No depender del orden de inserción de un `dict`/`set`.
- **Precisión fija** en números (evitar `repr` de float variable entre plataformas).
- **Sin datos dependientes del proceso**: no `pid`, no `thread id`, no punteros, no tiempos de performance reales.
- Resultado objetivo: **2 runs, misma seed + mismos input frames → archivo byte-igual** (esto es exactamente lo que QA dif-eará, 6.27c/C7).

### R5 — Formato y versionado
- **Formato estructurado**: JSON Lines (`.jsonl`) o binario versionado. Recomendado: **JSONL** en M0 (legible, difeable con `diff`, stdlib-only).
- **Schema versionado** en el header del log (`"version": 1`, `build`, `config_hash`). Si cambia el formato, sube la versión; los replays viejos deben seguir siendo interpretables.
- **Self-contained**: el replay debe ser reproducible **solo con el archivo** (inputs + seed + version de config). No depende de estado externo.
- El `config_hash` (hash de los datos de kit/matriz/arena) va en el header → detecta si el replay se reproduce contra una config distinta.

### R6 — Ubicación y manejo de archivos
- Logs/replays se escriben **local, en el directorio de usuario del juego** (no en el repo).
- **NUNCA** se commit-tean replays de partidas reales al repo.
- Las **fixtures de QA** (replays sintéticos) SÍ van al repo, pero son datos generados, sin PII/seed real de nadie → OK.
- **`.gitignore`** desde el día 1 debe excluir: `.env`, `*.replay.jsonl` de partidas reales, `logs/`, `saves/`. (Ver hallazgo H1 abajo.)

### R7 — Sin superficie de red (verificación)
- El writer de logs **no abre sockets, no llama a URLs, no hace fetch**. M0 = 0 dependencias de red (Bloque 6 / 8).
- El log debe poder escribirse en un sistema **sin red** sin degradarse ni fallar.

### R8 — Sin LLM en el log (verificación)
- Nada de prompts, ni responses, ni embeddings en el log. El producto **no tiene LLM en runtime** (Bloque 8). Si alguna herramienta del *process* del equipo toca el log, no debe inyectar texto de LLM al archivo de replay.

---

## 2. Checklist de revisión (cuando `31` entregue el diseño)

Marcar ✅/❌ contra el diseño de CombatCore:

- [ ] El log define campos **exclusivamente** de estado de juego (R1). ¿Aparece algún campo de identidad? (debe ser ninguno)
- [ ] No hay ruta de logueo que pueda imprimir `os.environ`/`.env`/secretos (R2).
- [ ] La seed va en el log, es determinística-reproducible y no codifica secretos (R3).
- [ ] El tiempo es por **tick/frame**, no wall-clock (R4).
- [ ] Serialización determinista (orden fijo, precisión fija) → diff byte-igual posible (R4).
- [ ] Formato versionado + `config_hash` en header; replay self-contained (R5).
- [ ] Destino de escritura local; fixtures vs. partidas reales separadas; `.gitignore` cubre `.env`/replays/saves (R6).
- [ ] El writer de logs no abre red (R7).
- [ ] Ningún dato de LLM en el log (R8).
- [ ] **Cero** mecánica RPG en el esquema del log (sin campos `level`/`xp`/`stat_growth`) — coherente con el veto anti-RPG (Bloque 6.27e / 8).

**Criterio de aceptación:** todos ✅ → "log/replay aprobado por Seguridad". Un solo ❌ en R1/R2/R4 = **no aprobado** (bloquea determinismo o introduce PII/secretos).

---

## 2.1. VEREDICTO (2026-10-18) — Diseño de `31` + formato canónico de `a8` + código de `29`

| Req | Resultado | Evidencia |
|---|---|---|
| R1 solo datos de juego | ✅ | El doc del replay (`save_replay`) contiene solo: format/version, engine{name,version}, seed, matrix_version, config{tick_ms, duration, arena, teams=kit_ids}, inputs{t,side,seat,move,actions}, tail{frames_total, final_state_hash, rejected_inputs, outcome}. Side/seat anónimos; cero identidad. |
| R2 sin credenciales | ✅ | `replay.py`/`tty.py`/`headless.py` no tocan `os.environ`/`.env`; headless declara "el tiempo de pared JAMÁS entra en el log". |
| R3 seed registrada | ✅ | `seed` en el header del replay; PRNG sembrado único en el core (`random.Random(seed)`, arch §4.7); nota sem 3: snapshot debe incluir `rng.getstate()`. |
| R4 determinismo | ✅ | Ticks lógicos 0-based (sin wall-clock en el doc); serialización canónica `json.dumps(sort_keys=True)`; registros ordenados por (t, side, seat); actions `sorted()`; movimiento/daño en enteros/fixed-point; `final_state_hash` = sha256 del digest canónico; `verify_replay()` re-juega y exige state_hash+outcome+rejected idénticos. Empírico: 34/34 tests verdes incl. determinismo 10.000 frames diff=0. |
| R5 formato versionado | ✅ | `podo.replay` v1; `load_replay` rechaza format/version desconocidos; self-contained (config + `matrix_version` + `engine.version`); regla de bump en spec §6. |
| R6 ubicación | ⚠️→✅ | **Gap detectado:** la TTY guarda replays de partidas reales en `podo/replays/tty-*.json` — fuera de los patrones de `.gitignore` (`*.replay.jsonl`, `logs/`). **Cerrado:** agregada `replays/` al `.gitignore` antes del commit 1 (H3). Fixtures sintéticas en `podo/fixtures/` = OK al repo. |
| R7 sin red | ✅ | Imports de los 3 módulos: stdlib solo (json, pathlib, select, termios, time…); cero sockets/URLs; core puro (regla 6, arch §2). |
| R8 sin LLM | ✅ | Nada de prompts/embeddings en el formato ni en el código de log. |
| Anti-RPG en el formato | ✅ | Cero campos level/xp/crecimiento en schema de replay; `FrozenStats` closed/frozen (arch §6). |

**Notas no bloqueantes (acta):**
- N1: TTY usa `seed = 42` hardcodeado. Para M0 es OK; **sem 3 (captura)** sembrar aleatoriamente por partida y dejarlo en el log (hoy toda partida TTY comparte seed).
- N2: `ARQUITECTURA-COMBATCORE-M0.md` §4.8 menciona `events` dentro del replay; el formato canónico de `a8` (`podo.replay` v1) no trae `events` (va `final_state_hash` + `rejected_inputs` + `outcome`). Alinear el doc de 31 con la spec de a8.
- N3: El *filename* del replay TTY lleva timestamp real (`tty-YYYYmmdd-HHMMSS-...`), pero queda **fuera del documento** (no afecta el diff de determinismo, que opera sobre el contenido).

**Dictamen: APROBADO por Seguridad** — el diseño de logs/replays cumple R1–R8 y deja la base lista para M2 (input frames atómicos, formato versionado, seed autoritativa heredable, log sin PII/secretos).

---

## 3. Hallazgos del workspace (fuera del juego, pero del repo futuro)

### H1 — `.env` legado con credencial viva en el workspace ⚠️
- Archivo: `.env` (del curso **LangGraph anterior**, no de PODO).
- Contiene `LANGCHAIN_API_KEY=lsv2_pt_d5c6…` (redactada) + base URL local de LLM.
- **Riesgo:** si el repo de PODO se crea en esta carpeta y alguien hace `git add .` / `git add -A`, la key se commitea y se filtra a cualquiera que clone el repo.
- **Acción (hoy, antes del primer commit del repo):**
  1. Agregar a `.gitignore` desde el día 1: `.env`, `.env.*`, `logs/`, `saves/`, `*.replay.jsonl`.
  2. **Rotar** la `LANGCHAIN_API_KEY` si se piensa hacer el repo público/shared (aun "no usada", ya vivió en disco).
  3. Confirmar con el Jefe/cliente si el `.env` del curso anterior sigue siendo necesario; si no, moverlo fuera del workspace.
- **No** bloquea M0 (el juego no lo lee), pero sí es un riesgo de filtración real en el repo.

### H2 — Otros archivos no-proyecto en el workspace
- `CDR_…xlsx` (930 KB) y `manuales-usuario-plataformas-iacu/` son de **otro contexto** (no PODO).
- **Acción:** excluirlos del repo de PODO (no son contenido del juego). El repo debe contener solo: código + GDD/plataforma + docs + fixtures de QA.

---

## 4. Línea de base para M2 (lo que M0 debe dejar listo)

Para que el doc anti-cheat M2 (`seguridad-anticheat-m2.md`) sea viable **sin rediseño**, M0 debe garantizar:
1. **Input frames como unidad atómica serializable** (M2 los envía al servidor; el servidor re-simula).
2. **El log ya es el formato de replay** (M2 lo reutiliza como evidencia/auditoría server-side).
3. **Determinismo** probado en M0 (M2 lo exige para lockstep/rollback + anti-cheat).
4. **Cero PII/secretos en el log** desde el día 1 (M2 lo hereda).

> Si M0 cumple esto, M2 no toca el formato de log: solo agrega transporte + validación server-side.
