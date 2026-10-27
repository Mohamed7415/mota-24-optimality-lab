"""Fetch public H5Mota24 source text privately, recording every URL and SHA256.

Only plain JSON assignment data is parsed to discover map filenames. No media,
JavaScript evaluation, login or score submission occurs.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from import_h5_24_json import parse_assignment


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Mota24OptimalityLab research'})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(5_000_001)
        final=response.geturl()
    if len(data)>5_000_000:
        raise ValueError('Source-file limit exceeded')
    return data,final


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default='https://h5mota.com/games/24/')
    parser.add_argument('--out',type=Path,default=Path('generated/H5Mota24Fetched'))
    parser.add_argument('--check',type=Path,help='Require all source hashes in a published static-import receipt')
    args=parser.parse_args()
    base=args.base.rstrip('/')+'/'
    args.out.mkdir(parents=True,exist_ok=False)
    first,first_url=fetch(base+'project/data.js')
    config=parse_assignment(first)
    floor_ids=config['main']['floorIds']
    if config['firstData']['name']!='24' or len(floor_ids)!=27 or any(not re.fullmatch(r'MT(?:\d+[wes]?|_\d+)',name) for name in floor_ids):
        raise ValueError('Unsupported project identity/map list')
    files=['project/'+name+'.js' for name in ('data','enemys','items','events','maps','icons','functions','plugins')]
    files += ['project/floors/'+name+'.js' for name in floor_ids]+['index.html','main.js']
    def one(filename):
        url=base+filename
        try:
            data,final=(first,first_url) if filename=='project/data.js' else fetch(url)
            target=args.out/filename
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            return dict(file=filename,url=url,finalURL=final,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        except Exception as error:
            return dict(file=filename,url=url,error=str(error))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(one,files):
            rows.append(row)
            (args.out/'provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(row['file'],'error' if 'error' in row else 'ok',flush=True)
    failures=[r for r in rows if 'error' in r]
    if failures:
        raise RuntimeError(f'{len(failures)} source fetches failed; preserve the manifest and diagnose')
    if args.check:
        wanted=json.loads(args.check.read_text())['provenance']
        actual={r['file']:r['sha256'] for r in rows}
        expected={r['file']:r['sha256'] for r in wanted}
        if actual!=expected:
            changed=sorted(name for name in actual.keys()|expected.keys() if actual.get(name)!=expected.get(name))
            raise ValueError('Public project differs from pinned source files: '+','.join(changed))
    print('COMPLETE',len(rows),'source files; no media or project functions executed.',flush=True)


if __name__=='__main__':
    main()
