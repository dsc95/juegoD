# PODO — Pokémon Odisea · *World Tour Arena*

**Entregable del curso "reflexion-agente" — M0: vertical slice jugable del combate 3v3 en tiempo real.**

Juego de acción para PC (**NO es RPG**): control directo de tu Pokémon en arenas 3v3 (5:00, gana por KO o por score), con party de 6 (3 por partido), switch en caliente con coste, captura y medallas como desbloqueo. M0 = **simulación determinista en Python** (CombatCore headless + adapter TTY): 1 arena, 3 kits, 100% offline.

## Estado

- **Fase actual:** M0 — Semana 2 (kickoff 2026-10-17; engine 3v3 + replays `podo.replay` v1 entregados en `podo/`)
- **Puerta de aceptación:** Bloque 6 de `FORMULARIO-PROYECTO.md` (10 criterios + vetos absolutos de determinismo y anti-RPG)

## Documentos (fuente de verdad)

| Doc | Qué es |
|---|---|
| `FORMULARIO-PROYECTO.md` | Brief del cliente, 40/40 (rige) |
| `PLAN-DE-TRABAJO-M0.md` | Plan por agente + cronograma + restricciones no negociables |
| `diseño-pokemon-odisea.md` | GDD v2 (acción, sin RPG) |
| `plataforma-juego-pc.md` | Plataforma técnica (motor, netcode, roadmap) |
| `estudio-pokemon-nintendo.md` | Estudio de la franquicia (contexto de dominio) |
| `seguridad-review-logs-replays.md` | Requisitos de seguridad de logs/replays — `4e` |
| `seguridad-anticheat-m2.md` | Posición anti-cheat M2 — `4e` |
| `seguridad-legal-ip-nocomercial.md` | Validación legal IP / uso no-comercial — `4e` |

## Reglas duras del repo

- **Nada sensible**: sin credenciales, PII ni artefactos de runtime (ver `.gitignore`).
- **M0 offline**: sin red, sin LLM en runtime, sin RNG sin semilla.
- **Veto anti-RPG**: cero niveles/XP/crecimiento de stats (prueba estática, Bloque 6.27e).

## Uso y propiedad intelectual (LEER)

- Este proyecto es un **entregable de curso, 100% no-comercial y educativo**.
- **Pokémon** es propiedad de **Nintendo / Creatures Inc. / GAME FREAK / The Pokémon Company**. Este trabajo es un proyecto fan/educativo **sin vínculo ni aval** de esas compañías y **no reclama derechos** sobre esa IP.
- La obra se publica bajo **CC BY-NC 4.0** (ver `LICENSE`): se permite usar y compartir **solo sin fines comerciales**, con atribución.
- Quien reutilice el trabajo con fines comerciales debe migrar **antes** a **IP original** (nombres, especies, arte y regiones propios). Las mecánicas pueden conservarse; la expresión (nombres/especies/arte) no.
