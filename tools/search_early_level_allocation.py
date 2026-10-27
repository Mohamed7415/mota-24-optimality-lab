"""Bounded real-map prefix with eight low-gold stats and one paid XP level.

The fixed encounter order advances the existing F5 left corridor/potion after
F7's potions. Purchases happen as soon as affordable after actual shop access;
only their ATK/DEF split is enumerated. Every retained final witness is replayed
through reviewed original bytecode, including path and shop affordability.
This does not search the remaining tower or prove global optimality.
"""
import argparse
import hashlib
import json
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]/'src')]
from original_route import OriginalRoute
from flash_model import gate, pre_damage, ordinary_cost
from route_sections import metadata

SOURCE = Path('experiments/full-route-hp28568-proposal.json')
SOURCE_SHA = '0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9'


def run(swf, out):
    started = time.perf_counter()
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Pinned proposal mismatch')
    actions = json.loads(raw)['actions']
    end = next(i for i,a in enumerate(actions) if a['floor']==8 and a.get('originalTile')==49)
    advance = [118,124,125,173,174,650,175,176,177,178]
    order = list(range(118))+advance+[i for i in range(118,end+1) if i not in advance]
    order = [i for i in order if actions[i]['kind']!='shop']
    base = OriginalRoute(swf, random_policy='worst-support')
    dp = {(10,10,0,0):(1000,())}
    gold = xp = 0
    keys = [0,1,1]
    gold_open = level = False
    labels, transitions = 1,0
    def keep(dst, key, value):
        if key not in dst or dst[key][0] < value[0]:
            dst[key] = value
    dp_started = time.perf_counter()
    for step,index in enumerate(order):
        action = actions[index]
        before = actions[index-1]['resourcesAfter'] if index else base.resources()
        after = action['resourcesAfter']
        gold += after['money']-before['money']
        xp += after['experience']-before['experience']
        keys = [k+b-c for k,b,c in zip(keys,after['keys'],before['keys'])]
        if min(keys)<0:
            raise ValueError('Fixed order overspends keys')
        new = {}
        for (atk,defense,g,x),(hp,path) in dp.items():
            aa,dd,hh = atk,defense,hp
            if 'randomDraws' in action:
                enemy_id = action['originalTile']-40
                enemy = base.root['boss_man'][enemy_id]
                if not gate(enemy,hh,aa,dd,enemy_id):
                    continue
                hh -= pre_damage(enemy_id,hh)+ordinary_cost(enemy,aa,dd)
            else:
                aa += after['atk']-before['atk']
                dd += after['def']-before['def']
                hh += after['hp']-before['hp']
            if index==178:
                if xp<100:
                    continue
                aa+=7;dd+=7;hh+=1000
            if hh>0:
                keep(new,(aa,dd,g,x),(hh,path))
        dp = new
        gold_open |= index==27
        level |= index==178
        for shop,cost,gain,cap,counter in [(1,25,4,8,2),(5,30,5,7,3)]:
            if shop==1 and not gold_open or shop==5 and not level:
                continue
            while True:
                new = {};bought=False
                for key,(hp,path) in dp.items():
                    budget = gold-25*key[2] if shop==1 else xp-100-30*key[3]
                    if budget>=cost and key[counter]<cap:
                        bought=True
                        for choice in (2,3):
                            transitions+=1
                            target=list(key);target[counter]+=1
                            target[0]+=gain*(choice==2);target[1]+=gain*(choice==3)
                            keep(new,tuple(target),(hp,path+((step,shop,choice),)))
                    else:
                        keep(new,key,(hp,path))
                dp=new
                if not bought:
                    break
        labels+=len(dp)
        if not dp:
            break
    dp_elapsed=time.perf_counter()-dp_started
    survivors=sorted([(hp,key,path) for key,(hp,path) in dp.items() if key[2:]==(8,7)],reverse=True) if step==len(order)-1 else []
    witnesses=[]
    for rank,(hp,key,path) in enumerate(survivors):
        route=OriginalRoute(swf,random_policy='worst-support')
        choices=defaultdict(list)
        for at,shop,choice in path:
            choices[at].append((shop,choice))
        for at,index in enumerate(order):
            route.replay_action(actions[index])
            if index==178:
                route.touch(5,1,7,shop_choice=1)
            for shop,choice in choices[at]:
                route.touch(3,5,0,shop_choice=choice) if shop==1 else route.touch(5,1,7,shop_choice=choice)
        expected=dict(hp=hp,atk=key[0],**{'def':key[1]},level=2,keys=keys,money=gold-200,experience=xp-310)
        if route.resources()!=expected:
            raise AssertionError('Original bytecode/resources disagree')
        proposal=dict(scope='Numerical prefix only; no native/full completion or record claim',randomPolicy=route.random_policy,
                      actions=route.actions,resources=route.resources(),location=route.location(),draws=route.draws,sections=metadata(route.sections))
        directory=out/str(rank);directory.mkdir(parents=True,exist_ok=False)
        data=(json.dumps(proposal,indent=2)+'\n').encode();(directory/'proposal.json').write_bytes(data)
        witnesses.append(dict(rank=rank,resources=expected,allocationChoices=path,originalBytecodeReplayPassed=True,
                              proposalSHA256=hashlib.sha256(data).hexdigest()))
    return dict(schemaVersion=1,scope='Exact ATK/DEF allocation in one fixed encounter/earliest-purchase schedule only; no global bound or native/record claim',
                sourceProposalSHA256=SOURCE_SHA,originalSWFSHA256=hashlib.sha256(Path(swf).read_bytes()).hexdigest(),
                randomPolicy='worst-support (draw199)',sourceOrder=order,insertedLevelAfterSource=178,
                lowGoldStatCount=8,cheapXPStatCount=7,cheapXPLevelCount=1,
                dominance='Retain maximum HP at identical ATK/DEF/purchase counters; fixed world, level, keys and currencies',
                storedLabels=labels,generatedPurchaseTransitions=transitions,sourceEndIndex=end,witnesses=witnesses,
                dpElapsedSeconds=dp_elapsed,totalElapsedSeconds=time.perf_counter()-started,
                processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swf',default='generated/private/mhhf.swf')
    parser.add_argument('--out',default='generated/EarlyLevelAllocation')
    parser.add_argument('--summary',default='generated/early-level-allocation.json')
    parser.add_argument('--check')
    args=parser.parse_args();result=run(args.swf,Path(args.out))
    if args.check:
        expected=json.loads(Path(args.check).read_text())
        def stable(value):
            return {k:([{a:b for a,b in w.items() if a!='proposalSHA256'} for w in v] if k=='witnesses' else v)
                    for k,v in value.items() if k not in ('originalSWFSHA256','dpElapsedSeconds','totalElapsedSeconds','processPeakRSSBytes')}
        if stable(result)!=stable(expected):
            raise AssertionError('Published bounded allocation changed')
    Path(args.summary).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sourceOrder','witnesses')}),flush=True)


if __name__=='__main__':
    main()
