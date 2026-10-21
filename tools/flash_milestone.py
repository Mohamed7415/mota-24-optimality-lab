#!/usr/bin/env python3
"""Run the M4 numeric benchmark. Assets remain local; result contains no bytecode."""
import argparse, hashlib, json, platform, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from flash_sections import sections, metadata, SWF_SHA
from flash_experiment import initial_world, verify, fixture, vm_combat, canonical
from flash_replay import prepare, replay
from flash_search import solve
from flash_model import gate, ordinary_cost
from original_grid import oracle


def initial_consistency(base, previous):
    map_matches = 0
    enemy_matches = 0
    for key, expected in previous["maps"].items():
        grid = canonical(base["mt_line_" + key.zfill(2)])
        actual = hashlib.sha256(
            json.dumps(grid, ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()
        if actual != expected["mapHash"]:
            raise AssertionError("Bytecode/FFDec map mismatch " + key)
        map_matches += 1
    for e in previous["enemyTupleMatches"]:
        if list(base["boss_man"][e["flashEnemyIndex"]][:5]) != e["numericTuple"]:
            raise AssertionError("Bytecode/FFDec enemy mismatch")
        enemy_matches += 1
    return {
        "mapArraysMatchingM3StaticExtraction": map_matches,
        "enemyTuplesMatchingM3StaticExtraction": enemy_matches,
    }


def benchmark(swf):
    s = sections(swf)
    base, stop = initial_world(s)
    differential = verify(s, base)
    previous = json.loads(Path("experiments/flash-mhhf-baseline.json").read_text())
    consistency = initial_consistency(base, previous)
    world, setup = prepare(s)
    experiments = []
    for mode in ["bestSupported", "adversarialSupported"]:
        battle_cases = []
        result = solve(world, mode, battle_cases=battle_cases)
        checks = []
        instructions = 0
        for enemy_id, hp, atk, defense in sorted(set(battle_cases)):
            actual, machine = fixture(s, base, enemy_id + 40, hp, atk, defense)
            instructions += machine.steps
            allowed = actual["Display_kill"] == 1
            expected = gate(base["boss_man"][enemy_id], hp, atk, defense)
            if allowed != expected:
                raise AssertionError("Reachable-state original admission mismatch")
            final_hp = None
            if allowed:
                _, final, n = vm_combat(
                    s,
                    base["boss_man"][enemy_id],
                    (hp, atk, defense, 1),
                    [0 if mode == "bestSupported" else 199] * 1000,
                )
                instructions += n
                final_hp = final["Now_hp"]
                expected_hp = hp - ordinary_cost(
                    base["boss_man"][enemy_id], atk, defense, mode == "bestSupported"
                )
                if final_hp != expected_hp:
                    raise AssertionError("Reachable-state original combat mismatch")
            checks.append([enemy_id, hp, atk, defense, allowed, final_hp])
        result["bytecodeReachableBattleCheck"] = {
            "cases": len(checks),
            "admittedCases": sum(x[4] for x in checks),
            "digest": hashlib.sha256(
                json.dumps(checks, separators=(",", ":")).encode()
            ).hexdigest(),
            "bytecodeInstructionsInterpreted": instructions,
            "scope": "All unique battle-input tuples considered at expanded quotient labels; does not enumerate dominated labels or actual PRNG states.",
        }
        result["independentOracle"] = oracle(world, mode == "bestSupported")
        if (
            not result["complete"]
            or result["bestExitHP"] != result["independentOracle"]["bestExitHP"]
        ):
            raise AssertionError("Independent original search disagreement")
        result["bytecodeRouteReplay"] = replay(s, result)
        experiments.append(result)
    enemy = base["boss_man"][0]
    r, _ = fixture(s, base, 40, hp=45, atk=11, defense=10)
    _, forced, _ = vm_combat(s, enemy, (45, 11, 10, 1), [199] * 20)
    equal_gate, _ = fixture(s, base, 40, hp=50, atk=10, defense=10)
    _, equal_final, _ = vm_combat(s, enemy, (50, 10, 10, 1), [199] * 20)
    cases = [
        {
            "name": "precheck_can_reject_a_numerically_survivable_battle",
            "enemyIndex": 0,
            "heroHP": 45,
            "heroAttack": 11,
            "heroDefense": 10,
            "originalAdmission": r["Display_kill"] == 1,
            "HPIfCombatRoutineIsForced": forced["Now_hp"],
            "meaning": "Forced battle is counterfactual: entry gate actually refuses it.",
        },
        {
            "name": "equal_gate_can_publish_zero_HP",
            "enemyIndex": 0,
            "heroHP": 50,
            "heroAttack": 10,
            "heroDefense": 10,
            "originalAdmission": equal_gate["Display_kill"] == 1,
            "combatRoutinePublishedHP": equal_final["Now_hp"],
            "meaning": "Routine-level observation, not proof of full engine behavior after zero HP.",
        },
    ]
    return {
        "schemaVersion": 1,
        "milestone": "M4",
        "swfSHA256": SWF_SHA,
        "sections": metadata(s),
        "initializationPrefix": stop,
        "dataConsistency": consistency,
        "openingAndArrival": setup,
        "differential": differential,
        "counterexamples": canonical(cases),
        "experiments": experiments,
        "limitations": [
            "Independent per-attack support 0..199 is a relaxation; actual PRNG state/sequence reachability is unverified.",
            "The whitelist VM is part of the trusted computing base, not a complete Flash Player.",
            "No native Flash Player or Ruffle integration replay has been performed.",
            "UI/animation completion is an explicit route-adapter boundary; clock/Date is not emulated.",
            "This proves only stated original MT1 numeric models, never original 24-floor global optimality.",
        ],
    }


def deterministic(value):
    if isinstance(value, dict):
        return {
            k: deterministic(v)
            for k, v in value.items()
            if k not in ["elapsedSeconds", "peakRSSBytes"]
        }
    if isinstance(value, (list, tuple)):
        return [deterministic(v) for v in value]
    return value


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("swf")
    ap.add_argument("--out", default="generated/flash-M4.json")
    ap.add_argument("--check")
    a = ap.parse_args()
    result = benchmark(a.swf)
    if a.check:
        expected = json.loads(Path(a.check).read_text())
        if deterministic(result) != deterministic(expected):
            raise AssertionError("M4 deterministic baseline differs")
    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "swfSHA256": result["swfSHA256"],
                "dataConsistency": result["dataConsistency"],
                "differential": {
                    k: v
                    for k, v in result["differential"].items()
                    if k != "openingTicks"
                },
                "counterexamples": result["counterexamples"],
                "experiments": [
                    {
                        k: v
                        for k, v in x.items()
                        if k
                        in [
                            "mode",
                            "bestExitHP",
                            "complete",
                            "metrics",
                            "independentOracle",
                        ]
                    }
                    for x in result["experiments"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
