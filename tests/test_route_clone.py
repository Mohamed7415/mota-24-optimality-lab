import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from route_clone import clone_for_search

class RouteCloneTests(unittest.TestCase):
    def model(self):
        root={'map':[1,2]};root['self']=root
        return SimpleNamespace(root=root,rng={'state':123},actions=[{'randomDraws':[199]}],events=[['display','old']],timeline=[12],draws=[199])
    def test_preserves_causal_graph_rng_and_action_evidence_without_aliasing(self):
        old=self.model();new=clone_for_search(old)
        self.assertIs(new.root['self'],new.root)
        self.assertEqual(new.rng,old.rng);self.assertEqual(new.actions,old.actions)
        new.root['map'][0]=9;new.rng['state']=456;new.actions[0]['randomDraws'].append(0)
        self.assertEqual(old.root['map'],[1,2]);self.assertEqual(old.rng['state'],123)
        self.assertEqual(old.actions[0]['randomDraws'],[199])
        self.assertEqual((new.events,new.timeline,new.draws),([],[],[]))
        self.assertEqual((old.timeline,old.draws),([12],[199]))
    def test_diagnostic_history_is_not_traversed(self):
        class Diagnostic:
            def __deepcopy__(self,memo):raise AssertionError('Old diagnostic was copied')
        old=self.model();old.events.append(Diagnostic())
        self.assertEqual(clone_for_search(old).events,[])
