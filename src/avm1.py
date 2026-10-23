"""Small fail-closed AVM1 test machine for pinned original-game sections.

No eval, Python exec, imports from game, network, files, Date, native player or
user-defined function dispatch. Bytecode may only modify a supplied data world.
Display/audio calls are recorded stubs, not a Flash renderer. Unsupported
opcodes/native calls, malformed jumps, stack/memory and instruction limits fail.
"""

from dataclasses import dataclass
import math
import struct


class Unsupported(ValueError):
    pass


class _Undefined:
    def __repr__(self):
        return "undefined"

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


UNDEFINED = _Undefined()


def string(v):
    if v is UNDEFINED:
        return "undefined"
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)) and math.isfinite(v) and v == int(v):
        return str(int(v))
    return str(v)


def number(v):
    if v is UNDEFINED:
        return math.nan
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        try:
            return float(v.strip()) if v.strip() else 0
        except ValueError:
            return math.nan
    raise Unsupported("Object-to-number coercion is outside this subset")


def integer32(v):
    n = number(v)
    if not math.isfinite(n) or n == 0:
        return 0
    n = math.trunc(n) % (1 << 32)
    return n - (1 << 32) if n >= (1 << 31) else n


def truth(v):
    if v is UNDEFINED or v is None:
        return False
    if isinstance(v, (int, float)):
        return v != 0 and not math.isnan(v)
    return bool(v)


class Obj(dict):
    """SWF6 case-insensitive ASCII identifiers; Unicode folding not claimed."""

    def __getitem__(self, k):
        return dict.get(self, string(k).lower(), UNDEFINED)

    def __setitem__(self, k, v):
        if len(self) > 10000:
            raise Unsupported("Object size limit")
        dict.__setitem__(self, string(k).lower(), v)

    def __init__(self, values=()):
        super().__init__()
        for k, v in dict(values).items():
            self[k] = v


def getmember(obj, key):
    if isinstance(obj, Obj):
        return obj[key]
    if isinstance(obj, list):
        if key == "length":
            return len(obj)
        n = number(key)
        if not math.isfinite(n) or n != int(n):
            raise Unsupported("Noninteger array index")
        return obj[int(n)] if 0 <= n < len(obj) else UNDEFINED
    raise Unsupported("Member access outside supplied data objects")


def setmember(obj, key, value):
    if isinstance(obj, Obj):
        obj[key] = value
        return
    if isinstance(obj, list):
        n = number(key)
        if not math.isfinite(n) or n != int(n) or not 0 <= n < 10000:
            raise Unsupported("Array index limit")
        i = int(n)
        if i >= len(obj):
            obj.extend([UNDEFINED] * (i + 1 - len(obj)))
        obj[i] = value
        return
    raise Unsupported("Write outside data objects")


def cstring(data, start):
    end = data.find(b"\0", start)
    if end < 0:
        raise Unsupported("Unterminated string")
    raw = data[start:end]
    try:
        value = raw.decode("utf-8")
    except UnicodeDecodeError:
        value = raw.decode("gb18030")
    return value, end + 1


@dataclass(frozen=True)
class Action:
    offset: int
    opcode: int
    data: bytes
    end: int
    body: bytes = b""
    name: str = ""
    parameters: tuple = ()


def actions(code):
    out = []
    p = 0
    while p < len(code):
        start = p
        op = code[p]
        p += 1
        n = 0
        if op >= 128:
            if p + 2 > len(code):
                raise Unsupported("Truncated action header")
            n = struct.unpack_from("<H", code, p)[0]
            p += 2
        end = p + n
        if end > len(code):
            raise Unsupported("Truncated action payload")
        data = code[p:end]
        body = b""
        name = ""
        params = []
        if op == 0x9B:
            name, q = cstring(data, 0)
            if q + 2 > len(data):
                raise Unsupported("Function parameter count")
            count = struct.unpack_from("<H", data, q)[0]
            q += 2
            for _ in range(count):
                x, q = cstring(data, q)
                params.append(x)
            if q + 2 != len(data):
                raise Unsupported("Function metadata shape")
            size = struct.unpack_from("<H", data, q)[0]
            if end + size > len(code):
                raise Unsupported("Truncated function body")
            body = code[end : end + size]
            end += size
        out.append(Action(start, op, data, end, body, name, tuple(params)))
        p = end
        if op == 0:
            if p != len(code):
                raise Unsupported("Trailing bytes after action terminator")
            break
    return out


def constant_pool(data):
    if len(data) < 2:
        raise Unsupported("Truncated constant pool")
    count = struct.unpack_from("<H", data)[0]
    p = 2
    values = []
    for _ in range(count):
        value, p = cstring(data, p)
        values.append(value)
    if p != len(data):
        raise Unsupported("Constant pool trailing data")
    return values


