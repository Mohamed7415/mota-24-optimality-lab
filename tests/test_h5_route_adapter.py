import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from h5_route_adapter import empty_path_to_contact,h5_prefix_expected,complete_fly,h5_floor_id,h5_contact_position

class H5AdapterTests(unittest.TestCase):
    def test_path_stops_before_target_and_never_crosses_an_unplanned_door(self):
        grid=[[1]*13 for _ in range(13)]
        for x,y in [(1,1),(1,2),(2,2),(3,2),(3,1)]:grid[y][x]=0
        grid[1][2]=81
        grid[1][4]=27
        path=empty_path_to_contact(grid,(1,1),(4,1))
        self.assertEqual(path[-1][1],(3,1))
        self.assertTrue(all(grid[y][x]==0 for _,(x,y) in path))
        self.assertNotIn((2,1),[p for _,p in path])
        grid[2][2]=81
        with self.assertRaises(ValueError):empty_path_to_contact(grid,(1,1),(4,1))

    def test_adjacent_target_requires_no_walking_and_bounds_are_checked(self):
        grid=[[1]*13 for _ in range(13)]
        self.assertEqual(empty_path_to_contact(grid,(2,2),(3,2)),[])
        with self.assertRaises(ValueError):empty_path_to_contact(grid,(-1,0),(3,2))

    def test_gem_order_matches_the_observed_stats_and_does_not_mutate_source(self):
        source={'atk':20,'def':13,'keys':[3,1,0]}
        changed=h5_prefix_expected(source,23)
        self.assertEqual((changed['atk'],changed['def']),(23,10))
        self.assertEqual((source['atk'],source['def']),(20,13))
        restored={'atk':23,'def':13,'keys':[3,1,0]}
        self.assertEqual(h5_prefix_expected(restored,24),restored)
        changed['keys'][0]=999
        self.assertEqual(source['keys'][0],3)

    def test_fly_uses_observed_selection_and_rejects_resource_changes(self):
        state={'event':{'id':'fly','flyFloorId':'MT14'},'hp':100};sent=[]
        def call(op,data):
            sent.extend(data['keys'])
            if data['keys']==['ArrowDown']:state['event']['flyFloorId']='MT13'
            if data['keys']==['Enter']:state['event']={'id':None};state['floorId']='MT13'
            return state
        result=complete_fly(13,{'hp':100},call,lambda s:s['hp'])
        self.assertEqual(result['floorId'],'MT13')
        self.assertEqual(sent,['g','ArrowDown','Enter'])
        with self.assertRaises(ValueError):complete_fly(13,{'hp':99},lambda op,data:{'hp':100,'event':{'id':'fly','flyFloorId':'MT14'}},lambda s:s['hp'])

    def test_fly_fails_if_ui_cannot_select_the_destination(self):
        state={'hp':100,'event':{'id':'fly','flyFloorId':'MT14'}}
        with self.assertRaises(ValueError):complete_fly(13,state,lambda op,data:state,lambda s:s['hp'])

    def test_fly_retries_only_a_closed_unchanged_panel_after_cooldown(self):
        state={'hp':100,'event':{'id':None}};sent=[];opens=[0]
        def call(op,data):
            sent.extend(data['keys'])
            if data['keys']==['g']:
                opens[0]+=1
                if opens[0]==2:state['event']={'id':'fly','flyFloorId':'MT13'}
            if data['keys']==['Enter']:state['event']={'id':None};state['floorId']='MT13'
            return state
        self.assertEqual(complete_fly(13,state,call,lambda s:s['hp'])['floorId'],'MT13')
        self.assertEqual(sent,['g','g','Enter'])

    def test_hidden_floor_aliases_match_the_static_map_comparison(self):
        self.assertEqual([h5_floor_id(n) for n in (20,21,22,23,24,25,26)],['MT20','MT21','MT22','MT23w','MT23s','MT23e','MT_1'])

    def test_21f_exit_uses_the_real_h5_stair_above_the_cleared_boss(self):
        self.assertEqual(h5_contact_position({'kind':'floor','floor':21,'toFloor':22,'position':[5,1]}),(6,1))
        self.assertEqual(h5_contact_position({'kind':'consume','floor':21,'position':[5,1]}),(6,2))

    def test_23w_red_gem_runs_shift_left_without_changing_pickup_order(self):
        for y in (0,10):
            self.assertEqual([h5_contact_position({'kind':'consume','floor':23,'position':[x,y],'originalTile':10})for x in (5,4,3)],[(5,y+1),(4,y+1),(3,y+1)])
