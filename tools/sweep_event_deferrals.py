"""Run the all-potion relaxation for a saved, bounded event-mutation list.

Each child writes an isolated result; resume skips only completed summaries with
matching inputs. Assets and full diagnostics remain under generated/.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mutations')
    ap.add_argument('--out', default='generated/EventAllDeferrals')
    args = ap.parse_args()
    source = Path(args.mutations)
    mutations = json.loads(source.read_bytes())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    results = []
    for index, pair in enumerate(mutations):
        folder = out / f'case-{index:04d}'
        summary = folder / 'summary.json'
        if not summary.exists():
            if folder.exists():
                raise RuntimeError(f'Incomplete case exists: {folder}; preserve it and choose another output directory')
            proc = subprocess.run([sys.executable, 'tools/search_potion_deferral.py', '--advance', ','.join(map(str, pair)), '--out', str(folder)], capture_output=True, text=True)
            (out / f'case-{index:04d}.log').write_text(proc.stdout + proc.stderr)
            if proc.returncode:
                raise RuntimeError(f'Case {index} failed; see its log')
        result = json.loads(summary.read_text())
        assert result['advancedEvent'] == pair and result['reservedSourceActions'] == [580,690,721]
        assert result['optionalPotionCount'] == 28 and not result['forcedEarly']
        assert result['sourceSHA256'] == '6ea34628fa4d8bd6eaa732ae0674951ccec90e5c1ce577852fe1bf1d2c921f4a'
        results.append(result)
        if result['targetNumericSurvives']:
            print('NUMERIC', index, pair, result, flush=True)
        if index % 100 == 0:
            print('PROGRESS', index, len(mutations), 'seconds', time.perf_counter() - started, flush=True)
    report = dict(schemaVersion=1, scope='Bounded single-event mutations, each with all early potion postponements; numeric path relaxation. Not global route optimality.',
                  mutationListSHA256=hashlib.sha256(source.read_bytes()).hexdigest(), cases=len(results),
                  sourceSHA256=results[0]['sourceSHA256'] if results else None,
                  representedSubsetsPerCase=2**28,
                  survivingCases=[dict(index=i, advance=mutations[i], hp=r.get('numericHP'), originalBytecodeVerified=r.get('originalBytecodeVerified',False)) for i,r in enumerate(results) if r['targetNumericSurvives']],
                  metrics=dict(states=sum(r['metrics']['states'] for r in results), transitions=sum(r['metrics']['transitions'] for r in results),
                               elapsedSeconds=time.perf_counter()-started, peakChildRSSBytes=max((r['metrics']['processPeakRSSBytes'] for r in results),default=0)))
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FINISHED',report,flush=True)


if __name__ == '__main__':
    main()
