# POKÉMON ODISEA — Plataforma de Juego (Técnica + Servicio)  ·  PC

> Documento de **plataforma y arquitectura** · 17-10-2026
> Acompaña a `diseño-pokemon-odisea.md` (v2: acción, sin RPG, PC).
> Objetivo: definir **con qué se construye, cómo se estructura, cómo se despliega y opera en línea**.

> ⚠️ **Nota legal (importante):** *Pokémon* es propiedad de **Nintendo / Game Freak / The
> Pokémon Company**. Un juego con el nombre, personajes y arte de Pokémon **no puede
> distribuirse comercialmente sin licencia** (que no se otorga a terceros). Para una
> producción real hay 3 caminos:
> 1. **Licencia oficial** (solo con acuerdo con TPC — muy improbable para un estudio independiente).
> 2. **Proyecto fan / no comercial** (sin distribución pública ni monetización).
> 3. **IP original inspirada** (mismas mecánicas, pero con nombres/arte propios) → la única
>    vía real para un producto vendible.
> Esta plataforma aplica igual en los 3 casos (el "motor" no depende de la marca).

---

## 1. Decisión de motor (el corazón de la plataforma)

### Recomendación principal: **Unreal Engine 5 (UE5)**
**Por qué UE5 para ESTE juego:**
- **Render de alta fidelidad** (Nanite + Lumen) para 10 regiones mundiales con biomas distintos.
- **C++ para el núcleo** (combate, netcode, balance) + **Blueprint** para contenido/nivel → prototipar rápido y optimizar donde duele.
- **Ecosistema de acción competitiva maduro** (sistemas de animación, hitbox, VFX, cámara).
- **Streaming de mundo** para regiones grandes sin cargar todo.
- Herramientas de **dedicated server**, **replays** y **espectador** más integradas.

### Alternativas (según tamaño de equipo)

| Motor | Ideal si… | Trade-off |
|-------|-----------|-----------|
| **Unreal Engine 5** | Buscas el producto final pulido, con equipo medio/grande | Curva de C++ alta, engine pesado |
| **Unity (URP/HDRP)** | Equipo más pequeño, quieres iterar rápido en C# | Render y herramientas competitivas un paso por debajo de UE5 |
| **Godot 4** | Equipo indie / presupuesto mínimo, quieres 100% free sin royalties | Techo de fidelidad 3D y netcode competitivo más bajo |
| **Motor propio (C++)** | Control total absoluto | Costo enorme, solo si ya lo tenés |

> **Mi elección decisiva:** **UE5** como meta de calidad; **Unity** si el equipo es < ~10
> personas. El **netcode es el cuello de botella real** y es **a-medida en cualquier motor**.

---

## 2. Arquitectura del proyecto (módulos)

```
/PokemonOdisea
├─ /Source (C++ — núcleo)
│  ├─ CombatCore/        Simulación determinista: hitboxes, daño, matrix de tipos, i-frames, perfect guard
│  ├─ Netcode/           Lockstep determinista / rollback, replicación, server authority, replays
│  ├─ PartySystem/       Party de 6, 3 por partido, switch con cooldown + ventana vulnerable
│  ├─ CaptureSystem/     Spawn salvaje, probabilidad por HP/ball, roster
│  ├─ Progression/       SIN niveles: medallas → desbloqueos (Pokémon, regiones, modos)
│  └─ WorldRegions/      Streaming de las 10 regiones, 80 arenas, hub map
├─ /Content
│  ├─ /Pokemon           Por Pokémon: mesh, animaciones, VFX + KitDefinition (data-driven)
│  ├─ /Regions           Kanto, Johto, Hoenn, … (niveles)
│  ├─ /UI                HUD (party, cooldowns, score, timer), menús, mapas
│  └─ /Audio
├─ /Config              Tablas de balance (CSV→generado): matrix de 18 tipos, kits, arenas, matchmaking
├─ /Tools               Autor de kits (GUI), importador de spreadsheet de balance
└─ /Servers             Dedicated server, servicio de replays, backend de ranked
```

### 2.1 Sistema de "Kits" (data-driven — clave)
- Cada Pokémon = **un asset de datos** (`KitDefinition`): tipo, rol, básica, habilidad ofensiva,
  habilidad defensiva, esquiva, guardia, **Ultimate**, cooldowns, balance.
- **Los diseñadores agregan Pokémon sin tocar código** (spreadsheet → generador).
- Esto hace viable un roster grande y **rebalanceable por temporada**.

### 2.2 Núcleo determinista (decide el netcode)
- La simulación de combate (físicas de hitbox, daño, cooldowns) corre **determinista**:
  mismas entradas → mismo resultado. Esto habilita **lockstep**, **replays** y **espectador**.
- Input del jugador (move, básica, Q, E, guard, dodge, ultimate, switch, ball) se serializa como un **input frame**.

---

## 3. Netcode y online (lo más difícil)

| Sistema | Enfoque |
|---------|---------|
| **PvP competitivo (1v1, 2v2, 3v3)** | **Lockstep determinista** (estilo UNITE) para fairness 5v5/3v3; **rollback** para 1v1 más responsivo |
| **Server authority** | Servidor dedicado valida ranked (anti-cheat, anti-exploit) |
| **Matchmaking** | Steam matchmaking (Steamworks) + ranking ELO/Glicko |
| **Espectador + replays** | Determinismo = replays baratos (guardar input frames); overlay de espectador |
| **Anti-cheat** | Easy Anti-Cheat / BattlEye + validación server-side + heurísticas de input |
| **Modo LAN/offline** | Campaña (medallas/torneos offline) sin red |

