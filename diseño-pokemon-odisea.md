# POKÉMON ODISEA — *World Tour Arena*  ·  **v2 (PC · Acción, NO RPG)**

> **Documento de diseño (GDD)** · 17-10-2026
> Género: **Acción / Arena (combate en tiempo real, control directo)** — **sin elementos de RPG**
> Plataforma: **PC (Windows, Steam)** · teclado+mouse y gamepad
> Tagline: *"Recorré las 10 regiones. Ganá cada medalla. Controlá a tu Pokémon."*

---

## 0. Cambios de v1 → v2 (lo que pediste)

| v1 (anterior) | **v2 (esta)** |
|---------------|---------------|
| "Action-RPG" | **Juego de acción / arena puro** |
| Niveles, XP, stats, árbol de movimientos | **CERO crecimiento de personaje**: todos los Pokémon nacen con el mismo poder (como en un *fighter*) |
| Cuadros de diálogo, quests, historia RPG | **Cero narrativa pesada**: solo el marco de un "World Tour" (gira mundial) |
| Nintendo Switch 2 | **PC: Windows (Steam)**, teclado+mouse y gamepad |
| Progresión = tu personaje subía | **Progresión = DESBLOQUEOS**: nuevos Pokémon, nuevas regiones, nuevos modos |

> **Definición de "no RPG" aplicada al diseño:**
> No hay niveles, ni XP, ni stats que suban, ni equipo, ni quests con diálogo.
> El poder del jugador = **su habilidad + el kit que eligió + el equipo (3 de su party)**.
> La progresión es **colección y desbloqueos** (roster de Pokémon, regiones, modos, torneos).

---

## 1. El pitch en una frase
> Un **juego de acción para PC** donde recorres **todas las regiones de Pokémon** por un mapa mundial, pasás **8 arenas (medallas) por región** subiendo hasta el **campeonato regional**, y cada combate es **en tiempo real controlando directamente a tu Pokémon** (ataques, defensas y un "Ultimate" estilo UNITE), con las **reglas de la serie**: party de 6, cambio en plena batalla y captura.

**Fusión:**
| De dónde viene | Qué aporta |
|----------------|-----------|
| **Pokémon UNITE** | El sistema de combate: básica + habilidad + esquiva + guardia + **Ultimate**, arena con objetivos y score |
| **La serie (anime)** | Party de 6, **switch en caliente**, **captura**, rival |
| **Pokémon Stadium / ligas** | Estructura de gimnasios → medallas → élite → campeón |
| **Fighters / Brawlhalla** | **Sin niveles**: roster de personajes balanceados, tu skill decide |
| **Todos los mundos** | Kanto → Johto → Hoenn → Sinnoh → Unova → Kalos → Alola → Galar → Paldea → Lumiose |

---

## 2. Pilares de diseño
1. **Tú ERES el Pokémon.** Corres, esquivás, guardás y atacás con mouse/teclado o gamepad.
2. **Sin niveles.** Ningún Pokémon es "mejor" por crecer: el poder es fijo; gana el **juego del jugador** (kit, matchup de tipos, timing).
3. **Progresión por desbloqueos.** Cada medalla = un Pokémon nuevo o una región nueva. El tour es el progreso.
4. **Reglas de la serie.** Party de 6, switch en caliente, captura (capturar = sumar un luchador a tu roster).
5. **PC competitivo.** 60–144 fps, precisión de mouse, ranked online, espectador, replays, esports.

---

## 3. Estructura del juego: el WORLD TOUR

### 3.1 Mapa mundial (hub)
- **10 regiones** en un mapa-mundo; viajás por tierra/transporte entre regiones (sin carga larga, estilo hub).
- Cada región = **8 arenas (gimnasios) en orden + 1 Arena de Campeonato**.
- Al fondo de cada región: **Élite 4 + Campeón** → **título regional** → desbloqueás la **región siguiente**.

