"""Recheck published numeric receipts; optionally reconstruct a native proposal.

This checks internal consistency against the pinned original, not authenticity
of private traces, observer-free equivalence, full completion or a record.
"""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from original_route import OriginalRoute,RESOURCE_FIELDS
from route_guidance import SHOPS
from shop_model import transact
from flash_model import combat_frames,pre_damage,gate
from game_milestone import digest

def verify(evidence,swf,proposal_out=None):
    receipt=json.loads(Path(evidence).read_text())
    assert hashlib.sha256(Path(swf).read_bytes()).hexdigest()==receipt['originalSWFSHA256']
    assert receipt['inputSHA256']==digest(receipt['inputs'])
    assert receipt['observedActions']==len(receipt['events'])
    assert receipt['ordinaryInputs']==len(receipt['inputs'])
    assert all(i['type']=='click' or i.get('key') in ('ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','j','2') for i in receipt['inputs'])
    r=OriginalRoute(swf,random_policy='worst-support');battle=0;previous=r.resources();witness=[]
    for index,event in enumerate(receipt['events']):
        assert event['index']==index
        if previous is not None:assert event['before']==previous
        f=event['floor'];x,y=event['position'];before=event['before'];actual=event['after']
        if event['kind']=='fly':
            assert r.location()==(f,y*11+x)
            expected=r.fly(event['toFloor'])
        elif event['kind']=='floor':expected=r.take_stair(f,x,y)
        else:
            tile=int(r.grid(f)[y][x]);assert tile==event['originalTile']
            if 40<=tile<=70 or tile in (188,198):
                idx=31 if tile==188 else 32 if tile==198 else tile-40
                enemy=list(r.root['boss_man'][idx][:5]);b=receipt['actualBattles'][battle];battle+=1
                hero=[before['hp']-pre_damage(idx,before['hp']),before['atk'],before['def'],before['level']]
                assert b['enemyIndex']==idx and b['enemy']==enemy
                assert b['heroHPBeforePreDamage']==before['hp'] and b['heroAfterPreDamage']==hero
                assert gate(enemy,before['hp'],before['atk'],before['def'],idx)
                assert all(isinstance(v,int) and 0<=v<200 for v in b['draws'])
                _,result=combat_frames(enemy,hero,b['draws'])
                assert result['Now_hp']==b['heroHPAfter']==actual['hp']
            choice=None
            if event['kind']=='shop':
                matches=[]
                for c in (1,2,3,4):
                    a=transact({k:int(r.root[k]) for k in RESOURCE_FIELDS},SHOPS[f,tile],c)
                    if [a[k] for k in RESOURCE_FIELDS[1:]]==[actual['atk'],actual['def'],actual['level'],*actual['keys'],actual['money'],actual['experience']]:
                        if actual['hp']-before['hp']==a['Now_hp']-r.resources()['hp']:matches.append(c)
                # Unaffordable choices and exit are observational identities.
                # Reconstruct the harmless exit rather than claim an intent.
                if len(matches)>1 and 4 in matches:matches=[4]
                assert len(matches)==1,matches;choice=matches[0]
            expected=r.touch(f,x,y,shop_choice=choice)
        assert actual['hp']>=expected['hp']
        assert all(actual[k]==v for k,v in expected.items() if k!='hp')
        witness.append({'kind':event['kind'],'floor':f,'position':[x,y],**({'toFloor':event['toFloor']} if event['kind']=='fly' else {}),'resourcesAfter':expected})
        previous=actual
    assert battle==len(receipt['actualBattles'])
    assert receipt['actualDraws']==sum(len(b['draws']) for b in receipt['actualBattles'])
    assert receipt['reconstructedNumericWitnessSHA256']==digest(witness)
    final=receipt['final']
    assert previous==dict(hp=final['Now_hp'],atk=final['Now_gong'],**{'def':final['Now_fang']},level=final['Now_life'],keys=[final[k] for k in RESOURCE_FIELDS[4:7]],money=final['Now_money'],experience=final['Now_mp'])
    if receipt.get('complete24Floors'):
        assert final['Now_line']==26 and final['_currentframe']>=4348 and final['Now_hp']>0
        assert r.location()[0]==26 and r.grid(26)[3][5]==0 and 'game_over' in r.timeline
        ending=receipt['nativeEnding']
        assert ending=={'mapId':26,'rootFrame':final['_currentframe'],'finalBossTile':0,'heroAlive':True}
    if proposal_out:
        Path(proposal_out).write_text(json.dumps({'scope':'Reconstructed numeric prefix; no full-game or record claim','randomPolicy':r.random_policy,'actions':r.actions,'resources':r.resources(),'location':r.location()},indent=2)+'\n')
    return {'verifiedActions':len(receipt['events']),'verifiedBattles':battle,'worstSupportFinal':r.resources(),'scope':'Published numeric receipt consistency only; no record certification'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('swf');p.add_argument('--proposal-out');a=p.parse_args()
    print(json.dumps(verify(a.evidence,a.swf,a.proposal_out)))
