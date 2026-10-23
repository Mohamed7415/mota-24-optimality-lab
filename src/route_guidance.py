"""Heuristic chunk planner toward full-game waypoints, checked by original VM.
A route proposal only: dynamic plot boundaries are not searched through.
"""
from functools import lru_cache
from collections import deque
from ruffle_rng import next_state,output
from flash_model import gate,pre_damage
from shop_model import FIELDS,COSTS,transact

PICKUPS=set(range(6,13))|set(range(30,40))|set(range(71,81))
FREE={0,97,98,99}
SHOPS={(3,22):1,(11,22):2,(5,27):3,(12,27):4,(5,26):5,(13,26):6}

@lru_cache(maxsize=100000)
def fight(enemy,atk,df,level,rng,seed,policy):
    remaining=enemy[0];loss=0
    while remaining>0:
        if policy=='worst-support':draw=199
        else:
            rng=next_state(rng or seed);draw=output(rng)
        remaining-=(atk-enemy[2])*(2 if draw<=level else 1)
        if remaining>0:loss+=max(0,enemy[1]-df)
    return loss,rng

class Guidance:
    def __init__(self,engine,target,max_floor=21):
        self.engine=engine;self.target=target[0]*121+target[1];self.limit=max_floor
        self.tiles=tuple(int(t) for f in range(27) for row in engine.grid(f) for t in row)
        self.enemies=tuple(tuple(e[:5]) if isinstance(e,list) else None for e in engine.root['boss_man'])
        self.objects={p:(i,t) for i,(p,t) in enumerate((p,t) for p,t in enumerate(self.tiles) if t in PICKUPS|{2,3,4,115} or 40<=t<=70 or t in (188,198))}
        self.floor_links={p:engine.floor_edge(p//121,p%121) for p,t in enumerate(self.tiles) if t in (13,14) or t==5 and p//121==24}
        self.shops={p:SHOPS[p//121,t] for p,t in enumerate(self.tiles) if (p//121,t) in SHOPS}
        r=engine.resources();f,pos=engine.location()
        self.initial=(0,f*121+pos,r['hp'],r['atk'],r['def'],r['level'],*r['keys'],r['money'],r['experience'],engine.rng.state)
        self.region=lru_cache(maxsize=8192)(self._region)
        self.distance=self._distances()
    def neighbors(self,p):
        q=p%121
        return [p+d for d in (-11,11,-1,1) if 0<=q+d<121 and abs((q+d)%11-q%11)+abs((q+d)//11-q//11)==1]
    def edges(self,p,mask,optimistic=False):
        for n in self.neighbors(p):
            t=self.tiles[n]
            if n//121>self.limit:continue
            if t in FREE or n in self.objects and (optimistic or mask>>self.objects[n][0]&1):yield n
            elif n in self.floor_links and self.floor_links[n] is not None:
                f,pos=self.floor_links[n]
                if f<=self.limit:yield f*121+pos
    def _distances(self):
        rev={}
        for p,t in enumerate(self.tiles):
            if p//121>self.limit:continue
            if t in FREE or p in self.objects:
                for n in self.edges(p,0,True):rev.setdefault(n,[]).append(p)
        d={n:0 for n in self.neighbors(self.target)};q=list(d)
        for p in q:
            for n in rev.get(p,[]):
                if n not in d:d[n]=d[p]+1;q.append(n)
        return d
    def _region(self,mask,pos):
        seen={pos};q=[pos];front=set();distance=100000
        for p in q:
            distance=min(distance,self.distance.get(p,100000))
            for n in self.neighbors(p):
                if n//121<=self.limit and (n==self.target or n in self.shops or n in self.objects and not (mask>>self.objects[n][0]&1)):front.add(n)
            for n in self.edges(p,mask):
                if n not in seen:seen.add(n);q.append(n)
        return tuple(sorted(front)),distance
    def next(self,s):
        mask,pos,hp,atk,df,lvl,yk,bk,rk,cash,xp,rng=s
        for p in self.region(mask,pos)[0]:
            if p==self.target:continue
            if p in self.shops:
                shop=self.shops[p]
                for c in (1,2,3):
                    before=dict(zip(FIELDS,[hp,atk,df,lvl,yk,bk,rk,cash,xp]))
                    budget=cash if shop in (1,2,3) else [yk,bk,rk][c-1] if shop==4 else xp
                    maximum=budget//COSTS[shop][c-1]
                    for quantity in sorted({1,2,3,maximum}):
                        if not 1<=quantity<=maximum:continue
                        after=before
                        for _ in range(quantity):after=transact(after,shop,c)
                        n=(mask,pos,*[after[k] for k in FIELDS],rng)
                        yield n,(p,c,quantity)
                continue
            i,t=self.objects[p];n=list(s);n[0]|=1<<i;n[1]=p
            if 40<=t<=70 or t in (188,198):
                idx=31 if t==188 else 32 if t==198 else t-40
                # World-tick boss upgrades require a fresh snapshot after the boundary.
                if p in (16*121+5*11+5,19*121+6*11+5,21*121+1*11+5) and p!=self.target:continue
                e=self.enemies[idx]
                if not gate(e,hp,atk,df,idx):continue
                pre=pre_damage(idx,hp);loss,n[11]=fight(e,atk,df,lvl,rng,self.engine.rng.seed,self.engine.random_policy);n[2]-=pre+loss;n[9]+=e[3];n[10]+=e[4]
            elif t in (2,3,4):
                if n[t+4]<=0:continue
                n[t+4]-=1
            elif t==115:pass
            elif t in (6,7,8):n[t]+=1
            elif t==9:n[4]+=3
            elif t==10:n[3]+=3
            elif t==11:n[2]+=200
            elif t==12:n[2]+=500
            elif t in (30,31):
                d=1 if t==30 else 3;n[5]+=d;n[2]+=d*1000;n[3]+=10*d;n[4]+=10*d
            elif t==33:n[2]*=2
            elif t==36:
                for j in (6,7,8):n[j]+=1
            elif t==39:n[9]+=300
            elif 71<=t<=75:n[3]+=[10,40,70,110,150][t-71]
            elif 76<=t<=80:n[4]+=[10,30,85,120,190][t-76]
            elif t==32:
                if self.engine.root['mt_GetMoney'][0]!=1:continue  # Preserve the original24-floor quest order.
            elif t in (34,35,37,38):pass
            else:raise ValueError(t)
            if n[2]>0:yield tuple(n),(p,None,1)
    def target_is_safe(self,s):
        t=self.tiles[self.target]
        if t in (2,3,4):return s[t+4]>0
        if 40<=t<=70 or t in (188,198):
            idx=31 if t==188 else 32 if t==198 else t-40;e=self.enemies[idx]
            if not gate(e,s[2],s[3],s[4],idx):return False
            loss,_=fight(e,s[3],s[4],s[5],s[11],self.engine.rng.seed,self.engine.random_policy)
            return s[2]>pre_damage(idx,s[2])+loss
        return True
    def solve(self,width=256,depth=220,hp_weight=2,required_cash=0,required_xp=0,required_atk=0,required_def=0):
        nodes=[(self.initial,None,None)];beam=[0];generated=0
        def score(s):
            return hp_weight*s[2]+500*(s[3]+s[4])+2000*(min(s[3],required_atk)+min(s[4],required_def))+20*s[9]+40*s[10]+50*s[6]+100*s[7]+300*s[8]-300*self.region(s[0],s[1])[1]
        for layer in range(depth):
            done=[i for i in beam if self.target in self.region(nodes[i][0][0],nodes[i][0][1])[0] and nodes[i][0][9]>=required_cash and nodes[i][0][10]>=required_xp and nodes[i][0][3]>=required_atk and nodes[i][0][4]>=required_def and self.target_is_safe(nodes[i][0])]
            if done:
                best=max(done,key=lambda i:score(nodes[i][0]));path=[]
                while nodes[best][1] is not None:path.append((nodes[best][2],nodes[best][0]));best=nodes[best][1]
                path.reverse();return path,{'depth':layer,'generatedTransitions':generated,'storedLabels':len(nodes),'beamWidth':width,'hpWeight':hp_weight,'selection':'resource-diverse beam; heuristic, not exhaustive','complete':False}
            candidates={}
            for i in beam:
                for n,a in self.next(nodes[i][0]):
                    generated+=1;k=(n[0],n[1],*n[3:]);old=candidates.get(k)
                    if old is not None and nodes[old][0][2]>=n[2]:continue
                    candidates[k]=len(nodes);nodes.append((n,i,a))
            if not candidates:break
            order=sorted(candidates.values(),key=lambda i:(-score(nodes[i][0]),i))
            beam=[];buckets=set()
            for i in order:
                s=nodes[i][0];bucket=(*s[3:9],s[9]//25,s[10]//30,self.region(s[0],s[1])[1])
                if bucket not in buckets:beam.append(i);buckets.add(bucket)
                if len(beam)>=width:break
            chosen=set(beam)
            if len(beam)<width:beam.extend(i for i in order if i not in chosen and len(beam)<width)
        self.last_nodes=nodes;self.last_beam=beam
        raise ValueError(f'No waypoint proposal found target{self.target//121,self.target%121}, expanded depth{layer}, generated{generated}')
    def apply(self,path):
        for (p,c,quantity),expected in path:
            for _ in range(quantity):actual=self.engine.touch(p//121,p%11,(p%121)//11,shop_choice=c)
            fields=[actual[k] for k in ('hp','atk','def','level')]+actual['keys']+[actual['money'],actual['experience']]
            if fields!=list(expected[2:11]):raise AssertionError(f'Original bytecode rejected planner model at F{p//121} {p%11,(p%121)//11}: {fields} != {expected[2:11]}')
