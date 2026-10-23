"""Bounded deterministic beam search on original first-three-floor data.
No upstream program evaluation. Every omitted transition is explicitly blocked.
The beam is heuristic; its best witness is a lower bound, never an optimum claim.
"""
from collections import deque
from functools import lru_cache
import hashlib,json,resource,sys,time
from flash_model import gate
from seed_search import battle

FREE={0,97,98,99}
ITEMS={6,7,8,9,10,11,12,71}
BLOCKED={1,5,21,23,26,27,34,115}
SEED=128188416

def receipt(s):
    return dict(hp=s[2],atk=s[3],**{'def':s[4]},keys=list(s[5:8]),money=s[8],experience=s[9])

class World:
    def __init__(self,grids,enemies):
        self.tiles=tuple(t for f in ('1','2','3') for row in grids[f] for t in row)
        self.enemies=tuple(tuple(e) if isinstance(e,list) else None for e in enemies)
        self.objects={p:(i,t) for i,(p,t) in enumerate((p,t) for p,t in enumerate(self.tiles) if t in ITEMS|{2,3,4} or 40<=t<=70)}
        unknown=set(self.tiles)-FREE-ITEMS-BLOCKED-{2,3,4,13,14,22}-set(range(40,71))
        if unknown:raise ValueError(f'Unclassified tiles: {unknown}')
        self.landings={(f,t):next(p for p in range((f-1)*121,f*121) if self.tiles[p]==t) for f in (1,2,3) for t in (97,98)}
        self.shop=next(p for p,t in enumerate(self.tiles) if t==22)
        # The canonical-region key requires reversible stair links. Fail closed
        # if a new map could enter a stair from a separate consumable branch.
        for p,t in enumerate(self.tiles):
            f=p//121+1;to=f+(1 if t==13 else -1)
            if t not in (13,14) or not 1<=to<=3:continue
            marker=98 if t==13 else 97
            approaches=[n for n in self.neighbors(p) if self.tiles[n] not in BLOCKED]
            if approaches!=[self.landings[f,marker]]:raise ValueError('Stair reversal geometry not verified')
        # Region memoization is bounded; it does not prune any search transition.
        self.region=lru_cache(maxsize=32768)(self._region)

    def neighbors(self,p):
        q=p%121;x=q%11;y=q//11
        return [p+d for d in (-11,11,-1,1) if 0<=q+d<121 and abs((q+d)%11-x)+abs((q+d)//11-y)==1]

    def free(self,p,mask):
        return self.tiles[p] in FREE or p in self.objects and bool(mask>>self.objects[p][0]&1)

    def links(self,p,mask):
        for q in self.neighbors(p):
            if self.free(q,mask):yield q,None
            elif self.tiles[q] in (13,14):
                f=q//121+1;to=f+(1 if self.tiles[q]==13 else -1)
                if 1<=to<=3:
                    yield self.landings[to,97 if to>f else 98],{'kind':'floor','floor':f,'position':[q%11,(q%121)//11],'toFloor':to}

    def _region(self,mask,pos):
        seen={pos};q=[pos];front=set()
        for p in q:
            for n in self.neighbors(p):
                if n==self.shop or n in self.objects and not (mask>>self.objects[n][0]&1):front.add(n)
            for n,_ in self.links(p,mask):
                if n not in seen:seen.add(n);q.append(n)
        return min(seen),tuple(sorted(front)),any(p<121 for p in seen)

    def contact(self,mask,pos,target):
        """Independent path reconstruction: explicit stairs, real adjacent endpoint."""
        q=deque([pos]);prev={pos:None};edge={}
        while q:
            p=q.popleft()
            if target in self.neighbors(p):
                stairs=[];end=p
                while prev[p] is not None:
                    if edge[p] is not None:stairs.append(edge[p])
                    p=prev[p]
                return list(reversed(stairs)),end
            for n,e in self.links(p,mask):
                if n not in prev:prev[n]=p;edge[n]=e;q.append(n)
        raise ValueError('Unreachable target')

    def finish(self,mask,pos):
        # Find a concrete free cell on MT1, retaining explicit stair transitions.
        q=deque([pos]);prev={pos:None};edge={}
        while q:
            p=q.popleft()
            if p<121:
                stairs=[]
                while prev[p] is not None:
                    if edge[p] is not None:stairs.append(edge[p])
                    p=prev[p]
                return list(reversed(stairs))
            for n,e in self.links(p,mask):
                if n not in prev:prev[n]=p;edge[n]=e;q.append(n)
        raise ValueError('MT1 not reachable')

    def upper(self,s):
        hp=s[2];gold=s[8]
        for p,(i,t) in self.objects.items():
            if s[0]>>i&1:continue
            if t in (11,12):hp+=200 if t==11 else 500
            if 40<=t<=70:gold+=self.enemies[t-40][3]
        return hp+(gold//25)*800

    def successors(self,s):
        mask,pos,hp,atk,df,yk,bk,rk,gold,xp,rng=s
        for p in self.region(mask,pos)[1]:
            if p==self.shop:
                if gold>=25:
                    for c in (1,2,3):
                        n=list(s);n[2 if c==1 else 3 if c==2 else 4]+=800 if c==1 else 4;n[8]-=25
                        yield tuple(n),{'kind':'shop','floor':3,'position':[p%11,(p%121)//11],'shop':1,'choice':c}
                continue
            i,t=self.objects[p];n=list(s);n[0]|=1<<i;n[1]=p;draws=();cost=0
            if 40<=t<=70:
                e=self.enemies[t-40]
                if t-40 in (10,12,17,20):raise ValueError('Special battle unsupported')
                if not gate(e,hp,atk,df):continue
                cost,n[10],draws=battle(e[0],atk-e[2],max(0,e[1]-df),rng,SEED)
                n[2]-=cost;n[8]+=e[3];n[9]+=e[4]
            elif t in (2,3,4):
                j=5+t-2
                if n[j]<=0:continue
                n[j]-=1
            elif t in (6,7,8):n[5+t-6]+=1
            elif t==9:n[4]+=3
            elif t==10:n[3]+=3
            elif t==11:n[2]+=200
            elif t==12:n[2]+=500
            elif t==71:n[3]+=10
            else:raise ValueError(t)
            if n[2]<=0:continue  # Do not admit a dead-hero continuation.
            yield tuple(n),{'kind':'consume','floor':p//121+1,'position':[p%11,(p%121)//11],'originalTile':t,'hpCost':cost,'randomDraws':list(draws),'rngStateAfter':n[10]}

    def key(self,s):
        # Shop choices change stats/cash independently of mask. Retain ALL of them.
        return (s[0],self.region(s[0],s[1])[0],*s[3:])


def solve(world,initial,width=256,max_depth=120,weights=(60,90)):
    start=time.perf_counter();nodes=[(initial,None,None)];beam=[0];best=0 if world.region(initial[0],initial[1])[2] else None
    expanded=generated=dominated=pruned=0;peak=1;layers=[]
    def score(s):return s[2]+weights[0]*s[3]+weights[1]*s[4]+28*s[8]+80*s[5]+160*s[6]+300*s[7]
    for depth in range(max_depth):
        candidates={}
        for idx in beam:
            s=nodes[idx][0];expanded+=1
            for n,a in world.successors(s):
                generated+=1;k=world.key(n);old=candidates.get(k)
                if old is not None and nodes[old][0][2]>=n[2]:dominated+=1;continue
                a|={'resourcesAfter':receipt(n)}
                ni=len(nodes);nodes.append((n,idx,a));candidates[k]=ni
                if world.region(n[0],n[1])[2] and (best is None or n[2]>nodes[best][0][2]):best=ni
        if not candidates:beam=[];break
        order=sorted(candidates.values(),key=lambda i:(-score(nodes[i][0]),-nodes[i][0][2],i))
        peak=max(peak,len(order));pruned+=max(0,len(order)-width);beam=order[:width]
        layers.append({'depth':depth+1,'candidates':len(order),'retained':len(beam),'bestHP':nodes[best][0][2] if best is not None else None})
    route=[];i=best
    if i is None:raise RuntimeError('No MT1-return witness')
    while nodes[i][1] is not None:route.append(nodes[i][2]);i=nodes[i][1]
    route.reverse()
    # Concrete stair reconstruction uses actual adjacent positions after interaction.
    actions=[];s=initial;pos=s[1]
    for a in route:
        target=(a['floor']-1)*121+a['position'][1]*11+a['position'][0]
        stairs,pos=world.contact(s[0],pos,target)
        actions.extend(e|{'resourcesAfter':receipt(s)} for e in stairs)
        n=next(n for n,b in world.successors(s) if b['kind']==a['kind'] and b['position']==a['position'] and b.get('choice')==a.get('choice') and b['floor']==a['floor'])
        if receipt(n)!=a['resourcesAfter']:raise AssertionError('Reconstructed resources differ')
        actions.append(a);s=n
    actions.extend(e|{'resourcesAfter':receipt(s)} for e in world.finish(s[0],pos))
    return {'algorithm':'deterministic event beam, exact transitions and same-state HP dominance','beamWidth':width,'maxDepth':max_depth,'scoreWeights':list(weights),'complete':False,'stoppingReason':'depth limit' if beam else 'retained frontier exhausted; earlier beam pruning prevents completeness','bestReturnHP':nodes[best][0][2],'admissibleInitialUpperHP':world.upper(initial),'initialResources':receipt(initial),'finalResources':receipt(nodes[best][0]),'actions':actions,'routeSHA256':hashlib.sha256(json.dumps(actions,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'metrics':{'expandedLabels':expanded,'generatedTransitions':generated,'sameStateDominated':dominated,'beamDiscarded':pruned,'storedLabels':len(nodes),'peakLayerCandidates':peak,'elapsedSeconds':time.perf_counter()-start,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)},'layers':layers}
