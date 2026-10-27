"""Numerical alternate XP objective; requires native replay before any score claim."""
import sys,json,time,hashlib,resource,argparse
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--swf',required=True);parser.add_argument('--out',default='generated/XPSuffixReproduction');args=parser.parse_args()
src=Path('experiments/full-route-hp28568-proposal.json');raw=src.read_bytes()
if hashlib.sha256(raw).hexdigest()!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Source proposal changed')
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Expected pinned2018 archive')
out=Path(args.out);out.mkdir(exist_ok=False)
r=OriginalRoute(args.swf,random_policy='worst-support');started=time.perf_counter();omitted=[];error=None;index=None
try:
 for index,a in enumerate(json.loads(raw)['actions']):
  if index>=1616 and a['kind']=='shop' and a['shop']==6:omitted.append(index);continue
  r.replay_action(a)
except Exception as e:error=f'{type(e).__name__}: {e}'
report=dict(scope='Original-bytecode numerical full-route alternative for XP; no native/H5 completion or record proof',sourceProposalSHA256=hashlib.sha256(raw).hexdigest(),omittedSourceActions=omitted,error=error,lastProcessedSourceAction=index,resources=r.resources(),location=r.location(),generatedActions=len(r.actions),completeNumericalReplay=error is None and index==1712,actualGameReplayed=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');(out/'proposal-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources()},indent=2)+'\n');print(json.dumps(report))