| Región | Gimnasios (tipos) | Recompensa al finalizar |
|--------|-------------------|--------------------------|
| **Kanto** | Fuego, Eléctrico, Hielo, Planta, Lucha, Roca, Fantasma, Dragón | Título Kanto + desbloqueo Johto |
| **Johto** | Planta, Roca, Eléctrico, Fantasma, Psíquico, Volador, Siniestro, Acero | Título Johto + desbloqueo Hoenn |
| **Hoenn** | Eléctrico, Lucha, Planta, Hielo, Psíquico, Fuego, Acero, Siniestro | Título Hoenn + desbloqueo Sinnoh |
| **Sinnoh** | Planta, Hielo, Fuego, Fantasma, Lucha, Acero, Psíquico, Normal | Título Sinnoh + desbloqueo Unova |
| **Unova** | Eléctrico, Roca, Planta, Volador, Fantasma, Fuego, Psíquico, Dragón | Título Unova + desbloqueo Kalos |
| **Kalos** | Fuego, Agua, Planta, Psíquico, Fantasma, Lucha, Dragón, Acero | Título Kalos + desbloqueo Alola |
| **Alola** | Planta, Hielo, Acero, Lucha, Psíquico, Fantasma, Fuego, Volador | Título Alola + desbloqueo Galar |
| **Galar** | Volador, Lucha, Hada, Fantasma, Roca, Psíquico, Planta, Siniestro | Título Galar + desbloqueo Paldea |
| **Paldea** | Planta, Hielo, Fuego, Fantasma, Psíquico, Eléctrico, Acero, Dragón | Título Paldea + desbloqueo Lumiose |
| **Lumiose (Z-A)** | (región final) | **Campeonato Mundial** |

> **Total: 80 medallas + 10 títulos.** Sin "niveles": cada medalla paga **un desbloqueo concreto** (Pokémon, modo, arena, cosmético).

### 3.2 Qué es una "arena" (gimnasio) — sin RPG
- Un **desafío de combate 3v3** contra el campeón de esa arena (un "jefe" con su estilo).
- **No hay diálogo largo ni quest**: una intro de 5 segundos (bandera, tipo, arena) y a pelear.
- **Ganás → medalla + desbloqueo.** Perder → reintentar cuando quieras (sin "necesito subir de nivel").
- Dificultad escalada por **el kit y la estrategia del jefe**, no por stats.

### 3.3 Torneos (la capa competitiva)
1. **Campeonato Regional** (tras las 8 medallas): bracket contra entrenadores de la región (Élite 4 + Campeón).
2. **Ranked online (Steam)**: 1v1 / 2v2 / 3v3 con matchmaking; **estaciones** de 3 meses con ranks (Bronce → Gran Maestro) y recompensas exclusivas de roster.
3. **Eventos temporales**: *Battle Royale* (arena gigante multi-entrenador), **co-op vs. Pokémon legendario** (2–4 jugadores).
4. **Campeonato Mundial** (endgame): el bracket final contra lo mejor de las 10 regiones + tu rival.

---

## 4. Sistema de combate (el corazón) — control directo, estilo UNITE

### 4.1 Controles **PC** (teclado + mouse)
| Tecla | Acción |
|-------|--------|
| **WASD** | Mover al Pokémon (8 direcciones, arena libre) |
| **Clic izq.** | **Ataque básico** (combo de 2–3, dirigido al mouse) |
| **Q** | **Habilidad 1 — Ofensiva** (aimada, cooldown ~6–10 s) |
| **E** | **Habilidad 2 — Defensiva / Útil** (cooldown ~8–12 s) |
| **Clic der. (mantener)** | **Guardia / Bloqueo** (−60% daño, corta combos; se quiebra con golpes pesados) |
| **Espacio** | **Esquiva** (dash direccional con i-frames) |
| **R** | **ULTIMATE / "Unite Move"** (se carga usando/recibiendo daño) |
| **Tab / 1–6** | **CAMBIAR** a otro Pokémon de la party |
| **F** | **Lanzar Poké Ball** (a salvaje debilitado, en modos de captura) |
| **M** | Mapa / **Esc** | Menú de party y habilidades |

