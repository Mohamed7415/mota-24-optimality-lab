import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shop_frontier import prune

class ShopFrontierTests(unittest.TestCase):
    def node(self):
        return {'resources':{'hp':100,'atk':20,'def':10,'level':1,'keys':[1,0,0],'money':0,'experience':30},'xpPurchases':5,'actions':[{'kind':'consume','floor':1,'position':[2,3],'originalTile':40,'resourcesAfter':{}}]}
    def test_higher_health_removes_only_the_weaker_matching_trace(self):
        weak=self.node();strong=copy.deepcopy(weak);strong['resources']['hp']=101
        kept,removed=prune([weak,strong]);self.assertEqual(kept,[strong]);self.assertEqual(removed[0]['removedIndex'],0)
        self.assertEqual(weak['resources']['hp'],100)
    def test_higher_purchase_cost_and_stat_tradeoffs_remain_incomparable(self):
        a=self.node();b=copy.deepcopy(a);b['resources']['hp']=101;b['xpPurchases']=6
        self.assertEqual(len(prune([a,b])[0]),2)
        b['xpPurchases']=5;b['resources']['atk']=19
        self.assertEqual(len(prune([a,b])[0]),2)
    def test_different_world_event_level_or_keys_prevent_pruning(self):
        for dimension in ('event','level','keys'):
            a=self.node();b=copy.deepcopy(a);b['resources']['hp']=101
            if dimension=='event':b['actions'][0]['position']=[3,3]
            elif dimension=='level':b['resources']['level']=2
            else:b['resources']['keys']=[0,1,0]
            self.assertEqual(len(prune([a,b])[0]),2)
    def test_identical_duplicates_keep_one_and_variable_shop_order_is_ignored(self):
        a=self.node();b=copy.deepcopy(a)
        a['actions'] += [{'kind':'shop','shop':1,'choice':c,'floor':3,'position':[5,0]} for c in (2,3)]
        b['actions'] += list(reversed(a['actions'][1:]))
        self.assertEqual(prune([a,b])[0],[a])

    def test_witnesses_resolve_to_retained_states(self):
        rows=[self.node() for _ in range(3)]
        for i,row in enumerate(rows):row['resources']['hp']+=i
        kept,removed=prune(rows)
        self.assertEqual(kept,[rows[2]])
        self.assertTrue(all(row['dominatingIndex']==2 for row in removed))
