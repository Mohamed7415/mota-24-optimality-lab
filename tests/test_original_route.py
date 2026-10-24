import os,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'tools')]
from avm1 import Machine,Obj,Unsupported
from swf_fixture import push
from fullgame_observer import field

class FullObserverTests(unittest.TestCase):
    def test_dynamic_map_read_handles_zero_padding_and_two_digit_floors(self):
        for floor in (0,3,9,10,16,26):
            row=[floor,2,3,4,5,6,7,8,9,10,11]
            game=Obj({'Now_line':floor,f'mt_line_{floor:02d}':[row[:] for _ in range(11)]});root=Obj({'game':game})
            Machine(root).run(push('result')+field('visibleMap.10')+b'\x1d')
            self.assertEqual(root['result'],row);self.assertEqual(game[f'mt_line_{floor:02d}'][10],row)
    def test_unreviewed_getproperty_still_denied(self):
        with self.assertRaises(Unsupported):Machine(Obj()).run(push('',3)+b'\x22\x17')
        with self.assertRaises(Unsupported):Machine(Obj()).run(b'\x04')
    def test_enemy_read_uses_current_boss_id(self):
        game=Obj({'Now_boss_id':1,'boss_man':[[1,2,3,4,5],[50,20,1,1,1]]});r=Obj({'game':game})
        Machine(r).run(push('result')+field('battleEnemy.2')+b'\x1d');self.assertEqual(r['result'],1)

class GuidanceTerminalTests(unittest.TestCase):
    def test_reachable_boss_is_not_a_surviving_route_until_gate_and_damage_pass(self):
        from types import SimpleNamespace
        from route_guidance import Guidance
        g=Guidance.__new__(Guidance);g.target=0;g.tiles=(53,)
        g.enemies=[None]*14;g.enemies[13]=(15000,1000,1000,100,100)
        g.engine=SimpleNamespace(rng=SimpleNamespace(seed=128188416),random_policy='worst-support')
        # (mask,position,hp,atk,def,level,yellow,blue,red,cash,xp,rng)
        for hp,atk,df,expected in [(588,869,561,False),(588,1001,561,False),(20000,2000,1000,True)]:
            self.assertEqual(g.target_is_safe((0,0,hp,atk,df,17,0,0,0,0,0,0)),expected)

