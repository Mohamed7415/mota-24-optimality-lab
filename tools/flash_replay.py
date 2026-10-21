"""Numerical route replay through original bytecode with an explicit UI adapter.

Not a Flash player: display/audio are stubs; animations/dialogue are acknowledged
at their completion boundaries by this adapter. Clock/PRNG are not emulated.
Every actual movement, combat gate, combat numeric frame, pickup and reward uses
pinned original bytecode. Every event's resources are compared to the pure model.
"""

import collections, copy, itertools, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from avm1 import Machine, Obj
from flash_search import graph, advance
from flash_experiment import initial_world, canonical, digest


def prepare(s):
    r, _ = initial_world(s)
    fairy = [
        (row, col)
        for row, line in enumerate(r["mt_line_00"])
        for col, t in enumerate(line)
        if t == 24
    ]
    if fairy != [(8, 5)]:
        raise ValueError("Unexpected opening fairy position")
    r["Display_say"][0] = 2
    r["mt_man_x"] = 8
    r["mt_man_y"] = 5
    r["mt_sister"] = Obj({"_x": 367})
    r["mt_Mykey"] = Obj()
    r["mt_Mylife"] = Obj()
    opening = Machine(r)
    opening.run(s["worldTick"]["bytes"], stop_before_date=True)
    if [r[k] for k in ["Now_yellow", "Now_blue", "Now_red"]] != [1, 1, 1]:
        raise ValueError("Opening keys")
    r["Now_line"] = 1
    r["mt_bgsound"] = Obj({"_currentframe": 11})
    arrival = Machine(
        r, Obj({"arrow_id": 1}), pool=s["SetLineDisplay"]["pool"], unbound_to_root=True
    )
    arrival.run(s["SetLineDisplay"]["bytes"])
    if [r["Now_yid"], r["Now_xid"]] != [5, 9]:
        raise ValueError("Original arrival coordinates")
    # UI completion boundary, no clock/animation claims.
    r["Display_lines"] = 0
    r["Now_key_flag"] = 1
    return r, {
        "openingInstructions": opening.steps,
        "floorArrivalInstructions": arrival.steps,
        "spawn": [5, 9],
    }


def replay(s, result):
    r, setup = prepare(s)
    g = graph(r)
    critical = result["mode"] == "bestSupported"
    state = (0, g["start"], 1000, 10, 10, (1, 1, 1), 0, 0)
    trace = []
    commands = []
    instructions = setup["openingInstructions"] + setup["floorArrivalInstructions"]
    random_draws = 0

    def invoke(arrow):
        nonlocal instructions
        vm = Machine(
            r,
            Obj({"arrow_id": arrow}),
            pool=s["Move_arrow"]["pool"],
            unbound_to_root=True,
        )
        vm.run(s["Move_arrow"]["bytes"])
        instructions += vm.steps

    def location():
        return int(r["Now_xid"]) * 11 + int(r["Now_yid"])

    def walk_to_contact(target):
        start = location()
        queue = collections.deque([start])
        prev = {start: None}
        end = None
        while queue:
            p = queue.popleft()
            if target in g["neighbors"](p):
                end = p
                break
            for q in g["neighbors"](p):
                if q not in prev and int(r["mt_line_01"][q // 11][q % 11]) in [
                    0,
                    97,
                    98,
                    99,
                ]:
                    prev[q] = p
                    queue.append(q)
        if end is None:
            raise ValueError("Bytecode route target not reachable")
        path = []
        p = end
        while prev[p] is not None:
            path.append(p)
            p = prev[p]
        for q in reversed(path):
            p = location()
            delta = q - p
            arrow = {-1: 1, 1: 2, -11: 3, 11: 4}[delta]
            invoke(arrow)
            if location() != q:
                raise AssertionError("Original movement mismatch")
            commands.append(arrow)
        delta = target - location()
        return {-1: 1, 1: 2, -11: 3, 11: 4}[delta]

    for action in result["route"]:
        x, y = action["position"]
        pos = y * 11 + x
        if int(r["mt_line_01"][y][x]) != action["originalTile"]:
            raise ValueError("Original route tile mismatch")
        arrow = walk_to_contact(pos)
        invoke(arrow)
        commands.append(arrow)
        if 40 <= action["originalTile"] <= 70:
            if r["Display_kill"] != 1:
                raise AssertionError("Original bytecode gate rejected route battle")
            actor = r["mt_kills"]
            vm = Machine(
                r,
                actor,
                random_values=itertools.repeat(0 if critical else 199),
                max_steps=2000000,
            )
            vm.run(s["combat1"]["bytes"])
            for _ in range(20000):
                vm.run(s["combat24"]["bytes"])
                vm.run(s["combat34"]["bytes"])
                if actor["left_hp"] <= 0:
                    break
            else:
                raise ValueError("Route battle limit")
            vm.run(s["combat35"]["bytes"])
            vm.run(s["combat54"]["bytes"])
            instructions += vm.steps
            random_draws += sum(event[0] == "random" for event in vm.events)
            if r["Display_kill"] != 2:
                raise AssertionError("Battle completion flag")
            # The worldTick handler clears this flag then invokes Move_arrow(100).
            # Dispatch that known original routine explicitly, never arbitrary code.
            r["Display_kill"] = 0
            invoke(100)
        out = advance(state, g["objects"][pos], pos, critical)
        if out is None:
            raise AssertionError("Model rejected bytecode route")
        state, cost = out
        actual = [
            r[k]
            for k in [
                "Now_hp",
                "Now_gong",
                "Now_fang",
                "Now_yellow",
                "Now_blue",
                "Now_red",
                "Now_money",
                "Now_mp",
            ]
        ]
        expected = [state[2], state[3], state[4], *state[5], state[6], state[7]]
        if actual != expected or cost != action["hpCost"] or r["mt_line_01"][y][x] != 0:
            raise AssertionError("Model/bytecode resource divergence")
        trace.append(
            {
                "position": [x, y],
                "originalTile": action["originalTile"],
                "resources": canonical(actual),
            }
        )
        # Text/door/tool animation acknowledgements are outside the numeric model.
        for flag in ["Display_text", "Display_other", "Open_room"]:
            r[flag] = 0
        r["Now_key_flag"] = 1
    invoke(walk_to_contact(g["exit"]))
    if r["Display_lines"] != 2 or r["My_lifes_up"] != 1:
        raise AssertionError("Upper stair trigger not observed")
    if r["Now_hp"] != result["bestExitHP"]:
        raise AssertionError("Terminal HP mismatch")
    return {
        "valid": True,
        "exitHP": int(r["Now_hp"]),
        "originalSpawn": setup["spawn"],
        "eventCount": len(trace),
        "directionCommandsBeforeExit": len(commands),
        "randomDrawsSupplied": random_draws,
        "bytecodeInstructionsInterpreted": instructions,
        "resourceTrace": trace,
        "resourceTraceHash": digest(trace),
        "directionCommandHash": digest(commands),
        "adapterBoundary": "Display/audio stubbed; UI completion acknowledged explicitly, no clock or full engine scheduling. Battle reward callback dispatches pinned Move_arrow(100).",
        "actualPRNGSequenceReachability": "unverified",
    }
