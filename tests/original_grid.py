"""Independent tile-step solver for the original MT1 support abstraction.
No frontier compression or HP dominance; stores the full exact numeric state.
"""

import math, time
from collections import deque


def oracle(world, critical, limit=2000000):
    grid = [[int(v) for v in row] for row in world["mt_line_01"]]
    bits = {}
    starts = []
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == 97:
                starts.append((x, y))
            if tile not in [0, 1, 13, 14, 97, 98, 99]:
                bits[x, y] = len(bits)
    if len(starts) != 1:
        raise ValueError("Spawn marker")
    initial = (
        *starts[0],
        0,
        int(world["Now_hp"]),
        int(world["Now_gong"]),
        int(world["Now_fang"]),
        int(world["Now_yellow"]),
        int(world["Now_blue"]),
        int(world["Now_red"]),
    )
    queue = deque([initial])
    seen = {initial}
    best = None
    started = time.perf_counter()
    while queue:
        if len(seen) > limit:
            raise ValueError("Independent original oracle state limit")
        x, y, mask, hp, atk, defense, ky, kb, kr = queue.popleft()
        for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if not (0 <= nx < 11 and 0 <= ny < 11):
                continue
            tile = grid[ny][nx]
            if tile == 13:
                best = max(best if best is not None else -1, hp)
                continue
            if tile in [1, 14]:
                continue
            nm = mask
            nh = hp
            na = atk
            nd = defense
            keys = [ky, kb, kr]
            if tile not in [0, 97, 98, 99]:
                bit = 1 << bits[nx, ny]
                if not mask & bit:
                    if 40 <= tile <= 70:
                        e = world["boss_man"][tile - 40]
                        if tile - 40 in [10, 12, 17, 20]:
                            raise ValueError("Special enemy not covered")
                        if atk <= e[2]:
                            continue
                        # Gate is deliberately separate from the attack-by-attack loop.
                        predicted = math.trunc(e[0] / (atk - e[2])) * (e[1] - defense)
                        if predicted > hp:
                            continue
                        remaining = e[0]
                        loss = 0
                        while remaining > 0:
                            remaining -= (atk - e[2]) * (2 if critical else 1)
                            if remaining > 0:
                                loss += max(0, e[1] - defense)
                        nh -= loss
                        if nh < 0:
                            raise ValueError("Negative HP in ordinary-only subset")
                    elif tile in [2, 3, 4]:
                        if keys[tile - 2] == 0:
                            continue
                        keys[tile - 2] -= 1
                    elif tile in [6, 7, 8]:
                        keys[tile - 6] += 1
                    elif tile == 9:
                        nd += 3
                    elif tile == 10:
                        na += 3
                    elif tile == 11:
                        nh += 200
                    elif tile == 12:
                        nh += 500
                    elif tile != 34:
                        raise ValueError("Unsupported original tile")
                    nm |= bit
            ns = (nx, ny, nm, nh, na, nd, *keys)
            if ns not in seen:
                seen.add(ns)
                queue.append(ns)
    return {
        "bestExitHP": best,
        "expandedFullStates": len(seen),
        "elapsedSeconds": time.perf_counter() - started,
        "complete": True,
        "method": "independent tile-step exhaustive enumeration, exact HP, no dominance or region compression",
    }
