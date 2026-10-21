"""Minimal trusted AVM1 fixture emitter. Generated SWFs are local test inputs."""
import struct

def push(*values):
    body=b''
    for v in values:
        if isinstance(v,str):body+=b'\0'+v.encode('utf8')+b'\0'
        elif isinstance(v,bool):body+=b'\x05'+bytes([v])
        elif isinstance(v,int) and -(1<<31)<=v<(1<<31):body+=b'\x07'+struct.pack('<i',v)
        elif v is None:body+=b'\x02'
        else:
            raw=struct.pack('<d',v);body+=b'\x06'+raw[4:]+raw[:4]
    if len(body)>65535:raise ValueError('Push payload too large')
    return b'\x96'+struct.pack('<H',len(body))+body

def tag(code,data=b''):
    n=len(data);return struct.pack('<H',(code<<6)|min(n,63))+(struct.pack('<I',n) if n>=63 else b'')+data

def swf(program,width=600,height=440,fps=60):
    n=max(width*20,height*20).bit_length()+1
    bits=f'{n:05b}'+''.join(f'{v:0{n}b}' for v in [0,width*20,0,height*20]);bits+='0'*((-len(bits))%8)
    rect=int(bits,2).to_bytes(len(bits)//8,'big')
    payload=rect+struct.pack('<HH',fps*256,1)+tag(12,program+b'\x07\x00')+tag(1)+tag(0)
    return b'FWS\x06'+struct.pack('<I',8+len(payload))+payload

def trace_string(s):return push(s)+b'\x26'
def getvar(name):return push(name)+b'\x1c'
def setvar(name,value):return push(name,value)+b'\x1d'
