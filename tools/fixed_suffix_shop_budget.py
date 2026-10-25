"""Exact currency DP, conditional on a route's remaining rewards/key costs.

Relax all purchase timing, navigation and HP gates. Grant the largest possible
integer fairy bonus for total AD, ignoring its split. This is an upper bound for
the fixed remaining reward/door multiset, never a global original-game bound.
"""
import argparse,hashlib,json,resource,sys,time
from pathlib import Path

def purchase_values(budget,offers):
    values=[0]*(budget+1)
    for amount in range(budget+1):
        values[amount]=max([values[amount-1] if amount else 0]+[
            values[amount-cost]+gain for cost,gain in offers if cost<=amount])
    return values

def optimize(attack_defense,gold,xp,later_gold,later_xp,later_ad):
    if min(attack_defense,gold,xp,later_gold,later_xp,later_ad)<0:
        raise ValueError('Nonnegative resource budgets required')
    gv=purchase_values(gold+later_gold,[(25,4),(100,20)])
    xv=purchase_values(xp+later_xp,[(30,5),(95,17)])
    # A non-improving budget has the same AD and less money left, so only
    # improvement points can be optimal. This removes no better candidate.
    gs=[0]+[i for i in range(1,gold+1) if gv[i]>gv[i-1]]
    xs=[0]+[i for i in range(1,xp+1) if xv[i]>xv[i-1]]
    best=None;count=0
    for g in gs:
        for x in xs:
            before=attack_defense+gv[g]+xv[x]
            upper=before+before//3+later_ad+gv[gold-g+later_gold]+xv[xp-x+later_xp]
            candidate=(upper,g,x,before)
            if best is None or candidate>best:best=candidate
            count+=1
    return dict(upperAD=best[0],preBoostGoldSpent=best[1],preBoostXPSpent=best[2],
                preBoostAD=best[3],purchaseBudgetPairs=count,currencyDPCells=len(gv)+len(xv))

def from_route(path,prefix_actions):
    started=time.perf_counter();raw=Path(path).read_bytes();p=json.loads(raw);ev=p['actions']
    if not 0<prefix_actions<len(ev):raise ValueError('Invalid prefix length')
    state=ev[prefix_actions-1]['resourcesAfter']
    boosts=[i for i,a in enumerate(ev) if i>=prefix_actions and a['floor']==0 and
            a.get('originalTile')==24 and a['resourcesAfter']['atk']>ev[i-1]['resourcesAfter']['atk']]
    if len(boosts)!=1:raise ValueError('Require one remaining fairy boost')
    boost=boosts[0]
    gold=xp=ad=0;key_delta=0;reward_events=0
    for i,a in enumerate(ev[prefix_actions:],prefix_actions):
        before=ev[i-1]['resourcesAfter'];after=a['resourcesAfter']
        if a['kind']=='shop':
            if a['shop'] in (3,4):
                if i<=boost:raise ValueError('Choose prefix after pre-boost key trades')
                delta=after['money']-before['money'];gold+=delta;key_delta+=delta
            elif a['choice']==1:raise ValueError('HP/level purchases outside this bound')
            continue
        if i==boost:continue
        if i<boost:
            if after!=before:raise ValueError('Unmodelled pre-boost reward')
            continue
        ad+=after['atk']+after['def']-before['atk']-before['def']
        # Final floor has no legal exit in the checked route; its currency is
        # terminal income, not shop budget. Its feathers still count as AD.
        if a['floor']!=26:
            gold+=after['money']-before['money'];xp+=after['experience']-before['experience']
            reward_events+=int(after['money']!=before['money'] or after['experience']!=before['experience'])
    result=optimize(state['atk']+state['def'],state['money'],state['experience'],gold,xp,ad)
    achieved=p['resources']['atk']+p['resources']['def']
    return dict(schemaVersion=1,scope='Fixed-prefix and fixed remaining reward/key-cost multiset only; timing/HP/location relaxed. Not global native optimality.',
                proposalSHA256=hashlib.sha256(raw).hexdigest(),prefixActions=prefix_actions,prefix=state,
                remainingNetShopGold=gold,remainingShopXP=xp,remainingFreeAD=ad,keyTradeNetGold=key_delta,
                rewardEvents=reward_events,**result,routeFinalAD=achieved,attainsConditionalUpper=achieved==result['upperAD'],
                assumptions=['Use the exact remaining enemy/item rewards and key transactions in this route.',
                             'No extra resource source, save/load exploit, repeated reward or alternative reward timing.',
                             'No spending final-floor income before the ending.',
                             'Fairy AD is bounded by S+floor(S/3); actual split may be worse.'],
                metrics=dict(elapsedSeconds=time.perf_counter()-started,processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('proposal');parser.add_argument('--prefix-actions',type=int,required=True);parser.add_argument('--out');parser.add_argument('--check')
    args=parser.parse_args();result=from_route(args.proposal,args.prefix_actions)
    if args.check:
        expected=json.loads(Path(args.check).read_text())
        assert {k:v for k,v in result.items() if k!='metrics'}=={k:v for k,v in expected.items() if k!='metrics'},'Conditional budget changed'
    if args.out:Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