> El **switch en caliente** y la **captura** en línea requieren reglas claras de input/replicación
> (ventana vulnerable, orden de KO) — se define en `CombatCore` y se valida en el servidor.

---

## 4. Plataforma de servicio (live-ops / "game service")

- **Cuentas**: Steam (primario) + cuentas propias opcionales para ranked/cosméticos.
- **Estaciones (seasons)**: ciclos de ~3 meses con ranks (Bronce → Gran Maestro), recompensas exclusivas de roster y cosméticos.
- **Live-ops**: eventos temporales (Battle Royale, co-op vs. legendario), parches de balance por kit, temporadas de regiones.
- **Backend**: servicio de ranked/leaderboards, replays, eventos, telemetría (balance real en vivo).
- **Tienda/cosméticos**: skins y efectos (sin pay-to-win — el poder de los kits es fijo por diseño).
  > **⚖️ Legal (nota 4e, 2026-10-18):** la vía comercial (tienda incluida) es **solo con IP original** — con IP Pokémon no existe vía comercial (sin licencia de TPC). Ver §1, nota legal.

---

## 5. Pipeline de assets (el costo real de arte)
- **Por Pokémon**: modelado, rigging, y **animaciones de combate** (básica, habilidad 1, habilidad 2, esquiva, guardia, KO, **Ultimate**). Esto es el mayor costo de producción.
- **Regiones**: arte de entorno de 10 mundos (biomas, arenas, hubs).
- **Herramientas**: Blender (gratis) o Maya; ZBrush para escultas; import DCC → UE5.
- **VFX/audio**: hit-stop, screen-shake, efectos por tipo, banda sonora.

---

## 6. PC: objetivos técnicos y despliegue
- **Windows 10/11** (Steam primario; GOG/Epic opcional). Port a Mac/Linux después.
- **60–144 fps** objetivo; 1080p mínimo; DLSS/FSR/XeSS.
- Requisitos base accesibles (competitivo en monitores 144 Hz).
- **Steamworks**: matchmaking, overlay, logros, cloud save, beta privada/pública, Steam Cloud.
- **Dedicados**: servidores públicos para ranked + servidores de torneo.

---

## 7. Equipo y tiempo (realidad de producción)
**Equipo mínimo para un producto completo (10 regiones):** ~15–40 personas.
- Programadores 2–4 (combate, netcode, sistemas)
- Diseñadores de mundo/nivel 2–3
- Artistas 4–8 (personajes, entorno, VFX) ← el roster es el gasto grande
- Animadores 1–2 (animaciones de combate por Pokémon)
- Audio 1 · QA 1–2 · Producción/Diseño 1–2

**Tiempo:**
- **Vertical slice** (1 arena, 3 Pokémon, feel de combate): **3–4 meses**
- **1 región completa** (Kanto, 8 arenas) jugable: **~9–12 meses**
- **Lanzamiento 3 regiones + online**: **~18–24 meses**
- **10 regiones completas**: **3–5 años**

**Presupuesto (orientativo, estudio occidental/latam):**
- Indie serio (3 regiones, ~40 kits): **~$1–4 M USD**
- Titulo completo 10 regiones: **$10–30 M USD** (o más)

---

## 8. Roadmap de plataforma
| Hito | Contenido | Meta |
|------|-----------|------|
| **M0 — Vertical slice** | 1 arena + 3 kits + combate (básica/Q/E/guard/esquiva/Ult/switch) | Sentir el *feel* |
| **M1 — 1 región** | Kanto completo (8 arenas + liga) offline | Bucle de medallas |
| **M2 — Online** | 1v1/3v3 + ranked + captura + replays | Servicio en línea |
| **M3 — Beta 3 regiones** | Kanto+Johto+Hoenn, seasons, live-ops | Beta pública Steam |
| **M4 — Lanzamiento** | 3 regiones pulido, tienda cosmética | Lanzamiento |
| **Estaciones** | Resto de 7 regiones + formas Mega + nuevos modos | Live-ops continuo |

---

## 9. Riesgos técnicos (y mitigación)
1. **Netcode determinista + switch/captura en línea** → prototipar M0/M2 temprano; servidor authority.
2. **Balance de 40+ kits en tiempo real** → data-driven + spreadsheet + telemetría de live-ops para re-balancear.
3. **Costo de animación por Pokémon** → priorizar ~40 kits al launch; el resto por estaciones.
4. **Streaming de 10 regiones** → UE5 World Partition; lanzar con 3 regiones.
5. **Scope** → el launch es 3 regiones; el mundo completo es el plan de estaciones.

---

## 10. Resumen de la plataforma
- **Motor:** **Unreal Engine 5** (C++ núcleo + Blueprint contenido). Alternativa: **Unity** si equipo chico.
- **Núcleo:** simulación **determinista** (habilita lockstep, replays, espectador).
- **Kits:** **data-driven** (agregás Pokémon sin código; balance por temporada).
- **Online:** Steam (matchmaking/overlay), ranked con **server authority** + anti-cheat, seasons.
- **Despliegue:** **Windows/Steam**, 60–144 fps, servidores dedicados.
- **Producción:** equipo 15–40, 18–24 meses para 3 regiones, $1–4 M (indie) o más.
- **Legal:** necesita **licencia de TPC** o ser **fan/no-comercial** o **IP original** para ser vendible.
