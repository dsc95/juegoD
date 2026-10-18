"""Entidades de combate: máquina de estados entera (PODO M0, semana 2).

Estados (str fijos, serializables):
  idle, moving, windup, active, recovery, guarding, dodging, ko, bench

Reglas de la máquina (semana 2):
- Un swing consume el input: WINDUP(windup) → ACTIVE(ACTIVE_TICKS) →
  RECOVERY(windup) → IDLE. Un combo (hits=N) resuelve 1 hit por tick
  ACTIVE en los N primeros ticks.
- Guardia: estado GUARDING; `guard_started` marca el tick de entrada
  (ventana de perfect guard = los primeros `perfect_ticks`).
- Esquiva: estado DODGING `dodge_ticks`; i-frames = los primeros
  `iframes_ticks` (la sim compara contra eso en el resolve).
- CC/buffs son ventanas de ticks (no estados): vulnerable/shield/
  reflect/stagger/slow → `*_until`. Stagger bloquea el input.
- Bench: miembro del equipo que no está activo (3v3).
"""
from __future__ import annotations

from .constants import ACTIVE_TICKS, ARENA_H, ARENA_W, DIAG_SCALE, TICK_MS

IDLE = "idle"
MOVING = "moving"
WINDUP = "windup"
ACTIVE = "active"
RECOVERY = "recovery"
GUARDING = "guarding"
DODGING = "dodging"
KO = "ko"
BENCH = "bench"

SWING_STATES = (WINDUP, ACTIVE, RECOVERY)
_ACTIONABLE = (IDLE, MOVING)


def dodge_steps(distance: int, ticks: int) -> tuple:
    """Reparte `distance` unidades en `ticks` pasos enteros (suma exacta).

    Distribución canónica determinista: base = d//n, y los `d % n`
    primeros ticks suman 1 (p.ej. 180u en 13 ticks → 14,13,13,…,13).
    """
    if ticks <= 0:
        return ()
    base, extra = divmod(distance, ticks)
    return tuple(base + 1 if i < extra else base for i in range(ticks))


class Entity:
    def __init__(self, eid: int, kit, team: int, x: int, y: int,
                 facing_x: int, facing_y: int):
        self.eid = eid
        self.kit = kit
        self.team = team
        self.x = int(x)
        self.y = int(y)
        self.facing_x = facing_x
        self.facing_y = facing_y
        self.max_hp = int(kit.max_hp)
        self.hp = self.max_hp
        self.state = IDLE
        self.state_ticks = 0
        # swing en curso
        self.abl = None              # Ability (kits.py)
        self.swing_kind = None       # "basic" | "q" | "e" | "ultimate"
        self._swing_target = None    # eid, lockeado en WINDUP→ACTIVE
        # guardia
        self.guard_started = -1
        # esquiva
        self.dodge_dir = (0, 0)
        # ventanas (ticks absolutos; 0 = fuera)
        self.vulnerable_until = 0
        self.shielded_until = 0
        self.shield_mult = 0         # décimas de daño recibido (4 = ×0.4)
        self.reflect_until = 0
        self.reflect_pct = 0         # centenas del daño crudo devueltas
        self.staggered_until = 0
        self.slowed_until = 0
        # ultimate
        self.charge = 0              # centi-porcentaje (10000 = 100 %)
        # cooldowns (tick absoluto en que desbloquean)
        self.cd_q = 0
        self.cd_e = 0
        self.cd_dodge = 0

    # ------------------------------------------------------------------ info
    @property
    def alive(self) -> bool:
        return self.state not in (KO, BENCH)

    @property
    def in_swing(self) -> bool:
        return self.state in SWING_STATES

    # --------------------------------------------------------------- movement
    def step_movement(self, mx: int, my: int, tick: int) -> None:
        """1 tick de movimiento (8 dir., diagonal ×707, clamp al arena).

        Fixed-point en MILLI-U (cierre 31/a8/29): delta por tick =
        speed(u/s) × TICK_MS(ms) milli-u — EXACTO, sin truncamiento
        (414 u/s → 6624 milli-u/tick). El resto sub-u vive en la posición
        misma (estado de sim → va en el digest). slow ×0.5 y diagonal
        ×707/1000 también en entero.
        """
        delta = self.kit.speed * TICK_MS          # milli-u/tick
        if tick < self.slowed_until:
            delta //= 2
        if mx != 0 and my != 0:
            delta = (delta * DIAG_SCALE) // 1000
        self.x = max(0, min(ARENA_W, self.x + mx * delta))
        self.y = max(0, min(ARENA_H, self.y + my * delta))
        if mx != 0 or my != 0:
            self.facing_x, self.facing_y = mx, my

    def step_dodge(self, step_units: int) -> None:
        """1 tick de dash de esquiva (dirección fijada al iniciar).

        `step_units` viene de la secuencia exacta `dodge_steps` (la suma
        de la secuencia = dodge_distance, sin pérdida por truncamiento).
        """
        dx, dy = self.dodge_dir
        self.x = max(0, min(ARENA_W, self.x + dx * step_units))
        self.y = max(0, min(ARENA_H, self.y + dy * step_units))

    # ----------------------------------------------------------------- swing
    def advance_swing(self) -> None:
        """Avanza la máquina WINDUP→ACTIVE→RECOVERY→IDLE (1 tick)."""
        self.state_ticks += 1
        w = self.abl.windup
        if self.state == WINDUP and self.state_ticks >= w:
            self.state, self.state_ticks = ACTIVE, 0
        elif self.state == ACTIVE and self.state_ticks >= ACTIVE_TICKS:
            self.state, self.state_ticks = RECOVERY, 0
        elif self.state == RECOVERY and self.state_ticks >= max(ACTIVE_TICKS, w):
            self.state = IDLE
            self.state_ticks = 0
            self.abl = None
            self._swing_target = None

    # -------------------------------------------------------------- targeting
    def dist2(self, other: "Entity") -> int:
        dx, dy = other.x - self.x, other.y - self.y
        return dx * dx + dy * dy

    def in_reach(self, other: "Entity") -> bool:
        """¿`other` está dentro del alcance (círculo) de mi ability actual?

        M0: los kits de a8 no definen arco → hitbox circular de `range`.
        El facing solo interviene en el tie-break de aim (ángulo).
        """
        a = self.abl
        if a is None:
            return False
        return self.dist2(other) <= a.range * a.range

    # ------------------------------------------------------------------ CC
    def in_iframes(self, tick: int, iframes_ticks: int) -> bool:
        return self.state == DODGING and self.state_ticks < iframes_ticks

    def vulnerable(self, tick: int) -> bool:
        return tick < self.vulnerable_until

    def shielded(self, tick: int) -> bool:
        return tick < self.shielded_until

    def reflecting(self, tick: int) -> bool:
        return tick < self.reflect_until

    def staggered(self, tick: int) -> bool:
        return tick < self.staggered_until
