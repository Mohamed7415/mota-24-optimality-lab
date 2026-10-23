"""Audit native full-route progress. Does not certify a record or full completion."""
import argparse,hashlib,json,os,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from flash_model import combat_frames,pre_damage,gate
from game_milestone import rows,digest

def audit(directory,swf=None):
    d=Path(directory);native=json.loads((d/'fullroute-native.json').read_text());schema=json.loads((d/'observer-schema.json').read_text());timeline=rows(json.loads((d/'fullroute-traces.json').read_text()),schema['fields'])
    source=Path(swf or os.environ.get('MOTA_FLASH_SWF','generated/private/mhhf.swf'))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==native['originalSWFSHA256']
    assert hashlib.sha256((d/'observer.swf').read_bytes()).hexdigest()==native['observerSHA256']==schema['sha256']
    final_raw=native['final']
    victory=(final_raw['Now_line']==26 and final_raw['Now_hp']>0 and final_raw['_currentframe']>=4348 and final_raw['visibleMap.3'][5]==0)
    assert bool(native.get('complete24Floors'))==victory
    assert all(i['type']=='click' or i.get('key') in ('ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space') for i in native['inputs'])
    assert native['realClock'] and not native['seedControl'] and not native['gameVariableWrites'] and not native['errors']
    assert all(s['rootIsSelf'] for s in timeline if s['Now_line'] is not None)
    from original_route import OriginalRoute
    oracle=OriginalRoute(source,random_policy='worst-support')
    expected_battles=0;witness=[];battle_events=[]
    for b in native['events']:
        f=b['floor'];x,y=b['position']
        if b['kind']=='floor':
            expected=oracle.take_stair(f,x,y)
        else:
            tile=int(oracle.grid(f)[y][x]);assert tile==b['originalTile']
            expected_battles+=int(40<=tile<=70 or tile in (188,198))
            if 40<=tile<=70 or tile in (188,198):
                idx=31 if tile==188 else 32 if tile==198 else tile-40
                battle_events.append((idx,list(oracle.root['boss_man'][idx][:5]),b))
            # Shop number/choice are verified against the actual resource delta.
            if b['kind']=='shop':
                matches=[]
                for choice in (1,2,3,4):
                    from shop_model import transact
                    after=transact({k:int(oracle.root[k]) for k in __import__('original_route').RESOURCE_FIELDS},__import__('route_guidance').SHOPS[f,tile],choice)
                    r=b['after']
                    keys=[after[k] for k in ['Now_yellow','Now_blue','Now_red']]
                    if [after[k] for k in ['Now_gong','Now_fang','Now_life','Now_money','Now_mp']]==[r['atk'],r['def'],r['level'],r['money'],r['experience']] and keys==r['keys']:matches.append(choice)
                # HP purchase and exit are distinguished by the observed HP delta.
                if len(matches)>1:matches=[c for c in matches if c==1 and b['after']['hp']>b['before']['hp'] or c==4 and b['after']['hp']==b['before']['hp']]
                assert len(matches)==1,matches
                expected=oracle.touch(f,x,y,shop_choice=matches[0])
            else:expected=oracle.touch(f,x,y)
        actual=b['after'];assert actual['hp']>=expected['hp']
        assert all(actual[k]==v for k,v in expected.items() if k!='hp')
        witness.append({'kind':b['kind'],'floor':f,'position':[x,y],'resourcesAfter':expected})
    battles=[];active=None;previous=None
    for s in timeline:
        fighting=s['Display_kill']==1
        if fighting and active is None:
            enemy=[s[f'battleEnemy.{i}'] for i in range(5)];hero=[s[k] for k in ['Now_hp','Now_gong','Now_fang','Now_life']]
            assert all(isinstance(v,int) for v in enemy+hero)
            original_hp=previous['Now_hp'];index=s['Now_boss_id'];assert original_hp-pre_damage(index,original_hp)==hero[0]
            assert gate(enemy,original_hp,hero[1],hero[2],index)
            active={'enemyIndex':index,'enemy':enemy,'heroAfterPreDamage':hero,'heroHPBeforePreDamage':original_hp,'draws':[],'seen':set()}
        if fighting:
            n=s['mt_kills.kill_number']
            if n is not None and n%2==1 and n not in active['seen']:
                active['seen'].add(n);active['draws'].append(s['mt_kills.kill_max'])
        elif active is not None:
            trace,final=combat_frames(active['enemy'],active['heroAfterPreDamage'],active['draws'])
            assert final['Now_hp']==s['Now_hp'],(active,final,s['Now_hp'])
            active.pop('seen');active['heroHPAfter']=s['Now_hp'];active['matchedFrameModel']=True;battles.append(active);active=None
        previous=s
    assert active is None
    assert len(battles)==expected_battles
    for battle,(idx,enemy,event) in zip(battles,battle_events):
        before=event['before']
        assert battle['enemyIndex']==idx and battle['enemy']==enemy
        assert battle['heroHPBeforePreDamage']==before['hp']
        assert battle['heroAfterPreDamage'][1:]==[before['atk'],before['def'],before['level']]
        assert battle['heroHPAfter']==event['after']['hp']
    numeric_checkpoints=[{'name':c['name'],'state':{k:v for k,v in c['state'].items() if not k.startswith('visibleMap.')}} for c in native['checkpoints']]
    final={k:v for k,v in native['final'].items() if not k.startswith('visibleMap.')}
    times=[s['NowGameTime'] for s in timeline if isinstance(s['NowGameTime'],int)];assert max(times)>min(times)
    return {'schemaVersion':1,'status':'verified-full-route-progress-only','complete24Floors':bool(native.get('complete24Floors')),'recordBreakingRoute':False,'originalSWFSHA256':native['originalSWFSHA256'],'observerSHA256':native['observerSHA256'],'observedActions':len(native['events']),'ordinaryInputs':len(native['inputs']),'maximumObservedMapId':max(c['state']['Now_line'] for c in native['checkpoints']),'maximumObservedFloor':max(24 if c['state']['Now_line']==26 else 23 if c['state']['Now_line'] in (23,24,25) else c['state']['Now_line'] for c in native['checkpoints']),'final':final,'nativeClock':{'realClock':True,'seedControl':False,'observedGameSecondsMin':min(times),'observedGameSecondsMax':max(times)},'modelPolicy':'worst-support original-bytecode reconstruction from native semantic actions','actualHPAtLeastWorstSupportProposal':True,'actualBattles':battles,'actualDraws':sum(len(b['draws']) for b in battles),'battleFrameModelAllMatch':True,'inputs':native['inputs'],'inputSHA256':digest(native['inputs']),'reconstructedNumericWitnessSHA256':digest(witness),'events':native['events'],'checkpoints':numeric_checkpoints,'scope':'Unchanged native original with normal DOM inputs and read-only observer; real clock and uncontrolled RNG. Numerical proposal uses199 worst-support draws, not an attainable fixed PRNG tape claim. Full24-floor completion, observer-free control and record comparison remain outstanding. Current map arrays and screenshots remain private.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',nargs='?',default='generated/FullRoute');a=p.parse_args();r=audit(a.directory);Path(a.directory,'progress-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['observedActions','ordinaryInputs','maximumObservedFloor','actualDraws','battleFrameModelAllMatch']}))
