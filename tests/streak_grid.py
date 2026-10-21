"""Independent full-state tile oracle, retaining the best battle HP for each final trailing run.
No region compression or HP dominance between map states. Battle outcomes are
first enumerated exhaustively, then only the smallest hit count per final run is kept.
"""
from collections import deque
from functools import lru_cache
import math,time

@lru_cache(None)
def outcomes(hp,delta,run):
    pending={(hp,run,0)};end=set()
    while pending:
        remaining,r,hits=pending.pop()
        for mult,nr in ((1,0),(2,r+1)):
            if nr>4:continue
            nh=remaining-mult*delta
            if nh<=0:end.add((hits,nr))
            else:pending.add((nh,nr,hits+1))
    return tuple((min(h for h,r in end if r==run),run) for run in sorted({r for _,r in end}))

def oracle(world,limit=3000000):
    grid=[[int(v) for v in row] for row in world['mt_line_01']];bits={};spawn=[]
    for y,row in enumerate(grid):
        for x,t in enumerate(row):
            if t==97:spawn.append((x,y))
            if t not in [0,1,13,14,97,98,99]:bits[x,y]=len(bits)
    assert len(spawn)==1
    init=(*spawn[0],0,int(world['Now_hp']),int(world['Now_gong']),int(world['Now_fang']),int(world['Now_yellow']),int(world['Now_blue']),int(world['Now_red']),0)
    q=deque([init]);seen={init};best=None;start=time.perf_counter()
    while q:
        if len(seen)>limit:raise RuntimeError('Independent grid state limit')
        x,y,mask,hp,atk,defense,ky,kb,kr,run=q.popleft()
        for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if not(0<=nx<11 and 0<=ny<11):continue
            t=grid[ny][nx]
            if t==13:best=max(best if best is not None else -1,hp);continue
            if t in [1,14]:continue
            nm=mask;nh=hp;na=atk;nd=defense;keys=[ky,kb,kr];opts=[(0,run)]
            if t not in [0,97,98,99] and not mask>>bits[nx,ny]&1:
                nm|=1<<bits[nx,ny]
                if 40<=t<=70:
                    e=world['boss_man'][t-40]
                    if t-40 in [10,12,17,20]:raise ValueError('Special enemy')
                    if atk<=e[2] or math.trunc(e[0]/(atk-e[2]))*(e[1]-defense)>hp:continue
                    opts=[(hits*max(0,e[1]-defense),nr) for hits,nr in outcomes(e[0],atk-e[2],run)]
                elif t in [2,3,4]:
                    if keys[t-2]==0:continue
                    keys[t-2]-=1
                elif t in [6,7,8]:keys[t-6]+=1
                elif t==9:nd+=3
                elif t==10:na+=3
                elif t==11:nh+=200
                elif t==12:nh+=500
                elif t!=34:raise ValueError(t)
            for cost,nr in opts:
                if nh-cost<0:continue
                ns=(nx,ny,nm,nh-cost,na,nd,*keys,nr)
                if ns not in seen:seen.add(ns);q.append(ns)
    return {'bestExitHP':best,'expandedFullStates':len(seen),'elapsedSeconds':time.perf_counter()-start,'complete':True,'method':'Independent tile-step exact HP and trailing-run enumeration; within-battle exhaustive outcomes reduced by final-run minimum hit count; no inter-map-state dominance/region compression'}
