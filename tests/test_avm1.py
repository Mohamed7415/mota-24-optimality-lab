import copy, struct, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from avm1 import Machine, Obj, Unsupported, UNDEFINED, actions, integer32
from flash_model import critical_probability, gate, ordinary_cost
from fractions import Fraction


def push(*values):
    payload = b""
    for v in values:
        if isinstance(v, str):
            payload += b"\x00" + v.encode() + b"\x00"
        elif isinstance(v, bool):
            payload += b"\x05" + bytes([v])
        elif isinstance(v, int):
            payload += b"\x07" + struct.pack("<i", v)
        else:
            raw = struct.pack("<d", v)
            payload += b"\x06" + raw[4:] + raw[:4]
    return b"\x96" + struct.pack("<H", len(payload)) + payload


class VMTests(unittest.TestCase):
    def test_variable_scope_case_and_mixed_endian_double(self):
        root = Obj()
        scope = Obj()
        vm = Machine(root, scope)
        vm.run(push("value", 3.25) + b"\x1d" + push("copy", "VaLuE") + b"\x1c\x1d\x00")
        self.assertEqual(scope["value"], 3.25)
        self.assertEqual(scope["COPY"], 3.25)
        self.assertIs(root["value"], UNDEFINED)
        vm = Machine(root, scope, unbound_to_root=True)
        vm.run(push("global", 7) + b"\x1d\x00")
        self.assertEqual(root["GLOBAL"], 7)
        self.assertIs(copy.deepcopy(UNDEFINED), UNDEFINED)

    def test_integer32_and_numeric_strict_equality(self):
        for value, expected in [
            (3.9, 3),
            (-3.9, -3),
            (2**32 + 1, 1),
            (2**31, -(2**31)),
            (float("inf"), 0),
            (float("nan"), 0),
        ]:
            self.assertEqual(integer32(value), expected)
        vm = Machine()
        vm.run(push("equal", 1, 1.0) + b"\x66\x1d\x00")
        self.assertTrue(vm.root["equal"])

    def test_unknown_opcode_native_function_and_method_denied(self):
        with self.assertRaises(Unsupported):
            Machine().run(b"\x83\x00\x00")  # GetURL, denied even with empty payload
        with self.assertRaises(Unsupported):
            Machine().run(push(0, "__import__") + b"\x3d\x17\x00")
        with self.assertRaises(Unsupported):
            Machine().call(Obj(), "untrusted", [])

    def test_bad_jump_and_instruction_budget(self):
        with self.assertRaises(Unsupported):
            Machine().run(b"\x99\x02\x00\xfd\xff\x00")
        with self.assertRaises(Unsupported):
            Machine(max_steps=4).run(b"\x99\x02\x00\xfb\xff")

    def test_function_body_boundary_and_no_implicit_execution(self):
        meta = b"f\x00\x00\x00\x01\x00"
        code = b"\x9b" + struct.pack("<H", len(meta)) + meta + b"\x00\x00"
        decoded = actions(code)
        self.assertEqual(decoded[0].name, "f")
        self.assertEqual(decoded[0].body, b"\x00")
        self.assertEqual(decoded[1].opcode, 0)
        with self.assertRaises(Unsupported):
            Machine().run(code)
        with self.assertRaises(Unsupported):
            actions(code[:-2])

    def test_random_tape_boundaries_and_exhaustion(self):
        code = push("draw", 200) + b"\x30\x1d\x00"
        for supplied in [0, 199]:
            vm = Machine(random_values=[supplied])
            vm.run(code)
            self.assertEqual(vm.root["draw"], supplied)
        for tape in [[], [-1], [200]]:
            with self.assertRaises(Unsupported):
                Machine(random_values=tape).run(code)

    def test_date_is_only_an_explicit_stop_boundary(self):
        code = push(0, "Date") + b"\x40\x17\x00"
        with self.assertRaises(Unsupported):
            Machine().run(code)
        self.assertEqual(
            Machine().run(code, stop_before_date=True)["reason"],
            "stopped before unmodelled Date constructor",
        )

    def test_gate_differs_from_normal_damage_and_support_probability(self):
        enemy = [50, 20, 1, 1, 1]
        self.assertFalse(gate(enemy, 45, 11, 10))
        self.assertEqual(ordinary_cost(enemy, 11, 10), 40)
        self.assertTrue(gate(enemy, 50, 10, 10))
        self.assertEqual(ordinary_cost(enemy, 10, 10), 50)
        self.assertEqual(critical_probability(1), Fraction(1, 100))
        self.assertEqual(critical_probability(198), Fraction(199, 200))
        self.assertEqual(critical_probability(199), 1)


if __name__ == "__main__":
    unittest.main()
