"""Exact event-frontier search for a declared, restricted REAL floor.
Never claims a whole-tower or Flash optimum. No dynamic event/code evaluation.
"""
import argparse, hashlib, json, math, platform, resource, sys, time
from collections import deque
from pathlib import Path

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def damage(enemy,atk,defense):
 if enemy['special']!=0:raise ValueError('Unsupported special')
 delta=atk-enemy['def']
 if delta<=0:return None
 return ((enemy['hp']-1)//delta)*max(0,enemy['atk']-defense)

def model(t,floor_id='MT1'):
 f=t['floors'][floor_id]['data'];values=t['config']['values']['data']
 for key in ['events','afterBattle','afterGetItem','afterOpenDoor','cannotMove']:
  if f.get(key):raise ValueError('Unsupported floor scripts: '+key)
 if f.get('firstArrive'):raise ValueError('Unsupported firstArrive')
 if t['config']['flags']['data']['equipment']:raise ValueError('Equipment mode unsupported')
 if t['config']['flags']['data']['enableNegativeDamage']:raise ValueError('Negative damage unsupported')
 initial=t['config']['firstData']['data']['hero'];assert initial['mdef']==0
 # Derive starting keys from MT0's firstArrive data; whitelist only the three known setValue forms.
 keys=dict(initial['items']['keys']);origins=[]
 for e in t['floors']['MT0']['data']['firstArrive']:
  if isinstance(e,dict) and e.get('type')=='setValue':
   name=e['name'].removeprefix('item:')
   if name not in keys or e['value']!=e['name']+'+1':raise ValueError('Unrecognized initial event')
   keys[name]+=1;origins.append({'name':e['name'],'value':e['value']})
 changes=f['changeFloor'];entry=[tuple(map(int,k.split(','))) for k,v in changes.items() if v['floorId']=='MT0'];exits=[tuple(map(int,k.split(','))) for k,v in changes.items() if v['floorId']=='MT2']
 if len(entry)!=1 or len(exits)!=1 or len(changes)!=2:raise ValueError('Expected MT1 entry and exit')
 start=entry[0][1]*13+entry[0][0];target=exits[0][1]*13+exits[0][0]
 effects={'redJewel':('atk',values['redJewel']),'blueJewel':('def',values['blueJewel']),'redPotion':('hp',values['redPotion']),'bluePotion':('hp',values['bluePotion'])}
 doors={'yellowDoor':0,'blueDoor':1,'redDoor':2};keynames=['yellowKey','blueKey','redKey'];objects={};empty=set();blocked=[]
 for y,row in enumerate(f['map']):
  for x,raw in enumerate(row):
   if not isinstance(raw,int):raise ValueError('Disabled/dynamic tile unsupported')
   pos=y*13+x
   if raw==0:empty.add(pos);continue
   if pos==start:continue # arrival is allowed; stepping back onto this stair exits scope
   if pos==target:continue
   tile=t['tiles'][str(raw)]['data'];id=tile['id'];cls=tile['cls'];effect=None
   if cls=='enemys':
    enemy=t['enemies']['data'][id]
    if enemy['special']!=0:raise ValueError('Special monster '+id)
    effect=('battle',enemy)
   elif cls=='items':
    if id in keynames:effect=('key',keynames.index(id))
    elif id in effects:effect=('stat',effects[id])
    elif id=='book':effect=('book',None) # no movement/stat/combat effect in scope
    else:raise ValueError('Unsupported item '+id)
   elif id in doors:effect=('door',doors[id])
   elif cls=='terrains' and id.endswith('Wall'):blocked.append(pos);continue
   else:raise ValueError('Unsupported tile '+id)
   objects[pos]={'index':len(objects),'id':id,'effect':effect,'xy':[x,y]}
 neighbors={p:tuple(q for q in [p-13,p+13,p-1,p+1] if 0<=q<169 and abs(q%13-p%13)+abs(q//13-p//13)==1) for p in range(169)}
 def region(pos,mask):
  seen={pos};stack=[pos];front=set();exit_reachable=False
  while stack:
   p=stack.pop()
   for q in neighbors[p]:
    if q==target:exit_reachable=True;continue
    if q in seen:continue
    if q in empty or (q in objects and mask>>objects[q]['index']&1):seen.add(q);stack.append(q)
    elif q in objects:front.add(q)
  return min(seen),sorted(front),exit_reachable
 initial_state=(0,start,initial['hp'],initial['atk'],initial['def'],tuple(keys[k] for k in keynames),initial['money'],initial['experience'])
 return {'floor':f,'objects':objects,'region':region,'initial':initial_state,'target':target,'start':start,'initialOrigins':origins,'blocked':blocked}

def transition(state,obj,pos):
 mask,_,hp,atk,defense,keys,money,exp=state;keys=list(keys);kind,value=obj['effect'];cost=0
 if kind=='battle':
  cost=damage(value,atk,defense)
  if cost is None or hp<=cost:return None
  hp-=cost;money+=value['money'];exp+=value['experience']
 elif kind=='key':keys[value]+=1
 elif kind=='door':
  if keys[value]<=0:return None
  keys[value]-=1
 elif kind=='stat':
  stat,delta=value
  if stat=='hp':hp+=delta
  elif stat=='atk':atk+=delta
  elif stat=='def':defense+=delta
 elif kind!='book':raise ValueError(kind)
 return (mask|1<<obj['index'],pos,hp,atk,defense,tuple(keys),money,exp),cost

def solve(t,max_states=1000000,seconds=60):
 m=model(t);objects=m['objects'];region=m['region'];initial=m['initial'];starttime=time.perf_counter()
 # Same mask fixes all resources except HP; component representative fixes available actions.
 # Normal enemies have HP-independent damage, so max HP is a sound dominance relation here.
 def key(s):return (s[0],region(s[1],s[0])[0])
 nodes=[(initial,None,None)];bestlabel={key(initial):0};queue=deque([0]);best=None;expanded=0;generated=0;dominated=0;peakqueue=1;complete=True;reason='frontier exhausted'
 while queue:
  if expanded>=max_states or time.perf_counter()-starttime>seconds:complete=False;reason='resource limit';break
  idx=queue.popleft();s=nodes[idx][0];k=key(s)
  if bestlabel[k]!=idx:continue
  expanded+=1;_,front,exit_reachable=region(s[1],s[0])
  if exit_reachable and (best is None or s[2]>nodes[best][0][2]):best=idx
  # Reaching exit adjacency permits choosing to wait/turn back. Exit tile itself terminates.
  for pos in front:
   out=transition(s,objects[pos],pos)
   if out is None:continue
   ns,cost=out;generated+=1;nk=key(ns);old=bestlabel.get(nk)
   if old is not None and nodes[old][0][2]>=ns[2]:dominated+=1;continue
   action={'position':objects[pos]['xy'],'tileId':objects[pos]['id'],'hpCost':cost}
   ni=len(nodes);nodes.append((ns,idx,action));bestlabel[nk]=ni;queue.append(ni)
  peakqueue=max(peakqueue,len(queue))
 elapsed=time.perf_counter()-starttime;path=[];terminal=None
 if best is not None:
  p=best;terminal=nodes[p][0]
  while nodes[p][1] is not None:path.append(nodes[p][2]);p=nodes[p][1]
  path.reverse()
 result={'schemaVersion':1,'experiment':'MT1-first-ascent-max-exit-HP','upstreamCommit':t['upstream']['commit'],'floorHash':digest(m['floor']),'dataHash':digest(t),'objective':'maximize HP when first stepping from MT1 into MT2, with no other-floor detours','scope':'ONLY remake MT1 from post-MT0 initial stats/keys; not Flash and not full tower','complete':complete,'stopReason':reason,'bestExitHP':terminal[2] if terminal else None,'optimumInterval':[terminal[2],terminal[2]] if complete and terminal else [terminal[2] if terminal else None,None],'metrics':{'expandedLabels':expanded,'generatedTransitions':generated,'uniqueMaskComponents':len(bestlabel),'storedLabels':len(nodes),'dominatedTransitions':dominated,'peakQueue':peakqueue,'elapsedSeconds':elapsed,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),'rssDefinition':'process lifetime peak RSS, includes JSON load; isolated CLI process recommended'},'environment':{'python':platform.python_version(),'platform':platform.platform()},'finiteModel':{'consumableObjects':len(objects),'cells':169,'maskBound':str(2**len(objects)),'hpUpperBound':initial[2]+sum(o['effect'][1][1] for o in objects.values() if o['effect'][0]=='stat' and o['effect'][1][0]=='hp'),'allActionsConsumeOneNewBit':True},'initial':{'hp':initial[2],'atk':initial[3],'def':initial[4],'keys':initial[5],'position':[m['start']%13,m['start']//13],'keyEvents':m['initialOrigins']},'bestFinal':{'hp':terminal[2],'atk':terminal[3],'def':terminal[4],'keys':terminal[5],'money':terminal[6],'experience':terminal[7]} if terminal else None,'route':path,'routeHash':digest(path),'assumptions':['No MT0 return, no MT2 detour, no shops, no clock or RNG.','Floor scripts/hooks empty; all present enemies special=0; mdef=0.','Starting stair can be left at initial arrival but cannot be re-entered; touching upper stair ends experiment.','Book pickup has no stat effect. Walking within a cleared component is free for this HP objective.'],'proofArgument':'Every meaningful action removes exactly one item/enemy/door. Flood fill enumerates every reachable frontier action. Identical consumed mask fixes stats/keys/rewards. Within the same free component, a higher-HP label dominates because all supported battle costs are HP-independent. Exhausting this finite quotient establishes the stated local optimum, conditional on the declared transition model.'}
 if terminal:result['replay']=replay(t,path,expected_hp=terminal[2])
 return result

def replay(t,path,expected_hp=None):
 m=model(t);s=m['initial']
 for i,a in enumerate(path):
  p=a['position'][1]*13+a['position'][0];_,front,_=m['region'](s[1],s[0])
  if p not in front:raise ValueError(f'Route action {i} is not reachable')
  o=m['objects'][p]
  if o['id']!=a['tileId']:raise ValueError('Tile mismatch')
  out=transition(s,o,p)
  if out is None:raise ValueError('Illegal route')
  s,cost=out
  if cost!=a['hpCost']:raise ValueError('Damage mismatch')
 if not m['region'](s[1],s[0])[2]:raise ValueError('Exit not reachable')
 if expected_hp is not None and s[2]!=expected_hp:raise ValueError('Final HP mismatch')
 return {'valid':True,'interactions':len(path),'exitHP':s[2]}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('--out',default='experiments/mt1.json');ap.add_argument('--max-states',type=int,default=1000000);ap.add_argument('--seconds',type=float,default=60);a=ap.parse_args();t=json.loads(Path(a.data).read_text());r=solve(t,a.max_states,a.seconds);Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['route','proofArgument','assumptions']},ensure_ascii=False,indent=2))
