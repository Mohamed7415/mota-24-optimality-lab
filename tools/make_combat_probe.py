"""Wrap unmodified original numeric action bodies in a LOCAL test movie.
Not a whole-game input replay. No fixture SWF or original bytecode is published.
"""
import hashlib,json,sys,struct
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from flash_sections import sections,SWF_SHA
from flash_experiment import initial_world
from ruffle_rng import RuffleRng
from swf_fixture import push,swf,trace_string,setvar,getvar
from make_player_probe import CLOCK_MS

def make(filename):
    s=sections(filename);world,_=initial_world(s);rng=RuffleRng(CLOCK_MS*1000)
    # Explicit no-op audio adapter, independent real AVM1 numeric execution.
    body=b'PlaySound\0'+struct.pack('<HH',0,1)+b'\0'
    code=b'\x9b'+struct.pack('<H',len(body)-1)+body
    expected=[];cases=0;draws=0
    fields=['left_hp','right_hp','kill_number','kill_left','kill_right','kill_max','Now_hp','Display_kill']
    def emit(frame,state):
        nonlocal code
        raw=s['combat'+str(frame)]['bytes'];assert raw[-1:]==b'\0'
        code+=raw[:-1]
        prefix=f'COMBAT|{cases}|{frame}|'
        code+=push(prefix)
        for j,k in enumerate(fields):
            if j:code+=push(',')+b'\x21'
            code+=getvar(k)+b'\x21'
        code+=b'\x26'
        expected.append(prefix+','.join(str(int(state.get(k,0))) for k in fields))
    for enemy in world['boss_man']:
        if not isinstance(enemy,list):continue
        for regime in range(3):
            cases+=1;delta=[max(1,enemy[0]//5),enemy[0],max(1,enemy[0]//3)][regime]
            atk=enemy[2]+delta;defense=[max(0,enemy[1]-10),enemy[1],enemy[1]+1][regime]
            level=[1,198,199][regime]
            state=dict(left_hp=enemy[0],left_gong=enemy[1],left_fang=enemy[2],right_hp=1000000,right_gong=atk,right_fang=defense,Now_life=level,kill_max=0,Now_hp=0,Display_kill=0)
            for k,v in state.items():code+=setvar(k,v)
            state.update(kill_number=0,kill_left=max(0,enemy[1]-defense),kill_right=delta)
            emit(1,state)
            for _ in range(20000):
                if state['kill_number']%2==0:
                    r=rng.draw();draws+=1;state['kill_max']=r
                    state['left_hp']=max(0,state['left_hp']-delta*(2 if r<=level else 1))
                else:state['right_hp']-=state['kill_left']
                state['kill_number']+=1;emit(24,state);emit(34,state)
                if state['left_hp']<=0:break
            else:raise ValueError('Limit')
            emit(35,state);state.update(Now_hp=state['right_hp'],Display_kill=2);emit(54,state)
    data=swf(code+trace_string('DONE'));out=Path('generated/M5');out.mkdir(parents=True,exist_ok=True)
    (out/'combat-probe.swf').write_bytes(data)
    result={'clockMilliseconds':CLOCK_MS,'seedUint32':CLOCK_MS*1000%(1<<32),'sourceSWFSHA256':SWF_SHA,'swfSHA256':hashlib.sha256(data).hexdigest(),'cases':cases,'randomDraws':draws,'traceLines':expected}
    (out/'combat-probe-expected.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='traceLines'}))
if __name__=='__main__':make(sys.argv[1])
