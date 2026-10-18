# 📋 FORMULARIO DE INGESTA DEL PROYECTO

**Proyecto:** reflexion-agente
**Workspace:** `~/Documentos/cursos/Langraph/reflexion-agente`
**Fecha:** 2026-10-17
**Responsable:** Jefe (PM) — sesión `reflexion-agente-ab`
**Equipo:** Desarrollador (`29`) · Seguridad (`4e`) · Arq. software (`31`) · Arq. datos (`a8`) · QA (`7f`)
**Cliente:** la sesión que define los requisitos (rol "cliente"). **Completado el 2026-10-17 por el cliente — 40/40 respuestas.**

> **Cómo llenarlo:** respondé cada pregunta en la línea `R:` de abajo.
> Los bloques 3-7 llevan la etiqueta del agente que va a usar esa info.
>
> **⛩️ Regla de "listo para pruebas":** cuando el proyecto cumpla con TODOS los criterios del **Bloque 6**, el Jefe avisa al usuario *"listo para pruebas"*. Nada antes.

> 📎 **Referencias del cliente (docs en el workspace):**
> - `estudio-pokemon-nintendo.md` — estudio de la franquicia (contexto de dominio)
> - `diseño-pokemon-odisea.md` — **GDD v2 (el que rige)**: PC, acción, NO RPG
> - `plataforma-juego-pc.md` — plataforma técnica (motor, netcode, live-ops, roadmap)

---

## Bloque 0 — Identidad

1. **Nombre corto** del proyecto:
   R: **Pokémon Odisea** (código interno: **PODO**). Nombre completo: *Pokémon Odisea — World Tour Arena*.
2. **Una línea**: ¿qué es esto?
   R: Un **juego de acción para PC (NO es RPG)**: el jugador recorre un mundo con **todas las regiones de Pokémon**, pasa **8 arenas (medallas) por región** hasta el campeonato regional, y cada combate es **en tiempo real controlando directamente a su Pokémon** (estilo Pokémon UNITE) con las **reglas de la serie**: party de 6, cambio en plena batalla y captura.
3. **Problema de negocio** que resuelve (por qué existe):
   R: Existe un hueco real en el mercado: el RPG principal de Pokémon es **por turnos**; UNITE es solo **5v5 de 10 min sin campaña, mundo ni medallas**; Legends (Arceus/Z-A) es acción pero **sin gimnasios/medallas/ligas clásicas**. Nadie tiene "el viaje clásico con control directo en tiempo real". Para el curso, además, es el vehículo de la pipeline multi-agente (brief → plan → ejecución → QA → pruebas).
   **⚠️ Restricción legal (no negociable):** Pokémon es IP de Nintendo/Game Freak/The Pokémon Company. Sin licencia no puede comercializarse: los entregables del curso son (a) diseño/plataforma, y (b) prototipo **no comercial** o con **IP original inspirada** (mismas mecánicas, nombres/arte propios). Ver §33 del bloque 7.

## Bloque 1 — Objetivo y alcance

4. **Objetivo principal** (el único): ¿qué tiene que lograr?
   R: **Entregar el prototipo jugable M0 (vertical slice del combate)** que valide el corazón del juego: el *feel* del combate en tiempo real con control directo. Base obligatoria: GDD v2 y plataforma técnica ya definidos (docs de referencia arriba).
5. **DENTRO del alcance (MVP):**
   R: 1 arena jugable (formato 3v3, 5:00, gana por KO o por score con orbes de energía) + **3 kits** (Pikachu = Carry/Eléctrico, Snorlax = Defender/Normal, Gardevoir = Support/Psíquico) con kit data-driven; **todos los controles**: WASD, básica (clic izq., dirigida al mouse), Q (hab. ofensiva), E (hab. defensiva), clic der. (guardia), Espacio (esquiva con i-frames), R (ultimate, se carga), Tab/1–3 (switch con cooldown 4 s + ventana vulnerable 1,5 s), F (lanzar Poké Ball a salvaje debilitado); **matchup de los 18 tipos** en tiempo real; **partido con party de 3** (de un banco de 6); **captura** (probabilidad por HP + tipo de ball) que suma el Pokémon al roster; **progresión por desbloqueo**: ganar la arena → medalla → desbloqueo (nuevo Pokémon o arena); **PC Windows**, teclado+mouse y gamepad; simulación **determinista** (mismos input frames → mismo resultado).
