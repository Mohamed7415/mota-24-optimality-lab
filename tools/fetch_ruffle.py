#!/usr/bin/env python3
"""Fetch the pinned official MIT/Apache Ruffle web release, hash before extract."""
import hashlib,io,json,urllib.request,zipfile
from pathlib import Path
VERSION='0.7.1'
URL=f'https://github.com/ruffle-rs/ruffle/releases/download/v{VERSION}/ruffle-{VERSION}-web-selfhosted.zip'
SHA='ef12edbee135d581a9cd523837d746da30a07a64dbf1cf472d2e472c656f4b5e'
DEST=Path('generated/private/ruffle-web')

def main():
    archive=DEST.parent/'ruffle-web.zip'
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA:
        req=urllib.request.Request(URL,headers={'User-Agent':'Mota24OptimalityLab/0.5'})
        with urllib.request.urlopen(req,timeout=180) as r:data=r.read()
        if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Ruffle archive SHA mismatch')
        archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(data)
    data=archive.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Unpinned Ruffle')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            p=Path(name)
            if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe ZIP member')
        z.extractall(DEST)
    print(json.dumps({'version':VERSION,'url':URL,'sha256':SHA,'bytes':len(data),'destination':str(DEST)}))
if __name__=='__main__':main()
