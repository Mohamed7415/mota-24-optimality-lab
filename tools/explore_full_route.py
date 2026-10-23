"""Work-in-progress full-tower route proposals, never record certification."""
import argparse,gc,json,resource,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from original_route import OriginalRoute
from route_guidance import Guidance

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--width',type=int,default=256);p.add_argument('--resume',action='store_true');p.add_argument('--hp-weight',type=int,default=4);a=p.parse_args()
    r=OriginalRoute(a.swf,random_policy='worst-support');out=Path('generated/FullRoute');out.mkdir(parents=True,exist_ok=True);chapters=[]
    if a.resume and (out/'proposal.json').exists():
        old=json.loads((out/'proposal.json').read_text());chapters=old['chapters']
        for action in old['actions']:
            if action['kind']!='floor':
                r.touch(action['floor'],*action['position'],shop_choice=action.get('choice'))
                assert r.resources()==action['resourcesAfter']
        assert r.resources()==old['resources']
    for index,(floor,x,y,choice,limit) in enumerate( [(5,1,7,1,7),(5,0,0,None,7),(6,0,0,None,10),(11,5,8,4,13),(5,10,3,3,13),(4,5,0,None,13),(2,7,10,None,13),(2,9,10,None,13),(9,0,10,None,13),(11,9,0,None,13),(5,10,3,3,16),(13,4,6,4,16),(5,10,3,3,16),(16,5,4,None,16),(16,4,4,None,16),(0,4,8,None,16),(7,5,4,None,16),(0,4,8,None,16),(5,10,3,2,18),(12,10,0,None,18),(4,5,0,None,18),(13,4,6,4,18),(16,5,5,None,18),(18,5,4,None,18),(19,2,7,None,20),(19,8,7,None,20),(19,5,7,None,20),(19,5,6,None,20),(21,5,1,None,21),(22,6,2,None,25),(23,4,5,None,25),(25,6,5,None,25),(22,6,2,None,25),(26,5,3,None,26)]):
        if index<len(chapters):
            if chapters[index]['target']!=[floor,x,y]:raise ValueError('Waypoint schedule changed; explicit replan required')
            continue
        start=time.perf_counter();g=Guidance(r,(floor,y*11+x),max_floor=limit);path,metrics=g.solve(width=a.width,hp_weight=a.hp_weight,required_cash=({2:50,3:100}.get(choice,0) if (floor,x,y)==(5,10,3) else 0),required_atk=1100 if index>17 and (floor,x,y)==(13,4,6) else 0,required_def=1000 if index>17 and (floor,x,y)==(13,4,6) else 0)
        metrics|={'elapsedSeconds':time.perf_counter()-start,'processPeakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),'requiredCash':({2:50,3:100}.get(choice,0) if (floor,x,y)==(5,10,3) else 0),'requiredAttack':1100 if index>17 and (floor,x,y)==(13,4,6) else 0,'requiredDefense':1000 if index>17 and (floor,x,y)==(13,4,6) else 0,'peakRSSScope':'Process lifetime including all previous chapters; not isolated per-chapter memory'}
        print(json.dumps({'proposedTarget':[floor,x,y],'search':metrics,'seconds':time.perf_counter()-start}),flush=True)
        g.apply(path);r.touch(floor,x,y,shop_choice=choice);chapters.append({'target':[floor,x,y],'metrics':metrics,'resources':r.resources(),'actionCount':len(r.actions)})
        print(json.dumps({'originalBytecodeChecked':r.resources(),'location':r.location(),'events':len(r.actions),'instructions':r.instructions}),flush=True)
        (out/'proposal.json').write_text(json.dumps({'scope':'Full-game work in progress, NOT a native complete replay or record','randomPolicy':r.random_policy,'chapters':chapters,'actions':r.actions,'resources':r.resources(),'location':r.location(),'draws':r.draws,'sections':__import__('route_sections').metadata(r.sections)},indent=2)+'\n')
        del g;gc.collect()
if __name__=='__main__':main()
