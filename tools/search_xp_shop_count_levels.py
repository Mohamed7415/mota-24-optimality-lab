"""Finite original-bytecode XP purchase-count experiment using level purchases.
Actual game completion and same-build record comparison remain separate obligations.
"""
import argparse,hashlib,itertools,json,resource,sys,time
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from flash_model import gate
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--swf',required=True);p.add_argument('--out',required=True);p.add_argument('--repair-attack-gates',action='store_true');p.add_argument('--single-cap',type=int);p.add_argument('--single-late-attack',type=int);p.add_argument('--early-gold-attack',type=int,default=0);p.add_argument('--first13-attack',type=int,default=0);args=p.parse_args()
raw=Path('experiments/full-route-hp28568-proposal.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
if digest!='0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9':raise ValueError('Proposal mismatch')
if hashlib.sha256(Path(args.swf).read_bytes()).hexdigest()!='40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896':raise ValueError('Archive mismatch')
actions=json.loads(raw)['actions'];out=Path(args.out);out.mkdir(exist_ok=False);rows=[];started=time.perf_counter();best=None
recipes=list(itertools.product((40,42,44,46,47,48,49,50,55,60),(0,8,16,32,60))) if args.repair_attack_gates else list(itertools.product((46,47,48,49,50,55,60),(0,2,4,8)))
if args.single_cap is not None:recipes=[r for r in recipes if r[0]==args.single_cap]
if args.single_late_attack is not None:recipes=[r for r in recipes if r[1]==args.single_late_attack]
if not recipes:raise ValueError('Requested recipe is outside the declared grid')
for cap,late_attack in recipes:
 r=OriginalRoute(args.swf,random_policy='worst-support');purchases=0;early_redirected=0;repairs=[];error=None;index=None;t=time.perf_counter()
 try:
  for index,a in enumerate(actions):
   if a.get('shop') in (5,6) and a.get('choice')in (1,2,3):
    previous=actions[index-1] if index else {}
    if not(previous.get('shop')==a['shop'] and previous.get('choice')in(1,2,3)):
     cost=100 if a['shop']==5 else 270
     if index==829:
      for _ in range(args.first13_attack):
       if purchases>=cap or r.resources()['experience']<95:break
       r.touch(a['floor'],*a['position'],shop_choice=2);purchases+=1
     while purchases<cap and r.resources()['experience']>=cost:
      r.touch(a['floor'],*a['position'],shop_choice=1);purchases+=1
    continue
   if args.repair_attack_gates and a['kind']=='consume':
    tile=int(r.grid(a['floor'])[a['position'][1]][a['position'][0]])
    if 40<=tile<=70:
     enemy=r.root['boss_man'][tile-40]
     for _ in range(32):
      hero=r.resources()
      if gate(enemy,hero['hp'],hero['atk'],hero['def'],enemy_id=tile-40):break
      chosen=None
      for destination,position,cost in ((11,(5,8),100),(3,(5,0),25)):
       if r.root['Max_line']<=destination or r.resources()['money']<cost:continue
       try:r.contact_path(destination,position[1]*11+position[0])
       except ValueError:
        if r.root.get('jump_flag')!=1:continue
        r.fly(destination)
       try:r.contact_path(destination,position[1]*11+position[0])
       except ValueError:continue
       chosen=(destination,position);break
      if chosen is None:raise ValueError('No affordable reachable attack shop for the current gate')
      destination,position=chosen
      r.touch(destination,*position,shop_choice=2)
      repairs.append({'beforeSourceAction':index,'floor':destination})
     else:raise ValueError('Attack-gate repair exceeded32 purchases')
   if args.repair_attack_gates and a.get('shop')in(1,2) and a.get('choice')in(1,2,3):
    if r.resources()['money']<(25 if a['shop']==1 else 100):continue
   if index>=930 and a.get('shop')in(1,2) and a.get('choice')==3 and early_redirected<args.early_gold_attack:
    a={**a,'choice':2};early_redirected+=1
   if 1555<=index<1555+late_attack:r.touch(a['floor'],*a['position'],shop_choice=2)
   else:r.replay_action(a)
 except Exception as e:error=f'{type(e).__name__}: {e}'
 row=dict(recipe=dict(xpPurchaseCap=cap,lateGoldDefenseRedirectedToAttack=late_attack,earlyGoldDefenseRedirectedToAttack=args.early_gold_attack,first13FloorAttackPurchases=args.first13_attack),actualXPPurchases=purchases,goldAttackGateRepairs=repairs,completeNumericalReplay=error is None and index==1712,lastSourceAction=index,error=error,resources=r.resources(),generatedActions=len(r.actions),bytecodeInstructions=r.instructions,metrics=dict(elapsedSeconds=time.perf_counter()-t));rows.append(row)
 if row['completeNumericalReplay'] and (best is None or (purchases,-row['resources']['hp'])<(best['actualXPPurchases'],-best['resources']['hp'])):
  best=row;(out/'proposal-best-private.json').write_text(json.dumps({'actions':r.actions,'resources':r.resources(),'recipe':row['recipe']},indent=2));print('BEST',json.dumps(row),flush=True)
 print('CASE',json.dumps(row),flush=True)
 report=dict(schemaVersion=1,scope='Finite XP-level purchase-cap recipes in2018 numerical VM; no actual-game or record proof',sourceProposalSHA256=digest,cases=len(recipes),completed=len(rows),complete=len(rows)==len(recipes),best=best,rows=rows,goldGateRepairEnabled=args.repair_attack_gates,unaffordableOriginalGoldPurchasesSkipped=args.repair_attack_gates,clockDeadlineSimulated=False,actualGameReplayed=False,recordBreakingRoute=False,metrics=dict(elapsedSeconds=time.perf_counter()-started,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),totalBytecodeInstructions=sum(x['bytecodeInstructions']for x in rows)))
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print('COMPLETE',json.dumps({k:v for k,v in report.items()if k!='rows'}),flush=True)
