import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from shop_diversity import select_diverse


class ShopDiversityTests(unittest.TestCase):
    def test_retains_objective_and_middle_of_dense_extreme_clusters(self):
        rows = []
        for atk, defense, xp in [(1000+i, 10, 100) for i in range(20)] + [(10, 1000+i, 100) for i in range(20)] + [(100, 100, 90)]:
            rows.append(dict(hp=100, atk=atk, def_=defense, experience=xp, money=0))
        resource = lambda r: dict(r, **{'def': r['def_']})
        kept = select_diverse(rows, 4, resource, lambda r: -r['experience'])
        self.assertTrue(any(r is rows[-1] for r in kept))
        self.assertEqual(max(r['experience'] for r in kept), 100)
        self.assertEqual(len({id(r) for r in kept}), 4)
        self.assertTrue(all(any(r is source for source in rows) for r in kept))

    def test_equal_resources_are_stable_and_have_no_zero_division(self):
        rows = [dict(hp=1, atk=1, experience=0, money=0, **{'def': 1}) for _ in range(5)]
        kept = select_diverse(rows, 3, lambda r: r, lambda r: 0)
        self.assertEqual([id(r) for r in kept], [id(r) for r in rows[:3]])
