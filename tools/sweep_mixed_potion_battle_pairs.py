"""Joint two-battle postponements on one fixed, original-derived schedule.

The 543 pinned single-delay candidates induce305 pairs sharing an insertion
point. Their baseline reachability does not establish joint reachability: the
allocation DP relaxes navigation, and only a separate original-bytecode replay
can accept a positive prefix. No whole-game/global/record claim follows.
"""
import argparse
import collections
import hashlib
import itertools
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

MUTATIONS = Path('experiments/early-battle-delay-mutations.json')
MUTATIONS_SHA = 'e043b54a00278995b6a240728c22fdaaeab5f37d010ce04443107d081ebc5ad4'
SOLVER = Path('tools/search_mixed_potion_reserve.py')
SOLVER_SHA = '70943c70a780611c1f90fd89fab8bc021c88447f2a9d77d58575b34928cb0e53'
SOURCE_SHA = '6ea34628fa4d8bd6eaa732ae0674951ccec90e5c1ce577852fe1bf1d2c921f4a'
SCOPE = 'Two jointly postponed battles in a fixed source schedule; allocation navigation relaxed, original-bytecode positive replay required. Prefix only, not a global/full-game/record proof.'


def candidates():
    raw = MUTATIONS.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MUTATIONS_SHA or hashlib.sha256(SOLVER.read_bytes()).hexdigest() != SOLVER_SHA:
        raise ValueError('Pinned mutation list or allocation solver changed')
    by_target = collections.defaultdict(list)
    for moved, target in json.loads(raw):
        by_target[target].append(moved)
    pairs = sorted((a, b, target) for target, moved in by_target.items()
                   for a, b in itertools.combinations(sorted(set(moved)), 2))
    assert len(pairs) == 305
    return pairs


def report(rows, total, elapsed, peak_rss_bytes):
    return dict(schemaVersion=1, scope=SCOPE, sourceProposalSHA256=SOURCE_SHA,
                singleDelayListSHA256=MUTATIONS_SHA, allocationToolSHA256=SOLVER_SHA,
                mutationPolicy='All distinct pairs of pinned single-delay battles with an identical insertion point, lexicographic order.',
                fixedAdvance=[135,143], fixedExtraAdvances=[[352,353],[352,549]],
                mustEat=[333,375,376,549], targetReservedHealing=1300, targetStats=[696,625,2],
                cases=total, completed=len(rows), complete=len(rows) == total,
                verifiedPrefixes=[dict(index=i, mutation=r['mutation']) for i,r in enumerate(rows) if r['originalBytecodeVerified']],
                results=rows, fullGameVerified=False, recordBreakingRoute=False,
                metrics=dict(storedLabels=sum(r['metrics']['states'] for r in rows),
                             transitions=sum(r['metrics']['transitions'] for r in rows),
                             elapsedSeconds=elapsed, childPeakRSSBytes=peak_rss_bytes))


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k,v in value.items() if k != 'metrics'}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='generated/MixedBattlePairReproduction')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--check')
    args = parser.parse_args()
    pairs = candidates()
    if args.limit < 0:
        raise ValueError('Nonnegative case limit required')
    if args.limit:
        pairs = pairs[:args.limit]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    rows = []
    for n,(a,b,target) in enumerate(pairs):
        directory = out/f'candidate-{n:04d}'
        command = [sys.executable, str(SOLVER), '--advance','135,143','--extra-advance','352,353',
                   '--extra-advance','352,549','--must-eat','333,375,376,549','--target-reserve','1300',
                   '--delay-group',f'{a},{b}:{target}','--out',str(directory)]
        with (out/f'candidate-{n:04d}.log').open('w') as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if child.returncode:
            raise RuntimeError(f'Allocation failed at candidate{n}; inspect the preserved log')
        data = json.loads((directory/'summary.json').read_text())
        row = dict(mutation=[a,b,target], numericPositive=data['targetNumericSurvives'],
                   originalBytecodeVerified=data.get('originalBytecodeVerified',False),
                   maximumReservedHealingForTargetStatsUnderCap=data['maximumReservedHealingForTargetStatsUnderCap'],
                   metrics=data['metrics'])
        if 'replayFailure' in data:
            row['replayFailure'] = data['replayFailure']
        rows.append(row)
        rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
        result = report(rows, len(pairs), time.perf_counter()-started, rss)
        (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        if n%20 == 0 or row['numericPositive']:
            print('PROGRESS',len(rows),len(pairs),'numeric',row['numericPositive'],'verified',row['originalBytecodeVerified'],flush=True)
        if row['originalBytecodeVerified']:
            break
    if args.check and stable(result) != stable(json.loads(Path(args.check).read_text())):
        raise AssertionError('Published bounded pair sweep changed')
    print('END',len(rows),'verified',result['verifiedPrefixes'],flush=True)


if __name__ == '__main__':
    main()
