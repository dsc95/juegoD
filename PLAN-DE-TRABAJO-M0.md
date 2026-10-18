# PLAN DE TRABAJO — M0 · "Pokémon Odisea" (PODO)

**Workspace:** `~/Documentos/cursos/Langraph/reflexion-agente`
**Versión del plan:** 1.2 — 2026-10-18 (Q1/Q2/Q3 cerradas por el cliente; §10 actualizado; errata matchups Q3: la canónica manda)
**Jefe (PM):** `reflexion-agente-ab` · **Cliente (requisitos):** `reflexion-agente-1f`
**Fuente de verdad:** `FORMULARIO-PROYECTO.md` (40/40) + GDD v2 (`diseño-pokemon-odisea.md`) + `plataforma-juego-pc.md` + `estudio-pokemon-nintendo.md`

---

## 1. Objetivo
Entregar el **M0 jugable**: vertical slice del combate en tiempo real (1 arena 3v3, 5:00, KO o score) sobre una **simulación determinista en Python** (CombatCore headless), que valide el *feel* del control directo y todo el sistema de controles. **Sin LLM en el producto, sin red, sin RPG.**

## 2. Alcance (M0)
**DENTRO:** 1 arena 3v3 · 3 kits data-driven (Pikachu Carry/Eléctrico, Snorlax Defender/Normal, Gardevoir Support/Psíquico) · todos los controles (WASD, básica, Q, E, guardia, esquiva con i-frames, ultimate con carga, switch Tab/1-3 con CD 4 s + ventana vulnerable 1,5 s, F captura) · matriz canónica 18×18 (arquitectura desde el día 1; el contenido puede arrancar con 8 tipos) · captura por probabilidad (HP + ball) · medalla → desbloqueo · save local · replay = log de input frames · score por orbes al agotar el tiempo · determinismo total · **salvajes: Rattata (obligatorio, baseline de la curva de captura) + Oddish (stretch, rama de resistencia)** con `KitDefinition` simplificado (básica + 1 habilidad, sin ultimate) · **hub TTY mínimo** (menú persistente): [Arena] · [Zona salvaje] · [Estado: medallas/roster/save] · [Replay última partida] · **equipo del jefe de arena_001 = trío ROCA (Geodude, Graveler, Onix — Q3 cerrada)** con kits simplificados (básica + 1 hab., sin ultimate) — ejerce matchup real en el 3v3 — pared 0,5× Snorlax→Roca ⇒ switch forzado (errata 18-10: eléctrico↔roca = 1×, la canónica manda); **corte si el checkpoint sem. 2 va en riesgo: jefe = 3 normales neutros** (flip de `boss_team_fallback_neutral` en arena_001.json, data only).
**FUERA (y vetos):** cualquier nivel/XP/crecimiento de stats (**veto absoluto**) · online/netcode (M2) · roster completo · 5v5 · mobile · monetización · prototipo HTML/mockup (rechazado explícitamente por el cliente) · **pygame en la puerta del Bloque 6 (veto duro)** — solo como stretch opcional, thin adapter device→input frames, y CombatCore jamás lo importa · "mundo caminable" (es del mundo de producción, no de M0).

## 3. Arquitectura (dueño: 31)
- **CombatCore** — Python puro, 0 dependencias, determinista: tick loop fijo (16 ms lógicos), stream de input frames serializable, máquinas de estado de entidades, daño con matriz de tipos canónica, cooldowns, i-frames, guardia/perfect guard, KO/score, captura, medallas/desbloqueos.
- **Datos** (a8) — `KitDefinition` JSON, matriz canónica 18×18 (verificada contra fuente oficial, versionada en repo), config de arena, árbol de medallas, formato de fixtures (secuencia de input frames = replay = fixture de QA).
- **Presentación fina** — M0: adapter TTY (teclado) para jugar/observar + runner headless para QA/replays. **Q1 cerrada (v1.1):** puerta = TTY solo (stdlib + pytest); pygame solo como stretch opcional, y solo como **thin input adapter** (device → los mismos input frames; CombatCore no importa pygame ni conoce de devices). **Spec básica dirigida en TTY:** objetivo más cercano según facing, con tie-break determinista: (1) menor distancia, (2) menor ángulo con el facing, (3) menor índice en la lista de entidades → testeable con fixture.
- **Reglas duras:** sin LLM en runtime · sin RNG sin semilla · sin red · sin credenciales (M0).

