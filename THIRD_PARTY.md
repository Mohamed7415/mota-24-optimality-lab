# Third-party sources and redistribution boundary

- [arcxingye/MagicTower](https://github.com/arcxingye/MagicTower), pinned commit
  `3bcfcc3e6dc082e8fef8ef9e62c0b70cb55d7ef9`, declares remake version 1.4.2.
  No LICENSE file was found in that checkout. The lab does not relicense it.
- [Flash 保存计划 download record](https://flash.homes/flash/5WB8-3BW6-TA04/download)
  supplies one SWF candidate, which static inspection found has only 22 map arrays.
- [MHHF record 5478](https://www.mhhf.com/game/detail/5478) supplies a different
  candidate with 27 map arrays and an embedded vector title reading Ver 1.12.
- [JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler), version 26.4.0,
  was used as an external static decompiler/renderer; it is not bundled.
- [Adobe SWF specification, version 19](https://open-flash.github.io/mirrors/swf-spec-19.pdf)
  describes the container structures inspected by `tools/inspect_swf.py`.
- `acorn` 8.15.0 is an MIT-licensed parser installed from the lockfile.

No SWF, game artwork, audio, complete dialogue or upstream game source is
committed. Public records contain facts, hashes, provenance, and numerical
experimental results. Full extracted JSON contains upstream text and opaque
function evidence, so it stays in ignored `generated/`. Reproduction fetches
upstream into ignored `vendor/`; no build or game script is run. CI uploads only
its numerical MT1 result, never the full data or downloaded assets.

A self-reported in-game version does not independently prove that an archived
file is an untouched author release. Exact byte identity is the research target.
