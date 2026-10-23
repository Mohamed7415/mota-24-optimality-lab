"""Read-only full-route observer: current map rows and numeric battle/plot state."""
import hashlib,json
from pathlib import Path
from game_observer import field as basic_field,function,FIELDS
from swf_fixture import push,swf,getvar

def field(name):
    if name.startswith('visibleMap.'):
        row=int(name.split('.')[1])
        # game["mt_line_" + int(Now_line/10) + Now_line%10][row]
        key=push('mt_line_')+basic_field('Now_line')+push(10)+b'\x0d\x18\x21'+basic_field('Now_line')+push(10)+b'\x3f\x21'
        return getvar('game')+key+b'\x4e'+push(row)+b'\x4e'
    if name.startswith('battleEnemy.'):
        col=int(name.split('.')[1]);return basic_field('boss_man')+basic_field('Now_boss_id')+b'\x4e'+push(col)+b'\x4e'
    return basic_field(name)

def make(out_dir='generated/FullRoute'):
    fields=FIELDS+['Display_other','Display_buy','Open_room','Now_boss_x','Now_boss_y','mt_buy_list._currentframe','mt_buy_list.now_case_id']
    fields += [f'mtsay_00{i}._currentframe' for i in (2,3,4,6,7,8)]
    fields += ['my_love','big_clean','mt_changes','Set_man_01','Set_man_02','Display_kills','mt_GetMoney','open_last_door','NowGameTime','mt_LastGame_ID','boss_kills','Max_line','jump_flag']
    fields += [f'visibleMap.{row}' for row in range(11)]+[f'battleEnemy.{i}' for i in range(5)]
    code=push('game')+push(1,'game',2)+getvar('_root')+push('createEmptyMovieClip')+b'\x52\x1d'
    code+=getvar('game')+push('_lockroot',True)+b'\x4f';body=push('GAME|')
    for i,k in enumerate(fields):
        if i:body+=push('|')+b'\x21'
        body+=field(k)+b'\x21'
    body+=push('|')+b'\x21'+basic_field('_root')+getvar('game')+b'\x49\x21\x26'
    code+=function('observe',body)+getvar('_root')+push('onEnterFrame')+getvar('observe')+b'\x4f'
    code+=push('game.swf',1)+getvar('game')+push('loadMovie')+b'\x52\x17'
    data=bytearray(swf(code,width=570,height=410,fps=100));data[3]=8
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);(out/'observer.swf').write_bytes(data)
    (out/'observer-schema.json').write_text(json.dumps({'fields':fields+['rootIsSelf'],'sha256':hashlib.sha256(data).hexdigest(),'gameVariableWrites':False,'mapReads':'Only current-floor row arrays; no original bytecode or variable writes'},indent=2)+'\n')
if __name__=='__main__':make()
