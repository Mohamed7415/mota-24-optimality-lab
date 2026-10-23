"""Reconstruct a numeric proposal using pinned original sections, never certify play."""
import argparse,hashlib,json,platform,resource,sys,time
from pathlib import Path
from original_route import OriginalRoute

def verify(path,swf):
    start=time.perf_counter();p=json.loads(Path(path).read_text());r=OriginalRoute(swf,random_policy=p['randomPolicy']);battles=0
    for i,a in enumerate(p['actions']):
        f=a['floor'];x,y=a['position']
        if a['kind']=='floor':
            actual=r.take_stair(f,x,y);assert r.location()[0]==a['toFloor'],i
        else:
            assert int(r.grid(f)[y][x])==a['originalTile'],i
            battles+=int(40<=a['originalTile']<=70 or a['originalTile'] in (188,198))
            actual=r.touch(f,x,y,shop_choice=a.get('choice'))
        assert actual==a['resourcesAfter'],(i,actual,a['resourcesAfter'])
    assert r.resources()==p['resources']
    return dict(schemaVersion=1,scope='Numerical proposal only. UI and clock abstractions; no native completion or record claim.',proposalSHA256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),originalSWFSHA256=hashlib.sha256(Path(swf).read_bytes()).hexdigest(),verifiedActions=len(p['actions']),battles=battles,worstSupportDraws=len(r.draws),final=r.resources(),plotFlags={k:r.root[k] for k in ['mt_LastGame_ID','mt_GetMoney','Set_man_01','Set_man_02','Display_kills']},metrics=dict(elapsedSeconds=time.perf_counter()-start,processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),interpretedInstructions=r.instructions),environment=dict(python=platform.python_version(),platform=platform.platform()),complete24Floors=False,recordBreakingRoute=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('proposal');p.add_argument('swf');p.add_argument('--out');a=p.parse_args();result=verify(a.proposal,a.swf)
    if a.out:Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
