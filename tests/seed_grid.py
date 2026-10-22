"""Independent tile-step search with exact HP and RNG state, no dominance.
Shares only the separately player-validated RNG primitive with event search.
"""
from collections import deque
import math,time
from ruffle_rng import RuffleRng

def oracle(world,seed=128188416,limit=1000000):
    grid=[[int(v) for v in row] for row in world['mt_line_01']];bits={};spawn=[]
    for y,row in enumerate(grid):
        for x,t in enumerate(row):
            if t==97:spawn.append((x,y))
            if t not in [0,1,13,14,97,98,99]:bits[x,y]=len(bits)
    assert len(spawn)==1
    initial=(*spawn[0],0,int(world['Now_hp']),int(world['Now_gong']),int(world['Now_fang']),int(world['Now_yellow']),int(world['Now_blue']),int(world['Now_red']),0)
    q=deque([initial]);seen={initial};best=None;start=time.perf_counter()
    while q:
        if len(seen)>limit:raise RuntimeError('Independent seed grid limit')
        x,y,mask,hp,atk,defense,ky,kb,kr,rngstate=q.popleft()
        for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if not(0<=nx<11 and 0<=ny<11):continue
            t=grid[ny][nx]
            if t==13:best=max(best if best is not None else -1,hp);continue
            if t in [1,14]:continue
            nm=mask;nh=hp;na=atk;nd=defense;keys=[ky,kb,kr];nr=rngstate
            if t not in [0,97,98,99] and not mask>>bits[nx,ny]&1:
                nm|=1<<bits[nx,ny]
                if 40<=t<=70:
                    if t-40 in [10,12,17,20]:raise ValueError('Special enemy')
                    e=world['boss_man'][t-40]
                    if atk<=e[2] or math.trunc(e[0]/(atk-e[2]))*(e[1]-defense)>hp:continue
                    rng=RuffleRng(seed);rng.state=rngstate;remaining=e[0]
                    while remaining>0:
                        remaining-=(atk-e[2])*(2 if rng.draw()<=1 else 1)
                        if remaining>0:nh-=max(0,e[1]-defense)
                    nr=rng.state
                elif t in [2,3,4]:
                    if keys[t-2]==0:continue
                    keys[t-2]-=1
                elif t in [6,7,8]:keys[t-6]+=1
                elif t==9:nd+=3
                elif t==10:na+=3
                elif t==11:nh+=200
                elif t==12:nh+=500
                elif t!=34:raise ValueError(t)
            ns=(nx,ny,nm,nh,na,nd,*keys,nr)
            if ns not in seen:seen.add(ns);q.append(ns)
    return {'bestExitHP':best,'expandedFullStates':len(seen),'complete':True,'elapsedSeconds':time.perf_counter()-start,'method':'Independent exact HP/RNG tile states, no dominance or region compression; shared player-validated RNG primitive only'}
