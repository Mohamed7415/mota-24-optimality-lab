"""Transition and bound invariants; full-map route independently replayed in CI."""
import copy,json,os,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tools')]
from crossfloor_search import World,receipt,solve
from shop_model import FIELDS,transact

class CrossfloorTests(unittest.TestCase):
    def world(self):
        g={str(f):[[1]*11 for _ in range(11)] for f in (1,2,3)}
        for f in g:
            g[f][1][1]=97;g[f][1][2]=98
        # First floor connected to second and third through genuine stair edges.
        g['1'][1][3]=13;g['2'][1][3]=13;g['2'][2][1]=14;g['3'][2][1]=14
        g['3'][0][1]=22;g['3'][1][3]=11;g['3'][1][4]=40
        return World(g,[[50,20,1,1,1]])
    def state(self):return (0,122+10,860,10,10,1,1,0,50,4,301989949)
    def test_stair_closure_and_real_contacts(self):
        w=self.world();s=list(self.state());s[1]=w.landings[2,97];s=tuple(s)
        self.assertTrue(w.region(s[0],s[1])[2]);stairs,p=w.contact(s[0],s[1],w.shop)
        self.assertEqual([e['toFloor'] for e in stairs],[3]);self.assertIn(w.shop,w.neighbors(p))
        # No resource-changing walking cycle is materialized in successors.
        self.assertTrue(all(a['kind'] in ('consume','shop') for _,a in w.successors(s)))
    def test_shop_changes_stats_without_mask_change_key_retains_them(self):
        w=self.world();s=list(self.state());s[1]=w.landings[2,97];s=tuple(s)
        purchases=[(n,a) for n,a in w.successors(s) if a['kind']=='shop']
        self.assertEqual(len(purchases),3);self.assertEqual(len({w.key(n) for n,_ in purchases}),3)
        before=dict(zip(FIELDS,[s[2],s[3],s[4],1,*s[5:8],s[8],s[9]]))
        for n,a in purchases:
            actual=transact(before,1,a['choice'])
            self.assertEqual([n[2],n[3],n[4],1,*n[5:8],n[8],n[9]],[actual[k] for k in FIELDS])
            self.assertLessEqual(w.upper(n),w.upper(s))
    def test_bound_and_mask_monotonicity(self):
        w=self.world();s=list(self.state());s[1]=w.landings[2,97];s=tuple(s)
        budget=s[8]+sum(w.enemies[t-40][3] for _,t in w.objects.values() if 40<=t<=70)
        rank=lambda z:(len(w.objects)-z[0].bit_count())*(budget+1)+z[8]
        for n,a in w.successors(s):
            self.assertLess(rank(n),rank(s))
            self.assertLessEqual(w.upper(n),w.upper(s))
            if a['kind']=='consume':self.assertGreater(n[0],s[0])
    def test_beam_never_claims_exhaustive_proof(self):
        w=self.world();s=list(self.state());s[1]=w.landings[2,97];s=tuple(s)
        r=solve(w,s,width=2,max_depth=4)
        self.assertFalse(r['complete']);self.assertGreaterEqual(r['bestReturnHP'],s[2]);self.assertLessEqual(r['bestReturnHP'],r['admissibleInitialUpperHP'])
    def test_unknown_tiles_fail_closed(self):
        w=self.world();g={str(f):[list(w.tiles[(f-1)*121+y*11:(f-1)*121+y*11+11]) for y in range(11)] for f in (1,2,3)};g['1'][4][4]=12345
        with self.assertRaises(ValueError):World(g,[[50,20,1,1,1]])

@unittest.skipUnless(os.environ.get('MOTA_FLASH_SWF'),'Set MOTA_FLASH_SWF for real-map search')
class RealCrossfloorTests(unittest.TestCase):
    def test_pinned_real_route_and_bound(self):
        from search_crossfloor import make
        r=make(os.environ['MOTA_FLASH_SWF'])
        self.assertGreater(r['bestReturnHP'],905);self.assertEqual(r['admissibleInitialUpperHP'],13860)
        self.assertFalse(r['complete']);self.assertGreater(r['metrics']['beamDiscarded'],0)
        self.assertTrue(any(a['kind']=='shop' for a in r['actions']))
        from crossfloor_route_oracle import verify
        from flash_sections import sections
        from flash_replay import prepare
        world,_=prepare(sections(os.environ['MOTA_FLASH_SWF']))
        plan=json.loads(Path('generated/M8/game-plan.json').read_text())
        self.assertTrue(verify(plan,world['boss_man'])['matched'])
        bad=copy.deepcopy(plan);bad['extension']['actions'][0]['resourcesAfter']['hp']+=1
        with self.assertRaises(AssertionError):verify(bad,world['boss_man'])
if __name__=='__main__':unittest.main()