> **Gamepad completo** (mismo mapping que v1: sticks + botones), para quien prefiera.

### 4.2 El kit de cada Pokémon (5 piezas, fijas — sin crecer)
1. **Ataque básico** (su combo de identidad).
2. **Habilidad Ofensiva** (su golpe fuerte con cooldown).
3. **Habilidad Defensiva/Útil** (su golpe de control: escudo, reflect, stun, curar, empujar).
4. **Esquiva + Guardia** (genéricos con flavor por tipo).
5. **ULTIMATE (Unite Move)**: su movimiento firma de gran impacto.

> **Ejemplos:**
> - **Pikachu** (Eléctrico · Carry): básica chispa en combo · **Q = Thunderbolt** (dash-ataque) · **E = Cola Ferro** (ataque-con-esquiva) · **Ult = Thunderbolt** (onda en área).
> - **Snorlax** (Normal · Defender): básica golpe pesado · **Q = Body Slam** (carga + knockback) · **E = Reflejo** (escudo que devuelve daño) · **Ult = Giga Impacto**.
> - **Gardevoir** (Psíquico · Support): básica ola psíquica · **Q = Psíquico** (rayo que interrumpe) · **E = Pantalla de Luz** (escudo de equipo) · **Ult = Moonblast**.

### 4.3 Defensas (expreso)
- **Guardia (clic der.)**: reduce daño y corta combos; con *perfect guard* (timed) devuelve parte del daño.
- **Esquiva (Espacio)**: i-frames para esquivar habilidades y Ultimates.
- **Habilidad defensiva (E)**: única por Pokémon.
- **Resistencias de tipo (18 tipos)**: multiplicadores **en tiempo real** al daño entrante/saliente.
- **Interrupciones**: beams/rayos cortan el cast del rival.

### 4.4 Switch (cambio) — la regla de la serie
- Tu entrenador elige **3 de su party de 6** por partido.
- **Cambiar en caliente** con **coste**: cooldown ~4 s + **ventana vulnerable de ~1.5 s** al entrar (premia timing, castiga el spam).
- **KO** (tu Pokémon se desmaya) → pasa al siguiente automáticamente; se te acabó el equipo → perdiste.

### 4.5 Formato de una arena (partido)
- **3v3**, **5:00 de tiempo límite**.
- **Ganás por KO** (acabar con el equipo rival) o, si se acaba el tiempo, **por SCORE** (estilo UNITE: puntos por golpes, KOs y orbes de energía del mapa).
- **Orbes/Unitespots** en la arena dan score y aceleran la carga del Ultimate.
- **Sin levels**: el daño lo definen los kits y el matchup de tipos.

### 4.6 Salvajes y CAPTURA (capturar = coleccionar)
- Pokémon salvajes roaman en los hubs/arenas de cada región.
- **Debilitalo → F (Poké Ball)**; la probabilidad depende de HP y tipo de ball (reglas de la serie).
- Al capturarlo: **se suma a tu roster como luchador nuevo** (mismo poder que todos — no crece, no tiene XP).
- **Sin "evolución" por nivel**: en su lugar, **formas alternativas** (p. ej. Mega) se **desbloquean como kits alternos** de tu Pokémon en torneos altos.

---

## 5. Reglas de la serie (mapeadas a acción, sin RPG)

| Regla de la serie | En este juego |
|-------------------|---------------|
| Entrenador manda, no pelea | Controlás **al Pokémon activo** (el "mandar" es tu acción) |
| Party de 6 | Banco de 6; **3 por partido** |
| Cambiar en plena pelea | **Switch en caliente** con cooldown + ventana vulnerable |
| Desmayado sale | **KO** → pasa al siguiente |
| Sanación | Entre partidas: el equipo se reinicia al 100% (no hay HP persistente); en batalla: 1–2 **ítems de urgencia** con cooldown (Poción) |
| Tipos (18) | **Matchup en vivo** (multiplicadores y resistencias) |
| Captura | **Capturar = sumar un luchador** al roster |
| Rival | Un **rival** te persigue por el tour (opcional, sin diálogos largos) |
| **NO hay**: niveles, XP, stats, moves por nivel, diálogos, inventario de equipo, quests | — |

