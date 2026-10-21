#!/usr/bin/env python3
"""Read SWF containers/fonts/static text; never execute ActionScript. Offsets use decompressed file."""
import argparse, collections, hashlib, json, math, re, struct, zlib
from pathlib import Path
class Bits:
 def __init__(self,b,p=0): self.b=b;self.p=p*8
 def u(self,n):
  if self.p+n>len(self.b)*8: raise ValueError('Truncated bit field')
  v=0
  for _ in range(n): v=(v<<1)|((self.b[self.p//8]>>(7-self.p%8))&1);self.p+=1
  return v
 def align(self):self.p=(self.p+7)//8*8
 @property
 def pos(self):return (self.p+7)//8
 def rect(self):n=self.u(5);v=[self.u(n) for _ in range(4)];self.align();return v
 def matrix(self):
  if self.u(1): n=self.u(5);self.u(n);self.u(n)
  if self.u(1): n=self.u(5);self.u(n);self.u(n)
  n=self.u(5);self.u(n);self.u(n);self.align()
def u16(b,p):return struct.unpack_from('<H',b,p)[0]
def tags(b,start,end,parent='root'):
 p=start
 while p+2<=end:
  off=p;h=u16(b,p);p+=2;code=h>>6;n=h&63
  if n==63:
   if p+4>end:raise ValueError('Truncated long tag header')
   n=struct.unpack_from('<I',b,p)[0];p+=4
  if p+n>end:raise ValueError(f'Truncated tag {code} at {off}')
  yield code,p,n,off,parent
  if code==39:yield from tags(b,p+4,p+n,f'{parent}/sprite:{u16(b,p)}')
  p+=n
  if code==0:break

def inspect(filename,url=None):
 original=Path(filename).read_bytes();sig=original[:3]
 if sig not in [b'FWS',b'CWS']:raise ValueError('Only FWS/CWS supported')
 b=original[:8]+(zlib.decompress(original[8:]) if sig==b'CWS' else original[8:]);declared=struct.unpack_from('<I',b,4)[0]
 if declared!=len(b):raise ValueError('Declared size mismatch')
 bits=Bits(b,8);bits.rect();p=bits.pos;framerate=u16(b,p)/256;frames=u16(b,p+2)
 ts=list(tags(b,p+4,len(b)));fonts={};errors=[]
 for code,p,n,off,parent in ts:
  if code in [48,75]:
   fid=u16(b,p);flags=b[p+2];ln=b[p+4];q=p+5+ln;name=b[p+5:q].decode('utf8','replace');count=u16(b,q);q+=2;base=q;wide=bool(flags&8);size=4 if wide else 2;cp=base+count*size
   tableOffset=int.from_bytes(b[cp:cp+size],'little');cp=base+tableOffset;wcode=bool(flags&4);width=2 if wcode else 1
   chars=[int.from_bytes(b[cp+i*width:cp+(i+1)*width],'little') for i in range(count)]
   fonts[fid]={'name':name,'codes':chars,'flags':flags}
  elif code==13: # DefineFontInfo supplies glyph -> code for DefineFont
   fid=u16(b,p);ln=b[p+2];flags=b[p+3+ln];q=p+4+ln;width=2 if flags&1 else 1;chars=[int.from_bytes(b[i:i+width],'little') for i in range(q,p+n,width)]
   fonts[fid]={'name':b[p+3:p+3+ln].decode('utf8','replace'),'codes':chars,'flags':flags}
 texts=[]
 for code,p,n,off,parent in ts:
  if code not in [11,33]:continue
  try:
   tid=u16(b,p);r=Bits(b,p+2);r.rect();r.matrix();q=r.pos;gb=b[q];ab=b[q+1];q+=2;fid=None;chunks=[]
   while q<p+n:
    f=b[q];q+=1
    if f==0:break
    if not f&128:raise ValueError('Invalid text record')
    if f&8:fid=u16(b,q);q+=2
    if f&4:q+=4 if code==33 else 3
    if f&1:q+=2
    if f&2:q+=2
    if f&8:q+=2
    count=b[q];q+=1;rr=Bits(b,q);glyphs=[]
    for _ in range(count):glyphs.append(rr.u(gb));rr.u(ab)
    q=rr.pos;ft=fonts.get(fid);chars=[]
    for g in glyphs:
     if not ft or g>=len(ft['codes']):chars.append('�')
     else:
      c=ft['codes'][g]
      if ft['flags']&64: # ShiftJIS font
       chars.append(c.to_bytes(2 if c>255 else 1,'big').decode('shift_jis','replace'))
      else:chars.append(chr(c))
    chunks.append(''.join(chars))
   text=''.join(chunks)
   if text.strip():texts.append({'characterId':tid,'tagOffset':off,'parent':parent,'text':text})
  except (ValueError,IndexError,struct.error) as e:errors.append({'tagOffset':off,'error':str(e)})
 hits=[t for t in texts if re.search(r'1[.．]\s*1\s*2|版本|胖|[Vv][Ee][Rr]|魔塔',t['text'])]
 ascii_hits=[]
 for m in re.finditer(rb'[ -~]{4,}',b):
  s=m.group().decode('ascii')
  if re.search(r'1\.12|1\.1\.2|version',s,re.I):ascii_hits.append({'offset':m.start(),'text':s[:200]})
 return {'schemaVersion':1,'url':url,'sha256':hashlib.sha256(original).hexdigest(),'fileBytes':len(original),'signature':sig.decode(),'swfFormatVersion':original[3],'declaredUncompressedBytes':declared,'frameRate':framerate,'rootFrames':frames,'tagCounts':dict(sorted(collections.Counter(t[0] for t in ts).items())),'fonts':len(fonts),'staticTextRecords':len(texts),'versionEvidence':hits,'asciiVersionCandidates':ascii_hits,'textDecodeErrors':errors,'allStaticText':texts,'internalVersionConclusion':'unverified; inspect versionEvidence, glyph mapping and placement before identification','limitations':['Shape-only text and nested display order not reconstructed.','No ActionScript executed; text evidence alone does not establish original author release lineage.']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('file');ap.add_argument('--url');ap.add_argument('--out',required=True);a=ap.parse_args();o=inspect(a.file,a.url);Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ['allStaticText','tagCounts']},ensure_ascii=False,indent=2))