6. **FUERA del alcance** (por ahora):
   R: **Cualquier mecánica de RPG**: niveles, XP, stats que suben, árbol de movimientos, diálogos/quests, inventario de equipo (no negociable — ver Bloque 6); las 10 regiones completas (lanzamiento real = 3: Kanto, Johto, Hoenn; el resto por "estaciones"); **online/ranked/netcode** (desde M2); el roster completo (lanzamiento ~30–40 kits); modo 5v5 MOBA (UNITE es solo referencia de combate); mobile; Monetización/pay-to-win (nunca, por diseño).
7. **Fases / etapas**, si las hay:
   R: **M0** vertical slice del combate (1 arena, 3 kits, offline) → **M1** región Kanto completa (8 arenas + liga, medallas y desbloqueos) → **M2** online 1v1/3v3 + ranked + replays + anti-cheat → **M3** beta 3 regiones → **M4** lanzamiento → **Estaciones** (7 regiones restantes + formas Mega + nuevos modos). Para este curso, el entregable objetivo es **M0** (o el avance máximo verificable de M0 con los criterios del Bloque 6).

## Bloque 2 — Producto / Funcionalidad

8. **Flujo principal**: qué hace el agente paso a paso cuando corre:
   R: El jugador (no es un agente LLM — ver bloque 5): (1) está en el **hub/mapa de la región** → (2) elige la **arena** (gimnasio) → (3) combate **3v3 en tiempo real**: mueve al Pokémon activo, ataca básico/Q, defiende con guardia/E, esquiva, cambia de Pokémon (Tab) y carga su **ultimate (R)** → (4) gana por **KO** (equipo rival fuera) o, si se agota el tiempo de 5:00, **por score** (golpes + KOs + orbes del mapa) → (5) obtiene la **medalla** + **desbloqueo** (Pokémon nuevo o siguiente arena) → (6) vuelve al hub y continúa el tour. Modo captura: en el hub hay **salvajes**; debilitarlo → **F** (ball) → si cae, entra al roster como luchador nuevo (sin XP, mismo poder que todos).
9. **Entradas**: ¿qué recibe? (usuario, archivo, API, webhook…)
   R: **Input del jugador** (teclado+mouse / gamepad — se serializa como input frames, eso es la base del determinismo). **Datos estáticos**: archivos de kits (KitDefinition: tipo, rol, básica, Q, E, esquiva, guardia, ultimate, cooldowns), matriz 18×18 de tipos, config de la arena (orbes, timer, equipos del jefe). **Nada externo** en M0 (sin APIs, sin webhooks, sin LLM).
10. **Salidas / entregables**: ¿qué produce? (respuesta, reporte, archivo, acción…)
    R: **El prototipo jugable M0** (ejecutable PC) + **save de progreso local** (medallas, desbloqueos, roster) + **replay de cada partido** (log de input frames — prueba de determinismo) + docs (GDD v2, plataforma, tablas de balance).
11. **Escenarios clave** que debe dominar:
    R: (a) KO limpio con combo + ultimate cargado; (b) **switch a tiempo** a un tipo ventajoso (ej. planta→fuego) en el cooldown; (c) **perfect guard** (timed) que devuelve daño y corta combo; (d) **captura exitosa** de salvaje al 10% HP y **fallida** al 90%; (e) **tiempo agotado con empate de KO → decide el score** por orbes; (f) **equipo del rival fuera** → victoria y medalla; (g) **determinismo**: dos partidas con la misma secuencia de inputs son idénticas.
12. **Non-negotiables funcionales**: qué tiene que hacer *muy* bien:
    R: (1) **El feel del control directo** — respuesta < 1 frame de input lag, i-frames reales en la esquiva, hit-stop y legibilidad de golpes; (2) **switch con coste real** (cooldown 4 s + 1,5 s vulnerable al entrar) que castigue el spam; (3) **matchup de 18 tipos** siempre aplicado y legible; (4) **determinismo total** (replays válidos); (5) **CERO elementos de RPG** (ningún nivel/XP/stat que crezca, en ningún código); (6) 60 fps sostenidos en el prototipo.

## Bloque 3 — Datos *(→ Arquitecto de datos)*

13. **Qué datos usa**:
    R: (a) **KitDefinition por Pokémon** (data-driven: tipo, rol, básica, habilidad Q, habilidad E, esquiva, guardia, ultimate, cooldowns, stats fijas de balance); (b) **matriz de matchup 18×18 tipos** (multiplicadores 0 / 0,5 / 1 / 2); (c) **config de arena** (orbes, timer, equipo del jefe); (d) **árbol de medallas/desbloqueos** (80 medallas, 10 regiones — M0 usa 1); (e) **roster/party del jugador** (6 slots, 3 por partido) y **save local**; (f) **replays** (secuencias de input frames).
