"""Exact local MT1 search with a fixed Ruffle 0.7.1 seed.
Tracks RNG state, assumes no draws outside ordinary hero attacks. Native replay
must verify that assumption for any claimed concrete path.
"""
from collections import deque
from functools import lru_cache
import resource,sys,time
from flash_search import graph,advance,hashdata
from flash_model import gate
from ruffle_rng import next_state,output

@lru_cache(None)
def battle(enemy_hp,delta,hit_loss,state,seed):
    if enemy_hp<=0 or delta<=0:raise ValueError("Positive enemy HP and attack delta required")
    hp=enemy_hp;cost=0;draws=[]
    while hp>0:
        if state==0:state=seed
        state=next_state(state);r=output(state);draws.append(r)
        hp-=delta*(2 if r<=1 else 1)
        if hp>0:cost+=hit_loss
    return cost,state,tuple(draws)

def solve(world,seed=128188416,max_states=1000000):
    if world['Now_life']!=1:raise ValueError('Fixed level1 only')
    seed&=0xffffffff;g=graph(world);region=g['region'];objects=g['objects']
    initial=(0,g['start'],int(world['Now_hp']),int(world['Now_gong']),int(world['Now_fang']),tuple(int(world[k]) for k in ['Now_yellow','Now_blue','Now_red']),int(world['Now_money']),int(world['Now_mp']))
    key=lambda s,r:(s[0],region(s[1],s[0])[0],r)
    nodes=[(initial,0,None,None)];labels={key(initial,0):0};q=deque([0]);best=None;expanded=generated=0;peak=1;start=time.perf_counter()
    while q:
        if expanded>=max_states:raise RuntimeError('State limit; no certificate')
        i=q.popleft();s,rng,_,_=nodes[i]
        if labels[key(s,rng)]!=i:continue
        expanded+=1;_,front,exit_reachable=region(s[1],s[0])
        if exit_reachable and (best is None or s[2]>nodes[best][0][2]):best=i
        for pos in front:
            obj=objects[pos];kind,value=obj['effect'];draws=();nr=rng
            if kind=='battle':
                if not gate(value,s[2],s[3],s[4]):continue
                cost,nr,draws=battle(value[0],s[3]-value[2],max(0,value[1]-s[4]),rng,seed)
                ns=(s[0]|1<<obj['index'],pos,s[2]-cost,s[3],s[4],s[5],s[6]+value[3],s[7]+value[4])
            else:
                v=advance(s,obj,pos,False)
                if not v:continue
                ns,cost=v
            generated+=1;k=key(ns,nr);old=labels.get(k)
            if old is not None and nodes[old][0][2]>=ns[2]:continue
            a={'position':[pos%11,pos//11],'originalTile':obj['tile'],'hpCost':cost,'randomDraws':list(draws),'rngStateAfter':nr,'resourcesAfter':{'hp':ns[2],'atk':ns[3],'def':ns[4],'keys':list(ns[5]),'money':ns[6],'experience':ns[7]}}
            labels[k]=len(nodes);q.append(len(nodes));nodes.append((ns,nr,i,a))
        peak=max(peak,len(q))
    route=[];i=best
    while i is not None and nodes[i][2] is not None:route.append(nodes[i][3]);i=nodes[i][2]
    route.reverse()
    return {'schemaVersion':1,'experiment':'original-MT1-first-ascent-fixed-Ruffle-seed','seedUint32':seed,'initialRngState':0,'complete':True,'bestExitHP':nodes[best][0][2] if best is not None else None,'initial':{'hp':initial[2],'atk':initial[3],'def':initial[4],'keys':list(initial[5]),'level':1},'route':route,'routeHash':hashdata(route),'mapHash':hashdata(g['grid']),'metrics':{'expandedLabels':expanded,'generatedTransitions':generated,'uniqueLabels':len(labels),'storedLabels':len(nodes),'peakQueue':peak,'elapsedSeconds':time.perf_counter()-start,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)},'proofArgument':'The key retains consumed mask, free region and exact post-draw RNG state; the mask fixes non-HP resources. Future deterministic ordinary-battle costs depend only on attack/defense and RNG state; gate is monotone in HP, so higher HP dominates. Events increase the mask; exhaustion proves only this local fixed-seed model, not unrestricted seeds or the full game.'}
