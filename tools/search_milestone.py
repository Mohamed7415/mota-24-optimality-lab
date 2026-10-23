"""M8 bounded real-map optimization with independent grid and native witnesses."""
import argparse,json,os,platform,subprocess,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from search_crossfloor import make
from crossfloor_route_oracle import verify
from flash_sections import sections
from flash_replay import prepare
from game_milestone import audit,stable
OUT=Path('generated/M8')

def collect(swf,elapsed=None):
    read=lambda n:json.loads((OUT/n).read_text())
    search=read('search-M8.json');plan=read('game-plan.json');native=read('native-replay.json');control=read('control-replay.json');schema=read('observer-schema.json');hud=read('hud-comparison.json')
    world,_=prepare(sections(swf));oracle=verify(plan,world['boss_man'])
    evidence=audit(native,control,read('native-traces.json'),schema,plan,hud)
    last=native['checkpoints'][-1]['state'];r=search['finalResources']
    assert last['Now_line']==1
    assert [last[k] for k in ['Now_hp','Now_gong','Now_fang','Now_money','Now_mp','Now_yellow','Now_blue','Now_red']]==[r['hp'],r['atk'],r['def'],r['money'],r['experience'],*r['keys']]
    cells={k:v for k,v in last.items() if k.startswith('mt_line_')};expected_count=oracle['consumedEvents']+len(plan['seedSearch']['route'])
    assert len(cells)==expected_count and all(v==0 for v in cells.values())
    return {'schemaVersion':1,'milestone':'M8','sourceSWFSHA256':plan['sourceSWFSHA256'],'environment':{'platform':platform.platform(),'python':platform.python_version()},'search':search,'independentGridRouteOracle':oracle,'nativeReplay':native,'observerFreeControl':control,'observer':schema,'hudComparison':hud,'replayAudit':evidence,'consumedCellsStillZero':cells,'boundInterval':{'lowerHP':search['bestReturnHP'],'upperHP':search['admissibleInitialUpperHP'],'meaning':'Restricted fixed-prefix, fixed-seed continuation only. Lower bound now witnessed by original whole-movie replay; upper bound is a resource relaxation. No completeness or global optimality claim.'},'metrics':{'elapsedSeconds':elapsed,'nativeInputs':len(native['inputs']),'nativeBattles':len(evidence['battleDraws']),'nativeDraws':len(evidence['actualDraws'])}}

def main():
    p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--check');p.add_argument('--reuse-local',action='store_true');a=p.parse_args();start=time.perf_counter()
    if not a.reuse_local:
        make(a.swf)
        world,_=prepare(sections(a.swf));verify(json.loads((OUT/'game-plan.json').read_text()),world['boss_man'])
        env=os.environ|{'MOTA_REPLAY_DIR':str(OUT),'MOTA_FLASH_SWF':str(Path(a.swf).resolve())}
        for command in [['node','tools/game_replay.mjs'],['node','tools/game_replay.mjs','--control'],['node','tools/compare_game_hud.mjs']]:subprocess.run(command,check=True,env=env)
    result=collect(a.swf,None if a.reuse_local else time.perf_counter()-start)
    (OUT/'optimization-M8.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    if a.check and stable(result)!=stable(json.loads(Path(a.check).read_text())):raise SystemExit('M8 stable baseline differs')
    print(json.dumps({'milestone':'M8','bounds':result['boundInterval'],'metrics':result['metrics']}))
if __name__=='__main__':main()
