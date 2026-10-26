"""Bounded order search: advance one baseline-reachable event, then allocate AD.

Only numeric proposals. Reachability is measured on the baseline, so each winning
mutation must separately pass all original-bytecode actions. No global-optimum
claim; no arbitrary game code execution or state edits. Original assets stay local.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import resource
import sys
import time

sys.path[:0] = ['tools', 'src']
from original_route import OriginalRoute
from flash_model import gate, pre_damage, ordinary_cost
from route_sections import metadata

SOURCE = Path('experiments/full-route-ending-10088-proposal.json')
# The pinned hash is checked below, separately from the target SWF's section guards.
SOURCE_SHA = '6ea34628fa4d8bd6eaa732ae0674951ccec90e5c1ce577852fe1bf1d2c921f4a'


def contacts(r):
    queue = [r.location()]
    seen = set(queue)
    found = set()
    for f, p in queue:
        for n in r.neighbors(p):
            found.add((f, n % 11, n // 11))
            tile = r.grid(f)[n // 11][n % 11]
            dest = (f, n) if tile in (0, 97, 98, 99) else r.floor_edge(f, n)
            if dest is not None and dest not in seen:
                seen.add(dest)
                queue.append(dest)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='generated/EventAdvancement')
    ap.add_argument('--limit', type=int, default=0, help='0 means all enumerated mutations')
    ap.add_argument('--reserve', default='580,690,721')
    ap.add_argument('--extra-potions', type=int, default=None, help='Instead of event advances, add up to N other early potions to postponement sets')
    ap.add_argument('--min-hp', type=int, default=0, help='Only replay candidates strictly above this HP')
    ap.add_argument('--improving-only', action='store_true', help='Replay only successive improvements')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    all_events = json.loads(raw)['actions']
    end = next(i for i, a in enumerate(all_events) if a['floor'] == 13 and a.get('originalTile') == 55)
    ev = all_events[:end + 1]
    r = OriginalRoute('generated/private/mhhf.swf', random_policy='worst-support')
    enemies = r.root['boss_man']
    initial = r.resources()
    candidates = []
    last_white = max(i for i, a in enumerate(ev) if a.get('originalTile') == 50)
    movable = [i for i, a in enumerate(ev) if a['kind'] == 'consume' and
               (a.get('originalTile') in set(range(6, 11)) | {30, 31, 39} | set(range(71, 81)) or
                40 <= a.get('originalTile', 0) <= 70 and a['originalTile'] not in (50, 53)) and i != end]
    for i, a in enumerate(ev):
        if args.extra_potions is None and a['kind'] != 'floor':
            reachable = contacts(r)
            for j in movable:
                b = ev[j]
                if j > i and (b['floor'], *b['position']) in reachable:
                    candidates.append((i, j))
        r.replay_action(a)
    if args.limit:
        candidates = candidates[:args.limit]
    (out / 'mutations.json').write_text(json.dumps(candidates) + '\n')
    print('ENUMERATED', len(candidates), 'elapsed', time.perf_counter() - started, flush=True)
    reserves = set(map(int, args.reserve.split(',')))
    assert all(ev[i].get('originalTile') == 12 for i in reserves)
    potions = [i for i, a in enumerate(ev) if (a['floor'], a['position'], a.get('originalTile')) in
               [(7, [2, 6], 11), (7, [8, 6], 11), (2, [4, 1], 12)]]
    postponements = [set(i for i, b in zip(potions, bits) if b)
                     for bits in itertools.product((0, 1), repeat=len(potions))]
    if args.extra_potions is not None:
        if not 0 <= args.extra_potions <= 3:
            raise ValueError('Bounded sweep supports zero through three extra potions')
        extras = [i for i, a in enumerate(ev[:last_white])
                  if a.get('originalTile') in (11, 12) and i not in potions]
        postponements = [base | set(extra) for base in postponements
                         for size in range(args.extra_potions + 1)
                         for extra in itertools.combinations(extras, size)]
    before = [initial] + [a['resourcesAfter'] for a in ev[:-1]]
    incomes = [a['resourcesAfter']['money'] - b['money'] for a, b in zip(ev, before)]
    # Synthetic purchases: (shop id, choice); choice is filled by the DP.
    gold = dict(kind='shop', floor=11, position=[5, 8], originalTile=22, shop=2)
    cheap = dict(kind='shop', floor=5, position=[1, 7], originalTile=26, shop=5)
    transitions = states = schedules = 0
    successes = []
    numeric_survivors = 0
    best_hp = args.min_hp
    for mutation_no, mutation in enumerate([None] + candidates):
        order = list(range(len(ev)))
        if mutation:
            i, j = mutation
            order.remove(j)
            order.insert(order.index(i), j)
        seq = []
        cash = 0
        high_open = False
        for i in order:
            a = ev[i]
            if i == last_white + 1:
                seq.append(('cheap', cheap))
            if i > 440 and a.get('shop') == 2 and a.get('choice') in (2, 3):
                continue
            seq.append((i, a))
            cash += incomes[i]
            high_open |= i == 440
            if high_open:
                while cash >= 100:
                    seq.append(('gold', gold))
                    cash -= 100
        for skip in postponements:
            selected = []
            for i, a in seq:
                if i == last_white + 1:
                    selected.extend((k, ev[k]) for k in sorted(skip))
                if i not in skip and i not in reserves:
                    selected.append((i, a))
            dp = {(10, 10, 1): (1000, ())}
            schedules += 1
            for step, (i, a) in enumerate(selected):
                variable = a.get('shop') in (1, 2, 5, 6) and a.get('choice', 2) in (2, 3)
                new = {}
                for (atk, df, level), (hp, choices) in dp.items():
                    for choice in ((2, 3) if variable else (None,)):
                        transitions += 1
                        aa, dd, ll, hh, cc = atk, df, level, hp, choices
                        if choice:
                            gain = {1: 4, 2: 20, 5: 5, 6: 17}[a['shop']]
                            aa += gain * (choice == 2)
                            dd += gain * (choice == 3)
                            cc += ((step, choice),)
                        elif 'randomDraws' in a:
                            t = a['originalTile']
                            enemy = enemies[t - 40]
                            if not gate(enemy, hp, atk, df, t - 40):
                                continue
                            hh -= pre_damage(t - 40, hp) + ordinary_cost(enemy, atk, df)
                        else:
                            b, after = before[i], a['resourcesAfter']
                            aa += after['atk'] - b['atk']
                            dd += after['def'] - b['def']
                            ll += after['level'] - b['level']
                            hh += after['hp'] - b['hp']
                        key = (aa, dd, ll)
                        if hh > 0 and (key not in new or new[key][0] < hh):
                            new[key] = (hh, cc)
                dp = new
                states += len(dp)
                if not dp:
                    break
            if (696, 625, 2) not in dp:
                continue
            hp, choices = dp[696, 625, 2]
            numeric_survivors += 1
            if hp <= (best_hp if args.improving_only else args.min_hp):
                continue
            chosen = dict(choices)
            test = OriginalRoute('generated/private/mhhf.swf', random_policy='worst-support')
            try:
                for step, (i, a) in enumerate(selected):
                    if a['kind'] == 'floor':
                        continue  # Walk to each interaction; old stair detours need not be retained.
                    event = dict(a)
                    if step in chosen:
                        event['choice'] = chosen[step]
                    test.replay_action(event)
                assert test.resources()['hp'] == hp
                assert test.resources()['atk'] == 696 and test.resources()['def'] == 625
                assert test.resources()['keys'] == [3, 1, 3]
                assert test.resources()['money'] == 78 and test.resources()['experience'] == 2314
            except Exception as error:
                print('REJECTED', mutation, sorted(skip), hp, step, str(error), flush=True)
                continue
            best_hp = max(best_hp, hp)
            name = f'proposal-{len(successes)}.json'
            result = dict(scope='Full prefix only; original-bytecode numeric verification, no native/record claim',
                          randomPolicy=test.random_policy, actions=test.actions, resources=test.resources(),
                          location=test.location(), draws=test.draws, sections=metadata(test.sections),
                          transformation=dict(sourceSHA256=SOURCE_SHA, advance=mutation, deferred=sorted(skip),
                                              reserve=sorted(reserves)))
            (out / name).write_text(json.dumps(result, indent=2) + '\n')
            successes.append(dict(file=name, mutation=mutation, deferred=sorted(skip), resources=test.resources()))
            print('VERIFIED', successes[-1], flush=True)
        if mutation_no % 100 == 0:
            print('PROGRESS', mutation_no, len(candidates), 'states', states, 'seconds', time.perf_counter() - started, flush=True)
    summary = dict(schemaVersion=1, scope='Bounded single-event advancement or early-potion postponement sweep; fixed shop schedule. No global impossibility/optimality claim.',
                   sourceSHA256=SOURCE_SHA, reservedSourceActions=sorted(reserves), enumeratedMutations=len(candidates),
                   extraPotionSweep=args.extra_potions, postponementSets=len(postponements),
                   schedules=schedules, numericSurvivors=numeric_survivors, minimumHPFilter=args.min_hp,
                   improvingOnly=args.improving_only, bestVerifiedHP=best_hp if successes else None, verified=successes,
                   metrics=dict(states=states, transitions=transitions, elapsedSeconds=time.perf_counter() - started,
                                processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('FINISHED', summary, flush=True)


if __name__ == '__main__':
    main()
