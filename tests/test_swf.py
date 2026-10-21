import json,struct,sys,tempfile,unittest,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from inspect_swf import inspect,tags,Bits
from flash_audit import extract
class SwfTests(unittest.TestCase):
 def test_minimal_compressed_container_and_truncation(self):
  # RECT Nbits=1 with four zeros => 9 bits padded; FPS 25, one frame, End.
  body=b'\x08\x00'+struct.pack('<HH',25*256,1)+b'\x00\x00';header=b'CWS\x06'+struct.pack('<I',8+len(body))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'fixture.swf';p.write_bytes(header+zlib.compress(body));r=inspect(p);self.assertEqual(r['swfFormatVersion'],6);self.assertEqual(r['frameRate'],25);self.assertEqual(r['rootFrames'],1)
   p.write_bytes(header[:-1]+b'\x01'+zlib.compress(body))
   with self.assertRaises(ValueError):inspect(p)
  with self.assertRaises(ValueError):list(tags(b'\xff\x00',0,2))
 def test_numeric_as2_extraction_rejects_incomplete_and_never_evaluates(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'test.as';rows='\n'.join(f'mt_line_01[{i}] = new Array('+','.join(['0']*11)+');' for i in range(11));p.write_text(rows+'\nboss_man[0] = new Array(50,20,1,1,1,"name");\nmt_line_99[0] = new Array(evil());')
   r=extract(d);self.assertEqual(len(r['maps']),1);self.assertEqual(r['enemies'][0]['hp'],50)
   p.write_text('mt_line_01[0] = new Array(0);\nboss_man[0] = new Array(50,20,1,1,1,"name");')
   with self.assertRaises(ValueError):extract(d)
if __name__=='__main__':unittest.main()
