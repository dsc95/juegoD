"""CombatCore: la simulación determinista del partido 3v3 (PODO M0, sem 2).

Contrato (Bloque 6, criterio 7 — VETO de determinismo):
  mismo seed + mismos input frames = mismo resultado (logs byte-iguales).
  - Sin tiempo real: el reloj es el tick (0-based, 16 ms; MAX por regla).
  - Sin RNG sin semilla: self.rng vive aquí, sembrado en el constructor;
    en sem 2 aún no se usa (captura lo usa en sem 3 → digest incluye
    rng.getstate(), nota dura de 31).
  - Todo el estado serializable es entero (o str de estado fijo).
  - Todo el daño pasa por contract.compute_damage (fórmula única, QA).
  - Todo cooldown/duración entra vía ticks_from_ms desde los JSON de a8
    (match_rules.json → rules.py; kits → kits.py). Nada de ms ni floats
    adentro de la sim.

Mecánicas sem 2 (cableadas sobre la data de a8):
  - Guardia / perfect guard (ventana + reflejo % + corte de combo).
  - Esquiva con i-frames (dash fijo, CD por kit).
  - Q/E con cooldowns y effects (enum cerrado: apply_state, knockback,
    pushback, heal, shield, reflect, team_shield, interrupt).
  - Ultimate con carga (daño causado/recibido/orbs) y release ×2.
  - Switch 3v3: Tab = siguiente vivo (CD 4 s); el que entra entra
    vulnerable 1.5 s (+50 %); KO del activo → auto-switch (sin CD).
  - Score (hit/ko/orb por match_rules) + orbs del arena; timeout decide
    por score (empate → draw).
  - Input inválido se DESCARTA Y SE REGISTRA: `self.rejected`
    ({t, side, seat, action, reason}) → va a tail.rejected_inputs del
    replay podo.replay v1.

NO incluye (sem 3): captura (la acción `ball` se rechaza en arena),
medallas, saves, hub.
"""
from __future__ import annotations

import hashlib
import json
import random
from functools import cmp_to_key
from math import isqrt
from pathlib import Path

from .constants import (
    ACTIVE_TICKS,
    ARENA_H,
    ARENA_W,
    MAX_TICKS,
    ticks_from_ms,
)
from .contract import compute_damage
from .entities import (
    ACTIVE,
    BENCH,
    DODGING,
    Entity,
    GUARDING,
    IDLE,
    KO,
    MOVING,
    RECOVERY,
    SWING_STATES,
    WINDUP,
    dodge_steps,
)
from .frames import InputFrame
from .kits import load_kits
from .rules import load_arena, load_rules
from .types import TypeMatrix

_DATA = Path(__file__).resolve().parent.parent / "data"

WIN_IN_PROGRESS = -2
WIN_DRAW = -1            # timeout sin ventaja de score → draw

