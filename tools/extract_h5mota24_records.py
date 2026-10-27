"""Extract public H5Mota24 standings from inert SSR JSON; never execute site JS.

Keep fetched HTML/game sources in generated/. Publish only receipt.json: scores,
submission IDs, source URLs/hashes and the limits of the comparison.
"""
import argparse
import datetime
import hashlib
import json
import re
import urllib.request
from pathlib import Path

SOURCES = {
    'h5mota-page.html': 'https://h5mota.com/tower/?name=24',
    'h5mota-verdict.js': 'https://static.mota.press/h5-front/878458b44a4cca3f40dad736bc75ab02bc4f35e934c20baf635e9b73d6605fc3/assets/VerdictIcon-ntIqIgAy.js',
    'h5mota-project-MT_1.js': 'https://h5mota.com/games/24/project/floors/MT_1.js',
}
VERDICT_SHA = 'bce5e02fc63fa9cf78c7e634944638483e55edf535a60dbcfd1210dcbb05694a'


def extract(raw):
    html = raw['h5mota-page.html'].decode()
    match = re.search(r'<script data-ssr="tower" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise ValueError('Expected public tower SSR JSON is absent')
    page = json.loads(match[1])
    if page['tower']['name'] != '24':
        raise ValueError('Unexpected tower')
    if hashlib.sha256(raw['h5mota-verdict.js']).hexdigest() != VERDICT_SHA:
        raise ValueError('Pinned public verdict renderer changed')
    # These are data strings in an inert floor object, never evaluated.
    ending = raw['h5mota-project-MT_1.js'].decode()
    floor = json.loads(ending.split('=',1)[1].strip().rstrip(';'))
    strings = []
    def walk(value):
        if isinstance(value, str):
            strings.append(re.sub(r'\s+', '', value))
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(floor)
    required = ['flag:t+(10000000000-100000*flag:t)',
                'status:def+(1000000000000-1000000*status:def)',
                '(status:atk+status:def)+(1000000000000-1000000*(status:atk+status:def))']
    if any(formula not in strings for formula in required):
        raise ValueError('Reviewed minimum-score encodings changed')
    records = []
    for group in page['record']:
        if group['name'] != '24':
            continue
        for board in group['endings']:
            name = board['name']
            if not name.startswith('24层结局（') or not board['submissions']:
                continue
            first = board['submissions'][0]
            raw_score = int(first['score'])
            value = raw_score
            encoding = 'score = value'
            if name in ('24层结局（最低商店购买次数）','24层结局（最低经验老人购买次数）'):
                numerator = 10**10-raw_score
                if numerator % 99999:
                    raise ValueError('Invalid minimum-count encoded score')
                value = numerator//99999
                encoding = 'score = 10000000000 - 99999 * value'
            elif name in ('24层结局（最低防御）','24层结局（最低攻防和）'):
                numerator = 10**12-raw_score
                if numerator % 999999:
                    raise ValueError('Invalid minimum-stat encoded score')
                value = numerator//999999
                encoding = 'score = 1000000000000 - 999999 * value'
            elif '最低' in name:
                raise ValueError('Unreviewed minimum-score category')
            records.append(dict(category=name, displayedRank=1, rawScore=raw_score,
                                metricValue=value, direction='minimize' if '最低' in name else 'maximize',
                                encoding=encoding, submissionId=int(first['id']),
                                submittedAtUnix=int(first['timestamp']), reportedVerificationCode=int(first['verify']),
                                platformReportedReplayVerificationPassed=int(first['verify']) == -1,
                                verifiedOnlyBoard=bool(board['verifiedOnly']), independentReplayVerified=False))
    return dict(schemaVersion=1, scope='Public listed H5Mota24 leaderboard first places and reported replay-verification flags. No project record broken; Flash, H5 and Mota Mod builds remain separate.',
                sourceURL=SOURCES['h5mota-page.html'], tower='24',
                reportedDescription=page['meta']['description'], leaderboardCount=len(records), records=records,
                verdictInterpretation={'-1':'Replay verification succeeded, according to the pinned public verdict renderer.',
                                       '0 or 8':'Unverified, according to that renderer.',
                                       'other':'Verification failure code, according to that renderer.'},
                provenance=[dict(url=url, sha256=hashlib.sha256(raw[name]).hexdigest(), bytes=len(raw[name]))
                            for name,url in SOURCES.items()],
                exactSubmissionGameBuildSHA256=None, projectRecordBreakingRouteExists=False,
                limitations=['Scores are listed platform records, not independently replayed by this project.',
                             'The per-submission complete game-build fingerprint is not provided by this public table.',
                             'The original SWF cannot be compared to these H5 records without establishing equal rules.',
                             'Other players replay files are not publicly downloadable through the normal site UI.'],
                replayAvailabilitySourceURL='https://h5mota.com/bbs/thread/?p=1&tid=1166')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='generated/H5Mota24RecordSnapshot')
    parser.add_argument('--from-local', help='Use previously fetched files with the three SOURCES basenames')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    raw = {}
    for name,url in SOURCES.items():
        if args.from_local:
            raw[name] = (Path(args.from_local)/name).read_bytes()
        else:
            request = urllib.request.Request(url, headers={'User-Agent':'Mota24OptimalityLab research'})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw[name] = response.read(20_000_001)
            if len(raw[name]) > 20_000_000:
                raise ValueError('Source exceeds bounded reader limit')
            (out/name).write_bytes(raw[name])
    receipt = extract(raw)
    receipt.update(extractedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   inputMode='provided cached source files' if args.from_local else 'fresh HTTPS GETs')
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    for row in receipt['records']:
        print(row['category'], row['metricValue'], 'platformVerified',row['platformReportedReplayVerificationPassed'])


if __name__ == '__main__':
    main()
