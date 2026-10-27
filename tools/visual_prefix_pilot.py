"""Experimental screenshot-only replay of a bounded pinned route prefix.

macOS/Vision required. This bounded pilot covers walking, early battles/loot,
stairs and early shops and dialogues (up to918 actions before the first compass use). It does not cover24 floors, later dialogue,
compass, final score or record verification. Source plans execute only the
reviewed numerical VM offline; the actual movie receives ordinary DOM inputs.
"""
import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from original_route import OriginalRoute

SOURCE = Path('experiments/full-route-hp28568-proposal.json')
SOURCE_SHA = '0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9'
ARCHIVE_SHA = '40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896'
ARROWS = {-1: 'ArrowLeft', 1: 'ArrowRight', -11: 'ArrowUp', 11: 'ArrowDown'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_plan(swf, count=29):
    if sha(SOURCE.read_bytes()) != SOURCE_SHA or sha(Path(swf).read_bytes()) != ARCHIVE_SHA:
        raise ValueError('Pinned source/archive mismatch')
    route = OriginalRoute(swf, random_policy='worst-support')
    plan = []
    for index, action in enumerate(json.loads(SOURCE.read_bytes())['actions'][:count]):
        if action['kind'] not in ('consume', 'floor', 'shop', 'dialogue'):
            raise ValueError('Unsupported pilot action')
        _, position = route.location()
        start_position = [position % 11, position//11]
        steps = []
        for floor, target, stair in route.contact_path(action['floor'], action['position'][1]*11+action['position'][0]):
            if stair:
                raise ValueError('Implicit stair outside pilot contract')
            steps.append(dict(key=ARROWS[target-position], x=target % 11, y=target//11))
            position = target
        contact = ARROWS[action['position'][1]*11+action['position'][0]-position]
        route.replay_action(action)
        floor, position = route.location()
        plan.append(dict(index=index, kind=action['kind'], tile=action.get('originalTile'),
                         steps=steps, startPosition=start_position, contact=contact, choice=action.get('choice'),
                         shop=action.get('shop'),
                         expectedFloor=floor, expectedPosition=[position % 11, position//11],
                         expectedResources=route.resources()))
    return plan


def matches(screen, expected):
    values = screen.get('values', {})
    required = {**{k: expected[k] for k in ('atk', 'def', 'level', 'money', 'experience')},
                **dict(zip(('yellow', 'blue', 'red'), expected['keys']))}
    return all(values.get(k) == value for k, value in required.items()) and values.get('hp', -1) >= expected['hp']


def hero(screen, position):
    return any([p['x'], p['y']] == position for p in screen.get('heroCandidates', []))


def action_visible(screen, expected_resources, expected_position, require_closed=True):
    """Confirm either a closed-map action or a shop transaction's open-menu state.

    Shop overlays can hide the hero sprite. For that intermediate state, require
    the modal to remain open and the exact purchased-resource HUD; the preceding
    path already confirmed each ordinary movement step and the shop contact.
    """
    closed = screen.get('orangeMaxRun', 0) < 100
    if not matches(screen, expected_resources):
        return False
    if require_closed:
        return closed and hero(screen, expected_position)
    return not closed


def complete_shop(action, press, confirm_purchase):
    """Select the requested shop option and leave its menu using ordinary keys."""
    if action['shop'] == 1:
        press('Space')
    for _ in range(action['choice']-1):
        press('2')
    press('Space')
    if action['choice'] != 4:
        confirm_purchase()
        for _ in range(4-action['choice']):
            press('2')
        press('Space')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swf', default='generated/private/gdut.swf')
    parser.add_argument('--out', default='generated/VisualPrefix29')
    parser.add_argument('--actions', type=int, choices=(29, 86, 184, 360, 426, 600, 918), default=29)
    args = parser.parse_args()
    plan = compile_plan(args.swf, args.actions)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out/'compiled-plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    helper = out/'read-visible-hud'
    subprocess.run(['swiftc', 'tools/read_visible_hud.swift', '-o', str(helper)], check=True)
    reader = subprocess.Popen([str(helper)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    environment = {**os.environ, 'MOTA_FLASH_SWF': str(Path(args.swf).resolve()),
                   'MOTA_VISUAL_HOST_DIR': str(out/'host')}
    log = (out/'host.log').open('w')
    host = subprocess.Popen(['node', 'tools/visual_prefix_host.mjs'], env=environment, stdout=log, stderr=subprocess.STDOUT)
    endpoint = None
    records = []
    boot_observations = []
    started = time.monotonic()
    failure = None
    failed_observation = None
    hud_source_sha = sha(Path('tools/read_visible_hud.swift').read_bytes())
    controller_source_sha = sha(Path(__file__).read_bytes())

    def call(operation, body=None):
        request = urllib.request.Request(endpoint+operation, json.dumps(body or {}).encode(),
                                         headers={'Content-Type': 'application/json'})
        return json.load(urllib.request.urlopen(request, timeout=30))

    def inspect_file(filename, read_hud=True):
        reader.stdin.write(json.dumps(dict(path=filename, readHUD=read_hud))+'\n')
        reader.stdin.flush()
        if not select.select([reader.stdout], [], [], 60)[0]:
            raise TimeoutError('Visible HUD reader stalled')
        screen = json.loads(reader.stdout.readline())
        if 'error' in screen:
            raise ValueError(screen['error'])
        screen.update(imageSHA256=sha(Path(filename).read_bytes()), imagePath=filename)
        return screen

    def capture(read_hud=True):
        return inspect_file(call('/capture')['path'], read_hud=read_hud)

    def boot_capture(stage):
        screen = capture()
        boot_observations.append(dict(stage=stage, observed=screen))
        (out/'boot-observations.json').write_text(json.dumps(boot_observations, indent=2)+'\n')
        return screen

    def press(key):
        call('/press', dict(keys=[key], gap=35, wait=150))

    def wait_action(action, allow_space=True, require_closed=True):
        limit = time.monotonic()+25
        while True:
            screen = capture()
            if action_visible(screen, action['expectedResources'], action['expectedPosition'], require_closed):
                return screen
            if time.monotonic() > limit:
                raise ValueError(f"Action{action['index']} not visually matched: {screen['values']}")
            closed = screen['orangeMaxRun'] < 100
            if allow_space and not closed:
                press('Space')
            else:
                time.sleep(.15)

    try:
        while time.monotonic()-started < 30:
            if host.poll() is not None:
                raise RuntimeError('Browser host exited during initialization')
            file = out/'host'/'endpoint.json'
            if file.exists():
                endpoint = json.loads(file.read_text())['address']
                try:
                    if call('/status')['ready']:
                        break
                except OSError:
                    pass
            time.sleep(.1)
        else:
            raise TimeoutError('Browser host not ready')
        capture()  # Warm Vision on actual pixels before starting the game.
        limit = time.monotonic()+60
        while True:
            menu = capture()
            if menu.get('menuCandidate'):
                break
            if time.monotonic() > limit:
                raise ValueError('Title/menu text regions did not become visible')
            time.sleep(.2)
        (out/'menu.json').write_text(json.dumps(menu, indent=2)+'\n')
        call('/start')
        press('Space')
        natural = dict(hp=1000, atk=10, **{'def': 10}, level=1, keys=[1, 1, 1], money=0, experience=0)
        for _ in range(60):
            fairy = boot_capture('fairy-dialogue')
            if matches(fairy, natural) and fairy['orangeMaxRun'] < 100:
                break
            if fairy['orangeMaxRun'] >= 100:
                press('Space')
            elif fairy['values'].get('hp') == 1000 and all(fairy['values'].get(k) == 0 for k in ('yellow', 'blue', 'red')) and hero(fairy, [5, 9]):
                press('ArrowUp')
            else:
                press('Space')
        else:
            raise ValueError('Natural fairy opening not visibly matched')
        natural['keys'] = [0, 1, 1]
        entry_seen = False
        for count in range(30):
            opening = boot_capture('enter-MT1')
            if matches(opening, natural) and hero(opening, [5, 9]) and opening['orangeMaxRun'] < 100:
                break
            if count >= 2 and hero(opening, [5, 9]) and opening['values'].get('yellow') == 0:
                # Do not press Up again while MT1's HUD is still being read;
                # the next Up would spend its red key and destroy this check.
                entry_seen = True
            if entry_seen:
                time.sleep(.2)
            elif opening['orangeMaxRun'] >= 100:
                press('Space')
            else:
                press('ArrowUp')
                if matches(opening, natural) and hero(opening, [5, 1]):
                    # This Up contacts the visible opening floor's stair.
                    # Wait through its transition before issuing more input;
                    # otherwise a queued Up can spend MT1's red key.
                    entry_seen = True
        else:
            raise ValueError('Natural MT1 entry not visibly matched')
        (out/'opening.json').write_text(json.dumps(opening, indent=2)+'\n')
        for action in plan:
            previous_position = action['startPosition']
            before_values = records[-1]['observed']['values'] if records else opening['values']
            for step in action['steps']:
                press(step['key'])
                for attempt in range(12):
                    # Ordinary walking needs only visible position and modal
                    # pixels. Keep full HUD OCR for action acceptance and for
                    # the rare retry that verifies the previous resource state.
                    screen = capture(read_hud=False)
                    if hero(screen, [step['x'], step['y']]) and screen['orangeMaxRun'] < 100:
                        break
                    # A battle can update the HUD before movement is enabled.
                    # Retry only when the image still shows the old cell AND
                    # the complete previous HUD; never infer a missing digit.
                    if attempt in (2, 5, 8) and screen['orangeMaxRun'] < 100 and hero(screen, previous_position):
                        previous = capture()
                        if previous['values'] == before_values and previous['orangeMaxRun'] < 100 and hero(previous, previous_position):
                            press(step['key'])
                    time.sleep(.15)
                else:
                    raise ValueError(f"Walking not visibly matched at action{action['index']}")
                previous_position = [step['x'], step['y']]
            press(action['contact'])
            if action['kind'] == 'shop':
                # Only the low-gold shop enters an introduction frame.
                # The XP shop opens its four options directly; Space there
                # would immediately buy the default paid level.
                complete_shop(action, press, lambda: wait_action(action, allow_space=False, require_closed=False))
            observed = wait_action(action)
            records.append(dict(actionIndex=action['index'], expectedFloor=action['expectedFloor'],
                                expectedPosition=action['expectedPosition'], expectedResources=action['expectedResources'],
                                observed=observed))
            (out/'progress.json').write_text(json.dumps(records, indent=2)+'\n')
            print(json.dumps(dict(index=action['index'], visible=observed['values'])), flush=True)
    except Exception as error:
        failure = str(error)
        if endpoint:
            try:
                failed_observation = capture()
                (out/'failure-observation.json').write_text(json.dumps(failed_observation, indent=2)+'\n')
            except (OSError, ValueError, TimeoutError):
                pass
        print('FAILED', failure, flush=True)
    finally:
        if endpoint:
            try:
                call('/close')
            except OSError:
                pass
        if host.poll() is None:
            host.terminate()
        host.wait(timeout=10)
        reader.terminate()
        reader.wait(timeout=10)
        log.close()
        receipt = dict(schemaVersion=1, scope=f'Experimental{args.actions}-action visible HUD/hero prefix check only; no24-floor or record proof',
                       sourceProposalSHA256=SOURCE_SHA, originalSWFSHA256=ARCHIVE_SHA,
                       hudReaderSourceSHA256=hud_source_sha, controllerSourceSHA256=controller_source_sha,
                       unattendedFromMenu=True, observerLoaded=False, gameVariableReads=False,
                       gameVariableWrites=False, seedControl=False, realClock=True, audioOutputDisabled=True,
                       requestedActions=args.actions, matchedActions=len(records), matchedRequestedPrefix=len(records) == args.actions and failure is None,
                       complete24Floors=False, recordBreakingRoute=False, floorLabelIndependentReviewPending=True,
                       elapsedSeconds=time.monotonic()-started, error=failure,
                       finalVisibleHUD=records[-1]['observed']['values'] if records else None,
                       limitations='Fixed screenshot layout, heuristic hero/modal detection; floor identity requires separate visual review; no later dialogue, compass or ending verification')
        inputs = out/'host'/'inputs.json'
        if inputs.exists():
            receipt.update(inputSHA256=sha(inputs.read_bytes()), ordinaryInputCount=len(json.loads(inputs.read_bytes())))
        (out/'visible-prefix.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(receipt), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
