"""Numerical original-bytecode route planner, with explicit UI boundary adapter.
NOT a player or an independent gameplay verification. Display/clock/dialogue
animation are abstracted; generated routes require unchanged native SWF replay.
No game-defined dispatch beyond four pinned reviewed functions and exact frames.
"""
import collections,copy,re,sys
from functools import lru_cache
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src')]
from avm1 import Machine,Obj,UNDEFINED,Unsupported,number,string,actions
from flash_sections import sections as base_sections
from route_sections import sections,metadata
from shop_sections import sections as shop_sections
from flash_replay import prepare
from ruffle_rng import RuffleRng

RESOURCE_FIELDS=['Now_hp','Now_gong','Now_fang','Now_life','Now_yellow','Now_blue','Now_red','Now_money','Now_mp']
NPC_ENDS={'mt_say_01':{'start':'568:32','say_two':'568:39','say_three':'568:59','say_four':'568:67','say_five':'568:72','say_six':'568:83'},'mt_say_02':{'start':'714:8','say_two':'714:19'},'mt_say_03':{'start':'695:8','say_two':'695:17','say_three':'695:23'},'mt_say_04':{'start':'745:17','say_two':'745:21'},'mt_say_06':{'start':'770:20'},'mt_say_07':{'start':'780:5'},'mt_say_08':{'start':'795:6','say_two':'795:9','say_three':'795:12'}}

@lru_cache(maxsize=64)
def parsed_program(code):return tuple(actions(code))

class RouteMachine(Machine):
    def program(self,code):return parsed_program(code)
    def __init__(self,adapter,*args,depth=0,**kwargs):
        super().__init__(*args,**kwargs);self.adapter=adapter;self.depth=depth
        if depth>4:raise Unsupported('Reviewed function call depth')
    def call(self,obj,name,args):
        name=string(name).lower()
        if obj is self.root:
            funcs={n.lower():n for n in ('Move_arrow','SetLineDisplay','DelLineDisplay','DelBaseDisplay')}
            if name in funcs:
                self.adapter.execute(funcs[name],args,depth=self.depth+1);return UNDEFINED
            if name=='number' and len(args)==1:return number(args[0])
            if name=='copymovie' and len(args)==5:
                base,instance,*_=args
                if re.fullmatch(r'mtsay_00[1-8]',instance):
                    self.root[instance]=Obj({'_base':base,'_label':'start','_instance':instance,'MT':Obj(),'bkground':Obj()});self.events.append(['displayCreate',base,instance]);return UNDEFINED
                result=super().call(obj,name,args)
                if isinstance(self.root[instance],Obj):
                    self.root[instance]['_base']=base;self.root[instance]['_label']='start';self.root[instance]['_instance']=instance
                return result
            if name in ('gotoandplay','gotoandstop'):
                self.adapter.timeline.append(args[0])
        if isinstance(obj,Obj) and name in ('gotoandplay','gotoandstop'):
            if isinstance(obj['_instance'],str):
                obj['_label']='start' if args[0]==1 else args[0]
                if isinstance(args[0],int):obj['_currentframe']=args[0]
        return super().call(obj,name,args)

