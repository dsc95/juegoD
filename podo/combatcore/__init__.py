"""CombatCore — simulación determinista del combate PODO (M0, semana 2).

Contrato de determinismo:
  mismo seed + mismos input frames = mismo resultado (logs byte-iguales).

Reglas duras:
  - Python 3 puro, stdlib únicamente.
  - Sin LLM, sin red, sin RNG sin semilla, sin tiempo real en la sim.
  - Todo el estado de la simulación son enteros (fixed-point: 1 unidad = 1/100 m).
  - CERO mecánicas RPG: kits fijos, sin nivel/XP/crecimiento de stats.
  - Todo el daño pasa por contract.compute_damage (fórmula única, shared QA).
  - Todo cooldown/duración entra vía ticks_from_ms desde la data de a8.
"""

# engine.version que va en los replays (podo.replay v1, pin para QA)
combatcore_version = "0.2.0"
__version__ = combatcore_version
