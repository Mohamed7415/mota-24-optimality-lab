"""Bounded ordinary-input current-H5 compatibility pilot, not a full game solver.
Prepare the official UI in ranked极速 mode and enterMT1 first. Engine state is
read passively. Uses only reviewed original VM compilation offline; never
executes extracted H5 functions. Raw snapshots remain private under generated/.
"""
import json,urllib.request,time,hashlib,argparse
from visual_prefix_pilot import compile_plan,SOURCE_SHA
from h5_route_adapter import empty_path_to_contact,h5_prefix_expected
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--endpoint',required=True)
parser.add_argument('--swf',required=True)
parser.add_argument('--actions',type=int,choices=(29,184),default=29)
parser.add_argument('--start-index',type=int,default=0)
parser.add_argument('--prior')
parser.add_argument('--out',required=True)
args=parser.parse_args()
if not 0<=args.start_index<args.actions:raise ValueError('Invalid start index')
if args.start_index and not args.prior:raise ValueError('Resume requires the previous private receipt')
out=Path(args.out);out.mkdir(exist_ok=False)
endpoint=json.load(open(args.endpoint))['address']
plan=compile_plan(args.swf,args.actions)
source_actions=json.load(open('experiments/full-route-hp28568-proposal.json'))['actions']
def call(op,data={}):
 return json.load(urllib.request.urlopen(urllib.request.Request(endpoint+'/'+op,json.dumps(data).encode(),{'Content-Type':'application/json'}),timeout=25))
def resources(s):
 h=s['hero'];t=h['items']['tools'];return dict(hp=h['hp'],atk=h['atk'],def_=h['def'],level=h['lv'],money=h['money'],experience=h['exp'],keys=[t.get(k,0)for k in ['yellowKey','blueKey','redKey']])
def equal(s,exp,index):
 r=resources(s);e=h5_prefix_expected(exp,index);e['def_']=e.pop('def')
 return all(r[k]>=v if k=='hp' else r[k]==v for k,v in e.items())
def settle(s):
 for _ in range(20):
  if not s.get('lockControl') or s.get('event',{}).get('id'):return s
  s=call('press',{'keys':[],'wait':300})
 return s

def adjacent_path(s,target):
 return empty_path_to_contact(s['map'],(s['hero']['loc']['x'],s['hero']['loc']['y']),target)
records=[];started=time.monotonic();error=None;s=None
try:
 s=call('state')
 if s.get('cacheVersion')!=5767 or s['hero']['flags']['开启暴击'] is not False:raise ValueError('Unreviewed build or mode')
 if s.get('event',{}).get('id'):raise ValueError('Close the UI event before starting the pilot')
 if args.start_index:
  records=json.load(open(args.prior))['records']
  if len(records)!=args.start_index or records[-1]['sourceActionIndex']!=args.start_index-1:raise ValueError('Prior scope mismatch')
  if not equal(s,plan[args.start_index-1]['expectedResources'],args.start_index-1):raise ValueError('Current resources differ from prior')
 else:
  if s['floorId']!='MT1' or resources(s)!={'hp':1000,'atk':10,'def_':10,'level':1,'money':0,'experience':0,'keys':[0,1,1]}:raise ValueError('Expected a fresh natural MT1 entry')
 for action in plan[args.start_index:]:
  i=action['index'];source=source_actions[i];f=source['floor'];target=tuple(v+1 for v in source['position'])
  assert s['floorId']==f'MT{f}'
  for key,position in adjacent_path(s,target):
   before=resources(s);s=settle(call('press',{'keys':[key],'wait':130}))
   if s.get('event',{}).get('id') or resources(s)!=before:raise ValueError(f'Unexpected event/resource change while walking at source{i}')
   if (s['hero']['loc']['x'],s['hero']['loc']['y'])!=position:raise ValueError(f'Walking position mismatch at source{i}')
  loc=s['hero']['loc'];delta=(target[0]-loc['x'],target[1]-loc['y']);key={(0,-1):'ArrowUp',(0,1):'ArrowDown',(-1,0):'ArrowLeft',(1,0):'ArrowRight'}[delta]
  s=settle(call('press',{'keys':[key],'wait':600}))
  if action['kind']=='consume':
   for _ in range(30):
    if s.get('event',{}).get('type')!='text':break
    s=settle(call('press',{'keys':['Enter'],'wait':300}))
  if action['kind']=='shop':
   capture=call('capture');json.dump(capture,open(out/'shop-open.json','w'))
   if s.get('event',{}).get('type')!='choices':raise ValueError('Shop choice menu not open')
   selection=s['event'].get('selection') or 0
   count=len(s['event']['choices'])
   s=call('press',{'keys':['ArrowDown']*((action['choice']-1-selection)%count)+['Enter'],'wait':500})
   if not equal(s,action['expectedResources'],i):raise ValueError('Shop purchase resource mismatch')
   s=settle(call('press',{'keys':['Escape'] if action['choice']!=4 else [],'wait':400}))
  if s.get('event',{}).get('id'):raise ValueError(f'Unclosed event at source{i}')
  if s['floorId']!=f"MT{action['expectedFloor']}" or not equal(s,action['expectedResources'],i):raise ValueError(f'Source{i} resource/floor mismatch: {resources(s)}')
  capture=call('capture');records.append({'sourceActionIndex':i,'state':s,'capture':capture['path']});json.dump(records,open(out/'progress.json','w'),ensure_ascii=False)
  print(json.dumps({'sourceActionIndex':i,'floor':s['floorId'],'resources':resources(s)},ensure_ascii=False),flush=True)
except Exception as e:
 error=str(e)
 try:json.dump(call('capture'),open(out/'failure.json','w'),ensure_ascii=False)
 except Exception as capture_error:(out/'capture-error.txt').write_text(str(capture_error))
 print('FAILED',error,flush=True)
finally:
 json.dump({'scope':f'{args.actions}-action H5 compatibility prefix; no ending or record proof','sourceProposalSHA256':SOURCE_SHA,'requestedActions':args.actions,'matchedActions':len(records),'resumedFromSourceIndex':args.start_index,'priorReceiptSHA256':hashlib.sha256(Path(args.prior).read_bytes()).hexdigest() if args.prior else None,'error':error,'elapsedSeconds':time.monotonic()-started,'final':resources(s) if s and s.get('hero') else None,'records':records,'gameVariableReads':True,'gameVariableWrites':False,'seedControl':False,'introWatched': bool(s and s.get('route') and s['route'][0]=='choices:0'),'mode':'极速模式','buildCacheVersion':5767},open(out/'receipt.json','w'),ensure_ascii=False,indent=2)

if error:raise SystemExit(1)
