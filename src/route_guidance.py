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
NPC_PURCHASES={15*121+3*11+4:(26,10,3),15*121+3*11+6:(27,9,4)}
PLOT_BOSSES={16*121+5*11+5,19*121+6*11+5,21*121+1*11+5}

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
    def __init__(self,engine,target,max_floor=21,reserved_tiles=(33,),valuation='legacy',allow_level_purchases=True,allow_hp_purchases=True,shop_caps=None,forbidden_positions=()):
        self.engine=engine;self.target=target[0]*121+target[1];self.limit=max_floor;self.reserved_tiles=frozenset(reserved_tiles)
        self.forbidden_positions=frozenset(forbidden_positions)
        if valuation not in ('legacy','replacement','retention'):raise ValueError('Unknown valuation')
        self.valuation=valuation;self.allow_level_purchases=allow_level_purchases
        self.allow_hp_purchases=allow_hp_purchases
        self.shop_caps={int(k):v for k,v in (shop_caps or {}).items()}
        if any(k not in COSTS or not isinstance(v,int) or v<0 for k,v in self.shop_caps.items()):raise ValueError('Invalid shop purchase cap')
        self.cap_index={k:14+i for i,k in enumerate(sorted(self.shop_caps))}
        self.initial_shop_purchases={k:sum(a.get('shop')==k and a.get('choice') in (1,2,3) for a in engine.actions) for k in self.cap_index}
        if any(self.initial_shop_purchases[k]>v for k,v in self.shop_caps.items()):raise ValueError('Existing prefix exceeds requested shop purchase cap')
        self.key_values=(66500,332500,665000) if valuation=='retention' else (95000,475000,950000)
        self.tiles=tuple(int(t) for f in range(27) for row in engine.grid(f) for t in row)
        self.enemies=tuple(tuple(e[:5]) if isinstance(e,list) else None for e in engine.root['boss_man'])
        self.objects={p:(i,t) for i,(p,t) in enumerate((p,t) for p,t in enumerate(self.tiles) if (p not in PLOT_BOSSES or p==self.target) and (t in PICKUPS|{2,3,4,115} or 40<=t<=70 or t in (188,198) or p in NPC_PURCHASES and t==NPC_PURCHASES[p][0]))}
        self.objects={p:value for p,value in self.objects.items() if p not in self.forbidden_positions}
        self.door_masks=tuple(sum(1<<i for i,t in self.objects.values() if t==color) for color in (2,3,4))
        self.floor_masks=tuple(sum(1<<i for p,(i,t) in self.objects.items() if p//121==f) for f in range(27))
        self.floor_links={p:engine.floor_edge(p//121,p%121) for p,t in enumerate(self.tiles) if t in (13,14) or t==5 and p//121==24}
        self.shops={p:SHOPS[p//121,t] for p,t in enumerate(self.tiles) if (p//121,t) in SHOPS}
        r=engine.resources();f,pos=engine.location()
        self.initial=(0,f*121+pos,r['hp'],r['atk'],r['def'],r['level'],*r['keys'],r['money'],r['experience'],engine.rng.state,0,0,*self.initial_shop_purchases.values())
        self.reward_values={};self.hp_rewards={}
        for p,(_,t) in self.objects.items():
            value=0;heal=0
            if 40<=t<=70 or t in (188,198):
                idx=31 if t==188 else 32 if t==198 else t-40;e=self.enemies[idx];value=9500*e[3]+8500*e[4]
            elif t in (6,7,8):value=self.key_values[t-6]
            elif t==36:value=sum(self.key_values)
            elif t==39:value=2850000
            elif t in (9,10):value=142500
            elif t in (30,31):
                n=1 if t==30 else 3;value=950000*n;heal=1000*n
            elif t in (11,12):heal=200 if t==11 else 500
            elif 71<=t<=75:value=47500*[10,40,70,110,150][t-71]
            elif 76<=t<=80:value=47500*[10,30,85,120,190][t-76]
            elif p in NPC_PURCHASES:
                value=120*47500-500*(8500 if NPC_PURCHASES[p][1]==10 else 9500)
            self.reward_values[p]=value;self.hp_rewards[p]=heal
        self.region=lru_cache(maxsize=8192)(self._region)
        self.floor_regions=lru_cache(maxsize=4096)(self._floor_regions)
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
    def _region_cells(self,mask,pos):
        seen={pos};q=[pos];front=set();distance=100000
        for p in q:
            distance=min(distance,self.distance.get(p,100000))
            for n in self.neighbors(p):
                if n//121<=self.limit and (n==self.target or n in self.shops or n in self.objects and not (mask>>self.objects[n][0]&1)):front.add(n)
            for n in self.edges(p,mask):
                if n not in seen:seen.add(n);q.append(n)
        return tuple(sorted(front)),distance
    def _floor_regions(self,f,mask):
        """Undirected walking components; inter-floor links stay directed."""
        labels=[None]*121;components={};base=f*121
        def free(p):
            t=self.tiles[p]
            return t in FREE or p in self.objects and bool(mask>>self.objects[p][0]&1)
        for start in range(121):
            if labels[start] is not None or not free(base+start):continue
            labels[start]=start;q=[base+start];front=set();links=set();distance=100000
            for p in q:
                distance=min(distance,self.distance.get(p,100000))
                for n in self.neighbors(p):
                    if f<=self.limit and (n==self.target or n in self.shops or n in self.objects and not (mask>>self.objects[n][0]&1)):front.add(n)
                    if free(n):
                        local=n%121
                        if labels[local] is None:labels[local]=start;q.append(n)
                    elif n in self.floor_links and self.floor_links[n] is not None:
                        dest=self.floor_links[n]
                        if dest[0]<=self.limit:links.add(dest)
            components[start]=(tuple(sorted(front)),tuple(sorted(links)),distance)
        return labels,components
    def _region(self,mask,pos):
        f,p=divmod(pos,121);labels,_=self.floor_regions(f,mask&self.floor_masks[f])
        if labels[p] is None:return self._region_cells(mask,pos)
        q=[(f,labels[p])];seen=set(q);front=set();distance=100000
        for floor,component in q:
            _,groups=self.floor_regions(floor,mask&self.floor_masks[floor]);items,links,d=groups[component]
            front.update(items);distance=min(distance,d)
            for dest_floor,dest_pos in links:
                dest_labels,_=self.floor_regions(dest_floor,mask&self.floor_masks[dest_floor]);dest=dest_labels[dest_pos]
                if dest is None:return self._region_cells(mask,pos)
                key=(dest_floor,dest)
                if key not in seen:seen.add(key);q.append(key)
        return tuple(sorted(front)),distance
    def next(self,s):
        mask,pos,hp,atk,df,lvl,yk,bk,rk,cash,xp,rng=s[:12]
        for p in self.region(mask,pos)[0]:
            # A shop waypoint may itself be the means of meeting the requested
            # stats. Only one-time target interactions are deferred to apply.
            if p==self.target and p not in self.shops:continue
            if p in self.shops:
                shop=self.shops[p]
                for c in (1,2,3):
                    if shop in (5,6) and c==1 and not self.allow_level_purchases:continue
                    if shop in (1,2) and c==1 and not self.allow_hp_purchases:continue
                    before=dict(zip(FIELDS,[hp,atk,df,lvl,yk,bk,rk,cash,xp]))
                    budget=cash if shop in (1,2,3) else [yk,bk,rk][c-1] if shop==4 else xp
                    maximum=budget//COSTS[shop][c-1]
                    if shop in self.shop_caps:maximum=min(maximum,self.shop_caps[shop]-s[self.cap_index[shop]])
                    if shop==3:
                        # Extra purchases beyond every remaining colored door
                        # can only be resold at a loss for an AD objective.
                        demand=(self.door_masks[c-1]&~mask).bit_count()
                        maximum=min(maximum,max(0,demand-s[5+c]))
                    for quantity in sorted({1,2,3,maximum}):
                        if not 1<=quantity<=maximum:continue
                        after=before
                        for _ in range(quantity):after=transact(after,shop,c)
                        n=[mask,pos,*[after[k] for k in FIELDS],rng,*s[12:]]
                        if shop in self.shop_caps:n[self.cap_index[shop]]+=quantity
                        yield tuple(n),(p,c,quantity)
                continue
            i,t=self.objects[p];n=list(s);n[0]|=1<<i;n[1]=p
            if t in self.reserved_tiles:continue
            n[12]+=self.reward_values[p];n[13]+=self.hp_rewards[p]
            if p in NPC_PURCHASES and t==NPC_PURCHASES[p][0]:
                _,currency,stat=NPC_PURCHASES[p]
                if n[currency]<500:continue
                n[currency]-=500;n[stat]+=120
            elif 40<=t<=70 or t in (188,198):
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
        if self.target in NPC_PURCHASES and t==NPC_PURCHASES[self.target][0]:return s[NPC_PURCHASES[self.target][1]]>=500
        if t in (2,3,4):return s[t+4]>0
        if 40<=t<=70 or t in (188,198):
            idx=31 if t==188 else 32 if t==198 else t-40;e=self.enemies[idx]
            if not gate(e,s[2],s[3],s[4],idx):return False
            loss,_=fight(e,s[3],s[4],s[5],s[11],self.engine.rng.seed,self.engine.random_policy)
            return s[2]>pre_damage(idx,s[2])+loss
        return True
    def solve(self,width=256,depth=220,hp_weight=2,required_cash=0,required_xp=0,required_atk=0,required_def=0,goal_slack=0,distance_weight=None):
        nodes=[(self.initial,None,None)];beam=[0];generated=0;best_done=None;first_done=None
        # Across depths, reject resource-losing cycles such as buying a key
        # for10 and reselling it for7. Compare only identical world, position,
        # stats, keys, RNG, reward credits and purchase-cap counters.
        pareto={};resource_dominated=0
        def retain(s,record=False):
            key=(s[0],s[1],*s[3:9],*s[11:]);value=(s[2],s[9],s[10])
            frontier=pareto.get(key,[])
            if any(all(a>=b for a,b in zip(old,value)) for old in frontier):return False
            if record:
                frontier=[old for old in frontier if not all(a>=b for a,b in zip(value,old))]
                pareto[key]=frontier+[value]
            return True
        retain(self.initial,True)
        front,distance=self.region(self.initial[0],self.initial[1])
        if distance==100000 and self.target not in front:
            self.last_nodes=nodes;self.last_beam=beam
            raise ValueError('Waypoint disconnected in this snapshot; resolve plot boundaries before searching resources')
        if distance_weight is None:distance_weight=10000 if self.valuation=='retention' else 300
        def score(s):
            base=hp_weight*s[2]+500*(s[3]+s[4])+2000*(min(s[3],required_atk)+min(s[4],required_def))-distance_weight*self.region(s[0],s[1])[1]
            if self.valuation=='legacy':return base+20*s[9]+40*s[10]+50*s[6]+100*s[7]+300*s[8]
            # Shadow values at the best ordinary AD exchange rates. Buying a
            # key preserves value; selling it loses the buy/sell spread. Scale
            # by95 to keep the XP coefficient exact (17*500 per95 XP).
            result=95*base+9500*s[9]+8500*s[10]+sum(v*k for v,k in zip(self.key_values,s[6:9]))
            # Credit uncollected rewards as already owned (up to a constant).
            # Merely harvesting a reward no longer improves the objective;
            # irreversible shop/door losses and HP damage drive the comparison.
            if self.valuation=='retention':result-=s[12]+95*hp_weight*s[13]
            return result
        def result(best,layer):
            path=[]
            while nodes[best][1] is not None:path.append((nodes[best][2],nodes[best][0]));best=nodes[best][1]
            path.reverse();return path,{'depth':len(path),'searchedThroughDepth':layer,'firstGoalDepth':first_done,'goalSlack':goal_slack,'distanceWeight':distance_weight,'generatedTransitions':generated,'storedLabels':len(nodes),'crossDepthResourceDominated':resource_dominated,'beamWidth':width,'hpWeight':hp_weight,'reservedTiles':sorted(self.reserved_tiles),'forbiddenPositions':sorted(self.forbidden_positions),'valuation':self.valuation,'allowLevelPurchases':self.allow_level_purchases,'allowHPPurchases':self.allow_hp_purchases,'shopCaps':self.shop_caps,'initialShopPurchases':self.initial_shop_purchases,'selection':'resource-diverse beam; heuristic, not exhaustive','complete':False}
        for layer in range(depth):
            done=[i for i in beam if self.target in self.region(nodes[i][0][0],nodes[i][0][1])[0] and nodes[i][0][9]>=required_cash and nodes[i][0][10]>=required_xp and nodes[i][0][3]>=required_atk and nodes[i][0][4]>=required_def and self.target_is_safe(nodes[i][0])]
            if done:
                best=max(done,key=lambda i:score(nodes[i][0]))
                if best_done is None or score(nodes[best][0])>score(nodes[best_done][0]):best_done=best
                if first_done is None:first_done=layer
            if first_done is not None and layer>=first_done+goal_slack:return result(best_done,layer)
            candidates={}
            for i in beam:
                # Beam-discarded labels never enter this cross-depth table.
                retain(nodes[i][0],True)
                for n,a in self.next(nodes[i][0]):
                    generated+=1
                    if not retain(n):resource_dominated+=1;continue
                    k=(n[0],n[1],*n[3:]);old=candidates.get(k)
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
        if best_done is not None:return result(best_done,layer)
        self.last_nodes=nodes;self.last_beam=beam
        raise ValueError(f'No waypoint proposal found target{self.target//121,self.target%121}, expanded depth{layer}, generated{generated}')
    def apply(self,path):
        for (p,c,quantity),expected in path:
            for _ in range(quantity):actual=self.engine.touch(p//121,p%11,(p%121)//11,shop_choice=c)
            fields=[actual[k] for k in ('hp','atk','def','level')]+actual['keys']+[actual['money'],actual['experience']]
            if fields!=list(expected[2:11]):raise AssertionError(f'Original bytecode rejected planner model at F{p//121} {p%11,(p%121)//11}: {fields} != {expected[2:11]}')
