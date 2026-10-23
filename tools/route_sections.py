"""Pinned static sections for full-route numerical planning; no assets published."""
import collections,hashlib,struct,sys,zlib
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from avm1 import actions,constant_pool
from inspect_swf import Bits,tags
from flash_sections import SWF_SHA
FUNCTIONS={'Move_arrow','SetLineDisplay','DelLineDisplay','DelBaseDisplay'}
# Only known completion boundaries, not arbitrary game-defined callbacks.
NPC={568:{32,39,59,67,72,83},714:{8,19},695:{8,17,23},745:{17,21},770:{20},780:{5},795:{6,9,10,12},636:{7}}

def sections(filename):
    raw=Path(filename).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SWF_SHA:raise ValueError('Unpinned original')
    b=raw[:8]+zlib.decompress(raw[8:]);r=Bits(b,8);r.rect();frame=collections.defaultdict(lambda:1);out={}
    for code,p,n,off,parent in tags(b,r.pos+4,len(b)):
        if code==12:
            if parent=='root' and frame[parent]==4346:
                pool=[]
                for a in actions(b[p:p+n]):
                    if a.opcode==0x88:pool=constant_pool(a.data)
                    if a.name in FUNCTIONS:
                        out[a.name]={'bytes':a.body,'pool':pool.copy(),'parameters':a.parameters,'parent':parent,'frame':frame[parent],'offset':p+a.end-len(a.body),'sha256':hashlib.sha256(a.body).hexdigest()}
            sprite=int(parent.rsplit(':',1)[1]) if '/sprite:' in parent else None
            if sprite==855 and frame[parent] in (1,6) or sprite in NPC and frame[parent] in NPC[sprite]:
                out[f'{sprite}:{frame[parent]}']={'bytes':b[p:p+n],'pool':[],'parameters':(),'parent':parent,'frame':frame[parent],'offset':p,'sha256':hashlib.sha256(b[p:p+n]).hexdigest()}
        if code==34 and parent=='root' and int.from_bytes(b[p:p+2],'little')==628:
            offset=int.from_bytes(b[p+3:p+5],'little');q=p+3+offset
            while q<p+n:
                size,conditions=struct.unpack_from('<HH',b,q);end=q+size if size else p+n
                if (conditions>>9)&127==32:
                    body=b[q+4:end];out['button628:Space']={'bytes':body,'pool':[],'parameters':(),'parent':parent,'frame':None,'offset':q+4,'sha256':hashlib.sha256(body).hexdigest(),'buttonId':628,'keyCode':32}
                if not size:break
                q=end
        if code==1:frame[parent]+=1
    expected=FUNCTIONS|{'855:1','855:6','button628:Space'}|{f'{s}:{f}' for s,fs in NPC.items() for f in fs}
    if set(out)!=expected:raise ValueError(f'Missing/duplicate full-route section: {expected-set(out)}')
    return out

def metadata(s):return {k:{n:v for n,v in x.items() if n not in ('bytes','pool')} for k,x in s.items()}
