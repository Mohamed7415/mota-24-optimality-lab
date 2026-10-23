#!/usr/bin/env python3
"""M6 full original-movie DOM replay and natural-start finite-model evidence."""
import argparse,hashlib,json,platform,resource,subprocess,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tests')]
from flash_sections import sections,SWF_SHA
from flash_replay import prepare
from flash_search import solve as support
from ruffle_bound import solve as bound
from seed_grid import oracle as seed_oracle
from streak_grid import oracle as streak_oracle
from original_grid import oracle as support_oracle
from seed_search import solve as seed_solve
from make_game_plan import make
from game_observer import make as make_observer

OUT=Path('generated/M6')

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def stable(v):
    omit={'elapsedSeconds','peakRSSBytes','processPeakRSSBytes','browser','platform','python','traceRecords','delaySincePreviousInputMs','nativeSHA256','controlSHA256','firstUpperStairFlag','menuWaitMilliseconds','initialMenuWaitMilliseconds'}
    if isinstance(v,dict):return {k:stable(x) for k,x in v.items() if k not in omit}
    if isinstance(v,list):return [stable(x) for x in v]
    return v

def rows(traces,fields):
    def val(s):
        if s=='undefined':return None
        if s in ['true','false']:return s=='true'
        if ',' in s:return [int(v) for v in s.split(',')]
        return int(s)
    return [dict(zip(fields,[val(v) for v in line.split('|')[1:]])) for line in traces]

def audit(native,control,traces,schema,plan,hud):
    if native['errors'] or control['errors']:raise AssertionError('Player errors')
    if any(not c['state']['rootIsSelf'] for c in native['checkpoints']):raise AssertionError('Child _root changed')
    if control['observerLoaded'] or control['gameVariableReads'] or control['gameVariableWrites']:raise AssertionError('Control must load original directly')
    sequence=[{k:c[k] for k in ['type','key','x','y'] if k in c} for c in native['inputs']]
    # Match the exact JS command order hash, then archive a canonical hash below.
    if control['inputCount']!=len(sequence):raise AssertionError('Control input count')
    ordered_hash=hashlib.sha256(json.dumps(sequence,separators=(',',':')).encode()).hexdigest()
    if ordered_hash!=control['inputSequenceSHA256']:raise AssertionError('Control input order')
    timeline=rows(traces,schema['fields']);draws=[];battles=[];active=False;seen=set()
    for s in timeline:
        now=s['Display_kill']==1
        if now and not active:battles.append({'enemyIndex':s['Now_boss_id'],'draws':[]});seen=set()
        n=s['mt_kills.kill_number']
        if now and n is not None and n%2==1 and n not in seen:
            seen.add(n);r=s['mt_kills.kill_max'];draws.append(r);battles[-1]['draws'].append(r)
        active=now
    expected_actions=plan['seedSearch']['route']+plan.get('extension',{}).get('actions',[])
    expected=[r for a in expected_actions for r in a.get('randomDraws',[])]
    if draws!=expected:raise AssertionError('Observed RNG differs from exact seed route')
    if len(battles)!=sum(bool(a.get('randomDraws')) for a in expected_actions):raise AssertionError('Battle lifecycle count')
    first_exit=next(s for s in timeline if s['Now_line']==2)
    if first_exit['Now_hp']!=plan['seedSearch']['bestExitHP']:raise AssertionError('First stair trigger HP differs')
    if not all(c['equal'] and c['differentChannels']==0 for c in hud):raise AssertionError('Observer-free HUD differs')
    return {'actualDraws':draws,'battleDraws':battles,'drawSequenceMatchesSeedModel':True,'firstUpperStairHP':first_exit['Now_hp'],'firstUpperStairFlag':first_exit['Display_lines'],'inputOrderSHA256':digest(sequence),'observerFreeHUDAllEqual':True,'normalizedCheckpointsSHA256':digest(native['checkpoints'])}

