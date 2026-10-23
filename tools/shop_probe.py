"""Differential original shop checks and independent-player fixture generation."""
import copy,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from avm1 import Machine,Obj
from shop_model import FIELDS,COSTS,transact,rank
from shop_sections import sections,metadata
from flash_sections import SWF_SHA
from swf_fixture import push,swf,setvar,getvar,trace_string
from make_player_probe import CLOCK_MS

def cases():
    for shop in range(1,7):
        for choice in range(1,5):
            for level in [1,198,199]:
                for offset in [-1,0,1]:
                    s=dict(zip(FIELDS,[1000,10,10,level,2,2,2,500,500]));threshold=COSTS[shop][min(choice,3)-1]
                    if shop<=3:source='Now_money'
                    elif shop==4:source=['Now_yellow','Now_blue','Now_red'][min(choice,3)-1]
                    else:source='Now_mp'
                    s[source]=threshold+offset
                    yield shop,choice,s

def make(filename):
    s=sections(filename);out=Path('generated/M7');out.mkdir(parents=True,exist_ok=True)
    # Sound adapter belongs to the lab, never changes numeric state.
    header=b'PlaySound\0'+struct.pack('<HH',0,1);code=b'\x9b'+struct.pack('<H',len(header))+header+b'\0'
    traces=[];checks=[];steps=0
    for i,(shop,choice,state) in enumerate(cases()):
        r=Obj({**state,'mt_Mylife':Obj(),'mt_Mykey':Obj()});actor=Obj({'this':None,'now_case_id':choice});actor['this']=actor
        vm=Machine(r,actor,pool=s[shop]['pool']);vm.run(s[shop]['bytes']);steps+=vm.steps
        expected=transact(state,shop,choice);actual={k:int(r[k]) for k in FIELDS}
        if actual!=expected:raise AssertionError(f'Shop mismatch {shop}/{choice}/{state}')
        # Unmodified frame defines its original routine and pool. Valid choices
        # are then invoked as a function, preserving Return/control semantics.
        raw=s[shop]['frameBytes'];assert raw[-1:]==b'\0';code+=raw[:-1]
        code+=push('mt_Mylife',0)+b'\x43\x1d'+push('mt_Mykey',0)+b'\x43\x1d'
        for k,v in {**state,'now_case_id':choice}.items():code+=setvar(k,v)
        code+=push(0,s[shop]['functionName'])+b'\x3d\x17'
        prefix=f'SHOP|{i}|';code+=push(prefix)
        for j,k in enumerate(FIELDS):
            if j:code+=push(',')+b'\x21'
            code+=getvar(k)+b'\x21'
        code+=b'\x26';traces.append(prefix+','.join(str(expected[k]) for k in FIELDS))
        checks.append({'shop':shop,'choice':choice,'before':state,'after':expected,'rankBefore':rank(state),'rankAfter':rank(expected)})
    data=swf(code+trace_string('DONE'));(out/'shop-probe.swf').write_bytes(data)
    expected={'clockMilliseconds':CLOCK_MS,'seedUint32':CLOCK_MS*1000%(1<<32),'sourceSWFSHA256':SWF_SHA,'swfSHA256':hashlib.sha256(data).hexdigest(),'cases':len(traces),'traceLines':traces}
    (out/'shop-probe-expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    result={'sourceSWFSHA256':SWF_SHA,'sections':metadata(s),'cases':len(traces),'vmSteps':steps,'records':checks}
    (out/'shop-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'cases':len(traces),'vmSteps':steps}))
if __name__=='__main__':make(sys.argv[1])
