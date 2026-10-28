import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from visual_prefix_pilot import action_visible, complete_shop, complete_compass, action_wait_seconds, collect_ending_frames, treasure_grant_visible, walk_empty_batches, requires_hidden_treasure_grant, battle_contact_retry_safe


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

    def test_battle_retry_requires_old_hud_position_and_a_real_nonhp_progress_signal(self):
        action={'kind':'consume','battleRandomDrawCount':2,'expectedResources':{**self.expected,'money':75,'experience':40}}
        screen={'values':self.hud,'orangeMaxRun':26,'heroCandidates':[{'x':9,'y':2}]}
        self.assertTrue(battle_contact_retry_safe(screen,self.hud,[9,2],action))
        self.assertFalse(battle_contact_retry_safe({**screen,'values':{**self.hud,'money':75}},self.hud,[9,2],action))
        self.assertFalse(battle_contact_retry_safe({**screen,'orangeMaxRun':333},self.hud,[9,2],action))
        self.assertFalse(battle_contact_retry_safe(screen,self.hud,[8,2],action))
        self.assertFalse(battle_contact_retry_safe(screen,self.hud,[9,2],{**action,'expectedResources':self.expected}))
        self.assertFalse(battle_contact_retry_safe(screen,self.hud,[9,2],{**action,'kind':'dialogue'}))

    def test_treasure_guard_follows_the_actual_npc_not_a_magic_action_index(self):
        npc={'kind':'dialogue','floor':16,'position':[4,4],'originalTile':26,'index':917}
        self.assertTrue(requires_hidden_treasure_grant(npc))
        self.assertFalse(requires_hidden_treasure_grant({**npc,'floor':5,'index':929}))
        self.assertFalse(requires_hidden_treasure_grant({**npc,'kind':'consume'}))

    def test_treasure_requires_grant_text_not_just_a_mention(self):
        self.assertFalse(treasure_grant_visible({'sceneText':[{'text':'我有神秘宝物','confidence':1}]}))
        self.assertFalse(treasure_grant_visible({'sceneText':[{'text':'你可以得到神秘宝物','confidence':1}]}))
        self.assertTrue(treasure_grant_visible({'sceneText':[{'text':'得到','confidence':1,'x':.4,'y':.5},{'text':'神秘宝物！','confidence':1,'x':.6,'y':.5}]}))
        self.assertTrue(treasure_grant_visible({'sceneText':[{'text':'得到 神秘宝物！','confidence':1}]}))
        self.assertFalse(treasure_grant_visible({'sceneText':[{'text':'得到 神秘宝物！','confidence':.2}]}))

    def test_empty_batch_retries_only_the_visible_remaining_cells(self):
        action={'index':7,'startPosition':[0,0],'steps':[{'key':'ArrowRight','x':x,'y':0} for x in (1,2,3)]}
        state={'x':0,'calls':[]}
        def press(keys):
            state['calls'].append(len(keys))
            state['x']+=2 if len(state['calls'])==1 else len(keys)
        def capture(full=True):
            return {'heroCandidates':[{'x':state['x'],'y':0}],'orangeMaxRun':0,'values':{'hp':100} if full else {}}
        walk_empty_batches(action,{'hp':100},press,capture,lambda _:None)
        self.assertEqual(state['calls'],[3,1])
        self.assertEqual(state['x'],3)

    def test_empty_batch_never_retries_after_a_resource_change(self):
        action={'index':7,'startPosition':[0,0],'steps':[{'key':'ArrowRight','x':x,'y':0} for x in (1,2,3)]}
        sent=[]
        def capture(full=True):
            return {'heroCandidates':[{'x':1,'y':0}],'orangeMaxRun':0,'values':{'hp':99} if full else {}}
        with self.assertRaises(ValueError):walk_empty_batches(action,{'hp':100},lambda keys:sent.append(len(keys)),capture,lambda _:None)
        self.assertEqual(sent,[3])

    def test_empty_batches_are_bounded_and_exclude_the_action_contact(self):
        action={'index':7,'startPosition':[0,0],'contact':'ArrowRight','steps':[{'key':'ArrowRight','x':x,'y':0} for x in range(1,10)]}
        state={'x':0,'calls':[]}
        def press(keys):state['calls'].append(len(keys));state['x']+=len(keys)
        def capture(full=True):return {'heroCandidates':[{'x':state['x'],'y':0}],'orangeMaxRun':0,'values':{'hp':100} if full else {}}
        self.assertEqual(walk_empty_batches(action,{'hp':100},press,capture,lambda _:None),2)
        self.assertEqual(state['calls'],[8,1])
        self.assertEqual(state['x'],9)

    def test_ending_samples_wait_without_sending_inputs_or_claiming_victory(self):
        elapsed = [0]
        def sleep(seconds):
            elapsed[0] += seconds
        def capture():
            return {'values': {}, 'boardBlackFraction': 1, 'sampleTime': elapsed[0]}
        samples = collect_ending_frames(capture, sleep)
        self.assertEqual([s['observed']['sampleTime'] for s in samples], [0, 2, 5, 10, 20, 40, 80, 120, 180])
        self.assertEqual(elapsed[0], 180)
        self.assertTrue(all('complete24Floors' not in s for s in samples))

    def test_long_battle_gets_a_bounded_wait_without_altering_acceptance(self):
        self.assertEqual(action_wait_seconds({}), 25)
        self.assertEqual(action_wait_seconds({'battleRandomDrawCount': 165}), 340)
        self.assertEqual(action_wait_seconds({'battleRandomDrawCount': 20000}), 600)
        battle = {'values': {'red': 2}, 'orangeMaxRun': 333, 'heroCandidates': []}
        self.assertFalse(action_visible(battle, self.expected, [5, 4]))

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

    def test_compass_selects_from_initial_floor_one_and_closes_the_selector(self):
        for destination in (1, 11, 20):
            with self.subTest(destination=destination):
                ui = dict(stage='map', cursor=None, landed=None, confirmed=0)

                def press(key):
                    if ui['stage'] == 'map':
                        self.assertEqual(key, 'j')
                        ui['stage'] = 'intro'
                    elif ui['stage'] == 'intro':
                        self.assertEqual(key, 'Space')
                        ui.update(stage='selector', cursor=1)
                    elif ui['stage'] == 'selector' and key == '2':
                        ui['cursor'] = ui['cursor'] % 20 + 1
                    elif ui['stage'] == 'selector' and key == 'Space':
                        ui.update(stage='landed', landed=ui['cursor'])
                    else:
                        self.fail('Unexpected compass input or input after landing')

                def confirm():
                    self.assertEqual(ui['stage'], 'intro')
                    ui['confirmed'] += 1

                complete_compass(dict(toFloor=destination), press, confirm)
                self.assertEqual(ui['landed'], destination)
                self.assertEqual(ui['confirmed'], 1)

    def test_compass_rejects_a_destination_outside_the_reviewed_ui(self):
        inputs = []
        with self.assertRaises(ValueError):
            complete_compass(dict(toFloor=21), inputs.append, lambda: None)
        self.assertEqual(inputs, [])


if __name__ == '__main__':
    unittest.main()
