"""Run M8 restricted real-map continuation; prepare a native movie input plan."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from flash_sections import sections,SWF_SHA
from flash_replay import prepare
from make_game_plan import make as base_plan
from crossfloor_search import World,solve
from game_observer import make as observer

def make(filename,width=1024,depth=140):
    plan=base_plan(filename);w,_=prepare(sections(filename))
    grids={str(f):[[int(t) for t in row] for row in w[f'mt_line_0{f}']] for f in [1,2,3]}
    for a in plan['seedSearch']['route']:
        x,y=a['position'];grids['1'][y][x]=0
    world=World(grids,w['boss_man']);initial=(0,world.landings[2,97],860,10,10,1,1,0,4,4,301989949)
    result=solve(world,initial,width,depth)
    result['inputDataFingerprints']={k:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest() for k,v in {'threeFloorsAfterFrozenPrefix':grids,'ordinaryEnemyTable':world.enemies}.items()}
    gold_budget=initial[8]+sum(world.enemies[t-40][3] for _,t in world.objects.values() if 40<=t<=70)
    result['finiteResourceCertificate']={'consumableEvents':len(world.objects),'totalAvailableGoldIncludingInitial':gold_budget,'maximumShopPurchases':gold_budget//25,'maximumResourceChangingActions':len(world.objects)+gold_budget//25,'strictRank':'(N - popcount(mask))*(B+1) + money; N=consumableEvents, B=totalAvailableGoldIncludingInitial','rankArgument':'Always 0<=money<=B. Consumption decreases N-popcount by1 and can raise money by at most B; shop purchase lowers money by25. Thus every retained transition strictly lowers a nonnegative integer rank. Walking/stairs are contracted.'}
    result|={'milestone':'M8','sourceSWFSHA256':SWF_SHA,'scope':{'objective':'Maximum HP on return to MT1 after the fixed M6 MT2 arrival; any finite sequence in restricted floors 1..3','prefixFrozen':True,'initialRngState':301989949,'ruffleSeed':128188416,'level':1,'allowed':'Ordinary enemies, doors 2/3/4, items 6..12 and 71, stairs within floors1..3, gold shop1 choices1..3','blockedTileIDs':[1,5,21,23,26,27,34,115],'blockedBoundaryCrossings':['MT1 to MT0','MT3 to MT4'],'excluded':'Plot/NPC/iron-door events, book UI, other shops, save/load, restart, real clock, other RNG consumption, alternate opening prefixes','globalOrThreeFloorOptimalityProven':False},'upperBoundArgument':'Current HP + all unconsumed HP potions + 800*floor((current gold + gold of all unconsumed ordinary enemies)/25). All damage is nonnegative, each resource event is once-only, only shop1 HP purchases raise HP otherwise. Ignore reachability, gates and all damage; no attack/defense spending. An upper bound for this restricted continuation only.','finitenessArgument':'Each consumed tile strictly increases a finite bitmask; between consumptions each successful shop purchase strictly decreases nonnegative integer gold by25. Gold rewards are fixed finite once-only tile rewards. Free walking/stairs/menu identities are contracted. Thus finite resource-changing paths and finite RNG states, with all exact integer resources bounded by finite rewards. This proves the restricted model finite, not whole-game finiteness.'}
    out=Path('generated/M8');out.mkdir(parents=True,exist_ok=True)
    (out/'search-M8.json').write_text(json.dumps(result,indent=2)+'\n')
    touched={(1,*a['position']) for a in plan['seedSearch']['route']}
    touched|={(a['floor'],*a['position']) for a in result['actions'] if a['kind']=='consume'}
    extras=['Display_buy','mt_buy_list._currentframe','mt_buy_list.now_case_id']+[f'mt_line_0{f}.{y}.{x}' for f,x,y in sorted(touched)]
    observer(str(out),extras)
    plan['extension']={'milestone':'M8','scope':result['scope'],'grids':grids,'actions':result['actions'],'finalResources':result['finalResources']}
    (out/'game-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['bestReturnHP','admissibleInitialUpperHP','metrics','stoppingReason']}));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--width',type=int,default=1024);p.add_argument('--depth',type=int,default=140);a=p.parse_args();make(a.swf,a.width,a.depth)
