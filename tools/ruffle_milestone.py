#!/usr/bin/env python3
"""M5: independent Ruffle execution, exhaustive RNG bound, real-map relaxation."""
import argparse,copy,hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tests')]
from flash_sections import sections,SWF_SHA
from flash_replay import prepare
from ruffle_bound import solve
from ruffle_rng import RuffleRng,output,next_state
from streak_grid import oracle

def run(args):subprocess.run(args,check=True)
def stable(x):
    if isinstance(x,dict):return {k:stable(v) for k,v in x.items() if k not in ['elapsedSeconds','elapsedCPUSeconds','peakRSSBytes','browser','platform','python','compiler']}
    if isinstance(x,list):return [stable(v) for v in x]
    return x

def benchmark(swf):
    out=Path('generated/M5');out.mkdir(parents=True,exist_ok=True)
    exe=out/'rng-scan'
    compiler=os.environ.get('CC','cc')
    run([compiler,'-std=c11','-O3','-Wall','-Wextra','-Werror','src/native/ruffle_rng_scan.c','-o',str(exe)])
    for seed in [0,1,128188416,0x80000000,0xffffffff]:
        got=json.loads(subprocess.check_output([str(exe),'--vectors',str(seed),'1000']))
        rng=RuffleRng(seed)
        if got!=[rng.draw() for _ in range(1000)]:raise AssertionError('C/Python RNG mismatch')
    scan=json.loads(subprocess.check_output([str(exe)]));(out/'rng-exhaustive.json').write_text(json.dumps(scan,indent=2)+'\n')
    if not scan['complete'] or scan['statesChecked']!=2147483647 or scan['maxConsecutiveCritical']!=4 or sum(scan['runLengthHistogram'])!=scan['statesChecked']:raise AssertionError('RNG certificate')
    state=scan['witnessState'];witness=[]
    for _ in range(5):witness.append(output(state));state=next_state(state)
    scan['witnessOutputs']=witness
    run([sys.executable,'tools/make_player_probe.py']);run(['node','tools/player_probe.mjs','rng'])
    run([sys.executable,'tools/make_combat_probe.py',swf]);run(['node','tools/player_probe.mjs','combat'])
    players={name:json.loads((out/f'{name}-player-result.json').read_text()) for name in ['rng','combat']}
    for r in players.values():
        if not r['matched'] or r['traceSHA256']!=r['expectedTraceSHA256'] or r['errors']:raise AssertionError('Independent player mismatch')
    world,_=prepare(sections(swf));bound=solve(world);grid=oracle(world)
    if not bound['complete'] or not grid['complete'] or bound['bestExitHP']!=grid['bestExitHP'] or bound['bestExitHP']>=995:raise AssertionError('Bound/oracle mismatch')
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    return {'schemaVersion':1,'milestone':'M5','originalSWFSHA256':SWF_SHA,'ruffleRelease':json.loads(Path('experiments/ruffle-release.json').read_text()),'environment':{'platform':platform.platform(),'python':platform.python_version(),'compiler':subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]},'rngExhaustion':scan,'nativePortCrossCheck':{'seeds':[0,1,128188416,2147483648,4294967295],'drawsPerSeed':1000,'matched':True},'independentPlayer':players,'localUpperBound':bound,'independentGrid':grid,'processPeakRSSBytes':rss,'conclusion':{'M4IndependentDrawUpper':995,'ruffleLocalUpper':bound['bestExitHP'],'M4Value995ExcludedInThisConditionalModel':True,'is980ReachableByActualSeed':'not established','wholeOriginalGameGlobalOptimum':'not established'},'assumptions':['Pinned candidate SWF and Ruffle 0.7.1 only; no claim about all Adobe players.','M4 local MT1 rules: level 1, HP1000/ATK10/DEF10, one key each, first ascent, no other-floor detours or shops.','Consecutive hero-attack draws share one RNG with no extra random calls inserted; resets, saves, clock and animation not modelled.','The automaton admits every critical/noncritical pattern without five consecutive criticals; many such patterns need not be RNG-realizable.','Player probes wrap exact original numeric combat bodies at the root, replacing audio with a no-op, controlling frame dispatch and recording numeric traces. Not whole-game keyboard replay.'],'trustBoundary':'Official release archive hashes + Chromium/WASM execution + two unsigned-integer ports + complete finite C scan + finite map search. No machine-checked proof or full native movie verification.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--check');a=p.parse_args()
    r=benchmark(a.swf);Path('generated/M5/ruffle-M5.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    if a.check:
        ref=json.loads(Path(a.check).read_text());aa=stable(r);bb=stable(ref)
        aa.pop('processPeakRSSBytes',None);bb.pop('processPeakRSSBytes',None)
        if aa!=bb:raise SystemExit('M5 deterministic baseline differs')
    print(json.dumps({'milestone':'M5','upperBound':r['localUpperBound']['bestExitHP'],'eventLabels':r['localUpperBound']['metrics']['expandedLabels'],'gridStates':r['independentGrid']['expandedFullStates'],'peakRSSBytes':r['processPeakRSSBytes']}))
if __name__=='__main__':main()
