"""Original-map heuristic proposals. Every result still needs native replay."""
import argparse,gc,json,resource,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from original_route import OriginalRoute
from route_guidance import Guidance
from route_sections import metadata

def goal(f,x,y,choice=None,limit=21,hp=None,**requirements):
    return dict(target=[f,x,y],choice=choice,maxFloor=limit,hpWeight=hp,requirements=requirements)

# Explicit experimental milestones; these are not an optimality certificate.
# Keep the fairy's stat boost until after the twentieth-floor resource sweep.
WAYPOINTS=[
    goal(5,1,7,1,7),goal(5,0,0,limit=7),goal(6,0,0,limit=10),
    goal(11,5,8,4,13),goal(5,10,3,3,13,required_cash=100),
    goal(4,5,0,limit=13),goal(2,7,10,limit=13),goal(2,9,10,limit=13),goal(9,0,10,limit=13),
    goal(11,9,0,limit=13,hp=1),goal(5,10,3,3,16,required_cash=100),goal(13,4,6,4,16,hp=1),
    goal(5,10,3,3,16,required_cash=100),goal(16,5,4,limit=16,hp=4),goal(16,4,4,limit=16),
    goal(0,4,8,limit=16),  # Mystery/ice-staff dialogue before carrying the cross.
    goal(13,4,6,4,18,hp=1,required_atk=1020,required_def=1000),
    goal(5,10,3,2,18,required_cash=50),goal(12,10,0,limit=18,hp=1),goal(4,5,0,limit=18),
    goal(5,10,3,3,18,required_cash=100),goal(5,10,3,3,18,required_cash=100),goal(13,4,6,4,18,hp=1,required_atk=1060,required_def=1150),goal(18,5,4,limit=18,hp=1),
    goal(19,2,7,limit=20,hp=1),goal(19,8,7,limit=20,hp=1),goal(19,5,7,limit=20),goal(19,5,6,limit=20,hp=1),
    *[goal(20,x,y,limit=20,hp=1) for x,y in [(1,0),(9,0),(1,10),(9,10),(0,5),(10,5),(5,0),(5,10)]],
    goal(16,5,5,limit=20,hp=1),goal(15,4,3,limit=20,hp=1,required_xp=500),goal(15,6,3,limit=20,hp=1,required_cash=500),
    goal(7,5,4,limit=20),goal(0,4,8,limit=20),
    goal(21,5,1,limit=21,hp=1),goal(23,4,5,limit=25,hp=1),goal(25,6,5,limit=25,hp=1),
    goal(22,6,2,limit=25),goal(26,5,3,limit=26,hp=1),
]

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--width',type=int,default=512)
    p.add_argument('--resume',action='store_true');p.add_argument('--hp-weight',type=int,default=4)
    p.add_argument('--directory',default='generated/FullRoute');a=p.parse_args()
    r=OriginalRoute(a.swf,random_policy='worst-support');out=Path(a.directory);out.mkdir(parents=True,exist_ok=True);chapters=[]
    if a.resume and (out/'proposal.json').exists():
        old=json.loads((out/'proposal.json').read_text());chapters=old['chapters']
        for action in old['actions']:
            if action['kind']!='floor':
                r.touch(action['floor'],*action['position'],shop_choice=action.get('choice'))
                assert r.resources()==action['resourcesAfter']
        assert r.resources()==old['resources']
    for index,spec in enumerate(WAYPOINTS):
        f,x,y=spec['target']
        if index<len(chapters):
            if chapters[index]['target']!=[f,x,y]:raise ValueError('Waypoint schedule changed; explicit replan required')
            continue
        start=time.perf_counter();g=Guidance(r,(f,y*11+x),max_floor=spec['maxFloor'])
        hp=spec['hpWeight'] if spec['hpWeight'] is not None else a.hp_weight
        try:path,metrics=g.solve(width=a.width,hp_weight=hp,**spec['requirements'])
        except ValueError as error:
            (out/'search-failure.json').write_text(json.dumps({'target':spec,'resources':r.resources(),'error':str(error),'scope':'Heuristic failure, not an impossibility proof'},indent=2)+'\n');raise
        metrics|={'elapsedSeconds':time.perf_counter()-start,'processPeakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),'requirements':spec['requirements'],'peakRSSScope':'Process lifetime including previous chapters, not isolated per-chapter memory'}
        print(json.dumps({'proposedTarget':spec,'search':metrics}),flush=True)
        g.apply(path);tile=int(r.grid(f)[y][x])
        if tile!=0:r.touch(f,x,y,shop_choice=spec['choice'])
        chapters.append({'target':[f,x,y],'goal':spec,'status':'performed' if tile else 'already-cleared','metrics':metrics,'resources':r.resources(),'actionCount':len(r.actions)})
        print(json.dumps({'originalBytecodeChecked':r.resources(),'location':r.location(),'events':len(r.actions),'instructions':r.instructions}),flush=True)
        data={'scope':'Numerical original-bytecode proposal only; NOT native completion or a record','randomPolicy':r.random_policy,'chapters':chapters,'actions':r.actions,'resources':r.resources(),'location':r.location(),'draws':r.draws,'sections':metadata(r.sections),'plannedWaypointsComplete':index==len(WAYPOINTS)-1}
        tmp=out/'proposal.json.tmp';tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(out/'proposal.json')
        del g;gc.collect()
if __name__=='__main__':main()
