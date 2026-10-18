"""Adapter TTY: juega la sim desde la terminal (puerta M0, Q1 cerrada).

Teclas (M0, sem 2):
  W A S D / flechas   mover (8 direcciones; mantener = auto-repetir)
  J                   ataque básico (dirigida: objetivo más cercano
                      según facing — spec Q1 v1.1)
  G                   guardia (hold; la TTY no tiene key-up → se mantiene
                      GUARD_HOLD_TICKS tras la última pulsación)
  Q / E               habilidades (CD por kit)
  ESPACIO             esquiva (i-frames; CD por kit)
  R                   ultimate (carga al 100 %; vacía la barra)
  TAB / 1 / 2 / 3     switch (formato canónico: "switch" = siguiente vivo)
  F                   captura (sem 3; en arena se rechaza y queda en log)
  ESC / Ctrl-C        salir (guarda el replay podo.replay v1, forfeit)

Notas:
  - El adapter es SOLO presentación: el estado vive en CombatCore.
    El reloj real solo pacing (sleep hasta el deadline de 16 ms).
  - Cada partida queda guardada como replay en podo/replays/
    (formato podo.replay v1 de a8; una salida anticipada cierra con
    outcome reason "forfeit").
"""
from __future__ import annotations

import select
import sys
import termios
import time
import tty
from datetime import datetime
from pathlib import Path

from ..constants import ARENA_H, ARENA_W, TICK_MS
from ..frames import InputFrame
from .headless import DEFAULT_TEAMS, core_factory

GRID_W, GRID_H = 60, 16
ARROWS = {"A": "up", "B": "down", "C": "right", "D": "left"}
DIRS = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0),
}
GUARD_HOLD_TICKS = 20   # 320 ms: la guardia "se sostiene" tras pulsar G


# ------------------------------------------------------------------ teclado
def read_key():
    """Lee 1 tecla (sin bloquear). Devuelve str normalizado o None."""
    r, _, _ = select.select([sys.stdin], [], [], 0)
    if not r:
        return None
    c = sys.stdin.read(1)
    if c == "\x1b":
        r2, _, _ = select.select([sys.stdin], [], [], 0)
        if r2 and sys.stdin.read(1) == "[":
            return ARROWS.get(sys.stdin.read(1))
        return "esc"
    return c


def build_frame(tick: int, pressed: set, guard: bool = False) -> InputFrame:
    mx = my = 0
    for key, (dx, dy) in DIRS.items():
        if key in pressed:
            mx, my = dx, dy
    switch = 99 if (pressed & {"\t", "1", "2", "3"}) else 0
    return InputFrame(
        frame=tick, move_x=mx, move_y=my,
        basic="j" in pressed, q="q" in pressed, e="e" in pressed,
        guard=guard, dodge=" " in pressed, ultimate="r" in pressed,
        switch=switch, capture="f" in pressed,
    )


# ------------------------------------------------------------------- render
def _grid_line(core, gy: int) -> str:
    row = list(" " * GRID_W)
    for e in core.entities:
        if e.state == "ko":
            continue
        cx = min(GRID_W - 1, e.x * GRID_W // ARENA_W)
        cy = min(GRID_H - 1, e.y * GRID_H // ARENA_H)
        if cy == gy:
            row[cx] = "@" if e.team == 0 else "O"
    return "".join(row)


def render(core) -> str:
    out = ["\x1b[H\x1b[2J"]
    over = core.winner is not None
    sa, sb = core.score
    ch = core._by_eid[core._teams[0][core._active[0]]].charge
    out.append(f"PODO M0  tick {core.tick}/{core.max_ticks}   "
               f"SCORE {sa} : {sb}   carga {ch // 100}%")
    for e in sorted(core.entities, key=lambda e: e.eid):
        active = e.eid == core._by_eid[core._teams[e.team][core._active[e.team]]].eid
        mark = "*" if active else " "
        out.append(f"{mark}[{e.eid}] {e.kit.name:9s} hp={e.hp:4d}  "
                   f"estado={e.state:8s}"
                   + (f" carga={e.charge // 100}%" if active and e.team == 0 else ""))
    out.append("+" + "-" * GRID_W + "+")
    for gy in range(GRID_H):
        out.append("|" + _grid_line(core, gy) + "|")
    out.append("+" + "-" * GRID_W + "+")
    out.append("WASD mover · J básica · G guardia · Q/E skills · ESPACIO "
               "esquiva · R ultimate · TAB switch · ESC salir")
    if core.tick < core._switch_cd[0]:
        sw = f"cd {core._switch_cd[0] - core.tick} ticks"
    else:
        sw = "listo"
    out.append(f"switch: {sw}")
    if over:
        txt = {0: "GANA EQUIPO A", 1: "GANA EQUIPO B"}.get(
            core.winner, "EMPATE/TIEMPO")
        out.append(txt)
    return "\n".join(out)


# --------------------------------------------------------------------- main
def main() -> int:
    seed = 42
    core = core_factory(seed, DEFAULT_TEAMS)
    frames = []
    last_g = None
    replay_dir = Path(__file__).resolve().parents[2] / "replays"
    replay_dir.mkdir(exist_ok=True)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    quit_now = False
    try:
        tty.setraw(fd)
        print(render(core), end="")
        while not quit_now and core.winner is None \
                and core.tick < core.max_ticks:
            deadline = time.monotonic() + TICK_MS / 1000
            pressed = set()
            while True:
                k = read_key()
                if k is None:
                    break
                if k in ("esc", "\x03"):
                    quit_now = True
                    break
                pressed.add(k)
            if quit_now:
                break
            if "g" in pressed:
                last_g = core.tick
            guard = last_g is not None and \
                (core.tick - last_g) < GUARD_HOLD_TICKS
            frame = build_frame(core.tick, pressed, guard=guard)
            frames.append(frame)
            core.step({0: frame})
            if core.tick % 4 == 0 or core.winner is not None:
                print(render(core), end="")
            elapsed = time.monotonic() - deadline
            if elapsed < 0:
                time.sleep(-elapsed)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

    from ..replay import save_replay
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    replay_path = replay_dir / f"tty-{stamp}-seed{seed}.json"
    dense = {0: frames,
             1: [InputFrame(frame=t) for t in range(core.tick)]}
    outcome = ({"winner": "draw", "reason": "forfeit",
                "score": list(core.score)} if core.winner is None else None)
    save_replay(replay_path, core, dense, outcome=outcome)
    if core.winner is None:
        print(f"\nsaliendo — ticks={core.tick} outcome=forfeit")
    else:
        print(f"\nsaliendo — ticks={core.tick} outcome={core.outcome()}")
    print(f"replay={replay_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
