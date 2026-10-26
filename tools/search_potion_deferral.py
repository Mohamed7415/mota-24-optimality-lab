"""Search all early potion-deferral subsets in a numeric path relaxation.

At a fixed event/shop schedule, keep maximum HP per (ATK, DEF, level, deferred
healing sum). Before the final white mage every potion branches eat/defer; after
that mage the deferred sum is added. This represents all 2^N subsets without
retaining their masks in the dominance key. Paths with different masks may differ:
therefore a surviving witness MUST pass a separate original-bytecode replay.
Failure is only for this fixed schedule, reserved potions and target stats.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
sys.path[:0] = ['tools', 'src']
from original_route import OriginalRoute
from flash_model import gate, pre_damage, ordinary_cost
from route_sections import metadata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='generated/AllPotionDeferrals')
    ap.add_argument('--reserve', default='580,690,721')
    ap.add_argument('--force-early', default='')
    ap.add_argument('--delay', help='Move source event I just before J, formatted I,J')
    ap.add_argument('--asap-gold', action='store_true', help='Buy the same 12 low-gold stats, then high-gold stats ASAP, reserving the required early red key')
    ap.add_argument('--asap-xp', action='store_true', help='Buy the same 31 cheap XP stats as soon as the source XP shop is open')
    ap.add_argument('--check', help='Compare deterministic fields with a public receipt')
    ap.add_argument('--advance', help='Move source event J before I, formatted I,J')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    source = Path('experiments/full-route-ending-10088-proposal.json')
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == '6ea34628fa4d8bd6eaa732ae0674951ccec90e5c1ce577852fe1bf1d2c921f4a'
    full = json.loads(raw)['actions']
    end = next(i for i, a in enumerate(full) if a['floor'] == 13 and a.get('originalTile') == 55)
    ev = full[:end + 1]
    last_white = max(i for i, a in enumerate(ev) if a.get('originalTile') == 50)
    reserves = set(map(int, args.reserve.split(',')))
    force_early = set(map(int, args.force_early.split(','))) if args.force_early else set()
    assert all(0 <= i < len(ev) and ev[i].get('originalTile') == 12 for i in reserves)
    assert all(0 <= i < last_white and ev[i].get('originalTile') in (11, 12) for i in force_early)
    r = OriginalRoute('generated/private/mhhf.swf', random_policy='worst-support')
    enemies = r.root['boss_man']
    before = [r.resources()] + [a['resourcesAfter'] for a in ev[:-1]]
    order = list(range(len(ev)))
    advance = list(map(int, args.advance.split(','))) if args.advance else None
    if advance:
        if len(advance) != 2 or not 0 <= advance[0] < advance[1] < end:
            raise ValueError('Expected I < J before the final target')
        at, moved = advance
        if ev[moved]['kind'] != 'consume' or ev[moved].get('originalTile') in (11, 12, 50, 53):
            raise ValueError('Only non-potion, non-white-mage consume events may advance')
        order.remove(moved)
        order.insert(order.index(at), moved)
    delay = list(map(int, args.delay.split(','))) if args.delay else None
    if delay:
        if len(delay) != 2 or not 0 <= delay[0] < delay[1] < end:
            raise ValueError('Expected I < J before the final target')
        moved, at = delay
        if 'randomDraws' not in ev[moved] or ev[moved]['originalTile'] == 50:
            raise ValueError('Only a non-white-mage battle may be delayed')
        order.remove(moved)
        order.insert(order.index(at), moved)
    sequence = []
    cash = xp = cheap_count = low_count = 0
    first_low = next(i for i,a in enumerate(ev) if a.get('shop') == 1 and a.get('choice') in (2,3))
    first_high = next(i for i,a in enumerate(ev) if a.get('shop') == 2 and a.get('choice') in (2,3))
    key_index = order.index(440)
    future_income = {i:sum(max(0,ev[j]['resourcesAfter']['money']-before[j]['money']) for j in order[k+1:key_index]) for k,i in enumerate(order)}
    low_open = high_asap_open = False
    first_xp = next(i for i, a in enumerate(ev) if a.get('shop') == 5 and a.get('choice') in (2,3))
    xp_open = False
    high_open = False
    for i in order:
        a = ev[i]
        xp_open |= i == first_xp
        low_open |= i == first_low
        high_asap_open |= i == first_high
        if i == last_white + 1:
            sequence.append(('restore', None))
            if not args.asap_xp:
                sequence.append(('cheap', dict(kind='shop', floor=5, position=[1, 7], originalTile=26, shop=5, choice=2)))
        replaced = (args.asap_gold and a.get('shop') in (1,2) and a.get('choice') in (2,3) or
                    args.asap_xp and a.get('shop') == 5 and a.get('choice') in (2,3) or
                    i > 440 and a.get('shop') == 2 and a.get('choice') in (2,3))
        if not replaced:
            if i not in reserves:
                sequence.append((i, a))
            cash += a['resourcesAfter']['money'] - before[i]['money']
            xp += a['resourcesAfter']['experience'] - before[i]['experience']
        if args.asap_xp and xp_open:
            while xp >= 30 and cheap_count < 31:
                sequence.append(('cheap', dict(kind='shop', floor=5, position=[1, 7], originalTile=26, shop=5, choice=2)))
                xp -= 30
                cheap_count += 1
        if args.asap_gold and low_open:
            while cash >= 25 and low_count < 12:
                sequence.append(('low-gold', dict(kind='shop',floor=3,position=[5,0],originalTile=22,shop=1,choice=2)))
                cash -= 25
                low_count += 1
        high_open |= i == 440
        reserve_cash = max(0,100-future_income[i]) if order.index(i) < key_index and args.asap_gold else 0
        if (high_asap_open if args.asap_gold else high_open):
            while cash - reserve_cash >= 100:
                sequence.append(('gold', dict(kind='shop', floor=11, position=[5, 8], originalTile=22, shop=2, choice=2)))
                cash -= 100
    if args.asap_gold:
        assert low_count == 12 and cash == 78, (low_count,cash)
    if args.asap_xp:
        assert cheap_count == 31, 'ASAP schedule did not fund all 31 purchases'
    optional = {i for i, a in enumerate(ev[:last_white]) if a.get('originalTile') in (11, 12)} - force_early
    dp = {(10, 10, 1, 0): (1000, (), ())}
    states = transitions = 0
    for step, (i, a) in enumerate(sequence):
        new = {}
        variable = a and a.get('shop') in (1, 2, 5, 6) and a.get('choice') in (2, 3)
        for (atk, df, level, stash), (hp, choices, skipped) in dp.items():
            options = (2, 3) if variable else ('eat', 'defer') if i in optional else (None,)
            for choice in options:
                transitions += 1
                aa, dd, ll, hh, ss, cc, pp = atk, df, level, hp, stash, choices, skipped
                if i == 'restore':
                    hh += stash
                    ss = 0
                elif variable:
                    gain = {1: 4, 2: 20, 5: 5, 6: 17}[a['shop']]
                    aa += gain * (choice == 2)
                    dd += gain * (choice == 3)
                    cc += ((step, choice),)
                elif choice == 'defer':
                    ss += {11: 200, 12: 500}[a['originalTile']]
                    pp += (i,)
                elif 'randomDraws' in a:
                    tile = a['originalTile']
                    enemy = enemies[tile - 40]
                    if not gate(enemy, hp, atk, df, tile - 40):
                        continue
                    hh -= pre_damage(tile - 40, hp) + ordinary_cost(enemy, atk, df)
                else:
                    after, prior = a['resourcesAfter'], before[i]
                    aa += after['atk'] - prior['atk']
                    dd += after['def'] - prior['def']
                    ll += after['level'] - prior['level']
                    hh += after['hp'] - prior['hp']
                key = (aa, dd, ll, ss)
                if hh > 0 and (key not in new or new[key][0] < hh):
                    new[key] = (hh, cc, pp)
        dp = new
        states += len(dp)
        if not dp:
            break
    summary = dict(schemaVersion=1, sourceSHA256=digest, scope='All early potion-deferral subsets and AD allocations, at one fixed event/shop schedule; navigation relaxed. Not a full-game or global bound.',
                   reservedSourceActions=sorted(reserves), advancedEvent=advance, forcedEarly=sorted(force_early), optionalPotionCount=len(optional), representedSubsets=2 ** len(optional),
                   cheapXPAsSoonAsPossible=args.asap_xp,
                   randomPolicy='worst-support', fixedShopPurchases={'1':12, '5':31},
                   assumptions=['Keep all other source events and key trades in their prescribed order.',
                                'Branch ATK/DEF purchases, with high-gold purchases advanced after source event 440.',
                                'Every early potion is either taken at its source position or just after the last white mage.',
                                'Ignore movement constraints in the DP; bytecode replay is required for positive witnesses.',
                                'Keep maximum HP per ATK/DEF/level/deferred-healing sum; no RNG or seed optimization.'],
                   targetStats=[696, 625, 2], survivors=len(dp), targetNumericSurvives=(696, 625, 2, 0) in dp,
                   stoppedAtSourceIndex=i, nativeRun=False, recordBreakingRoute=False)
    if delay:
        summary['delayedEvent'] = delay
    if args.asap_gold:
        summary['goldAsSoonAsPossible'] = True
        summary['assumptions'][1] = 'Buy exactly 12 low-gold stats and high-gold stats ASAP, preserving the source early red-key purchase budget.'
    if args.asap_xp:
        summary['assumptions'][0] = 'Keep all non-stat-purchase events and key trades in their prescribed order; buy the same 31 cheap XP stats ASAP.'
    if delay:
        summary['assumptions'][0] = 'Apply the declared battle delay; keep all other non-stat-purchase events and key trades ordered. ASAP purchases apply only when enabled.'
    if (696, 625, 2, 0) in dp:
        hp, choices, skipped = dp[696, 625, 2, 0]
        summary.update(numericHP=hp, deferredSourceActions=list(skipped))
        chosen = dict(choices)
        actual = OriginalRoute('generated/private/mhhf.swf', random_policy='worst-support')
        try:
            for step, (i, a) in enumerate(sequence):
                if i == 'restore':
                    for k in skipped:
                        actual.replay_action(ev[k])
                    continue
                if i in skipped or a['kind'] == 'floor':
                    continue
                event = dict(a)
                if step in chosen:
                    event['choice'] = chosen[step]
                actual.replay_action(event)
            assert actual.resources() == dict(hp=hp, atk=696, **{'def':625}, level=2, keys=[3,1,3], money=78, experience=2314)
            summary['originalBytecodeVerified'] = True
            proposal = dict(scope='Prefix-only numeric proposal; not native or record proof', randomPolicy=actual.random_policy,
                            actions=actual.actions, resources=actual.resources(), location=actual.location(), draws=actual.draws,
                            sections=metadata(actual.sections), transformation={k:v for k,v in summary.items() if k != 'metrics'})
            (out / 'proposal.json').write_text(json.dumps(proposal, indent=2) + '\n')
        except Exception as error:
            summary.update(originalBytecodeVerified=False, replayFailure=dict(step=step, sourceIndex=i, error=str(error), resources=actual.resources()))
    summary['metrics'] = dict(states=states, transitions=transitions, elapsedSeconds=time.perf_counter() - started,
                              processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024))
    if args.check:
        expected = json.loads(Path(args.check).read_text())
        assert {k:v for k,v in summary.items() if k != 'metrics'} == {k:v for k,v in expected.items() if k != 'metrics'}, 'Deferral receipt changed'
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
