"""Exact shop allocation on two fixed real encounter schedules.

Gold purchases can be skipped or changed to HP. Existing XP/high-gold stat
purchases can change between ATK and DEF. Full-prefix reduced-gold cases add
one high-gold stat purchase on the first existing high-gold shop visit.
No encounter, door, potion, feather or visit order is searched. Numerical VM
replay of each best survivor is required; this is not a native replay.
"""
import argparse
import hashlib
import json
import resource
import sys
import time
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1] / 'src')]
from original_route import OriginalRoute
from flash_model import gate, pre_damage, ordinary_cost
from route_sections import metadata

SOURCE = Path('experiments/full-route-hp28568-proposal.json')
SOURCE_HASH = '0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9'
CASES = [(12, 0, 'baseline'), (8, 0, 'eight-stats'),
         (8, 1, 'seven-stats-hp800'), (9, 1, 'eight-stats-hp800')]


def search(events, initial, enemies, cap, hp_cap, extra_high=False):
    # Level, keys, XP and world are fixed by this schedule. Gold is determined
    # by the number of low purchases and the declared extra high purchase.
    # Within identical ATK/DEF/counters only maximum HP is retained. Every
    # pre-battle gate and HP transition in this prefix is monotone in HP.
    dp = {(10, 10, 0, 0): (1000, ())}
    states, transitions, original_gold = 1, 0, 0
    extra_done = False
    began = time.perf_counter()
    for index, action in enumerate(events):
        before = events[index-1]['resourcesAfter'] if index else initial
        after = action['resourcesAfter']
        shop = action.get('shop')
        low = shop == 1
        variable = shop in (2, 5, 6) and action.get('choice') in (2, 3)
        if low:
            assert action['choice'] in (2, 3)
            original_gold += 1
        if shop == 2 and extra_high and not extra_done:
            expanded = {}
            for (atk, defense, count, hp_count), (hp, choices) in dp.items():
                for choice in (2, 3):
                    transitions += 1
                    key = (atk + 20*(choice == 2), defense + 20*(choice == 3), count, hp_count)
                    if key not in expanded or expanded[key][0] < hp:
                        expanded[key] = (hp, choices + ((index, choice, True),))
            dp = expanded
            states += len(dp)
            extra_done = True
        new = {}
        for (atk, defense, count, hp_count), (hp, choices) in dp.items():
            options = (0, 2, 3, 1) if low and hp_cap else (0, 2, 3) if low else (2, 3) if variable else (None,)
            for choice in options:
                transitions += 1
                aa, dd, gg, hh, health, path = atk, defense, count, hp_count, hp, choices
                if low:
                    if choice:
                        gg += 1
                        if gg > cap:
                            continue
                        if choice == 1:
                            hh += 1
                            if hh > hp_cap:
                                continue
                            health += 800
                        else:
                            aa += 4*(choice == 2)
                            dd += 4*(choice == 3)
                    path += ((index, choice, False),)
                elif variable:
                    gain = {2: 20, 5: 5, 6: 17}[shop]
                    aa += gain*(choice == 2)
                    dd += gain*(choice == 3)
                    path += ((index, choice, False),)
                elif 'randomDraws' in action:
                    enemy_id = action['originalTile']-40
                    assert 0 <= enemy_id <= 30
                    enemy = enemies[enemy_id]
                    if not gate(enemy, health, aa, dd, enemy_id):
                        continue
                    health -= pre_damage(enemy_id, health) + ordinary_cost(enemy, aa, dd)
                else:
                    aa += after['atk']-before['atk']
                    dd += after['def']-before['def']
                    health += after['hp']-before['hp']
                cash = after['money']+25*(original_gold-gg)-100*extra_done
                if health <= 0 or cash < 0:
                    continue
                key = (aa, dd, gg, hh)
                if key not in new or new[key][0] < health:
                    new[key] = (health, path)
        dp = new
        states += len(dp)
        if not dp:
            break
    return dp, dict(stoppedAt=index, reachedScheduleEnd=index == len(events)-1 and bool(dp),
                    storedLabels=states, generatedTransitions=transitions,
                    dpElapsedSeconds=time.perf_counter()-began)