def benchmark(swf):
    start=time.perf_counter();make_observer();plan=make(swf)
    for args in [['node','tools/game_replay.mjs'],['node','tools/game_replay.mjs','--control'],['node','tools/compare_game_hud.mjs']]:subprocess.run(args,check=True)
    read=lambda name:json.loads((OUT/name).read_text())
    native=read('native-replay.json');control=read('control-replay.json');schema=read('observer-schema.json');hud=read('hud-comparison.json')
    evidence=audit(native,control,read('native-traces.json'),schema,plan,hud)
    world,_=prepare(sections(swf));world['Now_yellow']=0
    seeded=plan['seedSearch'];independent_seed=seed_oracle(world)
    upper=bound(world);independent_upper=streak_oracle(world)
    supports=[]
    for mode in ['bestSupported','adversarialSupported']:
        r=support(world,mode);o=support_oracle(world,mode=='bestSupported')
        if r['bestExitHP']!=o['bestExitHP']:raise AssertionError('Support oracle mismatch')
        supports.append({'mode':mode,'bestExitHP':r['bestExitHP'],'complete':r['complete'],'metrics':r['metrics'],'independentGrid':o})
    if seeded['bestExitHP']!=860 or independent_seed['bestExitHP']!=860 or upper['bestExitHP']!=965 or independent_upper['bestExitHP']!=965:raise AssertionError('Natural-start bounds')
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    return {'schemaVersion':1,'milestone':'M6','originalSWFSHA256':SWF_SHA,'rngCertificateSHA256':hashlib.sha256(Path('experiments/ruffle-M5.json').read_bytes()).hexdigest(),'observer':schema,'environment':{'platform':platform.platform(),'python':platform.python_version()},'naturalOpening':{'openingGiftKeys':[1,1,1],'MT0YellowDoorSpent':1,'naturalMT1Keys':[0,1,1],'legacyM4M5FixedKeys':[1,1,1],'legacyResultsRemainConditional':True},'nativeReplay':native,'observerFreeControl':control,'hudComparison':hud,'replayAudit':evidence,'fixedSeedSearch':seeded,'independentSeedGrid':independent_seed,'naturalRunBound':upper,'independentRunGrid':independent_upper,'naturalSupportModels':supports,'scope':{'fixedSeedLocalOptimum':860,'allSeedsLocalInterval':[860,965],'is965ActualSeedReachabilityProven':False,'is24FloorGlobalOptimumProven':False,'clock':'Date frozen at 1600000000000 ms in fresh browser contexts. Natural wall-clock timing is deliberately not validated.','objective':'Max HP on first touch of MT1 upper stair, natural MT1 resources, level1, no other-floor detours/shops/save-load/restart/RNG-skipping strategies.','seedAssumption':'One shared Ruffle RNG, seed128188416, no draws outside hero attacks. Concrete replay draw sequence agrees; no claim for every full-game path.','observerBoundary':'Byte-identical whole original loaded as _lockroot child; parent traces reads only. Direct no-observer original run uses the same input order with longer settle delays; resource HUD regions match within each environment. This verifies the concrete path, not every possible state or Adobe Flash Player.'},'metrics':{'elapsedSeconds':time.perf_counter()-start,'processPeakRSSBytes':rss}}

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--check');a=p.parse_args();r=benchmark(a.swf)
    (OUT/'whole-game-M6.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    if a.check and stable(r)!=stable(json.loads(Path(a.check).read_text())):raise SystemExit('M6 stable baseline differs')
    print(json.dumps({'milestone':'M6','fixedSeedLocalOptimum':r['fixedSeedSearch']['bestExitHP'],'allSeedsConditionalInterval':[860,965],'nativeInputCount':len(r['nativeReplay']['inputs']),'actualDraws':len(r['replayAudit']['actualDraws']),'observerFreeHUDMatch':True}))
if __name__=='__main__':main()