## 4. Asignación por agente
| Agente | Alcance |
|---|---|
| **31** Arq. software | Arquitectura CombatCore (tick loop, input frames, estado, contrato de determinismo) + adapter de presentación fina + plan anti-RPG por diseño + esquema netcode lockstep/rollback para M2 (solo doc de diseño) |
| **a8** Arq. datos | Modelo `KitDefinition` · **matriz canónica 18×18 verificada contra fuente oficial** (no de memoria) · estructura de medallas/desbloqueos · formato de fixtures/replays |
| **29** Desarrollador | Implementación M0 sobre CombatCore: controles, partido 3v3, switch con coste, captura, medalla/desbloqueo, saves, replays, score/orbes |
| **4e** Seguridad | Review de arquitectura de logs/replays (sin datos sensibles — offline, verificar) · posición anti-cheat M2 (doc corto) · validación legal IP / uso no comercial (cláusula en README/LICENCE) |
| **7f** QA | Suite completa del Bloque 6 con fixtures propias: unitarias (324 combinaciones de tipos, daño, cooldowns, i-frames, captura, score, fin de partida) · e2e (7 escenarios de 2.11) · determinismo (fixture 10.000 frames, 2 runs, diff=0) · balance (banda ±10%) · anti-RPG estático · performance (p99 <16 ms, partida 5:00 <5 s) |
| **ab** Jefe | Plan, kickoff, consolidación, avances por hito, aviso formal **"listo para pruebas"** |

