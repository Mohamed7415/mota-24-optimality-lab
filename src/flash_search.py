"""Exact local search on ORIGINAL numeric map and verified normal-enemy rules.

Two conditional support models: all critical hits (best supported case), or
adversarial supported draws (all ordinary hits at fixed level 1). No claim about
actual PRNG sequence reachability, real-time engine scheduling or whole tower.
"""

import argparse, hashlib, json, platform, resource, sys, time
from collections import deque
from pathlib import Path
from flash_model import gate, ordinary_cost


def hashdata(v):
    def clean(x):
        if isinstance(x, float) and x.is_integer():
            return int(x)
        if isinstance(x, list):
            return [clean(v) for v in x]
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        return x

    return hashlib.sha256(
        json.dumps(clean(v), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def graph(world):
    grid = [[int(v) for v in row] for row in world["mt_line_01"]]
    if len(grid) != 11 or any(len(row) != 11 for row in grid):
        raise ValueError("Original MT1 dimensions")
    starts = [
        y * 11 + x for y, row in enumerate(grid) for x, v in enumerate(row) if v == 97
    ]
    exits = [
        y * 11 + x for y, row in enumerate(grid) for x, v in enumerate(row) if v == 13
    ]
    if len(starts) != 1 or len(exits) != 1:
        raise ValueError("Unique spawn/up-stair markers required")
    objects = {}
    free = set()
    effects = {
        6: ("key", 0),
        7: ("key", 1),
        8: ("key", 2),
        9: ("def", 3),
        10: ("atk", 3),
        11: ("hp", 200),
        12: ("hp", 500),
        34: ("display", 0),
    }
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            pos = y * 11 + x
            if v in [0, 97, 98, 99]:
                free.add(pos)
                continue
            if v in [1, 13, 14]:
                continue
            if v in [2, 3, 4]:
                effect = ("door", v - 2)
            elif v in effects:
                effect = effects[v]
            elif 40 <= v <= 70:
                if v - 40 in [10, 12, 17, 20]:
                    raise ValueError("HP-dependent/special enemy outside this model")
                effect = ("battle", world["boss_man"][v - 40])
            else:
                raise ValueError("Unmodelled original tile " + str(v))
            objects[pos] = {"index": len(objects), "tile": v, "effect": effect}

    def neighbors(pos):
        return [
            q
            for q in [pos - 11, pos + 11, pos - 1, pos + 1]
            if 0 <= q < 121 and abs(pos % 11 - q % 11) + abs(pos // 11 - q // 11) == 1
        ]

    def region(pos, mask):
        seen = {pos}
        stack = [pos]
        front = set()
        exit_reachable = False
        while stack:
            p = stack.pop()
            for q in neighbors(p):
                if q == exits[0]:
                    exit_reachable = True
                    continue
                if q in seen:
                    continue
                if q in free or q in objects and mask >> objects[q]["index"] & 1:
                    seen.add(q)
                    stack.append(q)
                elif q in objects:
                    front.add(q)
        return min(seen), sorted(front), exit_reachable

    return {
        "grid": grid,
        "objects": objects,
        "region": region,
        "start": starts[0],
        "exit": exits[0],
        "neighbors": neighbors,
    }


def advance(s, obj, pos, critical):
    mask, _, hp, atk, defense, keys, money, exp = s
    keys = list(keys)
    kind, value = obj["effect"]
    cost = 0
    if kind == "battle":
        if not gate(value, hp, atk, defense):
            return None
        cost = ordinary_cost(value, atk, defense, critical)
        if cost is None:
            raise ValueError("Gate/formula disagreement")
        hp -= cost
        if hp < 0:
            raise ValueError("Unexpected negative HP in normal-enemy model")
        money += value[3]
        exp += value[4]
    elif kind == "door":
        if keys[value] == 0:
            return None
        keys[value] -= 1
    elif kind == "key":
        keys[value] += 1
    elif kind == "hp":
        hp += value
    elif kind == "atk":
        atk += value
    elif kind == "def":
        defense += value
    elif kind != "display":
        raise ValueError("Unknown action")
    return (
        mask | 1 << obj["index"],
        pos,
        hp,
        atk,
        defense,
        tuple(keys),
        money,
        exp,
    ), cost


def solve(world, mode, max_states=1000000, seconds=60, battle_cases=None):
    if mode not in ["bestSupported", "adversarialSupported"]:
        raise ValueError(mode)
    critical = mode == "bestSupported"
    g = graph(world)
    region = g["region"]
    objects = g["objects"]
    # World passed here is after the verified one-time opening reward.
    if world["Now_life"] != 1:
        raise ValueError("This benchmark fixes level 1 without shops")
    initial = (
        0,
        g["start"],
        int(world["Now_hp"]),
        int(world["Now_gong"]),
        int(world["Now_fang"]),
        tuple(int(world[k]) for k in ["Now_yellow", "Now_blue", "Now_red"]),
        int(world["Now_money"]),
        int(world["Now_mp"]),
    )
    started = time.perf_counter()
    nodes = [(initial, None, None)]
    key = lambda s: (s[0], region(s[1], s[0])[0])
    labels = {key(initial): 0}
    q = deque([0])
    best = None
    expanded = 0
    generated = 0
    peak = 1
    complete = True
    while q:
        if expanded >= max_states or time.perf_counter() - started > seconds:
            complete = False
            break
        i = q.popleft()
        s = nodes[i][0]
        if labels[key(s)] != i:
            continue
        expanded += 1
        _, front, exit_reachable = region(s[1], s[0])
        if exit_reachable and (best is None or s[2] > nodes[best][0][2]):
            best = i
        for pos in front:
            if battle_cases is not None and objects[pos]["effect"][0] == "battle":
                battle_cases.append((objects[pos]["tile"] - 40, s[2], s[3], s[4]))
            result = advance(s, objects[pos], pos, critical)
            if result is None:
                continue
            ns, cost = result
            generated += 1
            k = key(ns)
            old = labels.get(k)
            if old is not None and nodes[old][0][2] >= ns[2]:
                continue
            action = {
                "position": [pos % 11, pos // 11],
                "originalTile": objects[pos]["tile"],
                "hpCost": cost,
            }
            labels[k] = len(nodes)
            q.append(len(nodes))
            nodes.append((ns, i, action))
        peak = max(peak, len(q))
    elapsed = time.perf_counter() - started
    route = []
    terminal = nodes[best][0] if best is not None else None
    i = best
    while i is not None and nodes[i][1] is not None:
        route.append(nodes[i][2])
        i = nodes[i][1]
    route.reverse()
    return {
        "schemaVersion": 1,
        "experiment": "original-MT1-first-ascent",
        "mode": mode,
        "complete": complete,
        "stopReason": "frontier exhausted" if complete else "resource limit",
        "objective": "maximize HP at first touch of upper stair 13, no other-floor detours",
        "scope": "Original numeric MT1 subset with verified gate/items/normal combat; supplied-draw support abstraction, not full original-engine optimum",
        "supportAssumption": "Each hero attack may independently take any integer 0..199. Fixed level 1. Actual PRNG sequence reachability not established.",
        "bestExitHP": terminal[2] if terminal else None,
        "optimumInterval": (
            [terminal[2], terminal[2]]
            if complete and terminal
            else [terminal[2] if terminal else None, None]
        ),
        "initial": {
            "hp": initial[2],
            "atk": initial[3],
            "def": initial[4],
            "keys": initial[5],
            "level": 1,
            "position": [g["start"] % 11, g["start"] // 11],
        },
        "bestFinal": (
            {
                "hp": terminal[2],
                "atk": terminal[3],
                "def": terminal[4],
                "keys": terminal[5],
                "money": terminal[6],
                "experience": terminal[7],
            }
            if terminal
            else None
        ),
        "finiteModel": {
            "consumableObjects": len(objects),
            "cells": 121,
            "maskBound": str(1 << len(objects)),
            "hpUpperBound": initial[2]
            + sum(o["effect"][1] for o in objects.values() if o["effect"][0] == "hp"),
            "specialEnemies": False,
            "levelIsConstant": True,
        },
        "metrics": {
            "expandedLabels": expanded,
            "generatedTransitions": generated,
            "uniqueMaskComponents": len(labels),
            "storedLabels": len(nodes),
            "peakQueue": peak,
            "elapsedSeconds": elapsed,
            "peakRSSBytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024),
            "rssDefinition": "process lifetime peak, includes extraction and any prior runs in this process",
        },
        "route": route,
        "routeHash": hashdata(route),
        "mapHash": hashdata(g["grid"]),
        "proofArgument": "A finite consumed-object DAG. Same mask fixes non-HP resources; each supported ordinary battle cost is independent of current HP and admission is monotone in HP. Higher HP within the same free component therefore dominates. All-critical outcomes minimize every battle cost and all-noncritical maximize it at level 1; monotonicity makes these extremal draws sufficient for the two stated support models.",
    }