class Machine:
    def __init__(
        self,
        root=None,
        scope=None,
        pool=(),
        random_values=(),
        max_steps=100000,
        unbound_to_root=False,
    ):
        self.unbound_to_root = unbound_to_root
        self.root = root if root is not None else Obj()
        self.scope = scope if scope is not None else self.root
        self.pool = list(pool)
        self.random_values = iter(random_values)
        self.events = []
        self.steps = 0
        self.max_steps = max_steps
        self.registers = {}
        self.pc = None

    def getvar(self, name):
        name = string(name)
        if name.lower() == "_root":
            return self.root
        parts = name.split(".")
        if len(parts) > 1:
            v = self.getvar(parts[0])
            for k in parts[1:]:
                v = getmember(v, k)
            return v
        v = self.scope[name]
        return self.root[name] if v is UNDEFINED else v

    def setvar(self, name, value, local=False):
        name = string(name)
        parts = name.split(".")
        if len(parts) > 1:
            obj = self.getvar(".".join(parts[:-1]))
            setmember(obj, parts[-1], value)
        elif local or name.lower() in self.scope:
            self.scope[name] = value
        else:
            (self.root if self.unbound_to_root else self.scope)[name] = value

    def call(self, obj, name, args):
        name = string(name).lower()
        if obj is None:
            if name == "number" and len(args) == 1:
                return number(args[0])
            if name == "int" and len(args) == 1:
                return integer32(args[0])
            raise Unsupported("Native function denied: " + name)
        if obj is self.root:
            if name == "playsound" and len(args) == 1 and isinstance(args[0], str):
                self.events.append(["sound", args[0]])
                return UNDEFINED
            if name == "copymovie" and len(args) == 5:
                base, instance, *_ = args
                if not isinstance(instance, str) or not instance.startswith("mt_"):
                    raise Unsupported("Display stub instance")
                obj[instance] = Obj(
                    {"_xscale": 100, "_yscale": 100, "MT": Obj(), "bkground": Obj()}
                )
                self.events.append(["displayCreate", base, instance])
                return UNDEFINED
            if name == "delmovie" and len(args) == 1:
                self.events.append(["displayDelete", string(args[0])])
                return UNDEFINED
        if isinstance(obj, Obj) and name in [
            "gotoandplay",
            "gotoandstop",
            "play",
            "stop",
        ]:
            self.events.append(["displayMethod", name, *args])
            return UNDEFINED
        raise Unsupported("Method dispatch denied: " + name)

    def program(self, code):
        return actions(code)

    def next_frame(self):
        raise Unsupported('Unreviewed NextFrame timeline control')

    def run(self, code, stop_before_date=False):
        program = self.program(code)
        by_offset = {a.offset: a for a in program}
        stack = []
        pc = 0

        def pop():
            if not stack:
                raise Unsupported("Stack underflow")
            return stack.pop()

        def args(n):
            if not isinstance(n, (int, float)) or n != int(n) or not 0 <= n <= 1024:
                raise Unsupported("Argument count")
            return [pop() for _ in range(int(n))]

        while pc < len(code):
            if pc not in by_offset:
                raise Unsupported("Branch into action payload")
            a = by_offset[pc]
            pc = a.end
            op = a.opcode
            d = a.data
            self.pc = a.offset
            self.steps += 1
            if self.steps > self.max_steps or len(stack) > 1024:
                raise Unsupported("Execution budget")
            if op == 0:
                break
            if op == 0x88:
                self.pool = constant_pool(d)
            elif op == 0x96:
                p = 0
                while p < len(d):
                    kind = d[p]
                    p += 1
                    if kind == 0:
                        v, p = cstring(d, p)
                    elif kind == 1:
                        v = struct.unpack_from("<f", d, p)[0]
                        p += 4
                    elif kind == 2:
                        v = None
                    elif kind == 3:
                        v = UNDEFINED
                    elif kind == 4:
                        v = self.registers.get(d[p], UNDEFINED)
                        p += 1
                    elif kind == 5:
                        v = bool(d[p])
                        p += 1
                    elif kind == 6:
                        raw = d[p : p + 8]
                        if len(raw) != 8:
                            raise Unsupported("Truncated double")
                        v = struct.unpack("<d", raw[4:] + raw[:4])[0]
                        p += 8
                    elif kind == 7:
                        v = struct.unpack_from("<i", d, p)[0]
                        p += 4
                    elif kind in [8, 9]:
                        index = d[p] if kind == 8 else struct.unpack_from("<H", d, p)[0]
                        p += 1 if kind == 8 else 2
                        if index >= len(self.pool):
                            raise Unsupported("Constant pool index")
                        v = self.pool[index]
                    else:
                        raise Unsupported("Push type " + str(kind))
                    stack.append(v)
            elif op == 0x1C:
                stack.append(self.getvar(pop()))
            elif op in [0x1D, 0x3C]:
                v = pop()
                name = pop()
                self.setvar(name, v, local=op == 0x3C)
            elif op == 0x04:
                self.next_frame()
            elif op == 0x22:
                index = integer32(pop())
                target = pop()
                if target != "" or index != 4:
                    raise Unsupported("Only current-scope _currentframe GetProperty is reviewed")
                stack.append(self.scope["_currentframe"])
            elif op == 0x4E:
                key = pop()
                obj = pop()
                stack.append(getmember(obj, key))
            elif op == 0x4F:
                v = pop()
                key = pop()
                obj = pop()
                setmember(obj, key, v)
            elif op == 0x17:
                pop()
            elif op == 0x4C:
                if not stack:
                    raise Unsupported("Duplicate on empty stack")
                stack.append(stack[-1])
            elif op == 0x4D:
                x = pop()
                y = pop()
                stack.extend([x, y])
            elif op == 0x87:
                if len(d) != 1 or not stack:
                    raise Unsupported("StoreRegister shape")
                self.registers[d[0]] = stack[-1]
            elif op == 0x12:
                stack.append(not truth(pop()))
            elif op == 0x4A:
                stack.append(number(pop()))
            elif op == 0x18:
                stack.append(integer32(pop()))
            elif op in [0x50, 0x51]:
                stack.append(number(pop()) + (1 if op == 0x50 else -1))
            elif op in [
                0x0A,
                0x0B,
                0x0C,
                0x0D,
                0x0E,
                0x0F,
                0x10,
                0x11,
                0x21,
                0x3F,
                0x47,
                0x48,
                0x49,
                0x66,
                0x67,
            ]:
                b = pop()
                a0 = pop()
                if (
                    op == 0x21
                    or op == 0x47
                    and (isinstance(a0, str) or isinstance(b, str))
                ):
                    v = string(a0) + string(b)
                elif op in [0x0E, 0x49, 0x66]:
                    v = (
                        (a0 == b)
                        if type(a0) == type(b) or a0 is UNDEFINED or b is UNDEFINED
                        else number(a0) == number(b)
                    )
                    if op == 0x66:
                        numeric = lambda x: isinstance(
                            x, (int, float)
                        ) and not isinstance(x, bool)
                        if not (numeric(a0) and numeric(b)) and type(a0) != type(b):
                            v = False
                elif op == 0x10:
                    v = truth(a0) and truth(b)
                elif op == 0x11:
                    v = truth(a0) or truth(b)
                else:
                    aa, bb = number(a0), number(b)
                    if op in [0x0A, 0x47]:
                        v = aa + bb
                    elif op == 0x0B:
                        v = aa - bb
                    elif op == 0x0C:
                        v = aa * bb
                    elif op == 0x0D:
                        v = (
                            aa / bb
                            if bb != 0
                            else (
                                math.nan
                                if aa == 0
                                else math.copysign(math.inf, aa * math.copysign(1, bb))
                            )
                        )
                    elif op == 0x3F:
                        v = math.fmod(aa, bb)
                    elif op in [0x0F, 0x48]:
                        v = aa < bb
                    elif op == 0x67:
                        v = aa > bb
                stack.append(v)
            elif op in [0x99, 0x9D]:
                if len(d) != 2:
                    raise Unsupported("Branch shape")
                if op == 0x99 or truth(pop()):
                    target = pc + struct.unpack("<h", d)[0]
                    if target not in by_offset and target != len(code):
                        raise Unsupported("Invalid jump target")
                    pc = target
            elif op == 0x30:
                maximum = number(pop())
                if maximum != 200:
                    raise Unsupported("Unexpected random range")
                try:
                    v = next(self.random_values)
                except StopIteration:
                    raise Unsupported("Random tape exhausted")
                if not isinstance(v, int) or not 0 <= v < maximum:
                    raise Unsupported("Random value out of range")
                stack.append(v)
                self.events.append(["random", int(maximum), v])
            elif op == 0x52:
                name = pop()
                obj = pop()
                count = pop()
                stack.append(self.call(obj, name, args(count)))
            elif op == 0x3D:
                name = pop()
                count = pop()
                stack.append(self.call(None, name, args(count)))
            elif op == 0x40:
                name = pop()
                count = pop()
                if string(name) == "Date" and stop_before_date:
                    return {
                        "reason": "stopped before unmodelled Date constructor",
                        "pc": a.offset,
                        "steps": self.steps,
                    }
                values = args(count)
                if name != "Array":
                    raise Unsupported("Constructor denied: " + string(name))
                if len(values) == 1 and isinstance(values[0], (int, float)):
                    n = number(values[0])
                    if n != int(n) or not 0 <= n <= 10000:
                        raise Unsupported("Array allocation limit")
                    stack.append([UNDEFINED] * int(n))
                else:
                    stack.append(values)
            elif op == 0x81:
                if len(d) != 2:
                    raise Unsupported("GotoFrame shape")
                self.events.append(["goto", struct.unpack("<H", d)[0] + 1])
            elif op == 0x06:
                self.events.append(["play"])
            elif op == 0x07:
                self.events.append(["stop"])
            elif op == 0x3E:
                return {"reason": "return", "value": pop(), "steps": self.steps}
            else:
                raise Unsupported(f"Opcode 0x{op:02x} denied at {a.offset}")
        if stack:
            raise Unsupported("Nonempty stack at section end")
        return {"reason": "end", "steps": self.steps}
