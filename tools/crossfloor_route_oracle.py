"""Independent per-floor grid replay of a proposed M8 route.
Does not import the event graph, beam, dominance key, or seed battle shortcut.
This checks the witness, not search completeness; official player is separate.
"""
import copy
from collections import deque
from flash_model import combat_frames
from shop_model import FIELDS,transact

def verify(plan,enemies):
    grids=copy.deepcopy(plan['extension']['grids']);floor=2
    pos=next(y*11+x for y,row in enumerate(grids['2']) for x,t in enumerate(row) if t==97)
    stats=dict(zip(FIELDS,[860,10,10,1,1,1,0,4,4]));rng=301989949;steps=draw_count=0;consumed=[]
    def neighbors(p):return [q for q in (p-11,p+11,p-1,p+1) if 0<=q<121 and abs(q%11-p%11)+abs(q//11-p//11)==1]
    def receipt():return dict(hp=stats['Now_hp'],atk=stats['Now_gong'],**{'def':stats['Now_fang']},keys=[stats[k] for k in ['Now_yellow','Now_blue','Now_red']],money=stats['Now_money'],experience=stats['Now_mp'])
    for a in plan['extension']['actions']:
        assert floor==a['floor'];x,y=a['position'];target=y*11+x;grid=grids[str(floor)];q=deque([(pos,0)]);seen={pos};contact=None
        while q:
            p,d=q.popleft()
            if target in neighbors(p):contact=p;steps+=d;break
            for n in neighbors(p):
                if n not in seen and grid[n//11][n%11] in (0,97,98,99):seen.add(n);q.append((n,d+1))
        assert contact is not None,'No ordinary grid walk to contact';pos=contact;t=grid[y][x]
        if a['kind']=='floor':
            assert t==(13 if a['toFloor']>floor else 14);floor=a['toFloor'];marker=97 if t==13 else 98
            pos=next(y*11+x for y,row in enumerate(grids[str(floor)]) for x,t in enumerate(row) if t==marker)
        elif a['kind']=='shop':
            assert floor==3 and t==22 and a['shop']==1
            before=stats;stats=transact(stats,1,a['choice']);assert stats!=before
        else:
            assert t==a['originalTile']
            if 40<=t<=70:
                e=enemies[t-40];delta=stats['Now_gong']-e[2]
                assert delta>0 and (e[0]//delta)*(e[1]-stats['Now_fang'])<=stats['Now_hp']
                draws=a['randomDraws']
                for expected in draws:
                    rng=(rng>>1)^(0x48000000 if rng&1 else 0)
                    # Exact integer port of the official Ruffle mixing/output.
                    from ruffle_rng import output
                    assert output(rng)==expected
                draw_count+=len(draws)
                trace,final=combat_frames(e,[stats[k] for k in ['Now_hp','Now_gong','Now_fang','Now_life']],draws)
                assert stats['Now_hp']-final['Now_hp']==a['hpCost'];stats['Now_hp']=final['Now_hp'];stats['Now_money']+=e[3];stats['Now_mp']+=e[4]
            elif t in (2,3,4):
                k=['Now_yellow','Now_blue','Now_red'][t-2];assert stats[k]>0;stats[k]-=1
            elif t in (6,7,8):stats[['Now_yellow','Now_blue','Now_red'][t-6]]+=1
            elif t==9:stats['Now_fang']+=3
            elif t==10:stats['Now_gong']+=3
            elif t==11:stats['Now_hp']+=200
            elif t==12:stats['Now_hp']+=500
            elif t==71:stats['Now_gong']+=10
            else:raise AssertionError('Unsupported oracle tile')
            assert rng==a['rngStateAfter'];grid[y][x]=0;consumed.append([floor,x,y])
        assert receipt()==a['resourcesAfter'];steps+=1
    assert floor==1 and receipt()==plan['extension']['finalResources']
    return {'matched':True,'finalFloor':floor,'finalResources':receipt(),'actionsChecked':len(plan['extension']['actions']),'extensionDraws':draw_count,'gridWalkAndInteractionSteps':steps,'consumedEvents':len(consumed),'consumedCoordinates':consumed,'independence':'Per-floor tile BFS + frame-level ordinary combat; no beam/event-region/dominance/battle-shortcut imports. Uses separately tested shop model and RNG output mixer. Not an exhaustive optimality oracle.'}
