import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from h5_route_adapter import empty_path_to_contact,h5_prefix_expected

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
