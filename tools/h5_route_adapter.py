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


def complete_fly(destination, initial, call, resource_snapshot):
    """Use the normal G panel and its observed selection; never call game methods."""
    before=resource_snapshot(initial)
    state=call('press',{'keys':['g'],'wait':200})
    if state.get('event',{}).get('id') is None and resource_snapshot(state)==before:
        # An immediately preceding shop close can leave a short input cooldown.
        # Retry only a panel that did not open, never an existing event.
        state=call('press',{'keys':[],'wait':500})
        if state.get('event',{}).get('id') is None and resource_snapshot(state)==before:
            state=call('press',{'keys':['g'],'wait':200})
    target=f'MT{destination}'
    for _ in range(40):
        event=state.get('event') or {}
        floor=event.get('flyFloorId')
        if event.get('id')!='fly' or not isinstance(floor,str) or not floor.startswith('MT'):
            raise ValueError('Fly panel or its selected floor is unavailable')
        if resource_snapshot(state)!=before:raise ValueError('Resources changed inside fly selection')
        if floor==target:break
        number={'MT23w':23,'MT23s':24,'MT23e':25,'MT_1':26}.get(floor)
        if number is None:number=int(floor[2:])
        direction='ArrowUp' if number<destination else 'ArrowDown'
        previous=floor
        state=call('press',{'keys':[direction],'wait':100})
        if state.get('event',{}).get('flyFloorId')==previous:raise ValueError('Fly destination cannot be selected')
    else:raise ValueError('Fly selection exceeded bound')
    return call('press',{'keys':['Enter'],'wait':600})


def h5_floor_id(original_floor):
    """Pinned source-map aliases already established by static map comparison."""
    return {23:'MT23w',24:'MT23s',25:'MT23e',26:'MT_1'}.get(original_floor,f'MT{original_floor}')


def h5_contact_position(source_action):
    # The cleared21F boss becomes an original stair at(5,1); H5 keeps the
    # next-floor stair one cell farther up at(6,1), separate from boss(6,2).
    if (source_action['kind']=='floor' and source_action['floor']==21
            and source_action.get('toFloor')==22 and source_action['position']==[5,1]):
        return (6,1)
    x,y=source_action['position']
    if (source_action['floor']==23 and source_action['kind']=='consume'
            and source_action.get('originalTile')==10 and x in (3,4,5) and y in (0,10)):
        # Three red gems shift one cell left, preserving the right-to-left order.
        return (x,y+1)
    return tuple(v+1 for v in source_action['position'])