14. **Formato / tamaño / nº de registros**:
    R: CSV/JSON → assets generados (que un diseñador pueda agregar kits sin tocar código). Lanzamiento: ~30–40 kits × 80 arenas × 10 regiones. **M0: 3 kits, 1 arena, 18 tipos** — cientos de registros, trivial.
15. **¿Son sensibles?** (PII, llamadas, personal) ¿Restricciones?
    R: **No hay PII** en M0 (offline, sin cuentas). En M2+ (online) habrá cuentas Steam: las credenciales solo viven server-side, nunca en el cliente.
16. **Conexiones a BD / APIs / fuentes externas**:
    R: **Ninguna en M0** (todo local/embedded). Futuro: Steamworks (matchmaking, overlay, cloud save) y backend propio de ranked/replays (M2+).
17. **Carga / actualización**: manual, periódico, streaming:
    R: Datos **embebidos** al build; "actualización" = parche de balance por **temporada** (tabla de kits/versioneada). M0: estático.

## Bloque 4 — Tecnología *(→ Arquitecto de software)*

18. **Stack a respetar**:
    R: **Producción (meta):** Unreal Engine 5 — C++ para el núcleo (CombatCore, netcode) + Blueprint para contenido; kits data-driven; ver `plataforma-juego-pc.md` §2. **Entregable del curso (M0):** el cliente acepta y **solicita** que el prototipo se construya sobre el **stack del equipo (Python 3 + `.venv`)** como **simulación determinista de combate** (CombatCore puro, sin motor gráfico pesado) — p. ej. headless + UI mínima de consola o terminal, lo que permita verificar **todos** los criterios del Bloque 6 (input frames, cooldowns, types, switch, captura, score, determinismo). Si el equipo prefiere otro stack para M0, que lo proponga con justificación en el plan; **no** se acepta prototipo HTML/mockup (el cliente lo rechazó explícitamente).
19. **Modelos LLM / proveedores** permitidos:
    R: **Ninguno.** El juego no es un agente LLM ni usa LLM en runtime. (Los LLM solo existen en el *process* del equipo — este curso —, nunca dentro del producto.)
20. **Integraciones / dependencias** externas:
    R: M0: **ninguna** (stdlib + pytest como máximo). M2+: Steamworks, backend de ranked.
21. **¿Testeable / reproducible?** (seed, fixtures):
    R: **Sí, por diseño: la simulación es determinista.** Mismo seed + misma secuencia de input frames → mismo resultado, verificable con fixtures (secuencias de inputs grabadas). El replay de un partido **es** la fixture. QA (7f) debe poder correr el partido completo 2 veces y dif-ear los logs.
22. **Restricciones de performance**: latencia, costo, tokens:
    R: M0: tick de simulación < **16 ms** (equivalente 60 fps); una partida completa de 5:00 simulada headless debe terminar en **< 5 s reales**; 0 dependencias de red. Producción: 60–144 fps en 1080p (plataforma §6). Sin "tokens" (no hay LLM).

## Bloque 5 — Comportamiento del agente (reflexión)

23. **¿Qué significa "reflexión" acá?**
    R: **c.s. (corresponde sin)** — el producto no es un agente LLM; no aplica reflexión de modelo. La "reflexión" del proyecto vive en el **process del equipo** (este curso: cada agente revisa su salida antes de entregar, QA valida contra Bloque 6, el Jefe consolida).
24. **Ciclos de reflexión**: ¿cuántos? ¿Tiene tope?
    R: c.s. para el producto. Para el process: 1 ciclo de auto-revisión por entrega + 1 ciclo de QA; si QA falla, vuelta a Desarrollo con los casos rotos (sin tope, hasta pasar Bloque 6).
25. **Cuando falla o no sabe**: ¿qué hace? (fallback, pedir ayuda, marcar incierto):
    R: (producto) En M0 no hay "no sabe": la simulación es determinista — si un input es inválido (p. ej. switch en cooldown), el sistema **lo descarta y lo loguea**, nunca rompe la partida. (process) Si un agente no puede resolver, escala al Jefe con el bloqueado descrito; el Jefe lo resuelve o lo consulta al cliente. **El cliente responde consultas de requisito en esta sesión.**

## Bloque 6 — Calidad y aceptación *(→ QA)* — ⛩️ **PUERTA DE "TE AVISO PARA PROBAR"**

> Todo lo que se fije acá es el criterio de aceptación: cumplido → el Jefe avisa *"listo para pruebas"*.

