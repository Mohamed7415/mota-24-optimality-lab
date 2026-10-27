"""Partial initial-map classification comparison, not gameplay equivalence.

Compare Flash internal maps1..26 to their H5 counterparts at x+1,y+1. The intro,
special items, arrivals, NPCs and runtime effects remain explicitly excluded.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'src')]
from original_route import OriginalRoute

ALIASES={14:'yellowKnight',15:'redKnight',25:'rock',28:'blueGuard'}
ITEMS={6:'yellowKey',7:'blueKey',8:'redKey',9:'blueGem',10:'redGem',11:'redPotion',12:'bluePotion'}


def compare(structured,swf):
    raw=structured.read_bytes()
    project=json.loads(raw)
    blocks=project['inputs']['maps']
    enemies=project['inputs']['enemys']
    original=OriginalRoute(swf,random_policy='worst-support')
    matches={}
    mapping=[]
    for index in range(33):
        enemy=original.root['boss_man'][index]
        ids=[]
        for name,data in enemies.items():
            fields=tuple(data.get(k) for k in ('hp','atk','def','money','exp'))
            if fields==tuple(enemy[:5]) and (data.get('name')==enemy[5] or ALIASES.get(index)==name):
                ids.append(name)
        matches[index]=ids
        mapping.append(dict(originalEnemyIndex=index,originalName=enemy[5],h5EnemyIds=ids,
                            fiveBaseFieldsMatched=bool(ids),nameAliasUsed=index in ALIASES and ALIASES[index] in ids))
    reverse={}
    for index,names in matches.items():
        for name in names:
            if name in reverse and reverse[name]!=index:
                raise ValueError('Ambiguous enemy classification')
            reverse[name]=index
    def flash(tile):
        if tile==0:return 'empty'
        if tile in (1,15,20):return 'wall'
        if tile in (2,3,4):return 'door:'+str(tile)
        if tile in ITEMS:return 'item:'+ITEMS[tile]
        if tile in (13,14):return 'stair:'+str(tile)
        if 40<=tile<=70:return 'enemy:'+str(tile-40)
        return None
    def h5(tile):
        if tile==0:return 'empty'
        block=blocks.get(str(tile),{})
        name=block.get('id')
        if name in ('yellowWall','whiteWall','blueWall','star'):return 'wall'
        if name in ('yellowDoor','blueDoor','redDoor'):return 'door:'+str({'yellowDoor':2,'blueDoor':3,'redDoor':4}[name])
        if name in ITEMS.values():return 'item:'+name
        if name in ('upFloor','downFloor'):return 'stair:'+str(13 if name=='upFloor' else 14)
        if block.get('cls')=='enemys' and name in reverse:return 'enemy:'+str(reverse[name])
        return None
    counts=collections.Counter()
    excluded=collections.Counter()
    different=[]
    unresolved=[]
    for floor in range(1,27):
        floor_id={23:'MT23w',24:'MT23s',25:'MT23e',26:'MT_1'}.get(floor,'MT'+str(floor))
        grid=project['floors'][floor_id]['data']['map']
        if len(grid)!=13 or any(len(row)!=13 for row in grid):
            raise ValueError('Expected the actual13x13 H5 layout')
        for y,row in enumerate(original.grid(floor)):
            for x,tile in enumerate(row):
                if int(tile)!=tile:
                    raise ValueError('Noninteger original tile')
                tile=int(tile)
                code=grid[y+1][x+1]
                left,right=flash(tile),h5(code)
                counts['totalCells']+=1
                if left is None:
                    counts['excludedOriginalCells']+=1
                    excluded[str(tile)]+=1
                    continue
                cell=dict(originalInternalMap=floor,h5MapId=floor_id,originalX=x,originalY=y,
                          h5X=x+1,h5Y=y+1,originalTile=tile,h5Tile=code)
                if right is None:
                    counts['unclassifiedH5Cells']+=1
                    unresolved.append(cell)
                    continue
                counts['comparableCells']+=1
                if left==right:
                    counts['matchedClassifications']+=1
                else:
                    different.append(dict(**cell,originalClassification=left,h5Classification=right))
    return dict(schemaVersion=1,scope=__doc__,
                originalSWFSHA256=hashlib.sha256(Path(swf).read_bytes()).hexdigest(),
                structuredInputSHA256=hashlib.sha256(raw).hexdigest(),h5SourceSetSHA256=project['sourceSetSHA256'],
                originalVMInitializationOnly=True,h5ProjectJavaScriptExecuted=False,
                coordinateTransform=dict(h5X='originalX+1',h5Y='originalY+1',explicitlyExcludedIntroMap=0),
                counts=dict(counts),classificationMismatches=len(different),mismatches=different,
                unclassifiedH5=unresolved,excludedOriginalTileCounts=dict(excluded),
                baseEnemyStatMatches=mapping,
                matchedBaseEnemyDefinitions=sum(bool(ids) for ids in matches.values()),
                comparedEnemyFields=['hp','attack','defense','money','experience'],
                specialEnemyEffectsCompared=False,itemEffectCodeExecuted=False,
                behavioralEquivalenceProved=False,recordBreakingRoute=False,
                limitations=['Only the declared initial cell classes are compared; excluded cells are not assumed equal.',
                             'Stairs can be created by later events; an initial-cell difference does not prove different final reachability.',
                             'Equal five-field enemy stats do not establish equal special attacks, RNG, gates or mutations.',
                             'TheH5 project contains opaque function/effect strings; this comparison does not implement them.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('structured',type=Path)
    parser.add_argument('--swf',default='generated/private/gdut-v112.swf')
    parser.add_argument('--out',type=Path,default=Path('generated/H5FlashGridComparison'))
    args=parser.parse_args()
    result=compare(args.structured,args.swf)
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(counts=result['counts'],mismatches=result['classificationMismatches'],baseEnemies=result['matchedBaseEnemyDefinitions'])))


if __name__=='__main__':
    main()
