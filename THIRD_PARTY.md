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
upstream JS into ignored `vendor/`; no upstream JS build or game script is run.
M4 interprets selected original AVM1 sections in a bounded data-only test machine
as documented in `docs/flash-M4-reproduction.md`. The remake CI jobs upload only
numerical MT1 results. The original-flash CI job
downloads the pinned public SWF into the ignored runner directory, checks its hash,
and uploads only numerical M4 evidence. Full data and downloaded assets are never
committed or uploaded as CI artifacts.

A self-reported in-game version does not independently prove that an archived
file is an untouched author release. Exact byte identity is the research target.

M5 additionally uses the official [Ruffle 0.7.1 release](https://github.com/ruffle-rs/ruffle/releases/tag/v0.7.1)
(MIT OR Apache-2.0) as a downloaded local WebAssembly player, not bundled here.
The Python/C RNG ports derive from `core/src/avm_rng.rs` under the MIT option;
its copyright and permission notice is preserved in `third_party/RUFFLE-LICENSE-MIT`.
Release/source URLs, SHA256s, and per-file hashes appear in `experiments/ruffle-release.json`.
Playwright 1.62.1 (Apache-2.0) is installed from the lockfile; Chromium is downloaded
by Playwright. Neither browser nor player binaries are committed.
M5 generated fixture movies contain selected original numeric action bodies and
remain ignored locally. CI uploads only `generated/M5/ruffle-M5.json`, never these
movies, game assets, decompiler exports, browser profiles, or original dialogue.

M6 intentionally executes the complete pinned original SWF in Ruffle for one
menu-to-MT2 route, using normal DOM mouse/keyboard input. A lab-written parent
movie reads numeric variables only, with `_lockroot` preserving the child's root.
An independent control loads the byte-identical original directly without that
parent and compares numeric HUD regions locally. Screenshots, original movies,
private map plans, browser storage, and generated movies are ignored and never
included in public artifacts. Only numeric traces/checkpoints, hashes, input
order and model results enter `experiments/whole-game-M6.json`. The remake's
upstream JavaScript is still parsed statically and never executed.

M7 extends the same untouched-movie replay through floors 1–3 and actual shop
purchase/return. Six shop functions are statically extracted with provenance and
run in local numeric fixtures; only boundary-case numbers and hashes are public.
Original shop dialogue, frame bytecode, fixture SWFs, screenshots and full map
plans remain ignored. The MIT lab's pure shop rules and decreasing-resource proof
do not relicense upstream game content. CI uploads numerical M7 evidence only.