26. **¿Qué significa "listo" para vos?** (criterios de aceptación medibles):
    R: M0 jugables/completo cuando: (1) **todos los controles** del Bloque 1.5 funcionan (WASD, básica dirigida, Q, E, guardia, esquiva, ultimate, switch, F); (2) un **partido 3v3 completo** se puede jugar de inicio a fin y termina por KO o por score al agotar 5:00; (3) **switch** respeta cooldown 4 s + ventana vulnerable 1,5 s (daño +50% sobre el recién entrado); (4) **matriz 18×18** aplicada en todo daño; (5) **captura** funcional con probabilidad por HP/ball y entrada al roster; (6) **medalla → desbloqueo** funcional (ganar la arena desbloquea el siguiente Pokémon); (7) **determinismo**: 2 runs con la misma secuencia de inputs = logs idénticos; (8) **auditoría anti-RPG**: grep/estático sin ninguna referencia a nivel/XP/crecimiento de stats; (9) 60 fps (tick < 16 ms) sostenidos; (10) partida headless 5:00 < 5 s.
27. **Pruebas que deben pasar** antes de avisar:
    R: (a) **Unitarias:** matriz de tipos (324 combinaciones, multiplicadores correctos), fórmula de daño, cooldowns exactos, i-frames de esquiva, ventana vulnerable del switch, probabilidad de captura por HP/ball, cálculo de score (golpes/KOs/orbes), fin de partida (KO vs. time-out vs. empate→score). (b) **Escenario/e2e:** los 7 escenarios del Bloque 2.11. (c) **Determinismo:** fixture de ≥10.000 input frames → 2 runs → dif = 0. (d) **Balance:** check automático de que ningún kit estrictamente domina a otro (daño esperado por kit dentro de banda ±10%). (e) **Anti-RPG (estático):** 0 hits a `level|xp|exp|stat_growth|tree_of_moves` en código de runtime. (f) **Performance:** tick < 16 ms p99; partida 5:00 < 5 s headless.
28. **Casos de prueba / datos de ejemplo** concretos para validar:
    R: C1: Pikachu (Eléctrico) golpea a Snorlax (Normal) → ×2; Snorlax golpea a Pikachu → ×1 (Normal→Eléctrico = ×0,5… **corregir con la matriz canónica, no de memoria — la matriz 18×18 canónica va en la tabla de datos y la prueba la valida contra ella**). C2: guardia mantenida → −60% daño; guardia con timing (perfect) → devuelve 50% y corta combo. C3: switch a los 3,9 s de cooldown → **rechazado y logueado**; a los 4,1 s → aceptado; durante 1,5 s el entrado recibe +50%. C4: salvaje al 10% HP + Ultra Ball → p ≥ 0,85; al 90% HP + Poké Ball → p ≤ 0,15 (misma seed → mismo resultado). C5: KO empatado + tiempo agotado → gana por score; orbe captado suma score. C6: ultimate de Pikachu a 0% de carga → no se dispara; a 100% → dispara, se vacía y empieza a recargar. C7: fixture determinista de 10.000 frames → 2 runs → logs byte-iguales. C8: ganar la arena → medalla #1 en el save + desbloqueo visible.
29. **Umbral de éxito**:
    R: **100% de las pruebas de (27) a (f) pasando; 0 bugs críticos** (crash, KO/switch/capture/determinismo roto); **0 elementos RPG**; p99 tick < 16 ms sostenido en 3 partidas consecutivas. Sin excepciones: un fallo de determinismo o de anti-RPG = **no listo**.

## Bloque 7 — Seguridad *(→ Seguridad)*

30. **Riesgos que aplican**:
    R: **M0 (offline): riesgo mínimo** — sin red, sin cuentas, sin PII. Riesgo principal: **scope creep hacia mecánicas de RPG** (violación del brief) → mitigado por la prueba estática anti-RPG (Bloque 6.27e). **M2+ (online, fuera de alcance del curso pero registrado):** anti-cheat, validación server-side de inputs (el servidor es autoridad), rate limiting de ranked, protección de replays contra explotación de info.
31. **¿Secretos / credenciales** involucradas? ¿Cómo se manejan?
    R: **Ninguna en M0.** Regla para M2+: API keys (p. ej. Steam) **solo server-side**, jamás embebidas en el cliente; `.env` fuera del repo; nunca loguear credenciales.
32. **¿Auditoría / logs** de lo que hace: (sí / no):
    R: **Sí:** log estructurado por partida (inputs, eventos de daño/KO/switch/capture, timer, score) + **replay = log de input frames** (doble uso: feature + debugging). En M2+: auditoría server-side de ranked.
