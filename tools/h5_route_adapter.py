"""Narrow adapter for current H5 cache5767, not a complete H5 simulator.
Only paths across observed empty cells are allowed; special cells are contacted
one at a time by the ordinary browser host. No H5 code strings are executed.
"""
from collections import deque


def empty_path_to_contact(grid, start, target):
    if len(grid) != 13 or any(len(row) != 13 for row in grid):
        raise ValueError('Only the observed13x13 H5 layout is supported')
    start, target = tuple(start), tuple(target)
    if any(not 0 <= n < 13 for p in (start, target) for n in p):
        raise ValueError('Coordinate outside map')
    queue = deque([start])
    previous = {start: None}
    keys = {}
    while queue:
        point = queue.popleft()
        if abs(point[0]-target[0])+abs(point[1]-target[1]) == 1:
            result = []
            while previous[point] is not None:
                result.append((keys[point], point))
                point = previous[point]
            return list(reversed(result))
        for dx, dy, key in ((0,-1,'ArrowUp'),(-1,0,'ArrowLeft'),(1,0,'ArrowRight'),(0,1,'ArrowDown')):
            neighbor = (point[0]+dx, point[1]+dy)
            if (0 <= neighbor[0] < 13 and 0 <= neighbor[1] < 13
                    and grid[neighbor[1]][neighbor[0]] == 0 and neighbor not in previous):
                previous[neighbor] = point
                keys[neighbor] = key
                queue.append(neighbor)
    raise ValueError('No empty-cell path to target contact')


def h5_prefix_expected(flash_expected, source_index):
    """The two3F gems swap: source23 gives ATK in H5, source24 restores totals.
    This adjustment is verified by pinned raw maps and actual ordinary inputs.
    It does not describe the other map/event differences later in the tower.
    """
    result = {**flash_expected, 'keys': list(flash_expected['keys'])}
    if source_index == 23:
        result['atk'] += 3
        result['def'] -= 3
    return result