def run(swf, out):
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError('Pinned source mismatch')
    actions = json.loads(raw)['actions']
    base = OriginalRoute(swf, random_policy='worst-support')
    results = []
    began = time.perf_counter()
    for name, floor, tile in [('first-red-bat', 8, 49), ('first-gold-captain', 13, 55)]:
        end = next(i for i, a in enumerate(actions) if a['floor'] == floor and a.get('originalTile') == tile)
        events = actions[:end+1]
        for cap, hp_cap, case in CASES:
            extra = name == 'first-gold-captain' and cap < 12
            survivors, metrics = search(events, base.resources(), base.root['boss_man'], cap, hp_cap, extra)
            result = dict(schedule=name, case=case, sourceEndIndex=end, lowGoldPurchaseCap=cap,
                          lowGoldHPPurchaseCap=hp_cap, extraHighGoldPurchase=extra, **metrics)
            if metrics['reachedScheduleEnd']:
                health, key, choices = max((hp, key, choices) for key, (hp, choices) in survivors.items())
                changed = {i: c for i, c, added in choices if not added}
                added = {i: c for i, c, added in choices if added}
                replay = OriginalRoute(swf, random_policy='worst-support')
                for index, original in enumerate(events):
                    action = original.copy()
                    if index in added:
                        replay.replay_action({**action, 'choice': added[index]})
                    if index in changed:
                        if changed[index] == 0:
                            continue
                        action['choice'] = changed[index]
                    replay.replay_action(action)
                actual = replay.resources()
                expected = {**events[-1]['resourcesAfter'], 'hp': health,
                            'atk': key[0], 'def': key[1],
                            'money': events[-1]['resourcesAfter']['money'] + 25*(12-key[2])-100*extra}
                if actual != expected:
                    raise AssertionError('Original VM disagrees with DP survivor')
                directory = out / (name+'-'+case)
                directory.mkdir(parents=True, exist_ok=False)
                proposal = dict(scope='Numerical fixed-prefix witness only; no native completion or record claim',
                                randomPolicy=replay.random_policy, actions=replay.actions, resources=actual,
                                location=replay.location(), draws=replay.draws, sections=metadata(replay.sections))
                data = (json.dumps(proposal, indent=2)+'\n').encode()
                (directory/'proposal.json').write_bytes(data)
                result.update(survivorStateCount=len(survivors), bestHP=health, resources=actual,
                              allocationChoices=choices, originalBytecodeReplayPassed=True,
                              witnessSHA256=hashlib.sha256(data).hexdigest())
            else:
                result.update(survivorStateCount=0, originalBytecodeReplayPassed=False)
            results.append(result)
            print(json.dumps({k: v for k, v in result.items() if k != 'allocationChoices'}), flush=True)
    return dict(schemaVersion=1, scope='Exact allocation only within two fixed encounter/shop-visit schedules; no global bound, native run or record claim',
                sourceProposalSHA256=SOURCE_HASH, originalSWFSHA256=hashlib.sha256(Path(swf).read_bytes()).hexdigest(),
                policy='worst-support (draw199), existing low-gold slots skip/ATK/DEF/HP; fixed XP/high-gold slots ATK/DEF; at most one extra high-gold buy at first existing high-gold visit for reduced-gold full prefixes',
                dominance='Maximum HP at identical ATK, DEF, low-gold purchase count and HP-purchase count; other world/resources follow fixed schedule',
                cases=results, totalElapsedSeconds=time.perf_counter()-began,
                processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swf', default='generated/private/mhhf.swf')
    parser.add_argument('--out', default='generated/EarlyGoldAllocation')
    parser.add_argument('--summary', default='generated/early-gold-allocation.json')
    parser.add_argument('--check')
    args = parser.parse_args()
    result = run(args.swf, Path(args.out))
    if args.check:
        expected = json.loads(Path(args.check).read_text())
        ignored = {'dpElapsedSeconds', 'witnessSHA256'}
        stable = lambda r: json.dumps([{k: v for k, v in c.items() if k not in ignored}
                                       for c in r['cases']], sort_keys=True)
        if stable(result) != stable(expected):
            raise AssertionError('Published case results differ')
    Path(args.summary).write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
