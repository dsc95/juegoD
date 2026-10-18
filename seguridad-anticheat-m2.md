# ANTI-CHEAT M2 — Posición de Seguridad (doc corto)

**Proyecto:** Pokémon Odisea (PODO) · **Autor:** Seguridad (`4e`) · **Fecha:** 2026-10-17
**Alcance:** M2 (online 1v1/3v3 + ranked + replays). M0 es offline: **no se implementa nada aquí en M0**; esto fija la posición para que M2 no rediseñe la sim ni el formato de log.

---

## 1. Principio rector

> **El servidor es la autoridad.** El cliente es un dispositivo de entrada + presentación.

Todo resultado (daño, KO, switch, captura, score, timer) lo decide **la sim determinista corriendo en el servidor**. El cliente **solo envía input frames** (los mismos de M0: el replay ya es el wire format). El servidor re-simula y todo estado que no derive de inputs válidos + sim autoritativa **no existe**.

Definición operativa de cheat: *cualquier resultado observable que no sea derivable de inputs válidos + la sim server-side.*

## 2. Validación server-side de inputs

1. **Whitelist de acciones** (move, básica, Q, E, guardia, esquiva, ultimate, switch, ball). Input inválido → **rechazar + loguear**, nunca romper la partida (mismo criterio que M0, Bloque 5.25).
2. **Reglas de juego aplicadas server-side**: switch en cooldown rechazado (4 s + ventana 1,5 s); ultimate solo al 100% de carga; captura solo con la probabilidad HP/ball **resuelta server-side**.
3. **Densidad/ritmo de inputs**: máx. 1 input frame por tick por jugador; exceso → drop + flag heurístico (no baneo automático; baneo = proceso con evidencia, no automático).
4. **Integridad de secuencia**: cada frame lleva `tick_index`, `player_slot`, `seq`. Out-of-order/duplicados fuera de la ventana de rollback → descartados.
5. **Estado = función(inputs, seed)**: el validador re-ejecuta la sim y compara estado de cliente vs. servidor; divergencia → marca de sospecha + grabación de evidencia (input frames + estado), nunca acción inmediata sin evidencia.
6. **Rate limiting de ranked/matchmaking** en el backend (ya previsto en Bloque 7.30), independiente del anti-cheat de partida.

## 3. Credenciales (Steamworks): solo server-side

- **Server keys de Steam (matchmaking, cloud save, leaderboard, overlays) NUNCA embebidas en el cliente.** Viven en el backend (regla dura, Bloque 7.31).
- El cliente se autentica **contra Steam** (Steam maneja el token del usuario); el backend valida la sesión server-side. El cliente jamás ve la server key.
- `.env`/secretos **fuera del repo** desde el día 1 (ver hallazgo H1 en `seguridad-review-logs-replays.md`: el workspace ya tiene un `.env` legado con key viva).
- **Nunca loguear credenciales**, tampoco en los logs de auditoría server-side de ranked (que reutilizan el formato de log de M0 → debe seguir siendo limpio por diseño).

## 4. Protección de replays

- El replay (log de input frames) en M2 es **evidencia de auditoría server-side**: inmutable, con `config_hash` + seed + firma de la partida.
- **No es canal de exfiltración**: el replay no contiene datos de cuenta/identidad/secretos (R1–R2 de la review de logs, heredados de M0).
- **No es vector de ataque**: un replay no puede "injetar" estado — al reproducirse solo acepta input frames y re-simula; cualquier campo de estado dentro de un replay es ignorado por el re-simulador.
- Distribución pública de replays (feature): solo se publica la **proyección pública** (inputs + metadata mínima), no los logs completos de auditoría.
- **Integridad**: hash del log + firma del servidor de la partida; un replay modificado no reproduce ni se acepta como evidencia.

## 5. RNG/seed en online

- **Seed de partida generada y custodiada server-side**; el cliente la recibe (para predecir visuals) pero no la elige.
- **Captura, drops, spawns: resolución server-side con la seed de la partida** (nunca RNG de cliente).
- La seed **no codifica ni deriva de secretos del servidor** (regla R3 de la review de logs, extendida a M2) y no se usa como oráculo de nada sensible.

## 6. Gate IP / no-comercial (mi ángulo — riesgo Bloque 7.30)

M2 es donde crece el riesgo legal (online ⇒ tentación de monetizar). Regla de hierro:

1. **Mientras la IP sea Pokémon, M2 es no-comercial**: ranked/seasons/replays OK, **cero pagos** (ni skins vendidas, ni battle pass, ni nada). La tienda cosmética del diseño solo existe en la vía de IP original.
2. **Monetización ⇒ IP original antes** (migración documentada: especies/regiones/nombres propios; mecánicas se conservan). Ver `seguridad-legal-ip-nocomercial.md` §2 y checklist §5.
3. Este gate se verifica **en la review de diseño de M2** (no ahora): cualquier campo de pago/monetización en el diseño de ranked/seasons con IP Pokémon = **no aprobado por Seguridad**.
4. Scope creep RPG (veto absoluto, Bloque 6): M2 no reintroduce nivel/XP/crecimiento vía "seasons" ni "recompensas de rank" que modifiquen stats (los ranks miden skill; las recompensas son roster/cosmético, **nunca** stats que crecen). La prueba estática anti-RPG de QA se extiende al código de M2.

## 7. Lo que M0 debe dejar listo (handoff)

- [ ] Input frames atómicos y serializables (ya son el replay).
- [ ] Formato de log versionado con `config_hash` + seed (review de logs, R3/R5).
- [ ] Determinismo probado (Bloque 6.27c) — es la base de lockstep/rollback y del validador server-side.
- [ ] Log libre de PII/secretos (R1/R2) — M2 lo hereda como log de auditoría.
- [ ] `.gitignore` con `.env`/replays/saves desde el primer commit (H1).

> Si M0 cierra con esto, M2 agrega transporte + validación sin tocar sim ni formato.
