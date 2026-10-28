"""Bounded original-bytecode low-gold-shop experiment; no native/H5 record claim."""
import sys,json,time,hashlib,resource,argparse
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from flash_model import gate,ordinary_cost
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--swf',required=True);parser.add_argument('--out',default='generated/GoldShopStatReproduction');args=parser.parse_args()
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Expected pinned2018 archive')
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes();
if hashlib.sha256(raw).hexdigest()!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Source proposal changed')
actions=json.loads(raw)['actions'];out=Path(args.out);out.mkdir(exist_ok=False);r=OriginalRoute(args.swf,random_policy='worst-support');started=time.perf_counter();error=None;index=None
try:
 for index,a in enumerate(actions[:-1]):
  if 1555<=index<1609:continue
  if 1225<=index<1232:r.touch(a['floor'],*a['position'],shop_choice=3)
  elif 1616<=index<=1666:r.touch(a['floor'],*a['position'],shop_choice=3)
  else:r.replay_action(a)
except Exception as e:error=f'{type(e).__name__}: {e}'
res=r.resources();enemy_receipt=Path('experiments/full-route-native-gdut-hp28568.json');enemy_raw=enemy_receipt.read_bytes();observed=json.loads(enemy_raw)
if observed['originalSWFSHA256']!=hashlib.sha256(Path(args.swf).read_bytes()).hexdigest():raise ValueError('Final-enemy evidence uses a different SWF')
enemy=[observed['final'][f'battleEnemy.{field}'] for field in range(3)];gap=res['atk']-enemy[2];hits=(enemy[0]+gap-1)//gap if gap>0 else None
report=dict(scope='Original-bytecode prefix through source1711; finalBoss checked only with independent noncritical formula. No final bytecode/native/H5 completion or record proof',sourceProposalSHA256=hashlib.sha256(raw).hexdigest(),error=error,lastProcessedSource=index,resources=res,location=r.location(),goldShopPurchases=sum(a.get('shop')in(1,2)and a.get('choice')in(1,2,3)for a in r.actions),independentFinalBossCheck=dict(enemy=enemy,enemySourceReceipt=str(enemy_receipt),enemySourceReceiptSHA256=hashlib.sha256(enemy_raw).hexdigest(),gate=gate(enemy,res['hp'],res['atk'],res['def']),hits=hits,hpCost=ordinary_cost(enemy,res['atk'],res['def'])),metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),complete24Floors=False,recordBreakingRoute=False)
(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');(out/'proposal-private.json').write_text(json.dumps({'actions':r.actions,'resources':res}));print(json.dumps(report))
