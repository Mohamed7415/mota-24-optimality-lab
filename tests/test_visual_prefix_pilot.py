import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from visual_prefix_pilot import action_visible, complete_shop


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

    def test_each_shop_option_closes_menu_without_an_extra_purchase(self):
        for shop in (1, 2, 5):
            for choice in (1, 2, 3, 4):
                with self.subTest(shop=shop, choice=choice):
                    menu = dict(intro=shop == 1, opened=True, cursor=1, purchases=[], confirmations=0)

                    def press(key):
                        self.assertTrue(menu['opened'], 'Input sent after shop had closed')
                        if menu['intro']:
                            self.assertEqual(key, 'Space')
                            menu['intro'] = False
                        elif key == '2':
                            menu['cursor'] = menu['cursor'] % 4 + 1
                        elif key == 'Space':
                            if menu['cursor'] == 4:
                                menu['opened'] = False
                            else:
                                menu['purchases'].append(menu['cursor'])
                        else:
                            self.fail('Unexpected shop key')

                    def confirm():
                        self.assertTrue(menu['opened'], 'An exit option cannot require an open purchase modal')
                        self.assertEqual(menu['purchases'], [choice])
                        menu['confirmations'] += 1

                    complete_shop(dict(shop=shop, choice=choice), press, confirm)
                    self.assertFalse(menu['opened'])
                    self.assertEqual(menu['purchases'], [] if choice == 4 else [choice])
                    self.assertEqual(menu['confirmations'], 0 if choice == 4 else 1)


if __name__ == '__main__':
    unittest.main()
