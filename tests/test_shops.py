import copy,os,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tools')]
from shop_model import FIELDS,transact,potential,rank

class ShopTests(unittest.TestCase):
    def state(self,**kwargs):return dict(zip(FIELDS,[1000,10,10,1,0,0,0,0,0]))|kwargs
    def test_key_round_trip_loses_budget(self):
        for choice,cash in [(1,10),(2,50),(3,100)]:
            a=self.state(Now_money=cash);b=transact(a,3,choice);c=transact(b,4,choice)
            self.assertEqual(potential(a),potential(b));self.assertLess(rank(b),rank(a));self.assertLess(rank(c),rank(b));self.assertLess(c['Now_money'],cash)
    def test_upgrade_above_199_not_capped_in_routine(self):
        a=self.state(Now_life=199,Now_mp=270)
        self.assertEqual(transact(a,5,1)['Now_life'],200);self.assertEqual(transact(a,6,1)['Now_life'],202)
    def test_fail_exit_identity(self):
        a=self.state()
        for shop in range(1,7):
            for choice in range(1,5):self.assertEqual(transact(a,shop,choice),a)
    def test_lexicographic_scalar_rank(self):
        # For every nonnegative cash<=P, all previous P blocks rank lower.
        for p in range(100):
            lo=p*(p+1)//2
            if p:self.assertLess((p-1)*p//2+p-1,lo)
    def test_negative_domain_rejected(self):
        with self.assertRaises(ValueError):transact(self.state(Now_money=-1),1,1)

@unittest.skipUnless(os.environ.get('MOTA_FLASH_SWF'),'Set MOTA_FLASH_SWF for original shop bytecode')
class ShopOriginalIntegration(unittest.TestCase):
    def test_all_216_original_boundary_cases(self):
        from avm1 import Machine,Obj
        from shop_probe import cases
        from shop_sections import sections
        s=sections(os.environ['MOTA_FLASH_SWF']);count=0
        for shop,choice,state in cases():
            root=Obj({**state,'mt_Mylife':Obj(),'mt_Mykey':Obj()});actor=Obj({'now_case_id':choice});actor['this']=actor
            vm=Machine(root,actor,pool=s[shop]['pool']);vm.run(s[shop]['bytes'])
            self.assertEqual({k:int(root[k]) for k in FIELDS},transact(state,shop,choice));count+=1
        self.assertEqual(count,216)
    def test_concrete_crossfloor_plan_receipts(self):
        from make_crossfloor_plan import make
        p=make(os.environ['MOTA_FLASH_SWF']);a=p['extension']['actions']
        self.assertEqual(sum(x['kind']=='floor' for x in a),7)
        self.assertEqual(p['extension']['finalResources'],{'hp':905,'atk':23,'def':10,'keys':[0,1,0],'money':9,'experience':31})
