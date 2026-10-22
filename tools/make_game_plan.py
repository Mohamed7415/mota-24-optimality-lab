"""Generate private real-map input plan from pinned original initialization."""
import argparse,json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from flash_sections import sections,SWF_SHA
from flash_replay import prepare
from seed_search import solve

def make(filename):
    world,_=prepare(sections(filename))
    # Native opening checkpoint and independently inspected MT0 door both show
    # the initial yellow key is spent before reaching MT1.
    world['Now_yellow']=0
    result=solve(world);out=Path('generated/M6');out.mkdir(parents=True,exist_ok=True)
    plan={'sourceSWFSHA256':SWF_SHA,'clockMilliseconds':1600000000000,'seedSearch':result,'grid':world['mt_line_01']}
    (out/'game-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    return plan
if __name__=='__main__':make(sys.argv[1])
