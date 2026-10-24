"""Persistent numeric route exploration via JSON commands, never native play.

Only data commands are accepted; no eval, source execution or object deserialization.
Every accepted path executes pinned, reviewed original AVM1 sections. Failed pure
searches leave the route unchanged; a transition mismatch aborts the process.
"""
import argparse,gc,json,resource,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from original_route import OriginalRoute
from route_guidance import Guidance, SHOPS
from route_sections import metadata
from flash_model import gate,pre_damage,ordinary_cost

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--proposal',required=True);p.add_argument('--directory',required=True);p.add_argument('--shop-caps');a=p.parse_args()
    old=json.loads(Path(a.proposal).read_text());r=OriginalRoute(a.swf,random_policy=old['randomPolicy']);chapters=old.get('chapters',[]);constraints=old.get('planningConstraints',{})
    if a.shop_caps:constraints['shopCaps']=json.loads(a.shop_caps)
    for action in old['actions']:
        f=action['floor'];x,y=action['position']
        actual=r.take_stair(f,x,y) if action['kind']=='floor' else r.touch(f,x,y,shop_choice=action.get('choice'))
        assert actual==action['resourcesAfter']
    assert r.resources()==old['resources']
    out=Path(a.directory);out.mkdir(parents=True,exist_ok=True)
    def emit(data):print(json.dumps(data),flush=True)
    def check_caps():
        for shop,limit in constraints.get('shopCaps',{}).items():
            if int(shop) not in range(1,7) or not isinstance(limit,int) or limit<0:raise ValueError('Invalid shop purchase cap')
            count=sum(e.get('shop')==int(shop) and e.get('choice') in (1,2,3) for e in r.actions)
            if count>limit:raise ValueError(f'Prefix exceeds shop {shop} purchase cap: {count}>{limit}')
    check_caps()
    def save():
        check_caps()
        data=dict(scope='Numerical original-bytecode proposal only; no native completion or record claim',randomPolicy=r.random_policy,planningConstraints=constraints,chapters=chapters,actions=r.actions,resources=r.resources(),location=r.location(),draws=r.draws,sections=metadata(r.sections))
        temp=out/'proposal.json.tmp';temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(out/'proposal.json')
    emit(dict(ready=True,resources=r.resources(),actions=len(r.actions)))
    for line in sys.stdin:
        spec=json.loads(line)
        if spec.get('quit'):break
        if 'direct' in spec:
            # Explicit numeric coordinates only. Every interaction still uses
            # the same original-bytecode adapter and ordinary grid walking.
            for event in spec['direct']:
                f,x,y=event['target'];tile=int(r.grid(f)[y][x])
                if 'tile' in event and tile!=event['tile']:
                    raise ValueError(f'Expected tile {event["tile"]}, found {tile} at {f,x,y}')
                for _ in range(event.get('count',1)):
                    r.touch(f,x,y,shop_choice=event.get('choice'))
                    save()
            chapters.append(dict(target=None,goal=spec,resources=r.resources(),actionCount=len(r.actions)));save()
            emit(dict(checked=True,resources=r.resources(),actions=len(r.actions)));continue
        if spec.get('farmSafe'):
            total=0;max_loss=spec.get('maxHPSpend',0);floors=spec.get('floors',range(1,8))
            pickups=set(range(6,13))|{30,31,34,35,36,37,38,39}|set(range(71,81))
            while True:
                candidates=[];state=r.resources()
                for floor in floors:
                    for y,row in enumerate(r.grid(floor)):
                        for x,t in enumerate(row):
                            t=int(t);loss=0;is_enemy=40<=t<=70
                            if is_enemy:
                                e=r.root['boss_man'][t-40]
                                if not gate(e,state['hp'],state['atk'],state['def'],t-40):continue
                                loss=pre_damage(t-40,state['hp'])+ordinary_cost(e,state['atk'],state['def'])
                                if loss>max_loss or loss>=state['hp']:continue
                            elif t not in pickups:continue
                            try:path=r.contact_path(floor,y*11+x)
                            except ValueError:continue
                            candidates.append((is_enemy,loss,len(path),floor,x,y))
                if not candidates:break
                _,_,_,floor,x,y=min(candidates);r.touch(floor,x,y);total+=1
            chapters.append(dict(target=None,goal=spec,resources=r.resources(),actionCount=len(r.actions)));save()
            emit(dict(checked=True,safeEvents=total,resources=r.resources(),actions=len(r.actions)));continue
        if spec.get('collectFreeHealth'):
            total=0
            while True:
                found=False
                for floor in spec.get('floors',range(27)):
                    try:r.match(floor,{11,12})
                    except ValueError as error:
                        if not str(error).startswith('No reachable'):raise
                    else:total+=1;found=True
                if not found:break
            chapters.append(dict(target=None,goal=spec,resources=r.resources(),actionCount=len(r.actions)));save()
            emit(dict(checked=True,freeHealthPickups=total,resources=r.resources(),actions=len(r.actions)));continue
        if 'inspectFloors' in spec:
            emit(dict(resources=r.resources(),enemies={i:list(r.root['boss_man'][i][:5]) for i in (13,17,18,19,31,32)},flags={k:r.root[k] for k in ['mt_GetMoney','mt_LastGame_ID','Set_man_01','Set_man_02','Display_kills']},tiles={f:[(x,y,int(t)) for y,row in enumerate(r.grid(f)) for x,t in enumerate(row) if t not in (0,1,15,19,20,97,98,99)] for f in spec['inspectFloors']}));continue
        f,x,y=spec['target'];g=Guidance(r,(f,y*11+x),max_floor=spec.get('maxFloor',26),valuation=spec.get('valuation','retention'),allow_level_purchases=spec.get('levelPurchases',False),allow_hp_purchases=spec.get('hpPurchases',False),shop_caps=spec.get('shopCaps',constraints.get('shopCaps')));start=time.perf_counter()
        options=dict(width=spec.get('width',512),depth=spec.get('depth',220),hp_weight=spec.get('hpWeight',1),goal_slack=spec.get('goalSlack',0),distance_weight=spec.get('distanceWeight'),**spec.get('requirements',{}))
        try:path,metrics=g.solve(**options)
        except ValueError as error:
            req=spec.get('requirements',{})
            def deficit(s):return max(0,req.get('required_atk',0)-s[3])+max(0,req.get('required_def',0)-s[4])+max(0,req.get('required_cash',0)-s[9])+max(0,req.get('required_xp',0)-s[10])
            closest=min((n[0] for n in g.last_nodes),key=lambda s:(deficit(s),-s[2]))
            emit(dict(searchFailed=str(error),target=spec,resources=r.resources(),closestRetainedResources=list(closest[2:11]),generatedLabels=len(g.last_nodes),elapsedSeconds=time.perf_counter()-start));del g;gc.collect();continue
        metrics|=dict(elapsedSeconds=time.perf_counter()-start,processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),options=options)
        g.apply(path);tile=int(r.grid(f)[y][x])
        # A shop can be a navigation waypoint. Enter and close it normally
        # when no purchase was requested, as the native action stream does.
        if tile:r.touch(f,x,y,shop_choice=spec.get('choice',4 if (f,tile) in SHOPS else None))
        chapters.append(dict(target=[f,x,y],goal=spec,metrics=metrics,resources=r.resources(),actionCount=len(r.actions)));save()
        emit(dict(checked=True,resources=r.resources(),location=r.location(),actions=len(r.actions),metrics=metrics));del g;gc.collect()
if __name__=='__main__':main()
