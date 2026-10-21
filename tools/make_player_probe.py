import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ruffle_rng import RuffleRng
from swf_fixture import push,swf,trace_string
CLOCK_MS=1600000000000
if __name__=='__main__':
    out=Path('generated/M5');out.mkdir(parents=True,exist_ok=True)
    code=b'';rng=RuffleRng(CLOCK_MS*1000);expected=[]
    for i in range(1000):
        code+=push(f'RNG|{i}|')+push(200)+b'\x30\x21\x26';expected.append(rng.draw())
    data=swf(code+trace_string('DONE'))
    (out/'rng-probe.swf').write_bytes(data)
    (out/'rng-probe-expected.json').write_text(json.dumps({'clockMilliseconds':CLOCK_MS,'seedUint32':CLOCK_MS*1000%(1<<32),'draws':expected,'swfSHA256':hashlib.sha256(data).hexdigest()},indent=2)+'\n')
