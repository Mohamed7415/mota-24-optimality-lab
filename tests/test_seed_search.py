import copy,os,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tools')]
from seed_search import battle,solve
from ruffle_rng import RuffleRng
from seed_grid import oracle
from ruffle_bound import solve as bound
from streak_grid import oracle as bound_oracle

class SeedBattleTests(unittest.TestCase):
    def test_rng_continues_across_battles(self):
        _,state,a=battle(50,9,10,0,128188416)
        _,_,b=battle(70,8,5,state,128188416)
        rng=RuffleRng(128188416)
        self.assertEqual(list(a+b),[rng.draw() for _ in range(len(a+b))])
    def test_zero_damage_still_consumes_rng(self):
        cost,state,draws=battle(1,10,0,0,128188416)
        self.assertEqual(cost,0);self.assertEqual(len(draws),1);self.assertNotEqual(state,0)
    def test_invalid_attack_rejected(self):
        with self.assertRaises(ValueError):battle(50,0,10,0,1)

@unittest.skipUnless(os.environ.get('MOTA_FLASH_SWF'),'Set MOTA_FLASH_SWF for natural-start original-map tests')
class NaturalOpeningIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from flash_sections import sections
        from flash_replay import prepare
        cls.sections=sections(os.environ['MOTA_FLASH_SWF']);cls.world,_=prepare(cls.sections);cls.world['Now_yellow']=0
    def test_actual_MT0_door_spends_yellow_key(self):
        from avm1 import Machine,Obj
        r=copy.deepcopy(self.world);r['Now_line']=0;r['Now_xid']=8;r['Now_yid']=5;r['Now_yellow']=1;r['mt_m_7_5']=Obj()
        vm=Machine(r,Obj({'arrow_id':3}),pool=self.sections['Move_arrow']['pool'],unbound_to_root=True);vm.run(self.sections['Move_arrow']['bytes'])
        self.assertEqual([r[k] for k in ['Now_yellow','Now_blue','Now_red']],[0,1,1]);self.assertEqual(r['mt_line_00'][7][5],0);self.assertEqual(r['Now_hp'],1000)
    def test_fixed_seeds_against_full_grid(self):
        for seed in [0,1,128188416,0xffffffff]:
            with self.subTest(seed=seed):
                a=solve(self.world,seed);b=oracle(self.world,seed)
                self.assertTrue(a['complete'] and b['complete']);self.assertEqual(a['bestExitHP'],b['bestExitHP']);self.assertTrue(860<=a['bestExitHP']<=965)
                if seed==128188416:self.assertEqual(a['bestExitHP'],860)
    def test_natural_any_seed_upper_bound(self):
        a=bound(self.world);b=bound_oracle(self.world)
        self.assertTrue(a['complete'] and b['complete']);self.assertEqual(a['bestExitHP'],965);self.assertEqual(a['bestExitHP'],b['bestExitHP'])
