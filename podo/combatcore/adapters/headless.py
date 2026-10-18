"""Runner headless: corre la sim sin UI (QA, fixtures, verificación).

Uso (desde podo/):
  python -m combatcore.adapters.headless --demo --ticks 2000 --save-replay demo.json
  python -m combatcore.adapters.headless --replay demo.json
  python -m combatcore.adapters.headless                # partido completo 5:00

El tiempo de pared se imprime SOLO como referencia de performance
(Bloque 6.27f); JAMÁS entra en el log del partido.

Sem 2: 3v3 sobre data canónica de a8; replays en formato podo.replay v1.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ..core import CombatCore
from ..frames import InputFrame, InputStream
from ..kits import load_kits
from ..replay import save_replay, verify_replay
from ..rules import load_arena
from ..types import TypeMatrix

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PLAYER_TEAM = ["pikachu", "snorlax", "gardevoir"]
SPAWN = {0: (250_000, 300_000), 1: (750_000, 300_000)}   # milli-u


def core_factory(seed, team_kit_ids=None) -> CombatCore:
    """Fábrica canónica: kit ids -> CombatCore (tests y verif. de replays).

    team b por defecto = `boss_team` del arena canónico (drop-in de la data
    de a8; el FLIP de corte neutro es un cambio en data, no en código).
    """
    kits = load_kits(DATA_DIR)
    matrix = TypeMatrix.load(DATA_DIR / "types" / "type_matrix_v1.json")
    arena = load_arena(DATA_DIR / "arenas" / "arena_001.json")
    if team_kit_ids is None:
        team_kit_ids = [PLAYER_TEAM, list(arena.boss_kits)]
    teams = []
    for t, ids in enumerate(team_kit_ids):
        x, y = SPAWN[t]
        teams.append([(kits[i], x, y) for i in ids])
    return CombatCore(seed, teams, matrix)


def demo_frames(ticks: int, side: int = 0) -> dict:
    """Patrón demo determinista (sin estado, por construcción).

    Acercarse 40 ticks, guardia 10 ticks cada 500, esquiva cada 500,
    básico periódico, switch/ultimate de team a cada 700/1000. Los inputs
    inválidos (ultimate sin carga, switch en CD) quedan en rejected_inputs.
    """
    out = {}
    mv = 1 if side == 0 else -1
    for t in range(ticks):
        if t < 40:
            out[t] = InputFrame(frame=t, move_x=mv)
        elif t % 500 in range(100, 110):
            out[t] = InputFrame(frame=t, guard=True)
        elif t % 500 == 300:
            out[t] = InputFrame(frame=t, dodge=True, move_x=mv)
        elif side == 0 and t % 1000 == 500:
            out[t] = InputFrame(frame=t, ultimate=True)
        elif side == 0 and t % 700 == 400:
            out[t] = InputFrame(frame=t, switch=99)
        elif t % (40 if side == 0 else 47) == 20:
            out[t] = InputFrame(frame=t, basic=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PODO CombatCore — runner headless")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ticks", type=int, default=2000,
                    help="ticks a simular en modo --demo")
    ap.add_argument("--demo", action="store_true",
                    help="genera streams demo deterministas (3v3)")
    ap.add_argument("--replay", type=Path,
                    help="re-correr un replay podo.replay v1 y verificarlo")
    ap.add_argument("--save-replay", type=Path,
                    help="guardar el replay del partido simulado")
    args = ap.parse_args(argv)

    if args.replay:
        ok = verify_replay(args.replay)
        print(json.dumps({"replay": str(args.replay), "verify": ok},
                         sort_keys=True))
        return 0 if ok else 1

    t0 = time.perf_counter()
    core = core_factory(args.seed)   # team b = boss_team del arena (data)
    if args.demo:
        streams = {0: InputStream(0, demo_frames(args.ticks, 0).values()),
                   1: InputStream(1, demo_frames(args.ticks, 1).values())}
        for t in range(args.ticks):
            core.step({tm: s.get(t) for tm, s in streams.items()})
        dense = {tm: [s.get(t) for t in range(core.tick)]
                 for tm, s in streams.items()}
    else:
        core.run({0: InputStream(0), 1: InputStream(1)})
        dense = {tm: [InputFrame(frame=t) for t in range(core.tick)]
                 for tm in (0, 1)}
    wall_ms = (time.perf_counter() - t0) * 1000

    print(json.dumps({
        "ticks": core.tick,
        "winner": core.winner,
        "outcome": core.outcome(),
        "events": len(core.events),
        "rejected": len(core.rejected),
        "wall_ms_ref": round(wall_ms, 1),   # referencia de perf, no es log
    }, sort_keys=True))
    for ev in core.events[:12]:
        print(json.dumps(ev, sort_keys=True))
    if len(core.events) > 12:
        print(f"... +{len(core.events) - 12} eventos")

    if args.save_replay:
        # partido cortado sin ganador = forfeit (replay podo.replay v1);
        # match completo (KO/timeout) usa el outcome real de la sim
        outcome = (None if core.winner is not None else
                   {"winner": "draw", "reason": "forfeit",
                    "score": list(core.score)})
        save_replay(args.save_replay, core, dense, outcome=outcome)
        print(json.dumps({"replay": str(args.save_replay),
                          "verify": verify_replay(args.save_replay)},
                         sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
