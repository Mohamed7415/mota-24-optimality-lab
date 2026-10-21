import fs from "node:fs";
import path from "node:path";
import { parse } from "acorn";
import { walk, literal, member, readSource, sha } from "./import.mjs";
export function differences(a, b, p = "$", out = []) {
  if (JSON.stringify(a) === JSON.stringify(b)) return out;
  if (a && b && typeof a === "object" && typeof b === "object") {
    for (const k of new Set([...Object.keys(a), ...Object.keys(b)]))
      differences(a[k], b[k], p + "/" + k, out);
  } else
    out.push({
      path: p,
      readableHash: sha(JSON.stringify(a) ?? "undefined"),
      deployedHash: sha(JSON.stringify(b) ?? "undefined"),
      readableType: typeof a,
      deployedType: typeof b,
    });
  return out;
}
export function audit(t, root) {
  let floors = {};
  for (const id of t.floorIds) {
    const f = t.floors[id].data;
    let counts = {};
    for (const row of f.map)
      for (const tile of row) {
        let id = t.tiles[parseInt(tile)]?.data?.id ?? "empty";
        counts[id] = (counts[id] ?? 0) + 1;
      }
    floors[id] = {
      mapHash: sha(JSON.stringify(f.map)),
      objectHash: sha(JSON.stringify(f)),
      tileCounts: counts,
      eventsHash: sha(
        JSON.stringify({
          events: f.events,
          firstArrive: f.firstArrive,
          changeFloor: f.changeFloor,
          afterBattle: f.afterBattle,
          afterGetItem: f.afterGetItem,
          afterOpenDoor: f.afterOpenDoor,
          cannotMove: f.cannotMove,
        }),
      ),
      provenance: t.floors[id].provenance,
    };
  }
  let changed = [];
  for (const v of t.validation.parity.filter(
    (x) => x.representationEqual === false,
  )) {
    let id = v.component;
    if (!t.floors[id]) continue;
    let u = readSource(root, `libs/floors/${id}.js`),
      raw;
    walk(u.ast, (n) => {
      if (
        n.type === "AssignmentExpression" &&
        member(n.left) === "main.floors." + id
      )
        raw = literal(n.right, u.source);
    });
    changed.push({
      floorId: id,
      readableFile: u.file,
      deployedFile: t.floors[id].provenance.file,
      normalizedAstEqual: v.equal,
      differences: differences(raw, t.floors[id].data),
    });
  }
  let eventTypes = {};
  let opaque = 0;
  walkJson(t, (v) => {
    if (v?.$opaque) opaque++;
  });
  for (const x of Object.values(t.floors)) {
    walkJson(x.data, (v) => {
      if (v && typeof v === "object" && typeof v.type === "string")
        eventTypes[v.type] = (eventTypes[v.type] ?? 0) + 1;
    });
  }
  return {
    schemaVersion: 1,
    upstream: t.upstream,
    sourceFiles: t.sourceFiles,
    counts: {
      floorObjects: t.floorIds.length,
      declaredEnemyDefinitions: Object.keys(t.enemies.data).length,
      declaredItemDefinitions: Object.keys(t.items.data).length,
      usedTileIds: t.validation.usedTileIds.length,
      opaqueFunctionEvidence: opaque,
    },
    floors,
    enemyFactsHash: sha(JSON.stringify(t.enemies.data)),
    itemDefinitionsHash: sha(JSON.stringify(t.items.data)),
    valuesHash: sha(JSON.stringify(t.config.values.data)),
    parity: t.validation.parity,
    readableDeployedDifferences: changed,
    eventTypes,
    originalFlashEquivalence: {
      status: "not established",
      reason:
        "Separate Flash fingerprint and rule evidence required; remake includes intentional behavior changes.",
    },
  };
}
function walkJson(v, fn) {
  fn(v);
  if (Array.isArray(v)) v.forEach((x) => walkJson(x, fn));
  else if (v && typeof v === "object")
    Object.values(v).forEach((x) => walkJson(x, fn));
}
if (process.argv[1] && process.argv[1].endsWith("audit.mjs")) {
  let [data, root, out = "experiments/remake-baseline.json"] =
    process.argv.slice(2);
  let t = JSON.parse(fs.readFileSync(data));
  let a = audit(t, root);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(a, null, 2) + "\n");
  console.log(
    JSON.stringify(
      { counts: a.counts, changed: a.readableDeployedDifferences },
      null,
      2,
    ),
  );
}
