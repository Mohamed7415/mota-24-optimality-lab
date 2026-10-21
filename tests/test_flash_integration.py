"""Opt-in pinned original SWF tests: default offline unit suite skips this class.
CI's original-flash job sets MOTA_FLASH_SWF after downloading/verifying the file.
"""

import copy, json, os, sys, unittest
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1] / "src"),
    str(Path(__file__).resolve().parents[1] / "tools"),
]
from avm1 import Unsupported
from flash_sections import sections
from flash_milestone import benchmark, deterministic
from flash_replay import prepare, replay
from flash_search import graph, solve

SWF = os.environ.get("MOTA_FLASH_SWF")


@unittest.skipUnless(
    SWF, "Set MOTA_FLASH_SWF for pinned original-bytecode integration tests"
)
class OriginalFlashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = benchmark(SWF)
        cls.sections = sections(SWF)
        cls.world, _ = prepare(cls.sections)

    def test_deterministic_baseline(self):
        expected = json.loads(Path("experiments/flash-M4.json").read_text())
        self.assertEqual(deterministic(self.result), deterministic(expected))

    def test_real_source_coverage(self):
        d = self.result["differential"]
        self.assertEqual(d["combatCases"], 596)
        self.assertEqual(d["frameSnapshotsCompared"], 4976)
        self.assertEqual(d["criticalOutputsAtLevel1"], 2)
        self.assertEqual(
            self.result["dataConsistency"]["mapArraysMatchingM3StaticExtraction"], 27
        )
        self.assertEqual(
            self.result["dataConsistency"]["enemyTuplesMatchingM3StaticExtraction"], 33
        )

    def test_original_spawn_and_conditional_optima(self):
        self.assertEqual(self.result["openingAndArrival"]["spawn"], [5, 9])
        a, b = self.result["experiments"]
        self.assertEqual([a["bestExitHP"], b["bestExitHP"]], [995, 860])
        self.assertEqual(
            [
                a["independentOracle"]["expandedFullStates"],
                b["independentOracle"]["expandedFullStates"],
            ],
            [27734, 43756],
        )
        for x in [a, b]:
            self.assertTrue(x["bytecodeRouteReplay"]["valid"])
            self.assertTrue(x["complete"])
            self.assertEqual(x["metrics"]["expandedLabels"], 416)

    def test_zero_hp_observation_does_not_mean_a_player_replay(self):
        a, b = self.result["counterexamples"]
        self.assertFalse(a["originalAdmission"])
        self.assertEqual(a["HPIfCombatRoutineIsForced"], 5)
        self.assertTrue(b["originalAdmission"])
        self.assertEqual(b["combatRoutinePublishedHP"], 0)

    def test_route_corruption_rejected(self):
        route = copy.deepcopy(self.result["experiments"][0])
        route["route"][0]["hpCost"] = 7
        with self.assertRaises(AssertionError):
            replay(self.sections, route)

    def test_special_tile_not_silently_approximated(self):
        world = copy.deepcopy(self.world)
        world["mt_line_01"][0][5] = 50
        with self.assertRaises(ValueError):
            graph(world)

    def test_budget_does_not_claim_optimality(self):
        x = solve(self.world, "bestSupported", max_states=1)
        self.assertFalse(x["complete"])
        self.assertIsNone(x["optimumInterval"][1])


if __name__ == "__main__":
    unittest.main()
