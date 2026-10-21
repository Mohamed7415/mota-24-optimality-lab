"""Independent numeric model of the pinned Flash candidate's local rule subset.

These functions do not read bytecode or call the test VM. They are compared
against independently interpreted original sections by flash_experiment.py.
"""

from fractions import Fraction
import math


def gate(enemy, hp, atk, defense, enemy_id=None):
    """Original pre-battle gate; distinct from actual damage calculation."""
    eh, ea, ed, *_ = enemy
    if ed >= atk:
        return False
    estimate = math.trunc(eh / (atk - ed)) * (ea - defense)
    if enemy_id == 20:
        estimate += 100
    elif enemy_id == 12:
        estimate += 300
    elif enemy_id == 10:
        estimate += math.trunc(hp / 4)
    elif enemy_id == 17:
        estimate += math.trunc(hp / 3)
    return estimate <= hp


def pre_damage(enemy_id, hp):
    if enemy_id == 20:
        return 100
    if enemy_id == 12:
        return 300
    if enemy_id == 10:
        return math.trunc(hp / 4)
    if enemy_id == 17:
        return math.trunc(hp / 3)
    return 0


def ordinary_cost(enemy, atk, defense, critical=False):
    eh, ea, ed, *_ = enemy
    if atk <= ed:
        return None
    per_hit = (atk - ed) * (2 if critical else 1)
    return ((eh - 1) // per_hit) * max(0, ea - defense)


def critical_probability(level):
    # The AVM1 specification gives random(200) support 0..199; uniformity and
    # independence are modelling assumptions, not a recovered PRNG algorithm.
    return Fraction(max(0, min(200, math.floor(level) + 1)), 200)


def combat_frames(enemy, hero, tape):
    """Independent frame-level numeric specification, not engine replay."""
    hp, atk, defense, level = hero
    state = {
        "left_hp": enemy[0],
        "left_gong": enemy[1],
        "left_fang": enemy[2],
        "right_hp": hp,
        "right_gong": atk,
        "right_fang": defense,
        "kill_number": 0,
        "kill_left": max(0, enemy[1] - defense),
        "kill_right": max(0, atk - enemy[2]),
    }
    tape = iter(tape)
    trace = []

    def snapshot(frame, events):
        trace.append({"frame": frame, "state": state.copy(), "events": events})

    snapshot(1, [])
    for _ in range(20000):
        events = []
        if state["left_hp"] > 0 or state["right_hp"] > 0:
            if state["kill_number"] % 2 == 0:
                r = next(tape)
                state["kill_max"] = r
                hit = state["kill_right"] * (2 if r <= level else 1)
                state["left_hp"] = max(0, state["left_hp"] - hit)
                events = [
                    ["random", 200, r],
                    ["sound", "music_08" if r <= level else "music_05"],
                ]
            else:
                state["right_hp"] -= state["kill_left"]
                events = [
                    [
                        "sound",
                        (
                            "music_12"
                            if state["left_gong"] > state["right_fang"]
                            else "music_13"
                        ),
                    ]
                ]
                if state["left_hp"] == 0:
                    events.extend([["goto", 35], ["play"]])
            state["kill_number"] += 1
        snapshot(24, events)
        snapshot(34, [["goto", 24], ["play"]] if state["left_hp"] > 0 else [])
        if state["left_hp"] <= 0:
            snapshot(35, [["sound", "music_07"]])
            snapshot(54, [["stop"]])
            return trace, {"Now_hp": state["right_hp"], "Display_kill": 2}
    raise ValueError("Nonterminating/oversized numeric battle")