@unittest.skipUnless(os.environ.get('MOTA_FLASH_SWF'),'Set MOTA_FLASH_SWF for pinned original route adapter')
class OriginalRouteTests(unittest.TestCase):
    def make(self):
        from original_route import OriginalRoute
        return OriginalRoute(os.environ['MOTA_FLASH_SWF'])
    def fixture(self,r,f,x,y):
        r.root['Now_line']=f;r.root['Now_xid']=y;r.root['Now_yid']=x
        r.execute('SetLineDisplay',[3]);r.ack_ui()
    def test_natural_M6_prefix_matches_existing_pinned_seed_certificate(self):
        import json
        r=self.make();self.assertEqual(r.grid(0)[7][5],0);self.assertEqual(r.grid(0)[9][5],0);certificate=json.loads((Path(__file__).resolve().parents[1]/'experiments/whole-game-M6.json').read_text())['fixedSeedSearch']
        for a in certificate['route']:
            actual=r.touch(1,*a['position']);self.assertEqual({k:v for k,v in actual.items() if k!='level'},a['resourcesAfter'])
        self.assertEqual(r.draws,[x for a in certificate['route'] for x in a['randomDraws']])
    def test_original_thief_episodes_change_actual_door_arrays(self):
        r=self.make();self.fixture(r,4,5,0);self.assertEqual(r.grid(2)[6][1],5)
        r.invoke_move(0);r.settle();self.assertEqual(r.grid(2)[6][1],0);self.assertEqual(r.root['Display_say'][3],3)
        r.root['big_clean']=1;r.invoke_move(0);r.settle();self.assertEqual(r.grid(4)[0][5],0);self.assertEqual([r.grid(18)[y][5] for y in [8,9]],[0,0]);self.assertEqual(r.root['big_clean'],0)
    def test_original_sword_reward_is_seventy_despite_display_text(self):
        r=self.make();self.fixture(r,2,7,10);before=r.resources()['atk'];r.invoke_move(0);r.settle()
        self.assertEqual(r.resources()['atk']-before,70);self.assertEqual(r.grid(2)[10][7],0)
    def test_tool_popup_space_sets_cross_flag_before_fairy_reward(self):
        r=self.make();self.fixture(r,7,5,4);r.invoke_move(0);r.settle();self.assertEqual(r.root['my_love'],1)
        self.fixture(r,0,5,8);before=r.resources();r.touch(0,4,8);after=r.resources()
        for key in ('hp','atk','def'):self.assertEqual(after[key],before[key]+before[key]//3)
        self.assertEqual(r.root['my_love'],0)
    def test_original24_floor_quest_requires_mystery_before_cross_dialogue(self):
        r=self.make();self.assertEqual(r.grid(20)[7][5],0);r.root['mt_changes']=1;self.fixture(r,0,5,8);r.touch(0,4,8)
        self.assertEqual(r.root['mt_GetMoney'][0],1);self.assertEqual(r.root['mt_LastGame_ID'],1);self.assertEqual(r.grid(0)[8][4],24)
        self.assertEqual(r.grid(20)[7][5],0)
        self.fixture(r,7,5,4);r.invoke_move(0);r.settle();self.fixture(r,0,5,8);r.touch(0,4,8)
        self.assertEqual(r.grid(0)[8][4],0);self.assertEqual(r.root['mt_LastGame_ID'],1)
        self.assertEqual(r.grid(20)[7][5],13)
        wrong=self.make();wrong.root['mt_changes']=1;wrong.root['my_love']=1;self.fixture(wrong,0,5,8);wrong.touch(0,4,8)
        self.assertEqual(wrong.root['mt_GetMoney'][0],0);self.assertEqual(wrong.root['mt_LastGame_ID'],0);self.assertEqual(wrong.grid(0)[8][4],0)
    def test_original_enemy_stage_buff_applies_once(self):
        r=self.make();old=[list(r.root['boss_man'][i][:5]) for i in [13,17,18,22]]
        r.grid(16)[5][5]=0;r.ack_ui()
        for i,values in zip([13,17,18,22],old):self.assertEqual(r.root['boss_man'][i][:5],[v+v//3 for v in values])
        after=[list(r.root['boss_man'][i][:5]) for i in [13,17,18,22]];r.ack_ui();self.assertEqual(after,[r.root['boss_man'][i][:5] for i in [13,17,18,22]])
    def test_boss_dialogue_created_by_world_tick_finishes_before_snapshot(self):
        r=self.make();r.root['mt_LastGame_ID']=1;r.grid(21)[1][5]=0
        r.settle()
        self.assertEqual(r.grid(21)[1][5],13);self.assertEqual(r.grid(21)[2][5],98)
        self.assertEqual(r.grid(21)[6][5],0);self.assertFalse(r.active_dialogues())
        self.assertEqual(r.root['Display_say'][8],10)
    def test_fifteenth_floor_reward_endpoint_cannot_spend_unavailable_currency(self):
        for x,currency,stat in [(4,'Now_mp','atk'),(6,'Now_money','def')]:
            r=self.make();self.fixture(r,15,x,4);r.root[currency]=499
            with self.assertRaises(Unsupported):r.touch(15,x,3)
            r=self.make();self.fixture(r,15,x,4);r.root[currency]=500;before=r.resources()[stat]
            r.touch(15,x,3);self.assertEqual(r.root[currency],0);self.assertEqual(r.resources()[stat]-before,120)
    def test_guidance_fifteenth_floor_purchase_is_checked_by_original_button(self):
        from route_guidance import Guidance
        for x,currency,stat in [(4,'Now_mp','atk'),(6,'Now_money','def')]:
            r=self.make();self.fixture(r,15,x,4);r.root[currency]=500
            target=15*121+3*11+x;g=Guidance(r,(15,3*11+x),max_floor=15)
            # The goal is excluded from successors; use a nearby distinct goal
            # to check this one-time purchase as an ordinary search transition.
            self.assertTrue(g.target_is_safe(g.initial));g.target=15*121
            found=[(a,s) for s,a in g.next(g.initial) if a[0]==target]
            self.assertEqual(len(found),1);before=r.resources()[stat];g.apply(found)
            self.assertEqual(r.resources()[stat],before+120);self.assertEqual(r.root[currency],0)
    def test_retention_state_survives_original_shop_successors(self):
        from route_guidance import Guidance
        r=self.make();self.fixture(r,5,1,8);r.root['Now_mp']=100
        g=Guidance(r,(5,0),max_floor=5,valuation='retention',allow_level_purchases=False)
        successors=list(g.next(g.initial));self.assertTrue(successors)
        self.assertTrue(any(a[1] in (2,3) for _,a in successors))
        self.assertTrue(all(len(s)==len(g.initial) for s,_ in successors))
    def test_shop_waypoint_can_purchase_its_own_required_stat(self):
        from route_guidance import Guidance
        r=self.make();self.fixture(r,5,1,8);r.root['Now_mp']=30
        g=Guidance(r,(5,7*11+1),max_floor=5,valuation='retention',allow_level_purchases=False,allow_hp_purchases=False)
        path,metrics=g.solve(width=16,depth=2,required_atk=15)
        self.assertEqual(len(path),1);self.assertEqual(path[0][0],(5*121+7*11+1,2,1))
        g.apply(path);self.assertEqual(r.resources()['atk'],15);self.assertEqual(r.resources()['experience'],0)
    def test_floor_component_cache_matches_cell_walk_with_directed_stairs(self):
        import random
        from route_guidance import Guidance,FREE
        r=self.make();r.root['mt_GetMoney']=[1,1,1]
        g=Guidance(r,(25,61),max_floor=26);rng=random.Random(4281)
        self.assertEqual(g.floor_links[24*121+6*11+5][0],26)
        self.assertNotIn(26*121+10*11+5,g.floor_links)  # Final floor has no return stair.
        free=[p for p,t in enumerate(g.tiles) if t in FREE]
        masks=[0,sum(1<<i for i,t in g.objects.values())]
        masks += [sum(1<<i for i,t in g.objects.values() if rng.randrange(3)==0) for _ in range(10)]
        # Counterfactual consumed masks test graph equivalence only; these are
        # not claimed feasible gameplay states or route-search witnesses.
        for mask in masks:
            for pos in rng.sample(free,8):
                self.assertEqual(g._region(mask,pos),g._region_cells(mask,pos),(mask,pos))
    def test_unknown_game_function_dispatch_still_denied(self):
        from original_route import RouteMachine
        r=self.make()
        with self.assertRaises(Unsupported):RouteMachine(r,r.root).call(r.root,'unreviewed_callback',[])
if __name__=='__main__':unittest.main()