## 5. Cronograma (4 semanas desde kickoff)
- **Semana 1** — 31: arquitectura aprobada + esqueleto core con 29 (tick loop, input frames, 1 entidad que se mueve y ataca). a8: modelo de datos + matriz v1 (8 tipos, arquitectura 18) + formato de fixtures. 7f: harness de tests + primeras fixtures unitarias. 4e: review de diseño de logs + doc anti-cheat corto.
- **⛩️ SEMANA 2 — CHECKPOINT DURE:** partido 3v3 jugable sin captura ni medalla (movimiento, básica/Q/E, guardia, esquiva, switch con coste, ultimate, KO y time-out→score). → avance a cliente + usuario (5 líneas). **Gate sem 2 (actualizado 18-10, incidente de integración):** contrato QA ✅ + arquitectura ✅ + **adapter de datos a8→engine (determinista, dueño 29) + confirm de 7f** al levantar los 6 BLOCK.
- **Estado 18-10 (tarde):** wiring 3v3 = 100 % (29, sobre data canónica: guardia/perfect, esquiva i-frames, Q/E, ultimate, switch 3v3, score/orbes) — suite 29 66/66 + 7f 56 PASS/0 FAIL/1 BLOCKED; el suite nuevo atrapó y corrigió 2 bugs reales de engine (resurrección de KO'd en `_do_switch`, switch doble-tick); **31 firmó el commit estable** con verificación propia; README merge hecho. Queda: **gate final de 7f contra el hash del commit 1** (ejecuta 4e). Borrado aprobado de los 3 archivos deprecados de a8 (`data/types.json`, `tools/gen_types_engine.py`, `data/gen_types_placeholder.py`) — 29 los elimina antes del commit 1 (trigger cumplido: fixtures de 7f migradas a la canónica).
- **Semana 3** — captura (salvajes + balls + probabilidad), medalla → desbloqueo, saves locales, replays, orbes/score completo, matriz 18 completa en contenido.
- **Semana 4** — Bloque 6 al 100%, vetos de QA, banda de balance, demo con replay reproducible, buffer.

**Avances:** por hito (no por día), formato 5 líneas (qué pasó / qué falta / riesgos), al cliente y al usuario.

## 6. Puerta "listo para pruebas" (Bloque 6 — sin excepciones)
Los 10 criterios del Bloque 6.26 + familias de pruebas 27(a–f). **Vetos absolutos:**
1. Cualquier fallo de **determinismo** (2 runs, mismos inputs → logs distintos) = **no listo**.
2. Cualquier aparición de **mecánica RPG** (nivel/XP/crecimiento de stats) = **no listo**.

## 7. Política de recorte (si se atrasa)
Prioridad del cliente: (1) feel del combate > (2) switch con coste > (3) matriz de tipos (arquitectura 18, contenido puede arrancar 8) > (4) captura > (5) medalla/desbloqueo > (6) score/orbes > (7) gamepad.
**Cortar primero:** gamepad, 3.º kit (bajar a 2), orbes, 18 tipos completos en contenido.
**Nunca cortar:** determinismo, anti-RPG, controles core.

## 8. Restricciones no negociables
- Sin LLM en el producto · sin red · sin RNG sin semilla · sin credenciales (M0) · stdlib + pytest como máximo (salvo Q1).
- **Legal:** entregable del curso no-comercial o IP original inspirada en Pokémon; nunca distribución comercial del prototipo con IP Pokémon.
- Cifras del caso C1 del formulario son ilustrativas: **la matriz canónica de a8 es la fuente de verdad** y las pruebas la validan contra ella (así lo definió el cliente).
- La suite QANTICA n8n y `/qantica doctor --fix` (mencionada en el pie del formulario) **no forman parte del M0** — son un activo distinto del repo.
- **Regla de proceso (acta 18-10, causa registrada: incidente de divergencia de formatos matriz/kits):** toda interfaz que toquen 2+ agentes se congela por **contrato escrito ANTES de trabajar en paralelo**. Contratos vigentes: schema v1.0.0 de a8 (datos canónicos, matriz fracciones + tip doble) + contrato de unidades de 31 (×10 exacto, `round`, `ticks_from_ms`) + contrato CombatCore de 7f. Adapter a8→engine: dueño 29.

## 9. Riesgos
| Riesgo | Impacto | Mitigación |
|---|---|---|
| Scope creep hacia RPG | Veto / no listo | Prueba estática anti-RPG + revisión de código |
| Matriz 18×18 de memoria | Data incorrecta | a8 verifica contra fuente oficial, versionada en repo |
| *Feel* no validable en headless | Producto no validado | Adapter TTY jugable desde sem. 2; decisión Q1 (pygame opcional) |
| Deslizamiento de las 4 semanas | Entrega del curso | Política de recorte §7 + checkpoint semana 2 |

## 10. Decisiones de cliente (CERRADAS en v1.1 — 2026-10-17)
Fuente: `DECISIONES-CLIENTE-Q1-Q2.md` (en vigor; el cliente lo emitió por archivo porque el canal cross-session estaba caído al escribirlo).
- **Q1 CERRADA:** puerta del Bloque 6 = **TTY solo** (stdlib + pytest, determinismo total); **pygame no entra en la puerta bajo ninguna circunstancia**. Stretch opcional: thin input adapter (mouse→aim, clic izq.→básica, clic der.→guardia/G, WASD) que emite los mismos input frames; CombatCore no lo importa. Si el checkpoint sem. 2 va en riesgo, el stretch se corta sin pena. **Spec nueva (sem. 1):** básica dirigida en TTY = objetivo más cercano según facing + tie-break determinista (distancia → ángulo con facing → índice de entidad); testeable con fixture.
- **Q2 CERRADA:** **Rattata (Normal) obligatorio** (baseline de la curva de captura: matchup neutro ×1 contra los 3 kits, aísla el factor HP+ball) + **Oddish (Planta) como stretch** (rama de resistencia: Psíquico ×0,5 obliga a switchar de Gardevoir). Salvajes = `KitDefinition` simplificado (básica + 1 habilidad, sin ultimate), misma CombatCore/determinismo/suite QA — no "enemigos scripteados aparte". **Hub mínimo TTY** (menú persistente): [Arena] · [Zona salvaje] · [Estado: medallas/roster/save] · [Replay última partida] — hace testeable el flujo e2e 2.8 y el caso C8; "mundo caminable" fuera de M0.
- **Q3 CERRADA (18-10, data-only, baja prioridad):** equipo del jefe de la arena M0 (arena_001, 1.er gimnasio de Kanto) = **tipo ROCA: Geodude, Graveler, Onix** — kits simplificados (básica + 1 habilidad, sin ultimate), mismas reglas que los wilds. Con esto el 3v3 ejerce matchup real sin tocar el trío — **matchups efectivos según la canónica (FLAG a8 18-10, verificado celda a celda):** Snorlax(normal)→roca = **0,5×** ⇒ pared y switch forzado (el diseño funciona como el cliente pidió); eléctrico→roca = 1× y roca→eléctrico = 1× — el «2× / 0,5×» del brief era **errata del Jefe, la matriz canónica manda (C1)**; el trío queda documentado como «muro» en TYPE-MATRIX.md §5. Opciones descartadas: (a) wild Oddish 2× en arena_001 (cambia el diseño de arena, fuera de brief) y (b) cambiar un kit (contra el trío que el cliente eligió explícitamente). `gym_type` de arena_001 pasa «fire» → «rock» (alinea el trío + canon Kanto, Brock; data only, aprobado 18-10). El escenario 2.11b pasa a ejercitarse en la arena. **Corte si el checkpoint sem. 2 va en riesgo:** jefe = 3 normales neutros (la matriz sigue validada por las 324 unitarias + wilds). El trío jugador queda como briefeado (mutuamente neutro; Carry/Defender/Support vale más que un triángulo de tipos para M0). Errata Q2a aplicada: planta no resiste psíquico; la rama 0,5× de Oddish es electric→grass (Pikachu es el desventajado).
- **C1 confirmada:** las cifras ilustrativas del caso C1 quedan reemplazadas por la matriz canónica de a8 (fuente de verdad, versionada en repo).
