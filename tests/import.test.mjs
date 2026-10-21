import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { parse } from "acorn";
import { literal, normalize } from "../src/import.mjs";
function expr(s) {
  return parse("(" + s + ")", { ecmaVersion: 2020 }).body[0].expression;
}
test("reject arbitrary execution, computed properties, duplicates and prototype keys", () => {
  for (const code of [
    "evil()",
    "new Evil()",
    "{[evil()]:1}",
    "{x:1,x:2}",
    "{__proto__:1}",
    "{x:getter()}",
    "[evil()]",
  ])
    assert.throws(() => literal(expr(code), code));
});
test("fold numeric fractions without eval and preserve opaque functions", () => {
  assert.equal(literal(expr("1/3"), "1/3"), 1 / 3);
  assert.equal(literal(expr("-1"), "-1"), -1);
  let f = expr('function(){throw Error("do not run")}');
  assert.equal(
    literal(f, '(function(){throw Error("do not run")})').$opaque,
    "function",
  );
});
test("function normalization ignores formatting only", () => {
  const a = "(function(){core.enemys.update();})",
    b = "(function(){core.enemys.update()})",
    c = "(function(){core.enemys.reset()})";
  assert.deepEqual(
    normalize(literal(expr(a.slice(1, -1)), a)),
    normalize(literal(expr(b.slice(1, -1)), b)),
  );
  assert.notDeepEqual(
    normalize(literal(expr(a.slice(1, -1)), a)),
    normalize(literal(expr(c.slice(1, -1)), c)),
  );
});
test("pinned real source baseline and minified data match", () => {
  let t = JSON.parse(fs.readFileSync("generated/tower.json")),
    actual = JSON.parse(fs.readFileSync("generated/remake-baseline.json")),
    expected = JSON.parse(fs.readFileSync("experiments/remake-baseline.json"));
  assert.equal(t.floorIds.length, 27);
  assert.equal(t.enemies.data.greenSlime.hp, 50);
  assert.equal(t.items.data.superPotion.cls, "items");
  assert.ok(t.validation.parity.every((x) => x.equal));
  assert.deepEqual(actual, expected);
  assert.deepEqual(t.validation.unmapped, []);
});
