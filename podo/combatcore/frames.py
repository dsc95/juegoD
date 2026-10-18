"""Input frames: la única entrada de la simulación.

Un InputFrame es la entrada de UN jugador en UN tick lógico. El stream
serializado (lista de tuplas en FIELD_ORDER) ES el replay y la fixture de
QA: mismo seed + mismos frames = mismo resultado (Bloque 6, criterio 7).

Ticks sin frame enviado = frame vacío (idle). Eso mantiene todo replay
bien definido para los 5:00 completos del partido.

Semántica de bordes (importante para netcode M2):
  - basic/q/e/dodge/ultimate/capture/switch: edge (se disparan 1 vez por frame).
  - move_x/move_y/guard: estado sostenido (el frame declara la intención
    del tick; guard solo tiene efecto mientras el frame lo declare).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

# Orden de campos FIJO: cambiarlo rompe el formato de replay (bump de versión).
FIELD_ORDER = (
    "frame",     # índice del tick (0-based)
    "move_x",    # -1 | 0 | 1
    "move_y",    # -1 | 0 | 1
    "basic",     # bool — ataque básico (clic izq. en PC real; J en TTY)
    "q",         # bool — habilidad ofensiva
    "e",         # bool — habilidad defensiva
    "guard",     # bool — guardia (mantener)
    "dodge",     # bool — esquiva
    "ultimate",  # bool — ultimate (R)
    "switch",    # int — 0 ninguno | 1..3 slot explícito | 99 Tab (siguiente)
    "capture",   # bool — lanzar pokéball (F)
)

REPLAY_FORMAT = "podo-replay/1"


@dataclass(frozen=True)
class InputFrame:
    frame: int
    move_x: int = 0
    move_y: int = 0
    basic: bool = False
    q: bool = False
    e: bool = False
    guard: bool = False
    dodge: bool = False
    ultimate: bool = False
    switch: int = 0
    capture: bool = False

    def __post_init__(self):
        validate(self)


def validate(frame: "InputFrame") -> "InputFrame":
    """Valida rangos; un input inválido NUNCA entra a la sim (Bloque 5.25:
    se descarta y se loguea — la validación de adapter lo hace)."""
    for name in ("move_x", "move_y"):
        v = getattr(frame, name)
        if not isinstance(v, int) or v not in (-1, 0, 1):
            raise ValueError(f"InputFrame.{name} debe ser -1|0|1, llegó {v!r}")
    if not isinstance(frame.frame, int) or frame.frame < 0:
        raise ValueError(f"InputFrame.frame debe ser int >= 0, llegó {frame.frame!r}")
    if not isinstance(frame.switch, int) or not (
        0 <= frame.switch <= 3 or frame.switch == 99
    ):
        raise ValueError(f"InputFrame.switch debe ser 0..3 o 99, llegó {frame.switch!r}")
    return frame


def frame_to_tuple(frame: "InputFrame") -> tuple:
    return tuple(getattr(frame, f) for f in FIELD_ORDER)


def frame_from_tuple(t: tuple) -> "InputFrame":
    if len(t) != len(FIELD_ORDER):
        raise ValueError(
            f"frame de input debe tener {len(FIELD_ORDER)} campos, llegó {len(t)}"
        )
    return validate(InputFrame(**dict(zip(FIELD_ORDER, t))))


def serialize_frames(frames) -> str:
    """JSON canónico y compacto: lista de tuplas en FIELD_ORDER."""
    return json.dumps([list(frame_to_tuple(f)) for f in frames],
                      separators=(",", ":"))


def deserialize_frames(text: str):
    rows = json.loads(text)
    if not isinstance(rows, list):
        raise ValueError("se esperaba una lista de frames")
    return [frame_from_tuple(tuple(r)) for r in rows]


class InputStream:
    """Stream de inputs de un jugador: frames indexados por tick (sparse OK).

    Los ticks sin frame devuelven un frame vacío (idle) — default
    determinista.
    """

    def __init__(self, player: int, frames=None):
        self.player = int(player)
        self._by_tick = {}
        for f in frames or ():
            validate(f)
            if f.frame in self._by_tick:
                raise ValueError(f"frame duplicado en el tick {f.frame}")
            self._by_tick[f.frame] = f

    def get(self, tick: int) -> "InputFrame":
        return self._by_tick.get(tick, InputFrame(frame=tick))

    def frames(self):
        """Frames declarados, ordenados por tick."""
        return [self._by_tick[t] for t in sorted(self._by_tick)]

    def __len__(self):
        return max(self._by_tick) + 1 if self._by_tick else 0
