import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from visual_prefix_pilot import action_visible


class ActionVisibleTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'hp': 700, 'atk': 100, 'def': 80, 'level': 2,
            'keys': [3, 4, 1], 'money': 60, 'experience': 25,
        }
        self.hud = {
            'hp': 700, 'atk': 100, 'def': 80, 'level': 2,
            'yellow': 3, 'blue': 4, 'red': 1, 'money': 60,
            'experience': 25,
        }

    def test_shop_purchase_can_be_confirmed_while_modal_hides_hero(self):
        screen = {'values': self.hud, 'orangeMaxRun': 223, 'heroCandidates': []}
        self.assertTrue(action_visible(screen, self.expected, [9, 3], require_closed=False))

    def test_shop_confirmation_requires_the_modal_to_remain_open(self):
        screen = {'values': self.hud, 'orangeMaxRun': 0, 'heroCandidates': []}
        self.assertFalse(action_visible(screen, self.expected, [9, 3], require_closed=False))

    def test_closed_map_action_still_requires_expected_hero_cell(self):
        screen = {'values': self.hud, 'orangeMaxRun': 0, 'heroCandidates': [{'x': 9, 'y': 3}]}
        self.assertTrue(action_visible(screen, self.expected, [9, 3]))
        screen['heroCandidates'] = []
        self.assertFalse(action_visible(screen, self.expected, [9, 3]))

    def test_pixel_only_walking_capture_cannot_confirm_a_source_action(self):
        screen = {'values': {}, 'hudRead': False, 'orangeMaxRun': 0,
                  'heroCandidates': [{'x': 9, 'y': 3}]}
        self.assertFalse(action_visible(screen, self.expected, [9, 3]))


if __name__ == '__main__':
    unittest.main()
