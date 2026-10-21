"""Identify pinned SWF action sections by tag/frame. Extract only; never run."""

import collections, hashlib, struct, sys, zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from avm1 import actions, constant_pool
from inspect_swf import Bits, tags

SWF_SHA = "04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9"


def sections(filename):
    original = Path(filename).read_bytes()
    if hashlib.sha256(original).hexdigest() != SWF_SHA:
        raise ValueError("Unpinned original SWF")
    b = original[:8] + zlib.decompress(original[8:])
    r = Bits(b, 8)
    r.rect()
    frame = collections.defaultdict(lambda: 1)
    blocks = []
    for code, p, n, off, parent in tags(b, r.pos + 4, len(b)):
        if code == 12:
            blocks.append(
                {
                    "parent": parent,
                    "frame": frame[parent],
                    "tagOffset": off,
                    "dataOffset": p,
                    "bytes": b[p : p + n],
                    "sha256": hashlib.sha256(b[p : p + n]).hexdigest(),
                }
            )
        if code == 1:
            frame[parent] += 1
    selected = {}
    for block in blocks:
        if block["parent"] == "root/sprite:453":
            selected["combat" + str(block["frame"])] = block
        if block["parent"] == "root" and block["frame"] == 4346:
            aa = actions(block["bytes"])
            if any(a.name == "Move_arrow" for a in aa):
                pool = []
                for a in aa:
                    if a.opcode == 0x88:
                        pool = constant_pool(a.data)
                    if a.name in ["Move_arrow", "SetLineDisplay"]:
                        selected[a.name] = {
                            **block,
                            "bytes": a.body,
                            "pool": pool.copy(),
                            "sha256": hashlib.sha256(a.body).hexdigest(),
                            "functionOffset": a.offset,
                            "bodyDataOffset": block["dataOffset"] + a.end - len(a.body),
                            "parameters": a.parameters,
                        }
            elif any(
                a.opcode == 0x88 and "mt_line_00" in constant_pool(a.data) for a in aa
            ):
                selected["initialData"] = block
        if block["parent"] == "root/sprite:855" and block["frame"] == 1:
            selected["worldTick"] = block
    if not all(
        k in selected
        for k in [
            "combat1",
            "combat24",
            "combat34",
            "combat35",
            "combat54",
            "Move_arrow",
            "SetLineDisplay",
            "initialData",
            "worldTick",
        ]
    ):
        raise ValueError("Missing pinned sections")
    return selected


def metadata(s):
    return {
        k: {x: v for x, v in b.items() if x not in ["bytes", "pool"]}
        for k, b in s.items()
    }


if __name__ == "__main__":
    import json

    s = sections(sys.argv[1])
    print(json.dumps(metadata(s), indent=2))