---

## 6. El roster (la "colección" que sí existe)
- **Arrancás eligiendo 1 inicial** de 3 (como la serie).
- **Crecés por:**
  - **Captura** (salvajes de cada región),
  - **Medallas** (cada arena desbloquea un Pokémon específico),
  - **Torneos/estaciones** (recompensas exclusivas),
  - **Eventos** (Pokémon limitados temporales).
- **Meta de lanzamiento: ~30–40 kits** diseñados a mano y balanceados al mismo tier.
- **Balance**: ningún Pokémon es estrictamente mejor; se compensan rol (Defender/Carry/Support/Flex) + tipo + kit.

---

## 7. Capa PC (lo que hace que sea "para computadora")
- **SO**: Windows 10/11 (Steam primero; GOG/Epic después). Port a Mac/Linux como objetivo secundario.
- **Motor**: **Unreal Engine 5** (o Unity HDRP). Objetivo **60–144 fps** en 1080p; soporte **DLSS/FSR/XeSS**.
- **Competitivo**:
  - **Ranked** por estaciones (3 meses) con ranks y recompensas.
  - **Espectador en vivo + replays** (simulación determinística/lockstep, estilo UNITE).
  - **Anti-cheat** + validación server-side en ranked.
  - **Modo torneo/lan** y overlay para streaming.
- **Multiplayer**: ranked 1v1/2v2/3v3, co-op vs. legendario, party online.
- **Requisitos accesibles**: CPU/GPU modestas para 60 fps (público amplio); perfil "Competitivo" a 144 Hz.

---

## 8. Alcance realista (lanzamiento)
- **Lanzamiento**: **3 regiones** (Kanto, Johto, Hoenn) + **24 arenas** + **~30 kits** + ranked 1v1/3v3 + 1 evento de temporada.
- **Estaciones/DLC**: las 7 regiones restantes, kits nuevos, modos (Battle Royale, co-op), formas alternativas (Mega).
- Esto mantiene el sueño de "todas las regiones" sin un alcance imposible al día 1.

---

## 9. Nombres (tono PC/arena)
- **Pokémon ODISEA — World Tour Arena** (proyectado)
- *Pokémon World Arena*
- *Pokémon Tour: Campeón del Mundo*

---

## 10. Riesgos y cómo se mitigan
| Riesgo | Mitigación |
|--------|-----------|
| Balancear 30+ kits en tiempo real | Tabla de roles/tiers, playtests constantes, parcheos de temporada (como UNITE) |
| Netcode de switch/captura en vivo | Simulación **determinística/lockstep** (probada en UNITE), rollback local |
| Alcance de 10 regiones | Lanzar con 3; el resto por estaciones (modelo "tour") |
| "Sin niveles" puede sentir progresión débil | **Diseñar bien cada desbloqueo** (cada medalla = un Pokémon nuevo visible) + ranks online como progreso de skill |
| 1000+ Pokémon no caben en kits a mano | Lanzar con 30–40 icónicos; el resto por temporadas |

---

## 11. Lo que lo hace único (vs. lo que existe hoy)
- **UNITE** es 5v5 de 10 min, sin campaña ni mundo. → **Este** tiene **campaña de tour por 10 regiones, medallas y torneos**, con el **mismo feel de combate**.
- **El RPG principal** es por turnos. → **Este** es **acción directa**.
- **Legends (Arceus/Z-A)** es acción pero sin gimnasios/medallas/ligas clásicas. → **Este** recupera la **estructura de medallas y ligas**.
- **Fighters (Brawlhalla/Skullgirls)**: sin niveles y con roster — **este** aplica ese modelo a Pokémon con las reglas de la serie (party, switch, captura).

> **En una línea: "UNITE con la campaña de medallas de la saga clásica, las reglas de la serie, y el corazón competitivo de un PC."**
