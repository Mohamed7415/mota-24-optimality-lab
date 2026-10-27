"""Replay a234-action numerical prefix through reviewed original bytecode.

Checks every resource checkpoint, actual reachability and the two still-closed
F5 doors. This is not a player run, full route, record or optimality proof.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
from original_route import OriginalRoute

PROPOSAL=Path('experiments/blue-door-bypass-prefix.json')
PROPOSAL_SHA='9f7235d860c3d71f594f42d54b430c59762b5d5c3d1f41b57d59e0d09d864d79'


def check(swf):
    raw=PROPOSAL.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PROPOSAL_SHA:
        raise ValueError('Pinned numerical prefix mismatch')
    proposal=json.loads(raw)
    route=OriginalRoute(swf,random_policy='worst-support')
    started=time.perf_counter()
    for index,action in enumerate(proposal['actions']):
        actual=route.replay_action(action)
        if actual!=action['resourcesAfter']:
            raise AssertionError(f'Resource checkpoint diverged at{index}')
    if route.resources()!=proposal['resources'] or list(route.location())!=proposal['location']:
        raise AssertionError('Final resources/location differ')
    if len(route.actions)!=234:
        raise AssertionError('Unexpected implicit action count')
    for item in proposal['doorContract']['omitted']:
        x,y=item['position']
        if route.grid(item['floor'])[y][x]!=item['tile']:
            raise AssertionError('An omitted door was consumed')
    for item in proposal['doorContract']['added']:
        x,y=item['position']
        if route.grid(item['floor'])[y][x]!=0:
            raise AssertionError('The bypass door was not opened')
    purchases=Counter((a.get('shop'),a.get('choice')) for a in route.actions if a['kind']=='shop')
    if purchases!=Counter({(1,2):9,(1,3):2,(1,1):2,(5,2):9}):
        raise AssertionError('Purchase ledger differs')
    return dict(schemaVersion=1,scope='Reviewed-bytecode234-action prefix only; no native/full completion or record/optimality proof',
                proposalSHA256=PROPOSAL_SHA,originalSWFSHA256=hashlib.sha256(Path(swf).read_bytes()).hexdigest(),
                originalBytecodeReplayPassed=True,resourceCheckpoints=234,resources=route.resources(),location=list(route.location()),
                doorContract=proposal['doorContract'],lowGoldStatPurchases=11,lowGoldHPPurchases=2,cheapXPStatPurchases=9,
                complete24Floors=False,recordBreakingRoute=False,elapsedSeconds=time.perf_counter()-started,
                processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swf',default='generated/private/mhhf.swf')
    parser.add_argument('--out')
    args=parser.parse_args();result=check(args.swf)
    if args.out:
        Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
