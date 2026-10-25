"""Reproduce a bounded allocation search on the published 10088 route prefix.

Keep the enemy/door order through F13's first gold captain. Branch each existing
stat purchase between attack and defense, advance high gold purchases when cash
permits after source action 440, add one early cheap XP purchase, and reserve two
F6 large potions. Enumerate eight postponement sets for three earlier potions.
The DP keeps maximum HP for each (attack, defense, level) at a fixed step. Currency,
keys and consumed set are fixed within each schedule. Successful candidates must
also pass the original-bytecode adapter. This is not global optimality or play.
"""
import json,sys,time,itertools,hashlib,resource
from pathlib import Path
sys.path[:0]=['tools','src']
from original_route import OriginalRoute
from flash_model import gate,pre_damage,ordinary_cost
from route_sections import metadata
source=Path('experiments/full-route-ending-10088-proposal.json');
assert hashlib.sha256(source.read_bytes()).hexdigest()=='6ea34628fa4d8bd6eaa732ae0674951ccec90e5c1ce577852fe1bf1d2c921f4a'
p=json.loads(source.read_bytes());all_ev=p['actions'];end=next(i for i,a in enumerate(all_ev) if a['floor']==13 and a.get('originalTile')==55)
ev=all_ev[:end+1];cheap=[i for i,a in enumerate(ev) if a.get('shop')==5 and a.get('choice') in (2,3)];remove=-1;last_white=max(i for i,a in enumerate(ev) if a.get('originalTile')==50)
base=OriginalRoute('generated/private/mhhf.swf',random_policy='worst-support');enemies=base.root['boss_man'];initial=base.resources();best=[];summaries=[];verified=[];start=time.perf_counter()
potions=[i for i,a in enumerate(ev) if (a['floor'],a['position'],a.get('originalTile')) in [(7,[2,6],11),(7,[8,6],11),(2,[4,1],12)]]
original_ev=ev[:];income={i:ev[i]['resourcesAfter']['money']-(ev[i-1]['resourcesAfter']['money'] if i else 0) for i in range(len(ev))}
synthetic=[];schedule=[];cash=0
for i,a in enumerate(original_ev):
 if i>440 and a.get('shop')==2 and a.get('choice') in (2,3):continue
 schedule.append(i);cash+=income[i]
 if i>440:
  while cash>=100:
   synthetic.append(dict(kind='shop',shop=2,choice=2,floor=11,position=[5,8],originalTile=22,resourcesAfter=a['resourcesAfter']))
   schedule.append(len(original_ev)+len(synthetic)-1);cash-=100
ev+=synthetic
extra=len(ev);ev.append(dict(kind='shop',shop=5,choice=2,floor=5,position=[1,7],originalTile=26,resourcesAfter=original_ev[-1]['resourcesAfter']))
schedule.insert(schedule.index(last_white+1),extra)
print('scheduled',len(synthetic),'cash',cash,flush=True)
for bits in itertools.product([0,1],repeat=len(potions)):
 skip={i for i,b in zip(potions,bits) if b};order=[]
 for i in schedule:
  if i==last_white+1:order.extend(sorted(skip))
  if i not in skip and i not in (690,721):order.append(i)
 dp={(10,10,1):(1000,())};count=1;generated=0
 for i in order:
  a=ev[i];before=original_ev[i-1]['resourcesAfter'] if 0<i<len(original_ev) else initial;after=a['resourcesAfter'];new={}
  variable=a.get('shop') in (1,2,5,6) and a.get('choice') in (2,3)
  for (atk,df,level),(hp,choices) in dp.items():
   for c in ((2,3) if variable else (None,)):
    generated+=1;aa,dd,ll,hh=atk,df,level,hp;cc=choices
    if c:
     gain={1:4,2:20,5:5,6:17}[a['shop']];aa+=gain*(c==2);dd+=gain*(c==3);cc+=((i,c),)
    elif 'randomDraws' in a:
     tile=a['originalTile'];assert 40<=tile<=70 and tile!=53
     enemy=enemies[tile-40]
     if not gate(enemy,hp,atk,df,tile-40):continue
     hh-=pre_damage(tile-40,hp)+ordinary_cost(enemy,atk,df)
    else:
     aa+=after['atk']-before['atk'];dd+=after['def']-before['def'];ll+=after['level']-before['level'];hh+=after['hp']-before['hp']
    if hh<=0:continue
    key=(aa,dd,ll)
    if key not in new or new[key][0]<hh:new[key]=(hh,cc)
  dp=new;count+=len(dp)
  if not dp:break
 summary=dict(deferred=sorted(skip),survivors=len(dp),states=count,transitions=generated,stoppedAt=i,bestHP=max((h for h,c in dp.values()),default=None));summaries.append(summary);print(json.dumps(summary),flush=True)
 if (696,625,2) in dp:
  key=(696,625,2);hp,choices=dp[key];best.append((hp,key,choices,order,sorted(skip),count,generated));print('TARGET',hp,flush=True)
dp_elapsed=time.perf_counter()-start;print('DP seconds',dp_elapsed,flush=True)
for rank,(hp,key,choices,order,skip,count,generated) in enumerate(sorted(best,reverse=True)[:3]):
 r=OriginalRoute('generated/private/mhhf.swf',random_policy='worst-support');chosen=dict(choices)
 try:
  for i in order:
   a=ev[i].copy()
   if i in chosen:a['choice']=chosen[i]
   if a['kind']=='floor':r.take_stair(a['floor'],*a['position'])
   else:r.touch(a['floor'],*a['position'],shop_choice=a.get('choice'))
  assert (r.resources()['atk'],r.resources()['def'],r.resources()['level'])==key
  assert r.resources()['hp']==hp
  assert r.resources()['money']==78 and r.resources()['experience']==2314 and r.resources()['keys']==[3,1,3]
  d=Path('generated/PrefixAllocation31-'+str(rank));d.mkdir(exist_ok=True)
  result=dict(scope='Numeric original-bytecode proposal only, no native or record claim',randomPolicy=r.random_policy,planningConstraints={'shopCaps':{'1':12,'5':31}},actions=r.actions,resources=r.resources(),location=r.location(),draws=r.draws,sections=metadata(r.sections),allocation=dict(parentSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),advancedGoldPurchases=len(synthetic),addedCheapPurchase=True,reservedPotionActions=[690,721],deferred=skip,choices=chosen,states=count,transitions=generated,scope='Exact maximum surviving HP per ATK/DEF/level for this fixed consumption/order; not global route search'))
  (d/'proposal.json').write_text(json.dumps(result,indent=2)+'\n');verified.append(dict(directory=str(d),resources=r.resources(),actions=len(r.actions)));print('VERIFIED',str(d),r.resources(),flush=True)
 except Exception as e:print('REPLAY FAILED',i,str(e),flush=True)

if not verified:raise SystemExit('No bytecode-verified candidate')
summary=dict(scope='Fixed-order/schedule allocation DP with eight HP-postponement choices; no native run, no global route optimum.',sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),schedules=summaries,verified=verified,metrics=dict(dpElapsedSeconds=dp_elapsed,totalElapsedSeconds=time.perf_counter()-start,dpStates=sum(s['states'] for s in summaries),dpTransitions=sum(s['transitions'] for s in summaries),processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
Path('generated/prefix-allocation-31.json').write_text(json.dumps(summary,indent=2)+'\n')
