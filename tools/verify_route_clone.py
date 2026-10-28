import argparse,copy,gc,hashlib,json,sys,time,tracemalloc
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from route_clone import clone_for_search
from avm1 import UNDEFINED
def encode_extra(value):
 if isinstance(value,type(UNDEFINED)):return {"avm1Type":"undefined"}
 raise TypeError(f"Unreviewed state value: {type(value)}")
p=argparse.ArgumentParser(description='One pinned full-route model clone equivalence and allocation benchmark')
p.add_argument('--swf',required=True);p.add_argument('--out',required=True);args=p.parse_args()
out=Path(args.out);out.mkdir(exist_ok=False)
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('SWF mismatch')
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes()
if hashlib.sha256(raw).hexdigest()!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Proposal mismatch')
x=json.loads(raw)['actions'];r=OriginalRoute(args.swf,random_policy='worst-support')
for action in x[:661]:r.replay_action(action)
measurements=[];results=[]
for mode,clone in [('normal',copy.deepcopy),('lean',clone_for_search)]:
 gc.collect();tracemalloc.start();start=time.perf_counter();child=clone(r);clone_seconds=time.perf_counter()-start;current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 assert child.resources()==r.resources() and child.location()==r.location() and child.rng.state==r.rng.state and child.actions==r.actions
 for action in x[661:]:child.replay_action(action)
 d={'mode':mode,'cloneElapsedSeconds':clone_seconds,'clonePeakTracedPythonBytes':peak,'resources':child.resources(),'location':child.location(),'fullActionSHA256':hashlib.sha256(json.dumps(child.actions,sort_keys=True).encode()).hexdigest(),'allMapsSHA256':hashlib.sha256(json.dumps([child.grid(f) for f in range(27)]).encode()).hexdigest(),'bossDefinitionsSHA256':hashlib.sha256(json.dumps(child.root['boss_man'],default=encode_extra).encode()).hexdigest(),'rngState':child.rng.state,'modelInstructions':child.instructions,'discardedDiagnosticsAtCopy':mode=='lean','completeNumericalReplay':len(child.actions)==1713}
 measurements.append(d);del child;gc.collect()
a,b=measurements
for key in ('resources','location','fullActionSHA256','allMapsSHA256','bossDefinitionsSHA256','rngState','modelInstructions','completeNumericalReplay'):assert a[key]==b[key],key
report={'schemaVersion':1,'scope':'One actual pinned complete-route clone equivalence check only; not universal equivalence or actual-game proof','originalSWFSHA256':hashlib.sha256(Path(args.swf).read_bytes()).hexdigest(),'sourceProposalSHA256':hashlib.sha256(Path('experiments/full-route-hp28568-proposal.json').read_bytes()).hexdigest(),'sourceCloneHelperSHA256':hashlib.sha256(Path('src/route_clone.py').read_bytes()).hexdigest(),'prefixActions':661,'fullRouteFieldsComparedEqual':True,'measurements':measurements,'recordBreakingRoute':False};(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
