"""Move already planned purchases earlier, then reexecute every original action.

This is a numeric candidate transformation, not a native play certificate.
No game variables are assigned; ordinary walking/shops run in OriginalRoute.
"""
import argparse,hashlib,json
from pathlib import Path
from original_route import OriginalRoute
from route_sections import metadata

def transform(source,swf,before,indices):
    raw=Path(source).read_bytes();old=json.loads(raw);events=old['actions']
    if not 0<=before<len(events) or len(indices)!=len(set(indices)):
        raise ValueError('Invalid insertion point or repeated source index')
    if any(i<=before or i>=len(events) or events[i]['kind']!='shop' or events[i].get('choice') not in (2,3) or events[i].get('shop') not in (1,2,5,6) for i in indices):
        raise ValueError('Only later attack/defense purchases can be advanced')
    r=OriginalRoute(swf,random_policy=old['randomPolicy']);selected=set(indices)
    order=[]
    for i in range(len(events)):
        if i==before:order.extend(indices)
        if i not in selected:order.append(i)
    for i in order:
        e=events[i];f=e['floor'];x,y=e['position']
        if e['kind']=='fly':r.fly(e['toFloor'])
        elif e['kind']=='floor':r.take_stair(f,x,y)
        else:
            assert int(r.grid(f)[y][x])==e['originalTile'],i
            previous=r.resources();r.touch(f,x,y,shop_choice=e.get('choice'))
            if i in selected and previous==r.resources():raise ValueError('Advanced purchase was unaffordable')
    if r.resources()!=old['resources']:raise ValueError('Transformation changed final resources')
    return dict(scope='Numerical original-bytecode proposal only; no native completion or record claim',randomPolicy=r.random_policy,transformation=dict(parentSHA256=hashlib.sha256(raw).hexdigest(),insertBeforeSourceAction=before,advancedSourceActions=indices,finalResourcesUnchanged=True),actions=r.actions,resources=r.resources(),location=r.location(),draws=r.draws,sections=metadata(r.sections))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('proposal');p.add_argument('swf');p.add_argument('--before',type=int,required=True);p.add_argument('--indices',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    result=transform(a.proposal,a.swf,a.before,json.loads(a.indices));out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(actions=len(result['actions']),draws=len(result['draws']),final=result['resources'],transformation=result['transformation'])))
