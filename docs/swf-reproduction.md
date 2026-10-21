# Reproduce static Flash evidence

The remake CI jobs do not download Flash resources. The M4 original-flash job
downloads the pinned file transiently and publishes numerical evidence only.
These commands reproduce the M3 static evidence locally. A changed hash is an error, not a new version label.

```sh
python3 tools/fetch_swf.py mhhf
python3 tools/inspect_swf.py generated/private/mhhf.swf \
  --url https://www.mhhf.com/files/game/5478/mota24.swf \
  --out generated/mhhf-inspection.json
python3 tools/fetch_swf.py archive
python3 tools/inspect_swf.py generated/private/archive.swf \
  --url https://swf.flash.homes/2f1681af86d28042009c7c1a43cfd9da8df20abcc598501db67175f31d87c646.swf \
  --out generated/archive-inspection.json
```

Use official [FFDec 26.4.0](https://github.com/jindrapetrik/jpexs-decompiler/releases/tag/version26.4.0)
with an installed JRE. The portable `ffdec_26.4.0.zip` must have SHA256
`56ce960aeafc7caf034e2052ba49f878a883f7c7ca690da6eeffca9587b5e4b9`.
Replace `/path/to/ffdec.jar` with its location. This is static decompilation and
vector rendering, never game/ActionScript execution.

```sh
java -Djava.awt.headless=true -jar /path/to/ffdec.jar \
  -export script,text generated/mhhf-export generated/private/mhhf.swf
java -Djava.awt.headless=true -jar /path/to/ffdec.jar \
  -format shape:png -export shape generated/mhhf-shapes generated/private/mhhf.swf
python3 tools/flash_audit.py generated/mhhf-export/scripts \
  generated/tower.json generated/mhhf-inspection.json \
  --facts generated/flash-mhhf-facts.json --out generated/flash-mhhf-baseline.json
```

Visually inspect `generated/mhhf-shapes/455.png`: `(Ver 1.12)` is part of
DefineShape character 455, not a plain-text string. Container format version 6
is a separate field. The shape tag begins at decompressed byte 227277; its
full-tag SHA256 is recorded in `experiments/swf-evidence.json`.

Compare the generated baseline with `experiments/flash-mhhf-baseline.json`.
Repeat with candidate `archive`; its unversioned title is shape 374 and its
recognized map set contains 22 maps, not the selected 27-map v1.12 candidate.
The AS2 numeric extractor uses strict patterns for numeric arrays, and never
executes expressions or decompiled code.

The pure Python SWF inspector does not decode shape outlines into text. Its
`internalVersionConclusion: unverified` is intentionally conservative; the
independent FFDec rendering and visual observation supply the version evidence.
Neither method establishes an authenticated original-author release chain.
