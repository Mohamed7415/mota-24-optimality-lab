"""Exact MT1 relaxation: critical runs have length <= 4, across battles.
The regular language strictly overapproximates the pinned Ruffle PRNG. Its
optimum is an upper bound for that player, not a reachable-RNG optimum.
"""
from collections import deque
from functools import lru_cache
import resource,sys,time
from flash_search import graph,advance,hashdata
from flash_model import gate

@lru_cache(None)
def battle_outcomes(enemy_hp,delta,start_run,limit=4):
    """Minimum hero attacks per possible final trailing run; witness C/N string.
    Each attack reduces enemy HP. FIFO visits minimum-length path first.
    For a fixed final run, extra attacks cannot improve HP or later RNG language.
    """
    if delta<=0: return ()
    q=deque([(enemy_hp,start_run,'')]);seen={(enemy_hp,start_run)};ends={}
    while q:
        hp,run,pattern=q.popleft()
        for critical in (False,True):
            if critical and run==limit: continue
            nr=run+1 if critical else 0; nh=hp-delta*(2 if critical else 1)
            text=pattern+('C' if critical else 'N')
            if nh<=0:
                if nr not in ends:ends[nr]=text
            elif (nh,nr) not in seen:
                seen.add((nh,nr));q.append((nh,nr,text))
    return tuple(sorted(ends.items()))

def solve(world,max_states=1000000):
    if world['Now_life']!=1:raise ValueError('Fixed level 1 required')
    g=graph(world);region=g['region'];objects=g['objects']
    initial=(0,g['start'],int(world['Now_hp']),int(world['Now_gong']),int(world['Now_fang']),tuple(int(world[k]) for k in ['Now_yellow','Now_blue','Now_red']),int(world['Now_money']),int(world['Now_mp']))
    key=lambda s,r:(s[0],region(s[1],s[0])[0],r)
    nodes=[(initial,0,None,None)];labels={key(initial,0):0};q=deque([0]);best=None;expanded=generated=0;peak=1;start=time.perf_counter()
    while q:
        if expanded>=max_states:raise RuntimeError('State limit; no certificate')
        i=q.popleft();s,run,_,_=nodes[i]
        if labels[key(s,run)]!=i:continue
        expanded+=1;_,front,exit_reachable=region(s[1],s[0])
        if exit_reachable and (best is None or s[2]>nodes[best][0][2]):best=i
        for pos in front:
            obj=objects[pos];kind,value=obj['effect'];options=[]
            if kind=='battle':
                if not gate(value,s[2],s[3],s[4]):continue
                for nr,pattern in battle_outcomes(value[0],s[3]-value[2],run):
                    cost=(len(pattern)-1)*max(0,value[1]-s[4])
                    ns=(s[0]|1<<obj['index'],pos,s[2]-cost,s[3],s[4],s[5],s[6]+value[3],s[7]+value[4])
                    if ns[2]<0:raise AssertionError('gate safety')
                    options.append((ns,cost,nr,pattern))
            else:
                v=advance(s,obj,pos,False)
                if v:options.append((*v,run,''))
            for ns,cost,nr,pattern in options:
                generated+=1;k=key(ns,nr);old=labels.get(k)
                if old is not None and nodes[old][0][2]>=ns[2]:continue
                a={'position':[pos%11,pos//11],'originalTile':obj['tile'],'hpCost':cost,'attackPattern':pattern,'trailingCriticalRun':nr}
                labels[k]=len(nodes);q.append(len(nodes));nodes.append((ns,nr,i,a))
        peak=max(peak,len(q))
    route=[];i=best
    while i is not None and nodes[i][2] is not None:route.append(nodes[i][3]);i=nodes[i][2]
    route.reverse()
    return {'schemaVersion':1,'experiment':'original-MT1-first-ascent','model':'no-five-consecutive-critical relaxation of Ruffle 0.7.1','complete':True,'bestExitHP':nodes[best][0][2] if best is not None else None,'initialTrailingRun':0,'route':route,'routeHash':hashdata(route),'mapHash':hashdata(g['grid']),'metrics':{'expandedLabels':expanded,'generatedTransitions':generated,'uniqueLabels':len(labels),'storedLabels':len(nodes),'peakQueue':peak,'elapsedSeconds':time.perf_counter()-start,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)},'proofArgument':'All nonzero post-transition RNG states have at most four critical outputs in a row; zero outputs 109 and cannot extend a critical run. This automaton admits all such output sequences, including unattainable ones. Battle BFS minimizes attack count separately for each final run. Same consumed mask, free component, and trailing run fix non-HP resources; higher HP dominates by monotone admission. Exhausting this finite DAG gives a player upper bound under the M4 local rules, not an attainable PRNG optimum.'}
