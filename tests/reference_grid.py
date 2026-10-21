"""Independent tile-step enumerator: no flood fill, no HP dominance.
Only this fixed MT1 benchmark is supported; complete state tuple deduplication.
"""
from collections import deque
import time

def oracle(t,limit=2000000):
 f=t['floors']['MT1']['data'];grid=f['map'];en=t['enemies']['data'];tiles=t['tiles'];values=t['config']['values']['data'];bits={};
 for y,row in enumerate(grid):
  for x,v in enumerate(row):
   if v not in [0,1,3,87,88]:bits[(x,y)]=len(bits)
 # State includes every quantity relevant to future local transitions, including exact HP.
 initial=(6,11,0,1000,10,10,1,1,1)
 q=deque([initial]);seen={initial};answer=None;start=time.perf_counter();expanded=0
 while q:
  s=q.popleft();expanded+=1
  if expanded>limit:raise RuntimeError('Reference oracle state limit')
  x,y,mask,hp,atk,defense,ky,kb,kr=s
  for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if not (0<=nx<13 and 0<=ny<13):continue
   tile=grid[ny][nx]
   if tile==87:answer=max(answer or 0,hp);continue
   if tile in [1,3]:continue
   nm=mask;nh=hp;na=atk;nd=defense;keys=[ky,kb,kr]
   if tile not in [0,88]:
    bit=1<<bits[(nx,ny)]
    if not mask&bit:
     info=tiles[str(tile)]['data'];id=info['id']
     if info['cls']=='enemys':
      e=en[id]
      if e['special']!=0:raise ValueError('Special unsupported')
      if atk<=e['def']:continue
      # Deliberately different implementation of ceil(HP/hit)-1 attacks.
      remaining=e['hp'];cost=0
      while remaining>0:
       remaining-=atk-e['def']
       if remaining>0:cost+=max(0,e['atk']-defense)
      if hp-cost<=0:continue
      nh=hp-cost
     elif id in ['yellowDoor','blueDoor','redDoor']:
      k=['yellowDoor','blueDoor','redDoor'].index(id)
      if keys[k]<=0:continue
      keys[k]-=1
     elif id in ['yellowKey','blueKey','redKey']:keys[['yellowKey','blueKey','redKey'].index(id)]+=1
     elif id=='redPotion':nh+=values[id]
     elif id=='bluePotion':nh+=values[id]
     elif id=='redJewel':na+=values[id]
     elif id=='blueJewel':nd+=values[id]
     elif id!='book':raise ValueError('Unknown tile '+id)
     nm|=bit
   ns=(nx,ny,nm,nh,na,nd,*keys)
   if ns not in seen:seen.add(ns);q.append(ns)
 return {'bestExitHP':answer,'expandedFullStates':expanded,'elapsedSeconds':time.perf_counter()-start,'method':'tile-step exhaustive enumeration, exact HP in visited key, no dominance or region compression'}
if __name__=='__main__':
 import json,sys
 from pathlib import Path
 t=json.loads(Path(sys.argv[1]).read_text());r=oracle(t);print(json.dumps(r,indent=2));
 if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n')
