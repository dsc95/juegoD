"""Replay / fixtures en el formato CANÓNICO `podo.replay` v1 (dueño: a8).

Spec: data/schema/replay.schema.json + docs/FIXTURES-AND-REPLAYS.md.
- Inputs event-sparse CON HOLD: cada registro es el estado de input
  COMPLETO de un (side, seat) desde su tick `t` hasta el próximo registro
  del mismo (side, seat). Antes del primer registro: estado neutro.
- `actions` son bordes (1 tick): basic/q/e/dodge/ultimate/switch/ball;
  la guardia es estado y se modela con guard_on/guard_off.
- `tail.final_state_hash` = "sha256:" + sha256(digest canónico del core).
- `tail.rejected_inputs` = inputs inválidos descartados y registrados.
- `tail.outcome` = {winner a|b|draw, reason ko|timeout_score|forfeit, score}.

Este módulo es el ÚNICO lugar que traduce entre el stream denso interno
(1 InputFrame por tick por side) y el formato canónico. El core no conoce
el JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import combatcore_version
from .core import CombatCore, _SPAWN
from .frames import InputFrame
from .kits import load_kits
from .rules import load_arena, load_rules
from .types import TypeMatrix

_DATA = Path(__file__).resolve().parent.parent / "data"
FORMAT = "podo.replay"
VERSION = 1


class ReplayInputs:
    """Expande el input event-sparse canónico en frames densos (lazy).

    El estado (move sostenido + guardia) es POR (side, seat): un switch
    cambia de seat y el nuevo seat arranca neutro hasta su primer registro.
    """

    def __init__(self, records, total_ticks: int, seats: int = 3):
        self.total = int(total_ticks)
        self._recs = sorted(records, key=lambda r: (r["t"], r["side"], r["seat"]))
        self._n = len(self._recs)
        self._p = 0
        self._state = {(s, i): {"move": (0, 0), "guard": False}
                       for s in (0, 1) for i in range(seats)}
        self._edges = {}

    def frame(self, side: int, seat: int, t: int) -> InputFrame:
        if not 0 <= t < self.total:
            raise ValueError(f"tick fuera de rango: {t}")
        while self._p < self._n and self._recs[self._p]["t"] <= t:
            r = self._recs[self._p]
            s = 0 if r["side"] == "a" else 1
            st = self._state[(s, int(r["seat"]))]
            inp = r.get("input") or {}
            m = inp.get("move")
            st["move"] = (0, 0) if m is None else (int(m["x"]), int(m["y"]))
            acts = list(inp.get("actions") or [])
            for a in acts:
                if a == "guard_on":
                    st["guard"] = True
                elif a == "guard_off":
                    st["guard"] = False
            if acts:
                self._edges[(t, s, int(r["seat"]))] = acts
            self._p += 1
        st = self._state[(side, seat)]
        acts = self._edges.get((t, side, seat), [])
        mx, my = st["move"]
        return InputFrame(
            frame=t, move_x=mx, move_y=my, guard=st["guard"],
            basic="basic" in acts, q="q" in acts, e="e" in acts,
            dodge="dodge" in acts, ultimate="ultimate" in acts,
            switch=99 if "switch" in acts else 0,
            capture="ball" in acts,
        )


def _edge_actions(f: InputFrame, prev_guard: bool):
    acts = []
    if f.basic:
        acts.append("basic")
    if f.q:
        acts.append("q")
    if f.e:
        acts.append("e")
    if f.dodge:
        acts.append("dodge")
    if f.guard and not prev_guard:
        acts.append("guard_on")
    elif not f.guard and prev_guard:
        acts.append("guard_off")
    if f.ultimate:
        acts.append("ultimate")
    if f.switch:
        acts.append("switch")
    if f.capture:
        acts.append("ball")
    return acts


def dense_to_records(core, dense_by_side: dict):
    """Stream denso ({side: [InputFrame]×core.tick}) → registros podo.replay v1.

    Cubre los ticks realmente simulados (core.tick): si el match terminó por
    KO antes de 5:00 o el jugador salió (forfeit), no se rellenan el resto.
    """
    total = core.tick
    recs = []
    last = {(s, i): {"move": (0, 0), "guard": False}
            for s in (0, 1) for i in range(3)}
    for t in range(total):
        for s in (0, 1):
            f = dense_by_side[s][t]
            seat = core._hist[t][s]   # seat ACTIVO al inicio del tick t
            st = last[(s, seat)]
            mv = (f.move_x, f.move_y)
            acts = _edge_actions(f, st["guard"])
            if mv != st["move"] or acts:
                inp = {"move": None if mv == (0, 0)
                       else {"x": mv[0], "y": mv[1]}}
                if acts:
                    inp["actions"] = sorted(acts)
                recs.append({"t": t, "side": "a" if s == 0 else "b",
                             "seat": seat, "input": inp})
            st["move"] = mv
            if f.guard != st["guard"]:
                st["guard"] = f.guard
    recs.sort(key=lambda r: (r["t"], r["side"], r["seat"]))
    return recs


def save_replay(path, core, dense_by_side: dict, outcome: dict = None) -> dict:
    """Guarda el replay podo.replay v1; devuelve el doc.

    `frames_total` = ticks realmente simulados (core.tick): si el match
    terminó por KO antes de 5:00, o si el jugador se va (forfeit, TTY),
    el replay cubre hasta ahí. `outcome` permite fijar "forfeit" en salidas
    anticipadas; por defecto usa core.outcome().
    """
    total = core.tick
    teams = {
        "a": [core._by_eid[eid].kit.kit_id for eid in core._teams[0]],
        "b": [core._by_eid[eid].kit.kit_id for eid in core._teams[1]],
    }
    doc = {
        "format": FORMAT,
        "version": VERSION,
        "engine": {"name": "CombatCore", "version": combatcore_version},
        "seed": core.seed,
        "matrix_version": core.matrix.version,
        "config": {
            "tick_ms": core.rules.tick_ms,
            "match_duration_ms": core.max_ticks * core.rules.tick_ms,
            "arena": core.arena.arena_id,
            "teams": teams,
        },
        "inputs": dense_to_records(core, dense_by_side),
        "tail": {
            "frames_total": total,
            "final_state_hash": "sha256:" + core.state_hash(),
            "rejected_inputs": core.rejected,
            "outcome": outcome if outcome is not None else core.outcome(),
        },
    }
    Path(path).write_text(json.dumps(doc, sort_keys=True,
                                     separators=(",", ":")),
                          encoding="utf-8")
    return doc


def load_replay(path) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("format") != FORMAT:
        raise ValueError(f"formato de replay inválido: {doc.get('format')!r}")
    if int(doc.get("version", 0)) != VERSION:
        raise ValueError(f"versión de replay no soportada: {doc.get('version')}")
    return doc


def rebuild_core(doc: dict, data_dir=None, max_ticks: int = None) -> CombatCore:
    """Reconstruye el core desde config del replay (determinista).

    `max_ticks` por defecto = tail.frames_total. Para replays forfeit el
    verificador pasa frames_total+1: el timeout del core debe quedar FUERA
    de la ventana re-jugada (el outcome "forfeit" lo cierra el adapter, no
    la sim).
    """
    data_dir = Path(data_dir) if data_dir else _DATA
    cfg = doc["config"]
    kits = load_kits(data_dir)
    teams = []
    for side, seat_kits in ((0, cfg["teams"]["a"]), (1, cfg["teams"]["b"])):
        teams.append([(kits[k], *_SPAWN[side]) for k in seat_kits])
    return CombatCore(
        seed=doc["seed"],
        teams=teams,
        matrix=TypeMatrix.load(data_dir / "types" / "type_matrix_v1.json"),
        rules=load_rules(data_dir / "config" / "match_rules.json"),
        arena=load_arena(data_dir / "arenas" / f"{cfg['arena']}.json"),
        max_ticks=max_ticks if max_ticks is not None
        else doc["tail"]["frames_total"],
    )


def run_replay(core: CombatCore, rep: ReplayInputs) -> None:
    """Cambia el core tick a tick con los inputs expandidos."""
    for t in range(rep.total):
        if core.is_over():
            return
        core.step({
            0: rep.frame(0, core._active[0], t),
            1: rep.frame(1, core._active[1], t),
        })


def verify_replay(path) -> bool:
    """Recorre el replay y cierra determinismo: state_hash + outcome +
    rejected_inputs deben coincidir con el tail.

    - Match completo (ko/timeout_score): se re-juegan frames_total ticks
      con max_ticks = frames_total; outcome completo debe coincidir.
    - Forfeit (salida anticipada, TTY/--demo): se re-juegan frames_total
      ticks con max_ticks = frames_total+1 (sin timeout en la ventana);
      el match debe haber quedado EN CURSO al final (winner None), y
      state_hash + score + rejected deben coincidir.
    """
    doc = load_replay(path)
    tail = doc["tail"]
    total = tail["frames_total"]
    forfeit = tail["outcome"].get("reason") == "forfeit"
    core = rebuild_core(doc, max_ticks=(total + 1) if forfeit else total)
    if core.matrix.version != doc["matrix_version"]:
        return False
    rep = ReplayInputs(doc["inputs"], total)
    run_replay(core, rep)
    want = tail["final_state_hash"]
    if not want.startswith("sha256:"):
        return False
    if forfeit:
        return (core.winner is None
                and core.state_hash() == want.removeprefix("sha256:")
                and core.score == tail["outcome"]["score"]
                and core.rejected == tail["rejected_inputs"])
    return (core.state_hash() == want.removeprefix("sha256:")
            and core.outcome() == tail["outcome"]
            and core.rejected == tail["rejected_inputs"])
