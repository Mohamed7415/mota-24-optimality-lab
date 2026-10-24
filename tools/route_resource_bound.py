"""Optimistic AD budget of a fixed post-21 numeric prefix, not a global theorem.

All remaining tile rewards, all keys sold without door costs, and free unclaimed
one-time equipment are granted. Shops convert gold at <=1/5 AD per gold and XP
at <=17/95 AD per XP. This bounds the declared numeric once-only reward model;
it is not an audit of every native callback or a native no-solution certificate.
"""
import argparse,hashlib,json,sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from original_route import OriginalRoute

def bound(r):
    assert all(r.root[k]==1 for k in ['Set_man_01','Set_man_02','Display_kills'])
    assert all(24 not in row for row in r.grid(0)), 'Unclaimed fairy boost needs a different bound'
    state=r.resources();gold=state['money'];xp=state['experience'];keys=state['keys'][:]
    attack=state['atk'];defense=state['def'];counts=Counter();hp_pickups=0;holy_water=0
    for f in range(27):
        for y,row in enumerate(r.grid(f)):
            for x,t in enumerate(row):
                t=int(t)
                if 40<=t<=70 or t in (188,198):
                    idx=31 if t==188 else 32 if t==198 else t-40
                    enemy=r.root['boss_man'][idx];gold+=int(enemy[3]);xp+=int(enemy[4]);counts['remainingEnemies']+=1
                elif t in (6,7,8):keys[t-6]+=1
                elif t==36:keys=[k+1 for k in keys]
                elif t==39:gold+=300
                elif t==10:attack+=3
                elif t==9:defense+=3
                elif t in (30,31):
                    n=1 if t==30 else 3;attack+=10*n;defense+=10*n;hp_pickups+=1000*n
                elif 71<=t<=75:attack+=[10,40,70,110,150][t-71]
                elif 76<=t<=80:defense+=[10,30,85,120,190][t-76]
                elif t in (11,12):hp_pickups+=200 if t==11 else 500
                elif t==33:holy_water+=1
                elif (f,x,y,t)==(2,7,10,26):attack+=70
                elif (f,x,y,t)==(2,9,10,27):defense+=30
                elif (f,x,y,t)==(15,4,3,26):attack+=120
                elif (f,x,y,t)==(15,6,3,27):defense+=120
    key_sale=sum(k*p for k,p in zip(keys,[7,35,70]));gold+=key_sale
    maximum=Fraction(attack+defense)+Fraction(gold,5)+Fraction(xp*17,95)
    return dict(scope='Conditional optimistic upper bound for this fixed numeric prefix; not global native optimality or native impossibility.',current=state,relaxedFixedAttack=attack,relaxedFixedDefense=defense,totalAvailableGoldIgnoringDoorCosts=gold,totalAvailableXP=xp,relaxedKeySaleGold=key_sale,remainingHPPickups=hp_pickups,remainingHolyWater=holy_water,counts=dict(counts),optimisticFinalADUpper=maximum.numerator//maximum.denominator,formula='fixed AD + gold/5 + 17*XP/95; grant all remaining rewards and ignore all door and NPC costs',canExceedPublished10088WithinThisModel=maximum>=10089)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('proposal');p.add_argument('swf');p.add_argument('--out');p.add_argument('--check');a=p.parse_args();proposal_bytes=Path(a.proposal).read_bytes();old=json.loads(proposal_bytes);r=OriginalRoute(a.swf,random_policy=old['randomPolicy'])
    for event in old['actions']:
        f=event['floor'];x,y=event['position']
        actual=r.take_stair(f,x,y) if event['kind']=='floor' else r.touch(f,x,y,shop_choice=event.get('choice'))
        assert actual==event['resourcesAfter']
    result=bound(r);result['proposalSHA256']=hashlib.sha256(proposal_bytes).hexdigest();result['originalSWFSHA256']=hashlib.sha256(Path(a.swf).read_bytes()).hexdigest()
    if a.check and result!=json.loads(Path(a.check).read_text()):raise ValueError('Conditional AD bound differs from checked numeric report')
    if a.out:Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
