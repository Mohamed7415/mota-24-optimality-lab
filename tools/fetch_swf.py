#!/usr/bin/env python3
"""Download pinned public research candidates locally, verify bytes, never execute."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
CANDIDATES={
 'archive':('https://swf.flash.homes/2f1681af86d28042009c7c1a43cfd9da8df20abcc598501db67175f31d87c646.swf','2f1681af86d28042009c7c1a43cfd9da8df20abcc598501db67175f31d87c646'),
 'mhhf':('https://www.mhhf.com/files/game/5478/mota24.swf','04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9')}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('candidate',choices=CANDIDATES);ap.add_argument('--directory',default='generated/private');a=ap.parse_args();url,expected=CANDIDATES[a.candidate];req=urllib.request.Request(url,headers={'User-Agent':'Mota24-Optimality-Lab/0.3 research'})
 with urllib.request.urlopen(req,timeout=45) as response:body=response.read(20_000_001)
 if len(body)>20_000_000:raise ValueError('Unexpected download size')
 actual=hashlib.sha256(body).hexdigest()
 if actual!=expected:raise ValueError(f'Candidate changed: expected {expected}; got {actual}. Do not silently relabel a version.')
 target=Path(a.directory)/f'{a.candidate}.swf';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);print(json.dumps({'path':str(target),'url':url,'sha256':actual,'bytes':len(body)},indent=2))
