"""Prepare a normal fresh ranked-speed H5 game using only observed UI choices.
No seed override, game function call, variable write or score submission.
"""
import argparse,hashlib,json,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--endpoint',required=True);p.add_argument('--out',required=True);p.add_argument('--resume-opening',action='store_true');args=p.parse_args()
out=Path(args.out);out.mkdir(exist_ok=False);endpoint=json.load(open(args.endpoint))['address'];started=time.monotonic();records=[]
def call(op,data={}):return json.load(urllib.request.urlopen(urllib.request.Request(endpoint+'/'+op,json.dumps(data).encode(),{'Content-Type':'application/json'}),timeout=25))
def capture(stage):
 r=call('capture');records.append({'stage':stage,**r,'imageSHA256':hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()});(out/'observations.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));return r['state']
while time.monotonic()-started<300:
 if call('status')['ready']:break
 time.sleep(2)
else:raise TimeoutError('Official game readiness')
s=call('state') if args.resume_opening else call('start');capture('resumed-opening' if args.resume_opening else 'normal-start');watched=bool(args.resume_opening and s.get('route',[])[:1]==['choices:0']);mode_selected=bool(args.resume_opening and s.get('hero',{}).get('flags',{}).get('开启暴击') is False)
for attempt in range(90):
 event=s.get('event')or{};kind=event.get('type');ident=event.get('id')
 if s.get('floorId')=='MT1' and not ident:
  h=s['hero'];keys=h['items']['tools']
  if s.get('cacheVersion')!=5767 or h['flags']['开启暴击']is not False:raise ValueError('Unreviewed build or mode')
  actual=[h[k]for k in ('hp','atk','def','lv','money','exp')]+[keys.get(k,0)for k in ('yellowKey','blueKey','redKey')]
  if actual!=[1000,10,10,1,0,0,0,1,1]:raise ValueError('Fresh opening resources differ')
  s=capture('verified-fresh-ranked-MT1');(out/'ready.json').write_text(json.dumps({'scope':'Fresh normal-input H5 opening only','watchedIntro':watched,'resumedExistingOpening':args.resume_opening,'speedModeSelected':mode_selected,'state':s,'gameVariableReads':True,'gameVariableWrites':False,'seedOverride':False,'recordBreakingRoute':False},ensure_ascii=False,indent=2));print('READY_FRESH_RANKED_MT1',flush=True);break
 if kind=='confirm' and event.get('text')=='是否观看片头？（十秒）' and not watched:
  selection=event.get('selection')or 0
  s=call('press',{'keys':(['ArrowLeft']if selection else[])+['Enter'],'wait':12000});watched=True;capture('intro-played');continue
 if kind=='choices' and not mode_selected:
  choices=event.get('choices')or[];matches=[i for i,v in enumerate(choices)if '极速' in v]
  if len(matches)!=1:raise ValueError(f'Unknown opening choices: {choices}')
  capture('mode-choice');selection=event.get('selection')or 0;s=call('press',{'keys':['ArrowDown']*((matches[0]-selection)%len(choices))+['Enter'],'wait':400});mode_selected=True;continue
 if kind in ('text','autoText') or ident=='text':
  s=call('press',{'keys':[]if kind=='autoText'else['Enter'],'wait':300});continue
 if not ident and s.get('floorId')=='MT0':
  h=s['hero'];loc=h['loc'];target=(loc['x'],loc['y']-1)
  if loc['x']!=6 or not 1<=loc['y']<=11:raise ValueError('Unreviewed opening position')
  tile=s['map'][target[1]][target[0]]
  if tile not in (0,124,81,87):raise ValueError('Unreviewed opening contact')
  if tile==124 and target!=(6,9):raise ValueError('Unknown opening NPC')
  if tile==81 and h['items']['tools'].get('yellowKey',0)<1:raise ValueError('Opening yellow key not granted')
  s=call('press',{'keys':['ArrowUp'],'wait':300});continue
 if not ident:
  s=call('press',{'keys':[],'wait':400});continue
 capture('unhandled-event');raise ValueError(f'Opening event not reviewed: {event}')
else:raise TimeoutError('Fresh opening did not finish within90 UI observations')
