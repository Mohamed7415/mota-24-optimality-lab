#!/usr/bin/env python3
"""Statically extract strictly numeric AS2 arrays from FFDec exports. No eval.
FFDec is an optional external static decompiler; it must not run the game.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def hashed(v):return sha(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())
def extract(root):
 root=Path(root);files={};maps={};enemies={};rules=[]
 for p in sorted(root.rglob('*.as')):
  raw=p.read_bytes();s=raw.decode('utf-8-sig');rel=p.relative_to(root).as_posix();lines=s.splitlines();files[rel]=sha(raw)
  def prov(i):return {'decompiledFile':rel,'sha256':sha(raw),'line':i,'method':'FFDec 26.4.0 static decompilation; no AVM execution'}
  for i,line in enumerate(lines,1):
   m=re.fullmatch(r'mt_line_(\d+)\[(\d+)\] = new Array\(([\d, -]+)\);',line.strip())
   if m:
    f,row=int(m[1]),int(m[2]);vals=[int(x.strip()) for x in m[3].split(',')];entry=maps.setdefault(f,{'rows':{},'rowProvenance':{}})
    if row in entry['rows']:raise ValueError('Duplicate map row')
    entry['rows'][row]=vals;entry['rowProvenance'][row]=prov(i)
   m=re.fullmatch(r'boss_man\[(\d+)\] = new Array\(([\d, -]+),(".*")\);',line.strip())
   if m:
    k=int(m[1]);vals=[int(x.strip()) for x in m[2].split(',')]
    if len(vals)!=5:raise ValueError('Enemy arity')
    enemies[k]={'hp':vals[0],'atk':vals[1],'def':vals[2],'money':vals[3],'experience':vals[4],'name':json.loads(m[3]),'provenance':prov(i)}
   for kind,pattern in [('randomRange',r'kill_max = random\((\d+)\);'),('criticalCondition',r'if\(kill_max <= _root.Now_life\)'),('clockThresholdSeconds',r'if\(_root.NowGameTime >= (\d+)\)'),('levelGating',r'_root.Now_life >= (\d+)')]:
    m=re.search(pattern,line)
    if m:rules.append({'kind':kind,'value':int(m[1]) if m.lastindex else 'kill_max <= Now_life','provenance':prov(i)})
 for f,v in maps.items():
  if sorted(v['rows'])!=list(range(11)) or any(len(row)!=11 for row in v['rows'].values()):raise ValueError('Map dimensions')
  v['map']=[v['rows'][i] for i in range(11)];del v['rows']
 if not maps or not enemies:raise ValueError('No recognized original data')
 return {'maps':maps,'enemies':enemies,'rules':rules,'sourceFiles':files}

def audit(facts,t,inspection):
 rows={str(k):{'mapHash':hashed(v['map']),'rows':11,'columns':11,'provenance':v['rowProvenance']} for k,v in facts['maps'].items()}
 # Exact 5-number matches do not assert mechanic equivalence or resolve all names.
 matches=[];unmatched=[]
 for k,e in facts['enemies'].items():
  candidates=[id for id,v in t['enemies']['data'].items() if all(e[s]==v[s] for s in ['hp','atk','def','money','experience'])]
  entry={'flashEnemyIndex':k,'numericTuple':[e[s] for s in ['hp','atk','def','money','experience']],'remakeCandidates':candidates,'provenance':e['provenance']}
  (matches if candidates else unmatched).append(entry)
 pairs=collections.defaultdict(collections.Counter)
 for y,row in enumerate(facts['maps'][1]['map']):
  for x,v in enumerate(row):pairs[v][str(t['floors']['MT1']['data']['map'][y+1][x+1])]+=1
 # Symbol correspondences are observations from aligned MT1 cells, not guessed labels.
 correspondence=[{'flashTile':k,'remakeTileCounts':dict(v),'oneToOneOnMT1':len(v)==1} for k,v in sorted(pairs.items())]
 return {'schemaVersion':1,'swf':{k:inspection[k] for k in ['url','sha256','fileBytes','signature','swfFormatVersion','declaredUncompressedBytes','frameRate','rootFrames']},'decompiler':{'name':'JPEXS FFDec','version':'26.4.0','execution':'static export script,text; game not executed'},'counts':{'mapArrays':len(rows),'baseEnemyDefinitions':len(facts['enemies']),'fiveNumberTupleMatches':len(matches),'unmatchedEnemyTuples':len(unmatched)},'maps':rows,'enemyTupleMatches':matches,'unmatchedEnemyTuples':unmatched,'rules':facts['rules'],'mt1CoordinateComparison':{'transform':'Flash [row][column] aligns remake [row+1][column+1] (outer wall border removed)','observedTileCorrespondence':correspondence,'limitation':'A co-occurrence table, not a complete semantic equivalence proof. Runtime map/event changes excluded.'},'originalEquivalence':'NOT established; RNG, clock, dynamic enemy changes, events and endings need a faithful model.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('export');ap.add_argument('tower');ap.add_argument('inspection');ap.add_argument('--facts',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();f=extract(a.export);t=json.loads(Path(a.tower).read_text());i=json.loads(Path(a.inspection).read_text());Path(a.facts).write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n');r=audit(f,t,i);Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'counts':r['counts'],'rules':r['rules']},ensure_ascii=False,indent=2))
