"""Import inert JSON assignments from an actual H5Mota24 project snapshot.

No eval/exec, plugin execution or invented event effects. Function strings and
effect expressions remain opaque data. The structured project stays in generated;
summary.json contains only provenance and counts and can be published separately.
"""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def parse_assignment(raw):
    text = raw.decode('utf-8')
    prefix = re.match(r'\s*(?:var\s+)?(?:[A-Za-z_][A-Za-z_0-9]*|main\.floors\.[A-Za-z_0-9]+)\s*=\s*', text)
    if not prefix:
        raise ValueError('Not a supported plain JSON assignment')
    def reject_constant(value):
        raise ValueError('Non-JSON numeric constant: '+value)
    decoder = json.JSONDecoder(object_pairs_hook=strict_object, parse_constant=reject_constant)
    data,end = decoder.raw_decode(text, prefix.end())
    if text[end:].strip() not in ('',';'):
        raise ValueError('Code after the JSON assignment is unsupported')
    if not isinstance(data,dict):
        raise ValueError('Expected object assignment')
    return data


def pointer_key(key):
    return str(key).replace('~','~0').replace('/','~1')


def run(source, out):
    manifest = json.loads((source/'provenance.json').read_text())
    verified = {}
    for row in manifest:
        if 'error' in row:
            raise ValueError('Source manifest has a failed fetch')
        filename = row['file']
        if Path(filename).is_absolute() or '..' in Path(filename).parts:
            raise ValueError('Unsafe relative source path')
        raw = (source/filename).read_bytes()
        if digest(raw) != row['sha256'] or len(raw) != row['bytes']:
            raise ValueError('Snapshot file does not match recorded HTTPS fetch: '+filename)
        verified[filename] = row
    def read(filename):
        if filename not in verified:
            raise ValueError('Unprovenanced project source: '+filename)
        return parse_assignment((source/filename).read_bytes())
    inputs = {name:read('project/'+name+'.js') for name in ('data','enemys','items','events','maps','icons')}
    if inputs['data']['firstData']['name'] != '24':
        raise ValueError('Snapshot is not the requested H5Mota24 project')
    floor_ids = inputs['data']['main']['floorIds']
    if len(floor_ids) != 27 or len(set(floor_ids)) != 27:
        raise ValueError('Expected27 distinct floors in this specific project')
    floors = {}
    opaque = []
    event_types = collections.Counter()
    def walk(value, filename, pointer=''):
        if isinstance(value,dict):
            if isinstance(value.get('type'),str):
                event_types[value['type']] += 1
            for key,item in value.items():
                child = pointer+'/'+pointer_key(key)
                if isinstance(item,str) and key in ('function','itemEffect','useItemEffect','canUseItemEffect','equipCondition'):
                    opaque.append(dict(file=filename,pointer=child,sha256=digest(item.encode()),
                                       disposition='Opaque code string; retained as data, not executed or assigned invented effects.'))
                walk(item, filename, child)
        elif isinstance(value,list):
            for index,item in enumerate(value):
                walk(item,filename,pointer+'/'+str(index))
    for name,value in inputs.items():
        walk(value,'project/'+name+'.js')
    cells = collections.Counter()
    for floor_id in floor_ids:
        if not re.fullmatch(r'MT(?:\d+[wes]?|_\d+)',floor_id):
            raise ValueError('Unexpected floor identifier')
        filename = 'project/floors/'+floor_id+'.js'
        floor = read(filename)
        if floor['floorId'] != floor_id:
            raise ValueError('Floor identity mismatch')
        width,height = floor['width'],floor['height']
        if len(floor['map']) != height or any(len(row) != width for row in floor['map']):
            raise ValueError('Floor map dimensions do not match actual rows')
        for row in floor['map']:
            for tile in row:
                if type(tile) is not int or tile < 0:
                    raise ValueError('Non-integer map tile')
                cells[tile] += 1
        walk(floor, filename)
        floors[floor_id] = dict(data=floor,provenance=dict(file=filename,sha256=verified[filename]['sha256'],
                                                        mapPointer='/map',coordinateSystem='Zero-based x/y in the source13x13 grid; never silently treated as original Flash coordinates.'))
    unresolved = {str(tile):count for tile,count in cells.items() if tile and str(tile) not in inputs['maps']}
    source_set = sorted((name,row['sha256']) for name,row in verified.items())
    set_hash = digest(json.dumps(source_set,separators=(',',':')).encode())
    out.mkdir(parents=True,exist_ok=False)
    structured = dict(schemaVersion=1,scope='Static source data only; not an executable H5 model or whole-game witness.',
                      sourceSetSHA256=set_hash,inputs=inputs,floors=floors,opaqueHooks=opaque)
    (out/'structured-private.json').write_text(json.dumps(structured,ensure_ascii=False,indent=2)+'\n')
    summary = dict(schemaVersion=1,scope='Strict static JSON-assignment import of the fetched H5Mota24 project. No arbitrary JavaScript executed; no native/replay/record proof.',
                   sourceSetSHA256=set_hash,sourceSetHashMeaning='SHA256 of sorted(relative source path, fetched fileSHA256) pairs; excludes un-fetched engine/runtime files and all media.',
                   verifiedSourceFiles=len(verified),parsedJSONAssignments=len(inputs)+len(floors),
                   internalMapCount=len(floors),mapCountMeaning='The24-floor game uses27 engine maps: intro0 and the three separate23F branches have their own files.',
                   floorDimensions={k:[v['data']['width'],v['data']['height']] for k,v in floors.items()},
                   mapCellCount=sum(cells.values()),distinctMapTileCodes=len(cells),unresolvedMapTileCodes=unresolved,
                   blockDefinitions=len(inputs['maps']),enemyDefinitions=len(inputs['enemys']),itemDefinitions=len(inputs['items']),
                   shopDefinitions=len(inputs['data']['firstData']['shops']),opaqueCodeStrings=len(opaque),
                   eventTypeCounts=dict(sorted(event_types.items())),
                   opaqueRuntimeSourceFiles=[name for name in sorted(verified) if name not in {*(f'project/{k}.js' for k in inputs),*(f'project/floors/{k}.js' for k in floors)}],
                   provenance=[dict(file=name,url=row['url'],sha256=row['sha256'],bytes=row['bytes']) for name,row in sorted(verified.items())],
                   projectJavaScriptExecuted=False,unsupportedEffectsInvented=False,completeBuildIdentityEstablished=False,
                   structuredGameSourceRedistributed=False,
                   limitations=['Opaque function/effect strings have not been converted to execution semantics.',
                                'JSON event trees are retained literally, not asserted fully supported by a solver.',
                                'An available block/enemy definition may be unused by the actual maps.',
                                'This source-set hash is not the per-submission game-build identity.'])
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--out',type=Path,default=Path('generated/H5Mota24Imported'))
    args = parser.parse_args()
    result = run(args.source,args.out)
    print(json.dumps({k:result[k] for k in ('verifiedSourceFiles','parsedJSONAssignments','internalMapCount','mapCellCount','enemyDefinitions','itemDefinitions','opaqueCodeStrings','unresolvedMapTileCodes','sourceSetSHA256')}))


if __name__ == '__main__':
    main()
