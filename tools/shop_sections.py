"""Static shop body extraction with exact SWF offsets and hashes."""
import collections,hashlib,struct,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from avm1 import actions,constant_pool
from inspect_swf import Bits,tags
from flash_sections import SWF_SHA

def sections(filename):
    raw=Path(filename).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SWF_SHA:raise ValueError('Unpinned original')
    b=raw[:8]+zlib.decompress(raw[8:]);r=Bits(b,8);r.rect();frame=collections.defaultdict(lambda:1);out={}
    for code,p,n,off,parent in tags(b,r.pos+4,len(b)):
        if code==12 and parent=='root/sprite:671':
            pool=[]
            for a in actions(b[p:p+n]):
                if a.opcode==0x88:pool=constant_pool(a.data)
                if a.name.startswith('Case_buy_'):
                    shop=int(a.name[-2:]);out[shop]={'frame':frame[parent],'parent':parent,'tagOffset':off,'bodyOffset':p+a.end-len(a.body),'sha256':hashlib.sha256(a.body).hexdigest(),'bodyBytes':len(a.body),'bytes':a.body,'pool':pool.copy(),'frameBytes':b[p:p+n],'functionName':a.name}
        if code==1:frame[parent]+=1
    if set(out)!=set(range(1,7)):raise ValueError('Missing shops')
    return out

def metadata(s):return {str(k):{x:v for x,v in b.items() if x not in ['bytes','pool','frameBytes']} for k,b in s.items()}
