"""Read-only parent observer for a byte-identical original SWF child.
_lockroot is set before load, so original _root references stay inside the child.
The observer never calls game functions or writes game variables.
"""
import hashlib,json,struct
from pathlib import Path
from swf_fixture import push,swf,getvar
FIELDS=['_currentframe','_framesloaded','begin_key','Now_line','Now_xid','Now_yid','Now_hp','Now_gong','Now_fang','Now_life','Now_yellow','Now_blue','Now_red','Now_money','Now_mp','Now_key_flag','Display_say','Display_kill','Display_lines','Display_list','Display_jump','Display_text','TimeRunID','Now_time','mtsay_001._currentframe','mt_kills._currentframe','mt_kills.kill_number','mt_kills.kill_max','mt_kills.left_hp','mt_kills.right_hp','Now_boss_id']

def function(name,body):
    body+=b'\0';head=name.encode()+b'\0'+struct.pack('<HH',0,len(body))
    return b'\x9b'+struct.pack('<H',len(head))+head+body

def field(name):
    code=getvar('game')
    for part in name.split('.'):code+=push(part)+b'\x4e'
    return code

def make(out_dir="generated/M6",extra_fields=()):
    fields=FIELDS+list(extra_fields)
    code=push('game')+push(1,'game',2)+getvar('_root')+push('createEmptyMovieClip')+b'\x52\x1d'
    code+=getvar('game')+push('_lockroot',True)+b'\x4f'
    body=push('GAME|')
    for i,k in enumerate(fields):
        if i:body+=push('|')+b'\x21'
        body+=field(k)+b'\x21'
    body+=push('|')+b'\x21'+field('_root')+getvar('game')+b'\x49\x21\x26'
    code+=function('observe',body)
    code+=getvar('_root')+push('onEnterFrame')+getvar('observe')+b'\x4f'
    code+=push('game.swf',1)+getvar('game')+push('loadMovie')+b'\x52\x17'
    data=bytearray(swf(code,width=570,height=410,fps=100));data[3]=8
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'observer.swf').write_bytes(data)
    (out/'observer-schema.json').write_text(json.dumps({'fields':fields+['rootIsSelf'],'sha256':hashlib.sha256(data).hexdigest(),'writes':['parent creates child game clip','child _lockroot=true before loading original'],'gameVariableWrites':False},indent=2)+'\n')
if __name__=='__main__':make()
