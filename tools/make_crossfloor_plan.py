"""Concrete real-map cross-floor witness, NOT an optimal route certificate."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from flash_sections import sections,SWF_SHA
from flash_replay import prepare
from make_game_plan import make as base_plan
from seed_search import battle
from flash_model import gate
from shop_model import transact
from game_observer import make as observer

def make(filename):
    plan=base_plan(filename);w,_=prepare(sections(filename));grids={str(f):[[int(t) for t in r] for r in w[f'mt_line_0{f}']] for f in [1,2,3]}
    for a in plan['seedSearch']['route']:
        x,y=a['position'];grids['1'][y][x]=0
    s=dict(Now_hp=860,Now_gong=10,Now_fang=10,Now_life=1,Now_yellow=1,Now_blue=1,Now_red=0,Now_money=4,Now_mp=4)
    rng=plan['seedSearch']['route'][-1]['rngStateAfter'];floor=2;actions=[]
    def resources():return dict(hp=s['Now_hp'],atk=s['Now_gong'],def_=s['Now_fang'],keys=[s['Now_yellow'],s['Now_blue'],s['Now_red']],money=s['Now_money'],experience=s['Now_mp'])
    def receipt():
        r=resources();r['def']=r.pop('def_');return {k:r[k] for k in ['hp','atk','def','keys','money','experience']}
    def stair(new):
        nonlocal floor
        tile=13 if new>floor else 14;positions=[(x,y) for y,row in enumerate(grids[str(floor)]) for x,t in enumerate(row) if t==tile];assert len(positions)==1
        actions.append({'kind':'floor','floor':floor,'position':list(positions[0]),'toFloor':new,'resourcesAfter':receipt()});floor=new
    def consume(x,y):
        nonlocal rng
        t=grids[str(floor)][y][x];draws=[];cost=0
        if 40<=t<=70:
            e=w['boss_man'][t-40]
            if not gate(e,s['Now_hp'],s['Now_gong'],s['Now_fang']):raise ValueError(f'Gate rejected F{floor} {(x,y)} {s}')
            cost,rng,draws=battle(e[0],s['Now_gong']-e[2],max(0,e[1]-s['Now_fang']),rng,128188416);s['Now_hp']-=cost;s['Now_money']+=e[3];s['Now_mp']+=e[4]
        elif t in [2,3,4]:
            key=['Now_yellow','Now_blue','Now_red'][t-2];assert s[key]>0;s[key]-=1
        elif t in [6,7,8]:s[['Now_yellow','Now_blue','Now_red'][t-6]]+=1
        elif t==71:s['Now_gong']+=10
        elif t==10:s['Now_gong']+=3
        elif t==11:s['Now_hp']+=200
        else:raise ValueError(f'Unsupported tile {t}')
        actions.append({'kind':'consume','floor':floor,'position':[x,y],'originalTile':t,'hpCost':cost,'randomDraws':list(draws),'rngStateAfter':rng,'resourcesAfter':receipt()});grids[str(floor)][y][x]=0
    stair(3)
    for x,y in [(4,8),(0,6),(0,5),(1,3),(1,2),(2,0),(1,0),(0,0),(1,1)]:consume(x,y)
    stair(2);stair(1)
    for x,y in [(3,2),(2,2),(0,2),(2,3)]:consume(x,y)
    stair(2);stair(3)
    for x,y in [(3,5),(4,5),(5,5),(5,3),(5,2)]:consume(x,y)
    before=copy.deepcopy(s);s=transact(s,1,1);assert s!=before
    actions.append({'kind':'shop','floor':3,'position':[5,0],'shop':1,'choice':1,'resourcesBefore':{k:before[k] for k in before},'resourcesAfter':receipt()})
    stair(2);stair(1)
    # Preserve original grids for the DOM walker; mutate copies only there.
    initial={str(f):[[int(t) for t in r] for r in w[f'mt_line_0{f}']] for f in [1,2,3]}
    for a in plan['seedSearch']['route']:
        x,y=a['position'];initial['1'][y][x]=0
    extra=['Display_buy','mt_buy_list._currentframe','mt_buy_list.now_case_id']
    touched={(1,*a['position']) for a in plan['seedSearch']['route']}
    touched|={(a['floor'],*a['position']) for a in actions if a['kind']=='consume'}
    extra += [f'mt_line_0{f}.{y}.{x}' for f,x,y in sorted(touched)]
    observer('generated/M7',extra)
    plan.update(extension={'scope':'Concrete cross-floor witness only, not globally optimized','grids':initial,'actions':actions,'finalResources':receipt()})
    out=Path('generated/M7');(out/'game-plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'extensionActions':len(actions),'final':receipt(),'shopMoneyBefore':before['Now_money']}));return plan
if __name__=='__main__':make(sys.argv[1])
