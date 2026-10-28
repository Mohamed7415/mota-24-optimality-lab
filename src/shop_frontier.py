"""Conservative resource-projection pruning for the fixed-order heuristic beam.
This is not a proof of whole-game state equivalence. In particular the original
PRNG is not recovered. Every retained candidate still requires complete replay.
"""
import hashlib
import json

RESOURCE_FIELDS=('hp','atk','def','money','experience')
VARIABLE_SHOPS=(1,2,5,6)
RESULT_FIELDS={'resourcesAfter','randomDraws','rngStateAfter','hpCost'}

def world_trace_key(node):
    trace=[]
    for action in node['actions']:
        if action.get('shop') in VARIABLE_SHOPS and action.get('choice')in(1,2,3):
            continue
        trace.append({k:v for k,v in action.items()if k not in RESULT_FIELDS})
    return hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def partition_key(node):
    r=node['resources']
    return world_trace_key(node),r['level'],tuple(r['keys'])

def dominates(left,right):
    """Comparable only within a caller-checked phase/world-trace partition."""
    a,b=left['resources'],right['resources']
    if a['level']!=b['level'] or a['keys']!=b['keys']:return False
    return (left['xpPurchases']<=right['xpPurchases']
            and all(a[k]>=b[k]for k in RESOURCE_FIELDS)
            and (left['xpPurchases']<right['xpPurchases']
                 or any(a[k]>b[k]for k in RESOURCE_FIELDS)))

def prune(frontier):
    keys=[partition_key(n)for n in frontier];kept=[];removed=[]
    for i,node in enumerate(frontier):
        winner=None
        for j,other in enumerate(frontier):
            if i==j or keys[i]!=keys[j]:continue
            equal=other['resources']==node['resources'] and other['xpPurchases']==node['xpPurchases']
            if dominates(other,node) or (equal and j<i):winner=j;break
        if winner is None:kept.append(node)
        else:removed.append({'removedIndex':i,'dominatingIndex':winner,'worldTraceSHA256':keys[i][0]})
    witnesses={row['removedIndex']:row['dominatingIndex'] for row in removed}
    for row in removed:
        witness=row['dominatingIndex'];seen=set()
        while witness in witnesses:
            if witness in seen:raise ValueError('Invalid dominance witness cycle')
            seen.add(witness);witness=witnesses[witness]
        row['dominatingIndex']=witness
    return kept,removed
