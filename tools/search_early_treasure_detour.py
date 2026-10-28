"""Find the first feasible treasure detour in one fixed numerical prefix order.
Clock deadline is not simulated; actual native grant banner is still required.
"""
import json,sys,time,copy,argparse,hashlib
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--swf',required=True);parser.add_argument('--out',default='generated/EarlyTreasureReproduction');args=parser.parse_args()
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes()
if hashlib.sha256(raw).hexdigest()!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Source changed')
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Expected pinned2018 archive')
source=json.loads(raw)['actions'];r=OriginalRoute(args.swf,random_policy='worst-support');started=time.perf_counter();out=Path(args.out);out.mkdir(exist_ok=False)
for i,a in enumerate(source[:927]):
 r.replay_action(a)
 if r.resources()['keys'][2]<1:continue
 try:path=r.contact_path(16,3*11+5)
 except ValueError:continue
 before=r.resources();origin=r.location();trial=copy.deepcopy(r)
 try:
  trial.touch(16,5,3);trial.touch(16,5,4);trial.touch(16,4,4)
  if trial.root['mt_changes']!=1:raise ValueError('Treasure flag not granted')
 except Exception as e:print('FIRST_REACH_FAILED',i,str(e),flush=True);continue
 print('EARLY_GRANT',i,origin,'resources',trial.resources(),'addedActions',len(trial.actions)-len(r.actions),'elapsed',time.perf_counter()-started,flush=True)
 try:
  for j,b in enumerate(source[i+1:],i+1):
   if j in (927,928,929):continue
   trial.replay_action(b)
  result={'scope':'Early hidden-treasure insertion on a fixed numerical route only; no real-clock/native or record proof','sourceProposalSHA256':hashlib.sha256(raw).hexdigest(),'clockDeadlineSimulated':False,'treasureFlagGrantedInModel':True,'treasureGrantBannerObservedInGame':False,'generatedActions':len(trial.actions),'recordBreakingRoute':False,'insertAfterSourceAction':i,'addedPrefixActions':len(trial.actions)-len(source)+3,'resources':trial.resources(),'completeNumericalReplay':True,'lastSourceAction':j,'elapsedSeconds':time.perf_counter()-started}
 except Exception as e:result={'scope':'Early treasure insertion numeric attempt only','insertAfterSourceAction':i,'lastSourceAction':j,'error':str(e),'resources':trial.resources(),'completeNumericalReplay':False}
 (out/'receipt.json').write_text(json.dumps(result,indent=2));(out/'proposal-private.json').write_text(json.dumps({'actions':trial.actions,'resources':trial.resources()},indent=2));print(json.dumps(result),flush=True);break
else:print('NO_EARLIER_REACH',flush=True)
