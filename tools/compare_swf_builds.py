"""Static comparison of two separately pinned archives; never execute game code.

Publish hashes, offsets and counts only. Identical scripts are a byte-level fact,
not a proof that different input, save and wall-clock rules are interchangeable.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import zlib
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'src')]
from avm1 import actions, constant_pool
from inspect_swf import Bits, tags
from flash_sections import SWF_SHA, GDUT_SWF_SHA


def digest(b):
    return hashlib.sha256(b).hexdigest()


def inspect(path, expected):
    raw = Path(path).read_bytes()
    if digest(raw) != expected:
        raise ValueError('Unpinned SWF build')
    if raw[:3] not in (b'CWS', b'FWS'):
        raise ValueError('Unsupported SWF signature')
    b = raw[:8] + zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw
    if len(b) != int.from_bytes(b[4:8], 'little'):
        raise ValueError('Declared SWF size mismatch')
    r = Bits(b, 8)
    rect = r.rect()
    frames = collections.defaultdict(lambda: 1)
    ordinals = collections.Counter()
    scripts, functions, buttons, alltags = {}, {}, {}, {}
    tagcounts = collections.Counter()
    title = None
    for code, p, n, off, parent in tags(b, r.pos + 4, len(b)):
        tagcounts[code] += 1
        key = (parent, frames[parent], code)
        ordinals[key] += 1
        key = f'{parent}/frame:{frames[parent]}/code:{code}/ordinal:{ordinals[key]}'
        item = dict(sha256=digest(b[p:p+n]), offset=p, length=n)
        alltags[key] = item
        if code in (12, 59):
            scripts[key] = item
            if code == 12 and parent == 'root':
                pool = []
                for a in actions(b[p:p+n]):
                    if a.opcode == 0x88:
                        pool = constant_pool(a.data)
                    # The reviewed gameplay functions use DefineFunction (0x9B).
                    # This is not a census of DefineFunction2/nested callbacks.
                    if a.name:
                        functions[f'{frames[parent]}:{a.name}'] = dict(
                            bodySHA256=digest(a.body),
                            poolSHA256=digest(json.dumps(pool, ensure_ascii=False).encode()),
                            parameters=list(a.parameters), bodyLength=len(a.body),
                            offset=p+a.end-len(a.body))
        if code == 34:
            buttons[str(int.from_bytes(b[p:p+2], 'little'))] = item
        if code == 2 and int.from_bytes(b[p:p+2], 'little') == 455:
            title = dict(characterId=455, tagWithHeaderSHA256=digest(b[off:p+n]), **item)
        if code == 1:
            frames[parent] += 1
    return dict(sha256=digest(raw), gitBlobSHA1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
                bytes=len(raw), signature=raw[:3].decode(), swfFormatVersion=raw[3], uncompressedBytes=len(b),
                stageRect=rect, frameRate=int.from_bytes(b[r.pos:r.pos+2], 'little')/256,
                rootFrames=int.from_bytes(b[r.pos+2:r.pos+4], 'little'), scripts=scripts,
                functions=functions, buttons=buttons, alltags=alltags, tagCounts={str(k):v for k,v in tagcounts.items()}, titleShape=title)


def compare(a, b, kind):
    out = []
    for key in sorted(set(a[kind]) | set(b[kind])):
        x, y = a[kind].get(key), b[kind].get(key)
        if x is None or y is None or any(x.get(t) != y.get(t) for t in ('sha256', 'bodySHA256', 'poolSHA256', 'parameters')):
            out.append(dict(key=key, mhhf=x, gdut=y))
    return out


def run(mhhf, gdut):
    a, b = inspect(mhhf, SWF_SHA), inspect(gdut, GDUT_SWF_SHA)
    hidden = {'scripts', 'functions', 'buttons', 'alltags'}
    return dict(schemaVersion=1, scope='Static byte/container comparison only; no game execution or global semantic-equivalence claim',
                mhhf={k:v for k,v in a.items() if k not in hidden}, gdut={k:v for k,v in b.items() if k not in hidden},
                scriptCounts=[len(a['scripts']), len(b['scripts'])], scriptDifferences=compare(a,b,'scripts'),
                rootDefineFunctionCounts=[len(a['functions']),len(b['functions'])],
                rootDefineFunctionCoverage='Top-level root DoAction DefineFunction only, including constant pools and parameters; excludes DefineFunction2 and nested functions.',
                functionDifferences=compare(a,b,'functions'), buttonDifferences=compare(a,b,'buttons'),
                tagCounts=[len(a['alltags']),len(b['alltags'])], tagDifferences=compare(a,b,'alltags'),
                titleShapeMatches=a['titleShape']['sha256']==b['titleShape']['sha256'])


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mhhf'); p.add_argument('gdut'); p.add_argument('--out',required=True); p.add_argument('--check')
    args=p.parse_args(); result=run(args.mhhf,args.gdut)
    if args.check:
        assert result==json.loads(Path(args.check).read_text()), 'Build comparison changed'
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:len(v) if k.endswith('Differences') else v for k,v in result.items() if k not in ('mhhf','gdut')}))
