"""Adapters de presentación (M0).

- headless: runner sin UI — QA, fixtures, verificación de replays.
- tty: adapter de terminal (decision Q1-a: TTY solo para la puerta M0).

Los adapters son SOLO presentación: todo el estado vive en CombatCore y
el reloj real nunca entra en la simulación (pacing con sleep, nada más).
"""
