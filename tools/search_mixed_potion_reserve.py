"""Bounded numeric search over potion timing and the amount kept for holy water.

An early potion can be taken now, after the last white mage, or after this prefix.
A later potion can be taken now or reserved. Keep maximum HP for identical ATK,
DEF, level, deferred healing and reserved healing. This ignores path differences
between masks, so any positive witness requires the original-bytecode replay.
All rewards and initial events come from the pinned public route. No original
map arrays, game assets or executable game sections are written publicly.
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
    ap.add_argument('--out', default='generated/MixedPotionReserve')
    ap.add_argument('--delay-group', help='Comma-separated indices, then colon and insertion index')
    ap.add_argument('--extra-advance', action='append', default=[])
    ap.add_argument('--target-reserve', type=int, default=1300)
    ap.add_argument('--must-eat', '--force-early', dest='force_early', default='', help='Original potion indices that must be consumed at their scheduled event')
    ap.add_argument('--delay', help='Move source event I just before J, formatted I,J')
    ap.add_argument('--asap-gold', action='store_true', help='Buy the same 12 low-gold stats, then high-gold stats ASAP, reserving the required early red key')
    ap.add_argument('--asap-xp', action='store_true', help='Buy the same 31 cheap XP stats as soon as the source XP shop is open')
    ap.add_argument('--check', help='Compare deterministic fields with a public receipt')
    ap.add_argument('--advance', help='Move source event J before I, formatted I,J')
    args = ap.parse_args()
    if args.target_reserve < 0:raise ValueError('Nonnegative reserved healing required')
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
    reserves = set()
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
    for text in args.extra_advance:
        at,moved=map(int,text.split(','))
        assert 0<=at<moved<end
        order.remove(moved)
        order.insert(order.index(at),moved)
    if args.delay_group:
        group,at=args.delay_group.split(':');group=list(map(int,group.split(',')));at=int(at)
        assert all(0<=i<at<end for i in group)
        for moved in group:order.remove(moved)
        for moved in group:order.insert(order.index(at),moved)
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
    dp = {(10, 10, 1, 0, 0): (1000, (), (), ())}
    states = transitions = 0
    for step, (i, a) in enumerate(sequence):
        new = {}
        variable = a and a.get('shop') in (1, 2, 5, 6) and a.get('choice') in (2, 3)
        for (atk, df, level, stash, reserved_hp), (hp, choices, skipped, reserved_indices) in dp.items():
            potion = a and a.get('originalTile') in (11,12)
            options = (2,3) if variable else ('eat','defer','reserve') if i in optional else ('eat','reserve') if potion else (None,)
            if potion and i in force_early:options = ('eat',)
            for choice in options:
                transitions += 1
                aa, dd, ll, hh, ss, cc, pp, rr, ri = atk, df, level, hp, stash, choices, skipped, reserved_hp, reserved_indices
                if i == 'restore':
                    hh += stash
                    ss = 0
                elif variable:
                    gain = {1: 4, 2: 20, 5: 5, 6: 17}[a['shop']]
                    aa += gain * (choice == 2)
                    dd += gain * (choice == 3)
                    cc += ((step, choice),)
                elif choice == 'reserve':
                    rr += {11:200,12:500}[a['originalTile']]
                    if rr > args.target_reserve:continue
                    ri += (i,)
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
                key = (aa, dd, ll, ss, rr)
                if hh > 0 and (key not in new or new[key][0] < hh):
                    new[key] = (hh, cc, pp, ri)
        dp = new
        states += len(dp)
        if not dp:
            break
    dp_elapsed = time.perf_counter() - started
    (out/'frontier.json').write_text(json.dumps([dict(stats=list(k),hp=v[0],deferred=list(v[2]),reserved=list(v[3])) for k,v in dp.items()],indent=2)+'\n')
    post_potions = sum(a.get('originalTile') in (11,12) for a in ev[last_white+1:])
    summary = dict(schemaVersion=1, sourceSHA256=digest,
                   scope='Fixed transformed event schedule and stat-purchase policy; numeric navigation relaxation. Prefix only, not global route optimality.',
                   advancedEvent=advance, extraAdvancedEvents=args.extra_advance, delayedGroup=args.delay_group,
                   mustConsumeAtScheduledEvent=sorted(force_early), earlyPotionChoices=len(optional),
                   latePotionChoices=post_potions, rawPotionChoiceUpperBound=3**len(optional)*2**post_potions,
                   requestedReservedHealing=args.target_reserve, cheapXPAsSoonAsPossible=args.asap_xp,
                   randomPolicy='worst-support', fixedShopPurchases={'1':12,'5':31},
                   assumptions=['Use the declared source-event transformations and purchase policy.',
                                'Early potions branch eat/defer/reserve; late potions branch eat/reserve, subject to must-eat constraints.',
                                'Merge HP labels only when ATK, DEF, level, deferred healing and reserved healing agree.',
                                'Movement is relaxed during DP; replay the selected witness in original bytecode before accepting it.',
                                'Resource rewards are read from the pinned source transitions; no new resource is granted.'],
                   targetStats=[696,625,2], survivors=len(dp),
                   maximumReservedHealingUnderCap=max((k[4] for k in dp),default=None),
                   maximumReservedHealingForTargetStatsUnderCap=max((k[4] for k in dp if k[:4]==(696,625,2,0)),default=None),
                   targetNumericSurvives=(696,625,2,0,args.target_reserve) in dp,
                   stoppedAtSourceIndex=i, nativeRun=False, recordBreakingRoute=False)
    if delay:
        summary['delayedEvent'] = delay
    if args.asap_gold:
        summary['goldAsSoonAsPossible'] = True
        summary['goldPurchasePolicy'] = '12 low-gold stats, then high-gold stats ASAP; reserve the early red-key budget.'
    if args.asap_xp:
        summary['xpPurchasePolicy'] = 'Buy the same 31 cheap XP stats ASAP.'
    if delay:
        summary['orderPolicy'] = 'Apply the declared battle delay to the otherwise declared schedule.'
    if (696, 625, 2, 0, args.target_reserve) in dp:
        hp, choices, skipped, reserved_indices = dp[696, 625, 2, 0, args.target_reserve]
        summary.update(numericHP=hp, deferredSourceActions=list(skipped),reservedSourceActions=list(reserved_indices),reservedHealing=args.target_reserve)
        chosen = dict(choices)
        actual = OriginalRoute('generated/private/mhhf.swf', random_policy='worst-support')
        try:
            for step, (i, a) in enumerate(sequence):
                if i == 'restore':
                    for k in skipped:
                        actual.replay_action(ev[k])
                    continue
                if i in skipped or i in reserved_indices or a['kind'] == 'floor':
                    continue
                event = dict(a)
                if step in chosen:
                    event['choice'] = chosen[step]
                actual.replay_action(event)
            assert actual.resources() == dict(hp=hp, atk=696, **{'def':625}, level=2, keys=[3,1,3], money=78, experience=2314)
            summary['originalBytecodeVerified'] = True
            proposal = dict(scope='Original-bytecode verified numeric prefix; no native or record claim', randomPolicy=actual.random_policy,
                            actions=actual.actions, resources=actual.resources(), location=actual.location(), draws=actual.draws,
                            sections=metadata(actual.sections), transformation={k:v for k,v in summary.items() if k != 'metrics'})
            (out / 'proposal.json').write_text(json.dumps(proposal, indent=2) + '\n')
        except Exception as error:
            summary.update(originalBytecodeVerified=False, replayFailure=dict(step=step, sourceIndex=i, error=str(error), resources=actual.resources()))
    summary['metrics'] = dict(states=states, transitions=transitions, dpElapsedSeconds=dp_elapsed, elapsedSeconds=time.perf_counter() - started,
                              processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024))
    if args.check:
        expected = json.loads(Path(args.check).read_text())
        assert {k:v for k,v in summary.items() if k != 'metrics'} == {k:v for k,v in expected.items() if k != 'metrics'}, 'Deferral receipt changed'
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
