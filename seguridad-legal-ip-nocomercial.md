# VALIDACIÓN LEGAL — Regla de IP / Uso No-Comercial (PODO)

**Proyecto:** Pokémon Odisea (PODO) · M0
**Autor:** Seguridad (`4e`) · **Fecha:** 2026-10-17
**Base:** FORMULARIO Bloque 0.3 + 7.33(3) · `plataforma-juego-pc.md` ⚠️ Nota legal · PLAN §8
**Estado:** ✅ Dictamen + **cláusula en README** (creado 18-10, listo para el primer commit) + **veredicto sobre el LICENSE adoptado** (§4, 18-10): ✅ APROBADA.

> ⚖️ **Disclaimer:** esto es una validación técnica/procesual del equipo de curso, **no asesoría legal**. Para una distribución pública (aunque sea no-comercial) o cualquier paso comercial, consultar con un abogado de propiedad intelectual.

---

## 1. El hecho jurídico (sin rodeos)

- **Pokémon** (nombre, personajes, especies, arte, música, universo) es IP de **Nintendo / Game Freak / The Pokémon Company**.
- **No se otorga licencia a terceros** (la vía "licencia oficial" es, en la práctica, inexistente para un proyecto de curso).
- Por lo tanto, el entregable del curso solo puede ser:
  - **(A) No-comercial:** fan/educativo — mismos nombres/mecánicas, **cero** distribución comercial, cero monetización, sin publicación en tiendas.
  - **(B) IP original inspirada:** mismas mecánicas (control directo, party, switch con coste, captura, 18 tipos, medallas) con **nombres, arte y personajes propios** → la única vía que permite comercializar.
- **El veto (7.33-3):** nunca distribuir comercialmente el prototipo con IP Pokémon sin licencia. Es **no negociable** y aplica a **todas las rutas futuras (M2 incluido)** — si M2 quiere monetizar/publicar en Steam, antes debe estar en la vía (B).

## 2. Dictamen para el entregable del curso (M0)

| Pregunta | Dictamen |
|---|---|
| ¿M0 puede usar nombres Pokémon (Pikachu, Snorlax, Gardevoir, 18 tipos, medallas)? | **Sí, si y solo si** el entregable se mantiene **100% no-comercial** (vía A). |
| ¿Se puede publicar el repo? | **Sí** como proyecto educativo/no-comercial (GitHub/GitLab), **con la cláusula del §3 visible** y LICENSE no-comercial. |
| ¿Se puede vender/monetizar/distribuir en Steam? | **No**, con IP Pokémon. Única vía: migrar a IP original (vía B) antes de cualquier paso comercial. |
| ¿Qué pasa en M2 (online/ranked/seasons)? | M2 con IP Pokémon debe seguir siendo **no-comercial** (ranked/seasons sin pagos). **Monetización ⇒ IP original antes.** (Ver doc anti-cheat §6, "gate IP"). |
| ¿Los nombres de tipos (Fuego, Eléctrico…) son un problema? | Nombres genéricos de tipos son de riesgo bajo, pero **el conjunto** (especies + tipos + Poké Ball + medallas + regiones como "Kanto/Johto") es lo que identifica la IP. En la vía B, se renombran especies/regiones/balls; las **mecánicas** (que son ideas, no expresión) pueden mantenerse. |

**Recomendación del equipo (y del PM/cliente):** M0 se entrega por la **vía A (no-comercial)**, que es la que permite usar el roster de los 3 kits tal cual. La vía B se diseña como **punto de migración documentado** para M2+, no como trabajo de la semana 1.

## 3. Cláusula para el README (draft — pegar tal cual en el README del repo)

```markdown
## Uso y propiedad intelectual (LEER)

Este proyecto es un **entregable de curso, 100% no-comercial y educativo**.

- **Pokémon** es propiedad de **Nintendo / Game Freak / The Pokémon Company**.
  Este trabajo es un **proyecto fan/educativo sin ningún vínculo ni aval** de esas
  compañías. **No se distribuye comercialmente y no se monetiza** de ninguna forma.
- Si este código/diseño se reutiliza con fines comerciales, el responsable debe
  migrar a **IP original** (nombres, personajes, arte y regiones propios) antes de
  cualquier distribución o venta. Las mecánicas pueden conservarse; la expresión
  (nombres/especies/arte) no.
- Restricciones detalladas: ver `LICENSE`.
```

