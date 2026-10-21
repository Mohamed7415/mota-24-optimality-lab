import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import { parse } from "acorn";
import { pathToFileURL } from "node:url";
export const COMMIT = "3bcfcc3e6dc082e8fef8ef9e62c0b70cb55d7ef9";
export const sha = (s) => crypto.createHash("sha256").update(s).digest("hex");
export function walk(n, fn) {
  if (!n || typeof n !== "object") return;
  if (n.type) fn(n);
  for (const [k, v] of Object.entries(n))
    if (k !== "loc") {
      if (Array.isArray(v)) v.forEach((x) => walk(x, fn));
      else if (v && typeof v === "object") walk(v, fn);
    }
}
export function member(n) {
  if (n.type === "ThisExpression") return "this";
  if (n.type === "Identifier") return n.name;
  if (n.type === "MemberExpression")
    return (
      member(n.object) + "." + (n.computed ? n.property.value : n.property.name)
    );
  return "";
}
function cleanAst(v) {
  if (Array.isArray(v)) return v.map(cleanAst);
  if (v && typeof v === "object")
    return Object.fromEntries(
      Object.entries(v)
        .filter(([k]) => !["start", "end", "loc", "raw"].includes(k))
        .map(([k, x]) => [k, cleanAst(x)]),
    );
  return v;
}
export function normalize(v) {
  if (v?.$opaque === "function")
    return { $opaque: "function", astSha256: v.astSha256 };
  if (Array.isArray(v)) return v.map(normalize);
  if (v && typeof v === "object")
    return Object.fromEntries(
      Object.entries(v).map(([k, x]) => [k, normalize(x)]),
    );
  return v;
}
export function literal(n, source) {
  if (n.type === "Literal") {
    if (n.regex) throw Error("Regex is not data");
    return n.value;
  }
  if (n.type === "ArrayExpression")
    return n.elements.map((x) => {
      if (!x) throw Error("Array hole");
      return literal(x, source);
    });
  if (n.type === "ObjectExpression") {
    let o = {};
    for (const p of n.properties) {
      if (p.type !== "Property" || p.computed || p.kind !== "init" || p.method)
        throw Error("Dynamic property");
      const k = p.key.name ?? p.key.value;
      if (["__proto__", "constructor", "prototype"].includes(k))
        throw Error("Unsafe key");
      if (Object.hasOwn(o, k)) throw Error("Duplicate key " + k);
      o[k] = literal(p.value, source);
    }
    return o;
  }
  if (n.type === "UnaryExpression" && ["+", "-", "!"].includes(n.operator)) {
    let v = literal(n.argument, source);
    return n.operator === "-" ? -v : n.operator === "+" ? +v : !v;
  }
  if (
    n.type === "BinaryExpression" &&
    ["/", "*", "+", "-"].includes(n.operator)
  ) {
    let a = literal(n.left, source),
      b = literal(n.right, source);
    if (typeof a !== "number" || typeof b !== "number")
      throw Error("Non numeric arithmetic");
    let v = {
      "/": () => a / b,
      "*": () => a * b,
      "+": () => a + b,
      "-": () => a - b,
    }[n.operator]();
    if (!Number.isFinite(v)) throw Error("Nonfinite");
    return v;
  }
  // Opaque function bodies are evidence, NEVER invoked.
  if (["FunctionExpression", "ArrowFunctionExpression"].includes(n.type))
    return {
      $opaque: "function",
      sha256: sha(source.slice(n.start, n.end)),
      astSha256: sha(JSON.stringify(cleanAst(n))),
      source: source.slice(n.start, n.end),
    };
  throw Error("Unsupported data syntax: " + n.type);
}
export function readSource(root, file) {
  let source = fs.readFileSync(path.join(root, file), "utf8");
  return {
    source,
    ast: parse(source, { ecmaVersion: 2020, locations: true }),
    file,
    hash: sha(source),
  };
}
export function provenance(unit, n) {
  return {
    file: unit.file,
    sha256: unit.hash,
    startLine: n.loc.start.line,
    endLine: n.loc.end.line,
    startOffset: n.start,
    endOffset: n.end,
    url: `https://github.com/arcxingye/MagicTower/blob/${COMMIT}/${unit.file}#L${n.loc.start.line}`,
  };
}
function assignments(u) {
  let out = new Map();
  walk(u.ast, (n) => {
    if (n.type === "AssignmentExpression" && n.operator === "=") {
      let name = member(n.left);
      if (
        /^(main\.floors\.|this\.(firstData|values|flags|enemys|items|floorIds|useCompress|version)$)/.test(
          name,
        )
      ) {
        if (out.has(name)) throw Error("Duplicate assignment " + name);
        out.set(name, {
          data: literal(n.right, u.source),
          provenance: provenance(u, n.right),
        });
      }
    }
  });
  return out;
}
export function importTower(root) {
  const head = execFileSync("git", ["-C", root, "rev-parse", "HEAD"], {
    encoding: "utf8",
  }).trim();
  if (head !== COMMIT) throw Error("Unpinned commit " + head);
  // Dirty checked-in JS would break commit provenance. Ignore untracked files.
  if (
    execFileSync(
      "git",
      ["-C", root, "status", "--porcelain", "--untracked-files=no"],
      { encoding: "utf8" },
    ).trim()
  )
    throw Error("Dirty upstream checkout");
  let sources = {},
    units = {};
  function unit(f) {
    if (!units[f]) {
      units[f] = readSource(root, f);
      sources[f] = units[f].hash;
    }
    return units[f];
  }
  let main = assignments(unit("main.js"));
  let floorIds = main.get("this.floorIds").data;
  let compressed = main.get("this.useCompress").data;
  let rawFloors = new Map();
  for (const id of floorIds) {
    for (const [k, v] of assignments(unit(`libs/floors/${id}.js`)))
      rawFloors.set(k, v);
  }
  let minFloors = assignments(unit("libs/floors.min.js"));
  let floors = {};
  let parity = [];
  for (const id of floorIds) {
    let key = "main.floors." + id;
    let raw = rawFloors.get(key),
      min = minFloors.get(key);
    if (!raw || !min) throw Error("Missing floor " + id);
    let eq =
      JSON.stringify(normalize(raw.data)) ===
      JSON.stringify(normalize(min.data));
    parity.push({
      component: id,
      equal: eq,
      representationEqual:
        JSON.stringify(raw.data) === JSON.stringify(min.data),
      readableHash: sha(JSON.stringify(raw.data)),
      deployedHash: sha(JSON.stringify(min.data)),
    });
    floors[id] = compressed ? min : raw;
    let f = floors[id].data;
    if (
      f.floorId !== id ||
      f.map.length !== 13 ||
      f.map.some((r) => r.length !== 13)
    )
      throw Error("Invalid floor " + id);
  }
  let config = {},
    enemies,
    items;
  for (const [file, names] of [
    ["data", ["firstData", "values", "flags"]],
    ["enemys", ["enemys"]],
    ["items", ["items"]],
  ]) {
    let raw = assignments(unit("libs/" + file + ".js")),
      min = assignments(unit("libs/" + file + ".min.js"));
    for (const name of names) {
      let a = raw.get("this." + name),
        b = min.get("this." + name);
      if (!a || !b) throw Error("Missing " + name);
      parity.push({
        component: name,
        equal:
          JSON.stringify(normalize(a.data)) ===
          JSON.stringify(normalize(b.data)),
        representationEqual: JSON.stringify(a.data) === JSON.stringify(b.data),
        readableHash: sha(JSON.stringify(a.data)),
        deployedHash: sha(JSON.stringify(b.data)),
      });
      let entry = compressed ? b : a;
      if (name === "enemys") enemies = entry;
      else if (name === "items") items = entry;
      else config[name] = entry;
    }
  }
  let mapUnit = unit(compressed ? "libs/maps.min.js" : "libs/maps.js");
  unit("libs/maps.js");
  let tiles = {};
  let blockFn;
  walk(mapUnit.ast, (n) => {
    if (
      n.type === "AssignmentExpression" &&
      member(n.left) === "maps.prototype.getBlock"
    )
      blockFn = n.right;
  });
  if (!blockFn) throw Error("Missing getBlock");
  let idVar = blockFn.params[2].name;
  let eventVar;
  walk(blockFn, (n) => {
    if (
      n.type === "VariableDeclarator" &&
      n.init?.type === "ObjectExpression" &&
      n.init.properties.some(
        (p) =>
          (p.key.name ?? p.key.value) === "id" && member(p.value) === idVar,
      )
    )
      eventVar = n.id.name;
  });
  walk(blockFn, (n) => {
    if (
      n.type !== "IfStatement" ||
      n.test.type !== "BinaryExpression" ||
      !["==", "==="].includes(n.test.operator) ||
      member(n.test.left) !== idVar ||
      n.test.right.type !== "Literal" ||
      typeof n.test.right.value !== "number"
    )
      return;
    let c = n.consequent;
    if (c.type === "BlockStatement" && c.body.length === 1) c = c.body[0];
    if (
      c.type === "ExpressionStatement" &&
      c.expression.type === "AssignmentExpression" &&
      member(c.expression.left) === eventVar + ".event"
    )
      tiles[n.test.right.value] = {
        data: literal(c.expression.right, mapUnit.source),
        provenance: provenance(mapUnit, c.expression.right),
      };
  });
  let used = new Set();
  for (const f of Object.values(floors))
    for (const r of f.data.map) for (const v of r) used.add(parseInt(v));
  let unmapped = [...used].filter((x) => x !== 0 && !tiles[x]);
  if (unmapped.length) throw Error("Unmapped tile IDs " + unmapped);
  let missingEnemies = [...used].filter(
    (x) => tiles[x]?.data.cls === "enemys" && !enemies.data[tiles[x].data.id],
  );
  if (missingEnemies.length) throw Error("Missing enemies");
  let mechanics = {};
  for (const file of ["libs/items.js", "libs/enemys.js", "libs/events.js"]) {
    let u = unit(file);
    walk(u.ast, (n) => {
      if (
        n.type === "AssignmentExpression" &&
        n.right.type === "FunctionExpression"
      )
        mechanics[member(n.left)] = {
          data: literal(n.right, u.source),
          provenance: provenance(u, n.right),
        };
    });
  }
  return {
    schemaVersion: 1,
    upstream: {
      repository: "https://github.com/arcxingye/MagicTower",
      commit: head,
      useCompress: compressed,
      version: main.get("this.version").data,
      redistribution:
        "No upstream license found; full derived data remains local and untracked.",
    },
    sourceFiles: sources,
    floorIds,
    floors,
    tiles,
    enemies,
    items,
    config,
    mechanics,
    validation: {
      usedTileIds: [...used].sort((a, b) => a - b),
      unmapped,
      parity,
    },
    limitations: [
      "Static extraction only; strings and opaque functions are not executed.",
      "Events and functions are preserved as evidence, not a complete simulator.",
      "Readable/minified divergence must be audited; deployed data selected by main.useCompress.",
    ],
  };
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const [root, out = "generated/tower.json"] = process.argv.slice(2);
  if (!root) throw Error("Usage: node src/import.mjs UPSTREAM_DIR [OUTPUT]");
  let t = importTower(root);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(t, null, 2) + "\n");
  console.log(
    JSON.stringify(
      {
        floors: t.floorIds.length,
        enemies: Object.keys(t.enemies.data).length,
        items: Object.keys(t.items.data).length,
        tiles: Object.keys(t.tiles).length,
        parityDifferences: t.validation.parity.filter((x) => !x.equal),
      },
      null,
      2,
    ),
  );
}
