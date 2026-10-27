import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from import_h5_24_json import parse_assignment


class StaticH5JSONImportTests(unittest.TestCase):
    def test_function_text_remains_inert_data(self):
        source=b'main.floors.MT1 = {"map":[[0]],"event":{"type":"function","function":"function(){untrusted();}"}};'
        value=parse_assignment(source)
        self.assertEqual(value['event']['function'],'function(){untrusted();}')
        self.assertEqual(value['map'],[[0]])

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_assignment(b'var tower = {"map":[],"map":[[0]]};')

    def test_executable_object_literal_and_trailing_code_are_rejected(self):
        for source in (b'var tower={"f":function(){return 1;}};',
                       b'var tower={};untrusted();'):
            with self.subTest(source=source),self.assertRaises(ValueError):
                parse_assignment(source)

    def test_non_json_numeric_constants_are_rejected(self):
        for value in (b'NaN',b'Infinity',b'-Infinity'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                parse_assignment(b'var tower={"value":'+value+b'};')


if __name__=='__main__':
    unittest.main()
