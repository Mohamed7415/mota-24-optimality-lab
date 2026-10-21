"""Ruffle v0.7.1 AVM RNG, ported from core/src/avm_rng.rs.
Algorithm/source: Ruffle LLC and contributors, MIT (third_party/RUFFLE-LICENSE-MIT).
This models that fixed emulator release, not a claim about every Adobe player.
"""
MASK=0xffffffff

def sar(v,n):
    v&=MASK
    return (v-(1<<32) if v&0x80000000 else v)>>n

def next_state(state):return (state>>1)^(0x48000000 if state&1 else 0)
def output(state):
    s=(state*71)&MASK;s=(((s<<13)^s)-sar(s,21))&MASK
    r=(s*s)&MASK;r=(r*15731+789221)&MASK;r=(r*s+1376312589)&MASK
    r&=0x7fffffff;r=(r+s)&MASK;r=(((r<<13)^r)-sar(r,21))&MASK
    return (r&0x7fffffff)%200

class RuffleRng:
    def __init__(self,seed):self.seed=seed&MASK;self.state=0
    def draw(self):
        if self.state==0:self.state=self.seed
        self.state=next_state(self.state)
        return output(self.state)
