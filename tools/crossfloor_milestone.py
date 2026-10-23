#!/usr/bin/env python3
"""M7 shop rank certificate plus concrete cross-floor whole-movie witness."""
import argparse,hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from game_milestone import audit,stable
from shop_model import FIELDS,COSTS,potential,rank
from shop_probe import make as make_shop
from make_crossfloor_plan import make as make_plan
OUT=Path('generated/M7')

def collect(elapsed=None):
    read=lambda n:json.loads((OUT/n).read_text())
    plan=read('game-plan.json');native=read('native-replay.json');control=read('control-replay.json');schema=read('observer-schema.json');hud=read('hud-comparison.json');shop=read('shop-checks.json');player=read('shop-player-result.json')
    evidence=audit(native,control,read('native-traces.json'),schema,plan,hud)
    if not player['matched'] or player['traceSHA256']!=player['expectedTraceSHA256'] or player['errors'] or player['cases']!=216:raise AssertionError('Shop player checks')
    last=native['checkpoints'][-1]['state'];consumed={k:v for k,v in last.items() if k.startswith('mt_line_')}
    if len(consumed)!=23 or any(v!=0 for v in consumed.values()):raise AssertionError('Consumed tiles restored on revisit')
    if last['Now_line']!=1 or last['Now_hp']!=905 or len(evidence['actualDraws'])!=115:raise AssertionError('Cross-floor result')
    purchase=next(c for c in native['checkpoints'] if c['name']=='M7-shop-purchase')['state']
    if [purchase[k] for k in ['Now_hp','Now_money']]!=[905,9]:raise AssertionError('Whole-game purchase')
    identity=changed=0
    for c in shop['records']:
        if c['before']==c['after']:identity+=1
        else:
            changed+=1
            if c['rankAfter']>=c['rankBefore']:raise AssertionError('Nondecreasing transaction')
    return {'schemaVersion':1,'milestone':'M7','originalSWFSHA256':plan['sourceSWFSHA256'],'environment':{'platform':platform.platform(),'python':platform.python_version()},'shopRules':{'fields':FIELDS,'costTable':{str(k):v for k,v in COSTS.items()},'sections':shop['sections'],'whitelistVMCases':shop['cases'],'vmSteps':shop['vmSteps'],'changedCases':changed,'identityCases':identity,'independentPlayer':player,'boundaryRecords':shop['records']},'shopFiniteness':{'domain':'Nonnegative exact integer currencies/keys/experience; numeric operations remain in the exact integer range. No edited/infinite resources.','potential':'P = money + 10*yellow + 50*blue + 100*red + experience','rank':'R = P*(P+1)/2 + money','argument':'Buying keys preserves P and lowers money; selling keys lowers P by 3/15/30. Gold and experience upgrades lower P. Since 0<=money<=P, each smaller P block has rank strictly below the current block. Every resource-changing shop transaction strictly decreases the nonnegative integer R. Identity failure/exit/navigation steps are collapsed. Thus shop-only resource-changing cycles and infinite sequences are impossible for a finite initial budget.','coarseSuccessfulTransactionBound':'R(initial), when there is no external reward input. A whole-game bound additionally requires finite, once-only external rewards; not established here.','wholeGameFiniteStateModelProven':False,'routineLevel199UpgradeOutputs':[200,202],'routineLevelCap200Enforced':False},'nativeReplay':native,'observerFreeControl':control,'observer':schema,'hudComparison':hud,'replayAudit':evidence,'consumedTilesStillZeroAfterRevisits':consumed,'witnessPlanActions':plan['extension']['actions'],'scope':{'result':{'floor':1,'hp':905,'atk':23,'def':10,'keys':[0,1,0],'money':9,'experience':31},'floorTransitionsAfterM6':7,'nativeInputs':len(native['inputs']),'battleCount':len(evidence['battleDraws']),'randomDraws':len(evidence['actualDraws']),'globalOrThreeFloorOptimalityProven':False,'searchClaim':'This is a concrete route witness and resource theorem, not an exhaustive multi-floor optimization. Walking uses BFS only.','clock':'Date frozen at1600000000000 ms; Ruffle0.7.1 seed128188416, fresh browser contexts. Real clock and save/load policies remain unmodelled.','comparisonToM6':'905 on return to MT1 after visiting MT3 is a different endpoint/action set from M6 first-ascent 860 or conditional upper965; these values must not be compared as the same optimization problem.'},'metrics':{'elapsedSeconds':elapsed,'nativeInputSpan':{'elapsedSeconds':sum(c['delaySincePreviousInputMs'] for c in native['inputs'])/1000,'definition':'First menu click to final input; excludes initial menu wait and final settle'},'processPeakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),'rssDefinition':'Python process lifetime peak; excludes browser and other child processes'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--check');p.add_argument('--reuse-local',action='store_true');a=p.parse_args();start=time.perf_counter()
    if not a.reuse_local:
        make_plan(a.swf);make_shop(a.swf)
        env=os.environ|{'MOTA_REPLAY_DIR':'generated/M7','MOTA_FLASH_SWF':str(Path(a.swf).resolve())}
        for command in [['node','tools/player_probe.mjs','shop'],['node','tools/game_replay.mjs'],['node','tools/game_replay.mjs','--control'],['node','tools/compare_game_hud.mjs']]:subprocess.run(command,check=True,env=env)
    result=collect(None if a.reuse_local else time.perf_counter()-start)
    (OUT/'crossfloor-M7.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    if a.check and stable(result)!=stable(json.loads(Path(a.check).read_text())):raise SystemExit('M7 stable baseline differs')
    print(json.dumps({'milestone':'M7','shopCases':216,'nativeInputs':result['scope']['nativeInputs'],'draws':115,'finalHP':905,'allHUDMatch':True}))
if __name__=='__main__':main()
