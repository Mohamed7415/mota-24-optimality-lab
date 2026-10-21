import fs from "node:fs";
import { execFileSync } from "node:child_process";
import { COMMIT } from "../src/import.mjs";
const root = process.argv[2] ?? "vendor/MagicTower";
if (!fs.existsSync(root)) {
  fs.mkdirSync("vendor", { recursive: true });
  execFileSync(
    "git",
    [
      "clone",
      "--no-checkout",
      "https://github.com/arcxingye/MagicTower.git",
      root,
    ],
    { stdio: "inherit" },
  );
  execFileSync("git", ["-C", root, "checkout", "--detach", COMMIT], {
    stdio: "inherit",
  });
}
execFileSync(
  process.execPath,
  ["src/import.mjs", root, "generated/tower.json"],
  { stdio: "inherit" },
);
execFileSync(
  process.execPath,
  [
    "src/audit.mjs",
    "generated/tower.json",
    root,
    "generated/remake-baseline.json",
  ],
  { stdio: "inherit" },
);
