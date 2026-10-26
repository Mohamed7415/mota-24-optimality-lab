"""Cross-archive checks are opt-in; both original files stay untracked."""
import json,os,sys,unittest
from pathlib import Path
sys.path[:0]=['tools','src']
from compare_swf_builds import run,inspect
from flash_sections import SWF_SHA,GDUT_SWF_SHA

@unittest.skipUnless(os.environ.get('MOTA_GDUT_SWF') and os.environ.get('MOTA_FLASH_SWF'),'Two pinned archives required')
class BuildComparisonTest(unittest.TestCase):
 def test_static_comparison_matches_public_receipt(self):
  r=run(os.environ['MOTA_FLASH_SWF'],os.environ['MOTA_GDUT_SWF'])
  self.assertEqual(r,json.loads(Path('experiments/swf-build-comparison.json').read_text()))
  self.assertEqual(r['scriptCounts'],[103,103]);self.assertEqual(len(r['scriptDifferences']),4)
  self.assertTrue(r['titleShapeMatches']);self.assertEqual(r['rootDefineFunctionCounts'],[10,10]);self.assertEqual(r['functionDifferences'],[])
 def test_build_labels_cannot_be_swapped(self):
  with self.assertRaisesRegex(ValueError,'Unpinned'):
   inspect(os.environ['MOTA_GDUT_SWF'],SWF_SHA)
 def test_archive_route_reaches_numeric_ending(self):
  from verify_route_proposal import verify
  r=verify('experiments/full-route-hp28554-proposal.json',os.environ['MOTA_GDUT_SWF'])
  self.assertEqual(r['originalSWFSHA256'],GDUT_SWF_SHA)
  self.assertEqual(r['verifiedActions'],1779);self.assertEqual(r['battles'],295)
  self.assertEqual(r['final']['hp'],28554)
  self.assertTrue(all(r['numericTerminal'][k] for k in ('finalBossTileCleared','heroAlive','endingTransitionRequested')))
  self.assertEqual(r['numericTerminal']['finalFloor'],26)
  self.assertFalse(r['complete24Floors']);self.assertFalse(r['recordBreakingRoute'])
if __name__=='__main__':unittest.main()