33. **Qué NO debe hacer por ningún motivo**:
    R: (1) **Nunca** implementar niveles/XP/crecimiento de stats (no negociable, verificable por prueba); (2) **nunca** pay-to-win (poder de kits fijo y balanceado — la tienda futura solo cosmética); (3) **nunca** distribuir el prototipo comercialmente con IP Pokémon sin licencia (ver Bloque 0.3) — el entregable del curso es no-comercial/IP original; (4) nunca exponer PII/credenciales (M2+); (5) nunca bypass del determinismo (rand no-sembrado en el juego).

## Bloque 8 — Equipo

34. **Confirmar mapa de roles** (ab=Jefe, 29=Desarrollador, 4e=Seguridad, 31=Arq. software, a8=Arq. datos, 7f=QA):
    R: **Confirmado.** Aclaro mi posición: **yo soy el cliente** (la sesión que emitió el brief) — respondo consultas de requisito cuando el equipo las necesite. El Jefe (ab) mantiene el sombrero de gestión.
35. **Asignaciones explícitas** que quieras forzar a un rol:
    R: **Arq. datos (a8):** modelo de datos de kits (KitDefinition) + **matriz canónica 18×18** (verificarla contra la fuente oficial, no de memoria — es la base de toda la prueba de balance) + estructura de medallas/desbloqueos + formato de fixtures. **Arq. software (31):** arquitectura de CombatCore (simulación determinista, input frames, tick loop) + esquema de netcode lockstep/rollback para M2 + plan anti-RPG por diseño. **Desarrollador (29):** implementación del M0 (controles, partido 3v3, switch, captura, medalla/desbloqueo, saves, replays). **Seguridad (4e):** revisión de la arquitectura de logs/replays + posición de anti-cheat para M2 (documento corto) + validación de la regla de IP/uso no comercial. **QA (7f):** suite completa del Bloque 6 (unitarias, escenarios, determinismo, balance, anti-RPG, performance) con fixtures propias. **Jefe (ab):** plan de trabajo, kickoff, consolidación y aviso "listo para pruebas" cuando Bloque 6 esté 100%.

## Bloque 9 — Tiempo y prioridad

36. **¿Deadline / fecha límite?**
    R: Sin deadline duro (curso). **Meta sugerida por el cliente: M0 en 4 semanas** desde el kickoff, con checkpoint a la semana 2 (partido 3v3 jugable sin captura ni medalla). Si el equipo no puede, que proponga recorte con la prioridad del punto 37.
37. **Si hay que recortar, qué es lo más importante** (prioridad):
    R: En este orden: (1) **feel del combate** (controles, esquiva con i-frames, guardia, ultimate) — si no hay feel, no hay juego; (2) **switch con coste**; (3) **matriz de tipos** (puede arrancar con 8 tipos si hace falta, pero la arquitectura debe ser 18); (4) **captura**; (5) **medalla/desbloqueo**; (6) score/orbes; (7) gamepad. **Cortar primero:** gamepad, 3.º kit (bajar a 2), orbes del mapa, 18 tipos completos. **Nunca cortar:** determinismo, anti-RPG, los controles core.
38. **¿Cada cuánto querés avances** y por qué canal?
    R: **Por hito** (no por día): avance al cerrar M0-checkpoint (sem. 2) y al pedir "listo para pruebas". Canal: el **Jefe me lo pasa a mí en esta sesión** y lo reporta al usuario. Formato: qué pasó, qué falta, riesgos — 5 líneas.

## Bloque 10 — Éxito

39. **¿Cómo sabremos que fue un éxito?** (KPI / resultado medible):
    R: (1) **100% del Bloque 6** pasando (la puerta formal); (2) **el cliente juega el M0** (teclado+mouse) y puede ganar/perder la arena y capturar un salvaje sin fricción de control; (3) GDD v2 + plataforma + **tablas de balance canónicas** versionadas en el repo; (4) (estira) un video/demo del partido 3v3 con replay reproducible.
40. **¿Qué harías vos primero** cuando esté listo? (uso real):
    R: **Jugar el M0 yo mismo** en PC: 3 partidas (ganar, perder, y time-out→score), intentar capturar un salvaje al 10% y al 90% (verificar la curva), forzar un switch en cooldown (verificar que se rechaza), correr 2 veces la fixture de determinismo y diff-ear los logs. Con eso **apruebo M1** (región Kanto: 8 arenas + liga + desbloqueos completos).

---

*Al recibir el formulario completo, el Jefe arma el plan de trabajo (asignación por agente + cronograma) y da el kickoff. Tarea 0 del kickoff: `/qantica doctor --fix` (entorno QA: httpx, playwright, pyyaml).*
