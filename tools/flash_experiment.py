#!/usr/bin/env python3
"""Pinned-bytecode differential checks, data-only output; no game assets copied."""
import argparse, copy, hashlib, itertools, json, math, platform, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from avm1 import Machine, Obj, UNDEFINED, Unsupported
from flash_model import combat_frames, gate, pre_damage
from flash_sections import SWF_SHA, sections, metadata


def canonical(x):
    if isinstance(x, float) and x.is_integer():
        return int(x)
    if isinstance(x, dict):
        return {k: canonical(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [canonical(v) for v in x]
    return x


def digest(x):
    return hashlib.sha256(
        json.dumps(
            canonical(x), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def initial_world(s):
    m = Machine()
    stop = m.run(s["initialData"]["bytes"], stop_before_date=True)
    if stop["reason"] != "stopped before unmodelled Date constructor":
        raise ValueError("Unexpected data prefix boundary")
    return m.root, stop


def fixture(
    s, base, tile, hp=1000, atk=10, defense=10, level=1, keys=(1, 1, 1), arrow=0
):
    r = copy.deepcopy(base)
    for name, value in [
        ("Now_line", 1),
        ("Now_xid", 5),
        ("Now_yid", 5),
        ("Now_hp", hp),
        ("Now_gong", atk),
        ("Now_fang", defense),
        ("Now_life", level),
        ("Now_yellow", keys[0]),
        ("Now_blue", keys[1]),
        ("Now_red", keys[2]),
    ]:
        r[name] = value
    r["mt_line_01"][5][5] = tile
    for k in ["mt_man", "mt_Mykey", "mt_Mylife", "mt_m_5_5"]:
        r[k] = Obj()
    v = Machine(
        r, Obj({"arrow_id": arrow}), pool=s["Move_arrow"]["pool"], unbound_to_root=True
    )
    v.run(s["Move_arrow"]["bytes"])
    return r, v


def vm_combat(s, enemy, hero, tape):
    hp, atk, defense, level = hero
    r = Obj({"Now_life": level})
    q = Obj(
        {
            "left_hp": enemy[0],
            "left_gong": enemy[1],
            "left_fang": enemy[2],
            "right_hp": hp,
            "right_gong": atk,
            "right_fang": defense,
        }
    )
    vm = Machine(r, q, random_values=tape, max_steps=2000000)
    trace = []
    fields = [
        "left_hp",
        "left_gong",
        "left_fang",
        "right_hp",
        "right_gong",
        "right_fang",
        "kill_number",
        "kill_left",
        "kill_right",
        "kill_max",
    ]

    def run(frame):
        old = len(vm.events)
        vm.run(s["combat" + str(frame)]["bytes"])
        trace.append(
            {
                "frame": frame,
                "state": {k: q[k] for k in fields if q[k] is not UNDEFINED},
                "events": vm.events[old:],
            }
        )

    run(1)
    for _ in range(20000):
        run(24)
        run(34)
        if q["left_hp"] <= 0:
            run(35)
            run(54)
            return (
                canonical(trace),
                canonical({"Now_hp": r["Now_hp"], "Display_kill": r["Display_kill"]}),
                vm.steps,
            )
    raise ValueError("Bytecode battle did not terminate")


def verify(s, base):
    start = time.perf_counter()
    case_digests = []
    count = 0
    steps = 0
    frame_count = 0
    # Every base enemy, three input regimes, and tapes testing the inclusive
    # critical threshold plus all/mixed critical choices. Positive bounded numbers.
    for enemy_id, enemy in enumerate(base["boss_man"]):
        if enemy is UNDEFINED:
            continue
        for regime in range(3):
            delta = [max(1, enemy[0] // 5), enemy[0], max(1, enemy[0] // 3)][regime]
            atk = enemy[2] + delta
            defense = [max(0, enemy[1] - 10), enemy[1], enemy[1] + 1][regime]
            level = [1, 198, 199][regime]
            hero = (1000000, atk, defense, level)
            for tape_name, pattern in [
                ("allCritical", [0]),
                ("maxDraw", [199]),
                ("threshold", [level, min(199, level + 1)]),
                ("mixed", [0, 199, 37, 1]),
            ]:
                tape = list(itertools.islice(itertools.cycle(pattern), 1000))
                actual, final, n = vm_combat(s, enemy, hero, tape)
                expected, expected_final = combat_frames(enemy, hero, tape)
                if actual != canonical(expected) or final != expected_final:
                    raise AssertionError(
                        f"Battle mismatch {enemy_id} {regime} {tape_name}"
                    )
                case_digests.append(digest([enemy_id, hero, tape_name, actual, final]))
                count += 1
                steps += n
                frame_count += len(actual)
    # Per-draw boundary test: every random output for level 1 and one real enemy.
    critical = 0
    for value in range(200):
        enemy = base["boss_man"][0]
        hero = (1000, 51, 10, 1)
        a, f, n = vm_combat(s, enemy, hero, [value])
        b, g = combat_frames(enemy, hero, [value])
        if a != canonical(b) or f != g:
            raise AssertionError("Exhaustive random boundary")
        critical += a[1]["events"][1][1] == "music_08"
        case_digests.append(digest([value, a, f]))
        count += 1
        steps += n
        frame_count += len(a)
    # The actual original Move_arrow function establishes the admission gate.
    admission = []
    item_cases = 0
    for enemy_id, enemy in enumerate(base["boss_man"]):
        if enemy is UNDEFINED or enemy_id > 30:
            continue  # multi-tile final bosses outside function fixture
        for hp, atk, defense in [
            (1, enemy[2], enemy[1]),
            (1, enemy[2] + 1, enemy[1] + 1),
            (50, enemy[2] + 10, max(0, enemy[1] - 5)),
            (100000, enemy[2] + enemy[0], 0),
        ]:
            r, v = fixture(s, base, enemy_id + 40, hp, atk, defense)
            allowed = r["Display_kill"] == 1
            expected = gate(enemy, hp, atk, defense, enemy_id)
            if allowed != expected:
                raise AssertionError(f"Gate mismatch {enemy_id} {hp,atk,defense}")
            if allowed and r["Now_hp"] != hp - pre_damage(enemy_id, hp):
                raise AssertionError("Prebattle special damage mismatch")
            admission.append([enemy_id, hp, atk, defense, allowed])
            steps += v.steps
    effects = {
        6: ("Now_yellow", 1),
        7: ("Now_blue", 1),
        8: ("Now_red", 1),
        9: ("Now_fang", 3),
        10: ("Now_gong", 3),
        11: ("Now_hp", 200),
        12: ("Now_hp", 500),
    }
    for tile, (key, delta) in effects.items():
        r, v = fixture(s, base, tile)
        before = {
            "Now_hp": 1000,
            "Now_gong": 10,
            "Now_fang": 10,
            "Now_yellow": 1,
            "Now_blue": 1,
            "Now_red": 1,
        }[key]
        if r[key] != before + delta or r["mt_line_01"][5][5] != 0:
            raise AssertionError("Pickup mismatch")
        item_cases += 1
        steps += v.steps
    for tile, key in [(2, "Now_yellow"), (3, "Now_blue"), (4, "Now_red")]:
        for available in [0, 1, 2]:
            r, v = fixture(s, base, tile, keys=(available, available, available))
            opened = available > 0
            if (
                r[key] != max(0, available - 1)
                or (r["mt_line_01"][5][5] == 0) != opened
            ):
                raise AssertionError("Door mismatch")
            item_cases += 1
            steps += v.steps
    # Opening reward: exercise actual worldTick with only that event active,
    # stop before Date; a second tick must not grant the three keys again.
    opening = copy.deepcopy(base)
    opening["Display_say"][0] = 2
    opening["mt_man_x"] = 8
    opening["mt_man_y"] = 5
    opening["mt_sister"] = Obj({"_x": 367})
    opening["mt_Mykey"] = Obj()
    opening["Now_line"] = 0
    opening_ticks = []
    for _ in range(2):
        vm = Machine(opening)
        boundary = vm.run(s["worldTick"]["bytes"], stop_before_date=True)
        opening_ticks.append(
            {
                "keys": [opening[k] for k in ["Now_yellow", "Now_blue", "Now_red"]],
                "sayFlag": opening["Display_say"][0],
                "fairyX": opening["mt_sister"]["_x"],
                "mapOld": opening["mt_line_00"][8][5],
                "mapNew": opening["mt_line_00"][8][4],
                "stop": boundary,
                "events": vm.events,
            }
        )
        steps += vm.steps
    if any(
        x["keys"] != [1, 1, 1]
        or x["sayFlag"] != 3
        or x["fairyX"] != 335
        or x["mapOld"] != 0
        or x["mapNew"] != 24
        for x in opening_ticks
    ):
        raise AssertionError("Opening reward/idempotence mismatch")
    if opening_ticks[1]["events"]:
        raise AssertionError("Opening reward repeated display effects")
    return {
        "openingTicks": canonical(opening_ticks),
        "combatCases": count,
        "frameSnapshotsCompared": frame_count,
        "admissionCases": len(admission),
        "pickupDoorCases": item_cases,
        "randomOutputsCheckedAtLevel1": 200,
        "criticalOutputsAtLevel1": critical,
        "combatTraceDigest": digest(case_digests),
        "admissionDigest": digest(admission),
        "bytecodeInstructionsInterpreted": steps,
        "elapsedSeconds": time.perf_counter() - start,
        "scope": "Pinned original bytecode vs independent numeric model. Display/audio stubbed; supplied random tapes; no Flash Player/Ruffle integration replay.",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("swf")
    ap.add_argument("--out", default="generated/flash-differential.json")
    a = ap.parse_args()
    s = sections(a.swf)
    base, stop = initial_world(s)
    r = verify(s, base)
    result = {
        "schemaVersion": 1,
        "swfSHA256": SWF_SHA,
        "sections": metadata(s),
        "initializationPrefix": stop,
        "metrics": r,
        "limitations": [
            "The whitelist VM is part of the trusted computing base and is not a complete AVM1 implementation.",
            "No native Flash/Ruffle runtime validation yet.",
            "Supplied random outputs validate the opcode support and branch, not actual PRNG states or independence.",
            "Date is not executed. worldTick is tested only with the opening event active and stops before Date; other global event branches are not validated.",
            "Original bytes stay local; CI re-downloads the pinned file, no assets committed.",
        ],
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
