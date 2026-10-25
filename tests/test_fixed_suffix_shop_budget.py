import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fixed_suffix_shop_budget import purchase_values,optimize

class CurrencyBudgetTests(unittest.TestCase):
    def test_cheaper_xp_purchases_can_beat_greedy_high_shop(self):
        values=purchase_values(300,[(30,5),(95,17)])
        for budget in range(301):
            exhaustive=max(5*l+17*h for l in range(budget//30+1) for h in range(budget//95+1) if 30*l+95*h<=budget)
            self.assertEqual(values[budget],exhaustive)
        self.assertEqual(values[120],20)
    def test_split_fairy_rounding_is_only_an_upper_bound(self):
        for a in range(20):
            for d in range(20):
                self.assertLessEqual(a+a//3+d+d//3,a+d+(a+d)//3)
    def test_checked_prefix_budget_can_tie_but_cannot_exceed_10088(self):
        result=optimize(4021,2809,2233,9991,6257,330)
        self.assertEqual(result['upperAD'],10088)
        self.assertEqual((result['preBoostGoldSpent'],result['preBoostXPSpent']),(2800,2215))