ORB_RADIUS = 24_000      # milli-u: radio de pickup de orb (engine)
_SPAWN = {0: (ARENA_W // 4, ARENA_H // 2),
          1: (3 * ARENA_W // 4, ARENA_H // 2)}


class CombatCore:
    def __init__(self, seed=42, teams=None, matrix=None,
                 rules=None, arena=None, max_ticks: int = None):
        """teams: lista de 2 equipos; cada equipo = lista de (kit, x, y).

        Por defecto: data canónica de a8 (3v3; team a = trio estándar,
        team b = boss_team de arena_001). matrix/rules/arena: None →
        data/types/type_matrix_v1.json, data/config/match_rules.json,
        data/arenas/arena_001.json.
        """
        self.rules = rules if rules is not None else load_rules(
            _DATA / "config" / "match_rules.json")
        self.arena = arena if arena is not None else load_arena(
            _DATA / "arenas" / "arena_001.json")
        if matrix is None:
            matrix = TypeMatrix.load(_DATA / "types" / "type_matrix_v1.json")
        self.matrix = matrix
        self.max_ticks = int(max_ticks if max_ticks is not None
                             else self.rules.max_ticks)
        self.seed = int(seed)
        self.rng = random.Random(self.seed)
        self._pending = {}            # buffer de apply_input_frame (QA)
        self.tick = 0
        self.events = []
        self.rejected = []          # → tail.rejected_inputs del replay
        self.winner = None          # None en curso; 0/1; WIN_DRAW al final
        self._end_reason = None     # "ko" | "timeout_score"
        self.score = [0, 0]
        self._active = [0, 0]       # seat activo por team
        self._switch_cd = [0, 0]    # tick en que se desbloquea el switch
        self._hist = []             # (seat_a, seat_b) al INICIO de cada tick
        if teams is None:
            teams = self._default_teams()
        self.entities = []
        self._by_eid = {}
        self._teams = []
        eid = 0
        for tm, members in enumerate(teams):
            members = list(members[: self.rules.party_size])
            if not members:
                raise ValueError("equipo vacío")
            eids = []
            for i, (kit, x, y) in enumerate(members):
                fx, fy = (1, 0) if tm == 0 else (-1, 0)
                e = Entity(eid, kit, tm, int(x), int(y), fx, fy)
                if i != 0:
                    e.state = BENCH
                self.entities.append(e)
                self._by_eid[e.eid] = e
                eids.append(e.eid)
                eid += 1
            self._teams.append(eids)
        self.orbs = [{"x": x, "y": y, "until": 0}
                     for (x, y, _r) in self.arena.orbs]
        self._dodge_seq = dodge_steps(self.rules.dodge_distance,
                                      self.rules.dodge_ticks)

    @staticmethod
    def _default_teams():
        kits = load_kits(_DATA)
        arena = load_arena(_DATA / "arenas" / "arena_001.json")
        trio = (kits["pikachu"], kits["snorlax"], kits["gardevoir"])
        boss = tuple(kits[k] for k in arena.boss_kits)
        return [
            [(trio[i], *_SPAWN[0]) for i in range(3)],
            [(boss[i], *_SPAWN[1]) for i in range(len(boss))],
        ]

    # ------------------------------------------------------------------ log
    def _log(self, **ev) -> None:
        ev["t"] = self.tick
        self.events.append(ev)

    def _reject(self, team: int, action: str, reason: str) -> None:
        """Input inválido: se descarta y queda registrado (QA lo cierra)."""
        self.rejected.append({
            "t": self.tick,
            "side": "a" if team == 0 else "b",
            "seat": self._active[team],
            "action": action,
            "reason": reason,
        })

    # ----------------------------------------------------------------- tick
    def step(self, frames: dict | None = None) -> None:
        """Avanza 1 tick. frames: {team: InputFrame} (sparse OK).

        El frame indexado en t es el input consumido al procesar el tick t.
        Solo el miembro ACTIVO de cada team procesa input.
        """
        if self.winner is not None or self.tick >= self.max_ticks:
            return
        self._hist.append((self._active[0], self._active[1]))
        frames = frames or {}
        # El seat ACTIVO se captura al inicio del tick: un switch manual
        # (que muta self._active) no hace que el nuevo miembro re-procese
        # el mismo frame (canon podo.replay: el nuevo seat arranca neutro).
        active_eids = (self._teams[0][self._active[0]],
                       self._teams[1][self._active[1]])
        for e in sorted(self.entities, key=lambda e: e.eid):
            if e.state in (KO, BENCH):
                continue
            if e.eid not in active_eids:
                continue
            f = frames.get(e.team)
            if f is None:
                f = InputFrame(frame=self.tick)
            self._drive(e, f)
        self._resolve_attacks()
        self._collect_orbs()
        self._check_end()
        self.tick += 1

    def run(self, streams: dict) -> "CombatCore":
        """Corre hasta el fin (KO o time-out). streams: {team: InputStream}."""
        while self.winner is None and self.tick < self.max_ticks:
            self.step({tm: s.get(self.tick) for tm, s in streams.items()})
        return self

    # ------------------------------------------------ capa de contrato (QA)
    def apply_input_frame(self, frame: InputFrame, team: int = 0) -> None:
        """Buffer un input frame para `team`; lo consume el próximo avance."""
        self._pending[int(team)] = frame

    def _step_buffered(self) -> None:
        frames = dict(self._pending)
        self._pending.clear()
        self.step(frames)

    def advance(self, n: int) -> None:
        """Avanza n pasos (se detiene al terminar el partido)."""
        for _ in range(int(n)):
            if self.is_over() or self.tick >= self.max_ticks:
                return
            self._step_buffered()

    def state_hash(self) -> str:
        """sha256 del digest canónico — huella de determinismo para QA."""
        return hashlib.sha256(self.digest_json().encode("utf-8")).hexdigest()

    def is_over(self) -> bool:
        return self.winner is not None

    def final_score(self, team: int) -> int:
        return self.score[int(team)]

    def outcome(self) -> dict:
        """tail.outcome del replay podo.replay v1 (a8)."""
        if self.winner is None:
            return {"winner": "draw", "reason": self._end_reason or "timeout_score",
                    "score": list(self.score)}
        name = "a" if self.winner == 0 else "b" if self.winner == 1 else "draw"
        return {"winner": name, "reason": self._end_reason, "score": list(self.score)}

    # ----------------------------------------------------------------- drive
    def _drive(self, e: Entity, f: InputFrame) -> None:
        # 0) CC (stagger/stun): no se procesa ningún input
        if e.staggered(self.tick):
            for action in self._action_flags(f):
                self._reject(e.team, action, "staggered")
            return
        # 1) switch (Tab): siguiente miembro vivo, con CD
        if f.switch:
            self._try_switch(e.team)
            return
        # 2) swing en curso: avanza y nada más
        if e.in_swing:
            was = e.state
            e.advance_swing()
            if was == WINDUP and e.state == ACTIVE:
                self._lock_target(e)
            return
        # 3) esquiva
        if f.dodge:
            if self.tick < e.cd_dodge:
                self._reject(e.team, "dodge", "cooldown")
            elif e.state in (IDLE, MOVING, GUARDING):
                self._start_dodge(e, f)
            return
        if e.state == DODGING:
            if e.state_ticks < len(self._dodge_seq):
                e.step_dodge(self._dodge_seq[e.state_ticks])
            e.state_ticks += 1
            if e.state_ticks >= self.rules.dodge_ticks:
                e.state, e.state_ticks = IDLE, 0
            return
        # 4) guardia (hold: guard_on/guard_off del formato podo.replay)
        if f.guard and e.state in (IDLE, MOVING):
            e.state, e.state_ticks, e.guard_started = GUARDING, 0, self.tick
        elif e.state == GUARDING and not f.guard:
            e.state, e.state_ticks = IDLE, 0
        if e.state == GUARDING:
            return
        # 5) movimiento
        if f.move_x != 0 or f.move_y != 0:
            e.step_movement(f.move_x, f.move_y, self.tick)
            e.state, e.state_ticks = MOVING, 0
        elif e.state == MOVING:
            e.state, e.state_ticks = IDLE, 0
        # 6) acciones: prioridad ultimate > q > e > basic
        if f.ultimate:
            if e.kit.ultimate is None:
                self._reject(e.team, "ultimate", "no_ultimate")
            elif e.charge < self.rules.ult_max_centi:
                self._reject(e.team, "ultimate", "not_charged")
            elif e.state in (IDLE, MOVING):
                e.charge = 0
                self._start_swing(e, e.kit.ultimate, "ultimate")
            return
        if f.q:
            if e.kit.q is None:
                self._reject(e.team, "q", "no_ability")
            elif self.tick < e.cd_q:
                self._reject(e.team, "q", "cooldown")
            elif e.state in (IDLE, MOVING):
                e.cd_q = self.tick + e.kit.q.cooldown
                self._start_swing(e, e.kit.q, "q")
            return
        if f.e:
            if e.kit.e is None:
                self._reject(e.team, "e", "no_ability")
            elif self.tick < e.cd_e:
                self._reject(e.team, "e", "cooldown")
            elif e.state in (IDLE, MOVING):
                e.cd_e = self.tick + e.kit.e.cooldown
                self._start_swing(e, e.kit.e, "e")
            return
        if f.basic and e.state in (IDLE, MOVING):
            self._start_swing(e, e.kit.basic, "basic")
        if f.capture:
            # sem 3; en arena no hay captura
            self._reject(e.team, "ball", "no_capture_in_arena")

    @staticmethod
    def _action_flags(f: InputFrame):
        for flag, name in ((f.basic, "basic"), (f.q, "q"), (f.e, "e"),
                           (f.dodge, "dodge"), (f.ultimate, "ultimate"),
                           (f.switch, "switch"), (f.capture, "ball")):
            if flag:
                yield name

    def _start_dodge(self, e: Entity, f: InputFrame) -> None:
        dx, dy = f.move_x, f.move_y
        if dx == 0 and dy == 0:
            dx, dy = e.facing_x, e.facing_y
        e.state, e.state_ticks = DODGING, 0
        e.dodge_dir = (dx, dy)
        e.cd_dodge = self.tick + e.kit.dodge_cd
        self._log(ev="dodge", src=e.eid, dx=dx, dy=dy)

    def _start_swing(self, e: Entity, abl, kind: str) -> None:
        e.state, e.state_ticks = WINDUP, 0
        e.abl, e.swing_kind = abl, kind
        e._swing_target = None

    # --------------------------------------------------------------- switch
    def _try_switch(self, team: int) -> None:
        eids = self._teams[team]
        cur = self._active[team]
        if self.tick < self._switch_cd[team]:
            self._reject(team, "switch", "cooldown")
            return
        seq = [(cur + i) % len(eids) for i in range(1, len(eids))]
        nxt = next((i for i in seq
                    if self._by_eid[eids[i]].state != KO), None)
        if nxt is None:
            self._reject(team, "switch", "no_alive")
            return
        self._do_switch(team, nxt, auto=False)
        self._switch_cd[team] = self.tick + self.rules.switch_cd

    def _do_switch(self, team: int, idx: int, auto: bool) -> None:
        eids = self._teams[team]
        old = self._by_eid[eids[self._active[team]]]
        new = self._by_eid[eids[idx]]
        # Un KO'd NO vuelve al banco: clobber KO→BENCH lo "resucitaría"
        # (state != KO lo contaba como vivo en _on_ko).
        if old.state != KO:
            old.state, old.state_ticks = BENCH, 0
        old.abl, old._swing_target = None, None
        sx, sy = _SPAWN[team]
        new.x, new.y = sx, sy
        new.facing_x, new.facing_y = (1, 0) if team == 0 else (-1, 0)
        new.state, new.state_ticks = IDLE, 0
        new.abl, new._swing_target = None, None
        new.vulnerable_until = self.tick + self.rules.vuln_ticks
        self._active[team] = idx
        self._log(ev="auto_switch" if auto else "switch",
                  team=team, frm=old.eid, to=new.eid)

    def _on_ko(self, team: int) -> None:
        eids = self._teams[team]
        alive = [i for i in range(len(eids))
                 if self._by_eid[eids[i]].state != KO]
        if not alive:
            if self.winner is None:
                w = 1 - team
                self._log(ev="match_end",
                          winner="a" if w == 0 else "b", reason="ko")
                self.winner, self._end_reason = w, "ko"
            return
        if self._by_eid[eids[self._active[team]]].state != KO:
            return  # KO en el banco: no hay switch (solo KO del activo)
        seq = [(self._active[team] + i) % len(eids)
               for i in range(1, len(eids) + 1)]
        nxt = next(i for i in seq if self._by_eid[eids[i]].state != KO)
        self._do_switch(team, nxt, auto=True)   # auto: sin CD, con ventana

    # -------------------------------------------------------------- targeting
    def _lock_target(self, e: Entity) -> None:
        """Aim (spec Q1 v1.1): se LOCKEA en WINDUP→ACTIVE.

        Círculo de alcance (los kits de a8 no definen arco). Tie-break:
        (1) menor dist², (2) menor ángulo con el facing (cruce de
        multiplicaciones enteras, sin floats), (3) menor eid.
        """
        a = e.abl
        if a.kind in ("aoe", "team_aoe"):
            return   # sin objetivo único: resuelve contra todos en alcance
        cands = []
        for t in sorted(self.entities, key=lambda x: x.eid):
            if t.team == e.team or t.state in (KO, BENCH) or not e.in_reach(t):
                continue
            ddx, ddy = t.x - e.x, t.y - e.y
            cands.append((t, ddx * ddx + ddy * ddy,
                          e.facing_x * ddx + e.facing_y * ddy))
        if not cands:
            e._swing_target = None
            return
        ex, ey = e.x, e.y

        def cmp(x, y):
            ta, da2, dota = x
            tb, db2, dotb = y
            if da2 != db2:
                return -1 if da2 < db2 else 1
            la = dota * dota * db2      # cos²·dist²_ajeno (cross, sin floats)
            lb = dotb * dotb * da2
            if la != lb:
                return -1 if la > lb else 1   # mayor cos² = menor ángulo = mejor
            return -1 if ta.eid < tb.eid else 1

        e._swing_target = min(cands, key=cmp_to_key(cmp))[0].eid

    # -------------------------------------------------------------- combates
    def _resolve_attacks(self) -> None:
        """Hits: un combo resuelve 1 hit por tick ACTIVE en sus N primeros.

        Orden: por eid (determinista). AOE/team_aoe golpea a todos los
        enemigos en alcance; el resto, al objetivo lockeado.
        """
        for e in sorted(self.entities, key=lambda e: e.eid):
            if e.state != ACTIVE or e.abl is None:
                continue
            if e.state_ticks >= e.abl.hits:
                continue
            a = e.abl
            targets = []
            if a.kind in ("aoe", "team_aoe"):
                cands = [t for t in self.entities
                         if t.team != e.team and t.state not in (KO, BENCH)
                         and e.in_reach(t)]
                cands.sort(key=lambda t: t.eid)
                targets = cands
            elif e._swing_target is not None:
                t = self._by_eid.get(e._swing_target)
                if t is not None and t.state not in (KO, BENCH):
                    targets = [t]
            for t in targets:
                self._apply_hit(e, t)

    def _apply_hit(self, e: Entity, t: Entity) -> None:
        # i-frames: invulnerabilidad total (los primeros ticks del dodge)
        if t.in_iframes(self.tick, self.rules.iframes_ticks):
            self._log(ev="dodge_blocked", src=e.eid, dst=t.eid)
            return
        guarding = t.state == GUARDING
        perfect = guarding and (self.tick - t.guard_started) <= self.rules.perfect_ticks
        shielded = t.shielded(self.tick) and t.shield_mult > 0
        vulnerable = t.vulnerable(self.tick)
        raw = compute_damage(e.abl.damage, e.kit.type, t.kit.type,
                             matrix=self.matrix)
        dmg = compute_damage(e.abl.damage, e.kit.type, t.kit.type,
                             matrix=self.matrix,
                             guarding=(guarding or shielded) and not perfect,
                             perfect_guard=perfect,
                             vulnerable=vulnerable,
                             is_ultimate=(e.swing_kind == "ultimate"))
        # perfect guard: daño → 0; refleja X % del daño CRUDO; corta el combo
        if perfect:
            refl = raw * self.rules.perfect_reflect // 100
            if refl > 0:
                e.hp -= refl
                self._log(ev="damage", src=t.eid, dst=e.eid,
                          atk="perfect_guard", kind="reflect",
                          mult=10, dmg=refl)
            if e.in_swing:
                e.state, e.state_ticks = RECOVERY, 0
                self._log(ev="interrupt", src=t.eid, dst=e.eid,
                          reason="perfect_guard")
            if e.hp <= 0:
                self._ko(e, t.eid)
            return
        if dmg <= 0:
            return   # inmunidad ×0 (tipo): ni carga, ni score
        # reflect (snorlax e): devuelve X % del daño recibido como contra
        if t.reflecting(self.tick) and t.reflect_pct > 0:
            refl = dmg * t.reflect_pct // 100
            e.hp -= refl
            self._log(ev="damage", src=t.eid, dst=e.eid, atk="reflect",
                      kind="reflect", mult=10, dmg=refl)
            if e.hp <= 0:
                self._ko(e, t.eid)
        t.hp -= dmg
        e.charge = min(self.rules.ult_max_centi,
                       e.charge + dmg * self.rules.ult_dealt_centi)
        t.charge = min(self.rules.ult_max_centi,
                       t.charge + dmg * self.rules.ult_taken_centi)
        self.score[e.team] += self.rules.score_hit
        self._log(ev="damage", src=e.eid, dst=t.eid, atk=e.abl.name,
                  kind=e.swing_kind,
                  mult=self.matrix.mult(e.kit.type, t.kit.type), dmg=dmg)
        for eff in e.abl.effects:
            self._apply_effect(e, t, eff)
        if t.hp <= 0:
            self.score[e.team] += self.rules.score_ko
            self._ko(t, e.eid)

    def _apply_effect(self, e: Entity, t: Entity, eff) -> None:
        if eff.type == "apply_state":
            if eff.state in (1, 2):      # stagger / stun = CC
                t.staggered_until = self.tick + ticks_from_ms(eff.ms)
            elif eff.state == 3:         # slow
                t.slowed_until = self.tick + ticks_from_ms(eff.ms)
            self._log(ev="state_applied", src=e.eid, dst=t.eid,
                      state=eff.state, ms=eff.ms)
        elif eff.type in ("knockback", "pushback"):
            dx, dy = t.x - e.x, t.y - e.y
            d2 = dx * dx + dy * dy
            if d2 > 0:
                d = isqrt(d2)
                # eff.value en milli-u; el push escala por masa (centenas)
                push = eff.value * 100 // max(1, t.kit.weight)
                t.x = max(0, min(ARENA_W, t.x + (dx * push + d // 2) // d))
                t.y = max(0, min(ARENA_H, t.y + (dy * push + d // 2) // d))
                self._log(ev="knockback", src=e.eid, dst=t.eid, push=push)
        elif eff.type == "interrupt":
            if t.in_swing:
                t.state, t.state_ticks = IDLE, 0
                t.abl, t._swing_target = None, None
                self._log(ev="interrupt", src=e.eid, dst=t.eid,
                          reason="skill")
        elif eff.type == "heal":
            t.hp = min(t.max_hp, t.hp + eff.value)
            self._log(ev="heal", dst=t.eid, amt=eff.value)
        elif eff.type == "reflect":
            t.reflect_until = self.tick + ticks_from_ms(eff.ms)
            t.reflect_pct = eff.value
            self._log(ev="reflect_on", dst=t.eid, ms=eff.ms, pct=eff.value)
        elif eff.type in ("shield", "team_shield"):
            targets = ([t] if eff.type == "shield"
                       else [m for m in self.entities
                             if m.team == e.team and m.state not in (KO,)])
            for m in targets:
                m.shielded_until = self.tick + ticks_from_ms(eff.ms)
                m.shield_mult = eff.value
                self._log(ev="shield_on", dst=m.eid, ms=eff.ms,
                          mult=eff.value)

    def _ko(self, e: Entity, src: int) -> None:
        e.hp = 0
        e.state, e.state_ticks = KO, 0
        e.abl, e._swing_target = None, None
        self._log(ev="ko", dst=e.eid, src=src)
        self._on_ko(e.team)

    # ------------------------------------------------------------------ orbs
    def _collect_orbs(self) -> None:
        for i, orb in enumerate(self.orbs):
            if self.tick < orb["until"]:
                continue
            for tm in (0, 1):
                e = self._by_eid[self._teams[tm][self._active[tm]]]
                dx, dy = e.x - orb["x"], e.y - orb["y"]
                if dx * dx + dy * dy <= ORB_RADIUS * ORB_RADIUS:
                    self.score[tm] += self.rules.score_orb
                    e.charge = min(self.rules.ult_max_centi,
                                   e.charge + self.rules.ult_orb_centi)
                    orb["until"] = self.tick + self.arena.orb_respawn
                    self._log(ev="orb", team=tm, orb=i)
                    break

    # ------------------------------------------------------------------- fin
    def _check_end(self) -> None:
        if self.winner is not None:
            return
        if self.tick >= self.max_ticks - 1:
            s0, s1 = self.score
            w = 0 if s0 > s1 else (1 if s1 > s0 else WIN_DRAW)
            name = "a" if w == 0 else "b" if w == 1 else "draw"
            self._log(ev="timeout")
            self._log(ev="match_end", winner=name, reason="timeout_score")
            self.winner = w
            self._end_reason = "timeout_score"
        alive = [
            sum(1 for e in self.entities if e.team == tm and e.state != KO)
            for tm in range(len(self._teams))
        ]
        if self.winner is None:
            if alive[0] == 0 and alive[1] == 0:
                self._log(ev="match_end", winner=WIN_DRAW, reason="ko")
                self.winner, self._end_reason = WIN_DRAW, "ko"
            elif alive[1] == 0:
                self._log(ev="match_end", winner=0, reason="ko")
                self.winner, self._end_reason = 0, "ko"
            elif alive[0] == 0:
                self._log(ev="match_end", winner=1, reason="ko")
                self.winner, self._end_reason = 1, "ko"

    # ------------------------------------------------------------- serializ.
    def digest(self) -> list:
        """Estado completo serializable (enteros) — huella de determinismo.

        TODO sem 3 (nota dura de 31): cuando la captura use self.rng, el
        digest DEBE incluir rng.getstate().
        """
        ents = [
            [e.eid, e.x, e.y, e.facing_x, e.facing_y, e.hp, e.state,
             e.state_ticks, e._swing_target if e._swing_target is not None
             else -1, e.abl is not None,
             e.swing_kind if e.swing_kind is not None else "",
             e.guard_started, e.dodge_dir[0], e.dodge_dir[1],
             e.vulnerable_until, e.shielded_until, e.shield_mult,
             e.reflect_until, e.reflect_pct, e.staggered_until,
             e.slowed_until, e.charge, e.cd_q, e.cd_e, e.cd_dodge]
            for e in sorted(self.entities, key=lambda e: e.eid)
        ]
        winner = self.winner if self.winner is not None else WIN_IN_PROGRESS
        return [
            self.tick, self.seed, ents,
            [self.score[0], self.score[1]],
            [self._active[0], self._active[1]],
            [self._switch_cd[0], self._switch_cd[1]],
            winner,
            [[o["x"], o["y"], o["until"]] for o in self.orbs],
            self._end_reason if self._end_reason is not None else "",
        ]

    def events_json(self) -> str:
        """Log de eventos en JSON canónico (byte-estable entre runs)."""
        return json.dumps(self.events, sort_keys=True, separators=(",", ":"))

    def digest_json(self) -> str:
        return json.dumps(self.digest(), sort_keys=True, separators=(",", ":"))
