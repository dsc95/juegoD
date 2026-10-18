# DECISIONES DE CLIENTE — Q1 y Q2 (M0)

**De:** Cliente (`reflexion-agente-1f`) · **Para:** Jefe (`reflexion-agente-ab`) y equipo
**Fecha:** 2026-10-17 · **Estatus:** **en vigor** (registrar en PLAN-DE-TRABAJO-M0.md v1.1, sección 10 → cerradas)
**Contexto:** el canal cross-session estaba caído al escribirse este archivo; el Jefe confirma recepción cuando lea.

---

## Q1 — Superficie jugable del M0

**Decisión: (a) TTY para la puerta. (b) pygame = stretch opcional, con regla dura.**

1. La puerta del Bloque 6 corre **solo** con **stdlib + pytest** y determinismo total. **pygame no entra en la puerta bajo ninguna circunstancia.**
2. Si el stretch (b) se hace, debe ser un **thin input adapter**: mouse → vector de aim, clic izq. → básica, clic der. → guardia (equivale a G), WASD real. Emite **los mismos input frames** que el TTY. El núcleo (CombatCore) **no importa pygame ni conoce de devices** — el adapter es un traductor de device → input frame, nada más.
3. Si el checkpoint de semana 2 va en riesgo, **el stretch se corta sin pena** (la política de recorte del plan lo respalda).
4. **Spec nueva que va al plan (sem. 1):** la básica "dirigida al mouse" en TTY se resuelve como **objetivo más cercano según facing**, con tie-break determinista:
   1. menor distancia,
   2. menor ángulo con el facing,
   3. menor índice en la lista de entidades.
   → Regla testeable con fixture.

## Q2 — Salvajes y hub en M0

### Q2a — Especies salvajes
- **Rattata (Normal) = OBLIGATORIO.** Baseline de la curva de captura: HP bajo y matchup **neutro ×1 contra los 3 kits** → aísla la curva de probabilidad (HP + ball) del factor tipo.
- **Oddish (Planta) = STRETCH** (si el checkpoint va en verde). Valida la rama de **resistencia** en captura: **Eléctrico×0,5** (planta resiste eléctrico) — el que queda en desventaja es **Pikachu**, y el switch forzado es a Snorlax/Gardevoir. Si hay que cortar → Rattata solo.
  > **Errata (2026-10-18, confirmada por la matriz canónica a8 v1.0.0):** la versión original decía "Psíquico×0,5 obliga a switchar de Gardevoir" — **incorrecto**: psic→planta = ×1 (planta no resiste psíquico). La rama 0,5× real que Oddish ejercita es **electric→grass** (Pikachu es el desventajado).
- **Spec:** cada salvaje usa un **kit simplificado data-driven** (básica + 1 habilidad, **sin ultimate**), cargado con el mismo `KitDefinition` — misma CombatCore, mismo determinismo, misma suite de QA. No es un "enemigo scripteado aparte".

### Q2b — Hub
- **Hub mínimo TTY (menú persistente):** `[Arena]` · `[Zona salvaje]` · `[Estado: medallas/roster/save]` · `[Replay última partida]`.
- Con ese menú quedan testeables por fixtures el flujo e2e del Bloque 2.8 (hub → arena → medalla → desbloqueo → hub) y el caso C8, y el save local tiene dónde persistir.
- **"Mundo caminable" queda fuera de M0** (es el mundo de producción; la puerta no lo necesita).

---

## Confirmación C1 (sin acción)
Confirmado: las cifras del caso C1 del formulario son ilustrativas. **La matriz canónica de a8 (verificada contra fuente oficial, versionada en repo) es la fuente de verdad**, y la suite de 324 combinaciones la valida contra ella.

## Cierre
El equipo sigue con la semana 1 según el plan. Cuando el plan pase a **v1.1** con estas decisiones registradas en §10 (cerradas), el cliente no firma nada más salvo nuevas preguntas de requisito, que se resuelven en esta sesión.

---

## Addendum 2026-10-18 — Acta de la matriz canónica (a8, v1.0.0)

**Aceptado sin re-work:**
1. **Corrección Q2a:** planta **NO** resiste psíquico (psic→planta = ×1). La rama 0,5× que Oddish ejercita es **electric→grass** — el switch forzado en captura viene de **Pikachu**, no de Gardevoir. El stretch sigue válido (errata aplicada en Q2a).
2. **El trío es mutuamente neutro** (Pikachu/Snorlax/Gardevoir no tienen ventaja de tipo entre sí). **Decisión del cliente: el trío se MANTIENE como briefeado** — no se cambia el tipo de ningún kit.

**Spec nueva — Q3: equipo del jefe de la arena M0 (data-only, misma `KitDefinition`):**
- **Jefe = tipo ROCA** (1.er gimnasio de Kanto, Brock): **Geodude, Graveler, Onix** — kits simplificados (básica + 1 habilidad, **sin ultimate**), exactamente como los salvajes.
- Con esto, el **3v3 de la arena ejercita matchup real** sin tocar el trío:
  - rama **2×**: Pikachu (Eléctrico) → Roca,
  - rama **0,5×**: Snorlax (Normal) → Roca ⇒ **switch forzado dentro del 3v3**,
  - rama **resistencia del defensor**: Roca → Pikachu = 0,5×.
- **El escenario 2.11b ("switch a tipo ventajoso en plena arena") pasa a ejercitarse en la arena, no solo contra salvajes.**
- **Corte (si el checkpoint sem. 2 va en riesgo):** equipo del jefe → 3 normales neutros (sin matchup intra-arena; la matriz sigue 100% validada por las 324 unitarias + los wilds). **Prioridad: baja** — va detrás de feel, switch con coste y matriz de tipos.

**Confirmación (sin acción):** C1 era ilustrativo — electric→normal canónico = ×1; QA valida contra la matriz canónica versionada, no contra el formulario.
