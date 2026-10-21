import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from search import damage,solve,replay,model
from reference_grid import oracle
T=json.loads(Path('generated/tower.json').read_text())
class SearchTests(unittest.TestCase):
 def test_combat_boundaries(self):
  e={'hp':50,'atk':20,'def':1,'special':0}
  self.assertEqual(damage(e,10,10),50)
  self.assertIsNone(damage(e,1,100))
  self.assertEqual(damage(e,51,0),0)
  self.assertEqual(damage(e,26,10),10)
  self.assertEqual(damage(e,10,100),0)
 def test_real_map_independent_oracle(self):
  a=solve(T);b=oracle(T);self.assertTrue(a['complete']);self.assertEqual(a['bestExitHP'],860);self.assertEqual(a['bestExitHP'],b['bestExitHP']);self.assertEqual(b['expandedFullStates'],89840);self.assertEqual(a['metrics']['expandedLabels'],832)
  expected=json.loads(Path('experiments/mt1.json').read_text());self.assertEqual(a['routeHash'],expected['routeHash']);self.assertEqual(a['dataHash'],expected['dataHash']);self.assertTrue(a['replay']['valid'])
 def test_route_corruption_rejected(self):
  r=solve(T);route=copy.deepcopy(r['route']);route[0]['hpCost']=1
  with self.assertRaises(ValueError):replay(T,route)
 def test_limits_do_not_claim_optimality(self):
  r=solve(T,max_states=1);self.assertFalse(r['complete']);self.assertIsNone(r['optimumInterval'][1])
 def test_unsupported_semantics_fail_closed(self):
  t=copy.deepcopy(T);t['floors']['MT1']['data']['events']={'1,1':['unknown']}
  with self.assertRaises(ValueError):model(t)
  t=copy.deepcopy(T);t['enemies']['data']['greenSlime']['special']=11
  with self.assertRaises(ValueError):model(t)
if __name__=='__main__':unittest.main()