class OriginalRoute:
    def __init__(self,swf,seed=128188416,random_policy='fixed-seed'):
        if random_policy not in ('fixed-seed','worst-support'):raise ValueError('Unknown RNG policy')
        self.sections=sections(swf);self.base=base_sections(swf);self.shops=shop_sections(swf)
        self.root,_=prepare(self.base);self.root['Now_yellow']=0;self.root['_root']=self.root
        # Native opening spends the yellow key AND clears the MT0 door/spawn.
        # Earlier local experiments prohibited re-entry, hiding the stale door.
        self.root['mt_line_00'][7][5]=0;self.root['mt_line_00'][9][5]=0
        self.rng=RuffleRng(seed);self.random_policy=random_policy;self.events=[];self.actions=[];self.timeline=[];self.instructions=0;self.draws=[]
        self.root['mt_bgsound']=Obj({'_currentframe':11});self.root['mt_man']=Obj();self.root['mt_lines']=Obj({'bkground':Obj({'_alpha':100})})
        self.execute('SetLineDisplay',[1]);self.ack_ui()
    def execute(self,name,args=(),actor=None,depth=0):
        s=self.sections[name];scope=actor if actor is not None else Obj(dict(zip(s['parameters'],args)))
        vm=RouteMachine(self,self.root,scope,pool=s['pool'],unbound_to_root=True,max_steps=1000000,depth=depth)
        vm.run(s['bytes'],stop_before_date=True);self.instructions+=vm.steps;self.events.extend(vm.events);return vm
    def resources(self):
        s=self.root;return dict(hp=int(s['Now_hp']),atk=int(s['Now_gong']),**{'def':int(s['Now_fang'])},level=int(s['Now_life']),keys=[int(s[k]) for k in RESOURCE_FIELDS[4:7]],money=int(s['Now_money']),experience=int(s['Now_mp']))
    def grid(self,f=None):return self.root[f'mt_line_{int(self.root["Now_line"]) if f is None else f:02d}']
    def location(self):return int(self.root['Now_line']),int(self.root['Now_xid'])*11+int(self.root['Now_yid'])
    def ack_ui(self):
        # Explicit abstraction boundaries. None of these writes occur in native replay.
        if self.root['Display_other']==1:
            actor=self.root['mt_otherlist'];frame=actor['_currentframe']
            if frame not in range(1,7):raise Unsupported('Unknown tool popup frame')
            self.execute('button628:Space',actor=actor);self.execute('636:7',actor=actor)
        for k in ('Display_text','Display_other','Display_buy','Open_room'):
            if self.root[k] in (1,2):self.root[k]=2
        self.execute('855:1');self.root['Display_lines']=0
        if self.root['Display_kill']==0 and not self.active_dialogues():self.root['Now_key_flag']=1
    def active_dialogues(self):
        return [(n,self.root[n]) for n in ['mtsay_001','mtsay_002','mtsay_003','mtsay_004','mtsay_006','mtsay_007','mtsay_008'] if isinstance(self.root[n],Obj) and self.root[n]['_base'] in NPC_ENDS]
    def settle(self):
        # Process exact original endpoint actions and their world-tick effects.
        for _ in range(8):
            active=self.active_dialogues()
            if not active:break
            for n,actor in active:
                endpoint=NPC_ENDS[actor['_base']].get(actor['_label'])
                if endpoint is None:raise Unsupported('Unknown dialogue episode')
                self.execute(endpoint,actor=actor);actor['_base']=None
            self.ack_ui()
        else:raise Unsupported('Dialogue settlement loop')
        self.ack_ui()
    def invoke_move(self,arrow):return self.execute('Move_arrow',[arrow])
    def battle(self):
        r=self.root;actor=r['mt_kills'];before=len(self.draws)
        def tape():
            while True:
                d=199 if self.random_policy=='worst-support' else self.rng.draw();self.draws.append(d);yield d
        vm=RouteMachine(self,r,actor,random_values=tape(),max_steps=2000000)
        vm.run(self.base['combat1']['bytes'])
        for _ in range(20000):
            vm.run(self.base['combat24']['bytes']);vm.run(self.base['combat34']['bytes'])
            if actor['left_hp']<=0:break
            if actor['right_hp']<=0:raise ValueError('Hero died')
        else:raise Unsupported('Battle frame limit')
        vm.run(self.base['combat35']['bytes']);vm.run(self.base['combat54']['bytes']);self.instructions+=vm.steps
        r['Display_kill']=0;self.invoke_move(100);return self.draws[before:]
    @staticmethod
    def neighbors(p):return [q for q in (p-11,p+11,p-1,p+1) if 0<=q<121 and abs(q%11-p%11)+abs(q//11-p//11)==1]
    def floor_edge(self,f,p):
        t=self.grid(f)[p//11][p%11]
        if t==13:
            to=({55:23,65:25,115:24}.get(p) if f==22 else f+1)
        elif t==14:to=22 if f in (23,24,25) else f-1
        elif t==5 and f==24 and all(x==1 for x in self.root['mt_GetMoney']):to=26;t=13
        else:return None
        if to is None or not 0<=to<=26:return None
        marker=97 if t==13 else 98
        matches=[y*11+x for y,row in enumerate(self.grid(to)) for x,v in enumerate(row) if v==marker]
        if not matches:return None
        return (to,matches[-1])
    def contact_path(self,floor,target):
        start=self.location();q=collections.deque([start]);prev={start:None};edge={}
        while q:
            f,p=q.popleft()
            if f==floor and target in self.neighbors(p):
                route=[];cur=(f,p)
                while prev[cur] is not None:route.append(edge[cur]);cur=prev[cur]
                return list(reversed(route))
            for n in self.neighbors(p):
                tile=self.grid(f)[n//11][n%11];dest=(f,n) if tile in (0,97,98,99) else self.floor_edge(f,n)
                if dest is not None and dest not in prev:
                    prev[dest]=(f,p);edge[dest]=(f,n,dest[0]!=f);q.append(dest)
        raise ValueError(f'Unreachable F{floor} target{target%11,target//11}')
    def walk_contact(self,floor,target):
        for f,p,stair in self.contact_path(floor,target):
            _,old=self.location();arrow={-1:1,1:2,-11:3,11:4}[p-old];before=self.resources();self.invoke_move(arrow)
            if stair:
                r=self.root;r['mt_lines']['bkground']['_alpha']=100;self.execute('855:6');self.ack_ui()
                self.actions.append({'kind':'floor','floor':f,'position':[p%11,p//11],'toFloor':int(r['Now_line']),'resourcesAfter':before})
            elif self.location()!=(f,p):raise ValueError('Original movement diverged')
    def take_stair(self,f,x,y):
        target=y*11+x;self.walk_contact(f,target);before=self.resources();_,old=self.location()
        self.invoke_move({-1:1,1:2,-11:3,11:4}[target-old])
        if self.root['My_lifes_up']!=1 and self.root['My_lifes_down']!=1:raise ValueError('Original stair not triggered')
        self.root['mt_lines']['bkground']['_alpha']=100;self.execute('855:6');self.ack_ui()
        self.actions.append({'kind':'floor','floor':f,'position':[x,y],'toFloor':int(self.root['Now_line']),'resourcesAfter':before})
        return self.resources()
    def touch(self,f,x,y,shop_choice=None):
        p=y*11+x;self.walk_contact(f,p);tile=int(self.grid(f)[y][x]);before=self.resources();_,old=self.location();self.invoke_move({-1:1,1:2,-11:3,11:4}[p-old]);draws=[]
        if self.root['Display_kill']==1:draws=self.battle()
        is_shop=(f,tile) in {(3,22),(11,22),(5,27),(12,27),(5,26),(13,26)}
        if is_shop:
            shop={(3,22):1,(11,22):2,(5,27):3,(12,27):4,(5,26):5,(13,26):6}[f,tile]
            if shop_choice is None:raise ValueError('Shop choice required')
            s=self.shops[shop];actor=Obj({'now_case_id':shop_choice});actor['this']=actor
            vm=RouteMachine(self,self.root,actor,pool=s['pool']);vm.run(s['bytes']);self.instructions+=vm.steps
        self.settle();after=self.resources()
        if before==after and self.grid(f)[y][x]==tile and not (is_shop and shop_choice==4) and not (tile in (24,25,26,27,28,119,129)):raise ValueError(f'No progress F{f} tile{tile}')
        a={'kind':'shop' if is_shop else 'dialogue' if tile in (24,25,26,27,28,119,129) else 'consume','floor':f,'position':[x,y],'originalTile':tile,'resourcesAfter':after}
        if is_shop:a|={'shop':shop,'choice':shop_choice}
        if draws:a|={'randomDraws':draws,'rngStateAfter':self.rng.state,'hpCost':before['hp']-after['hp']}
        self.actions.append(a);return after
    def match(self,f,tiles,count=1):
        for _ in range(count):
            candidates=[]
            for y,row in enumerate(self.grid(f)):
                for x,t in enumerate(row):
                    if t not in tiles:continue
                    try:path=self.contact_path(f,y*11+x)
                    except ValueError:continue
                    candidates.append((len(path),y,x))
            if not candidates:raise ValueError(f'No reachable F{f} tile in{tiles}')
            _,y,x=min(candidates);self.touch(f,x,y)
        return self.resources()