## 4. LICENSE (draft — archivo `LICENSE` del repo)

Licencia corta y legible (alternativa estándar para los docs de diseño: **CC BY-NC 4.0**; para el repo completo en curso, este texto propio es más claro):

```text
PODO — Pokémon Odisea · Licencia de uso (no-comercial / educativo)
Copyright (c) 2026 — equipo del curso "reflexion-agente"

1. ALCANCE Y NATURALEZA
   Este repositorio contiene un entregable de curso (diseño, simulación
   determinista, prototipo M0) con fines estrictamente EDUCATIVOS y NO-COMERCIALES.

2. PERMISOS (solo bajo esta licencia)
   Puedes usar, estudiar, copiar, modificar y compartir este trabajo:
     - con fines educativos, de investigación o de demostración no comercial;
     - citando la procedencia (nombre del curso/proyecto).

3. PROHIBICIONES
   a) Prohibida toda comercialización, venta, suscripción, publicidad,
      monetización por streaming/contenido o explotación económica de este
      trabajo o de derivados con IP Pokémon.
   b) Prohibida la distribución con IP de terceros sin licencia del titular.
      "Pokémon" es IP de Nintendo / Game Freak / The Pokémon Company; este
      proyecto NO tiene vínculo, aval ni licencia de esas compañías.
   c) Prohibido retirar o alterar esta licencia.

4. VIA DE MIGRACIÓN A IP ORIGINAL (única vía comercial)
   Quien quiera usar las MECÁNICAS de este trabajo con fines comerciales debe
   reemplazar TODA la expresión (nombres, especies, personajes, arte, nombres
   de regiones, ítems) por contenido propio, y no puede usar los nombres
   "Pokémon", las especies ni el universo de la franquicia. Las ideas y
   mecánicas (control directo, party, switch con coste, captura, matchup de
   tipos, medallas como desbloqueo) no son objeto de esta licencia.

5. EXENCIÓN DE RESPONSABILIDAD
   Se entrega "COMO ESTÁ", sin garantías de ningún tipo. El autor no se hace
   responsable de daños por su uso. Ante el conflicto entre esta licencia y la
   ley de propiedad intelectual de los titulares de la IP referida, prevalece
   la ley y los derechos de los titulares.

6. RESERVA
   Cualquier uso no cubierto por esta licencia requiere permiso escrito
   expreso del equipo autor y, de aplicarse, de los titulares de la IP.
```

> **⚖️ Veredicto final (18-10):** el equipo adoptó una versión más corta para el repo — `LICENSE` (draft de `a8`, aprobada por `ab`) basada en **CC BY-NC 4.0** + aviso de IP de terceros + exclusiones de secretos/PII/runtime + sin garantía. **Seguridad la validó: ✅ APROBADA** — cubre los 4 puntos no negociables: (1) no-comercial explícito, (2) aviso de que la IP es de Nintendo/Creatures/GAME FREAK y el proyecto no reclama derechos ni está avalado, (3) requisito de migración a IP original antes de cualquier uso comercial, (4) exclusión de credenciales/PII/artefactos.
> **Nota no bloqueante:** CC BY-NC está diseñada para obras creativas, no para software; si la vía B (IP original + comercialización) se concreta, el **código** debe relicenciarse a una licencia de software (MIT/Apache) y esta licencia queda para el contenido creativo. El draft de esta sección queda como antecedente.

## 5. Checklist de verificación (gate — aplicar antes de cada publicación)

- [ ] README trae la cláusula del §3 (texto visible, no solo en LICENSE).
- [x] `LICENSE` en la raíz del repo — versión adoptada (18-10): CC BY-NC 4.0 + aviso de IP (draft `a8`, aprobada por `ab`); veredicto Seguridad ✅ en §4. (El draft propio de §4 queda como antecedente.)
- [ ] **Cero** texto de "venta/pago/Steam comercial/monetización" en README, GDD o docs del repo (si aparece, debe ir explicitado como "solo con IP original").
- [ ] Meta descripciones (GitHub/GitLab) dicen "proyecto educativo no-comercial".
- [ ] Antes de M2/online: re-verificar que el diseño de ranked/seasons **no incluye pagos** mientras la IP siga siendo Pokémon (gate del doc anti-cheat §6).
- [ ] Si alguna vez se migra a IP original: actualizar README/LICENCE (quitar la referencia a la vía A) y registrar el cambio de decisión en el plan.
