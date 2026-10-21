import json,os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tools')]
from ruffle_rng import RuffleRng,next_state,output
from ruffle_bound import battle_outcomes,solve
from streak_grid import outcomes,oracle

class RNGTests(unittest.TestCase):
    def test_known_player_vectors(self):
        rng=RuffleRng(128188416)
        self.assertEqual([rng.draw() for _ in range(20)],[147,174,21,13,37,103,109,7,159,145,191,181,193,3,125,42,24,160,33,23])
    def test_transition_range_and_zero(self):
        self.assertEqual(output(0),109)
        for s in [0,1,2,0x7fffffff,0x80000000,0xffffffff]:
            t=next_state(s);self.assertTrue(0<=t<=0x7fffffff)
            if s and s<=0x7fffffff:self.assertNotEqual(t,0)
    def test_maximum_run_witness(self):
        s=121448050;v=[]
        for _ in range(5):v.append(output(s));s=next_state(s)
        self.assertTrue(all(x<=1 for x in v[:4]));self.assertGreater(v[4],1)
    def test_battle_pruning_independent_enumeration(self):
        for hp in range(1,18):
            for delta in range(1,6):
                for run in range(5):
                    actual={r:len(p)-1 for r,p in battle_outcomes(hp,delta,run)}
                    self.assertEqual(actual,{r:h for h,r in outcomes(hp,delta,run)})
    def test_native_port_vectors(self):
        with tempfile.TemporaryDirectory() as d:
            exe=str(Path(d)/'scan')
            subprocess.run(['cc','-std=c11','-O3','-Wall','-Wextra','-Werror','src/native/ruffle_rng_scan.c','-o',exe],check=True)
            for seed in [0,1,128188416,0x80000000,0xffffffff]:
                actual=json.loads(subprocess.check_output([exe,'--vectors',str(seed),'1000']))
                rng=RuffleRng(seed);self.assertEqual(actual,[rng.draw() for _ in range(1000)])

@unittest.skipUnless(os.environ.get('MOTA_FLASH_SWF'),'Set MOTA_FLASH_SWF for pinned-original M5 integration')
class StreakIntegration(unittest.TestCase):
    def test_original_map_bound_independent_oracle(self):
        from flash_sections import sections
        from flash_replay import prepare
        world,_=prepare(sections(os.environ['MOTA_FLASH_SWF']))
        a=solve(world);b=oracle(world)
        self.assertTrue(a['complete'] and b['complete']);self.assertEqual(a['bestExitHP'],980);self.assertEqual(a['bestExitHP'],b['bestExitHP'])
