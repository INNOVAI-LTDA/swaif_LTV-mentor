import assert from "node:assert/strict";

import {
  safeProgressPercent,
  deriveCommandCenterKpis,
  resolveSelectedStudentId,
} from "../../lib/commandCenterUtils.js";

function run(name, fn) {
  try {
    fn();
    console.log(`PASS - ${name}`);
  } catch (error) {
    console.error(`FAIL - ${name}`);
    console.error(error?.stack || String(error));
    process.exitCode = 1;
  }
}

run("safeProgressPercent uses day/totalDays when available", () => {
  assert.equal(safeProgressPercent({ day: 45, totalDays: 90, progress: 0.1 }), 50);
});

run("safeProgressPercent falls back to progress when totalDays is missing", () => {
  assert.equal(safeProgressPercent({ day: 0, totalDays: 0, progress: 0.68 }), 68);
});

run("safeProgressPercent handles invalid numeric values", () => {
  assert.equal(safeProgressPercent({ day: "x", totalDays: "y", progress: "0.25" }), 25);
});

run("deriveCommandCenterKpis computes active alerts and d45", () => {
  const kpis = deriveCommandCenterKpis([
    { id: "s1", urgency: "rescue", daysLeft: 20 },
    { id: "s2", urgency: "watch", daysLeft: 60 },
    { id: "s3", urgency: "normal", daysLeft: 45 },
    { id: "s4", urgency: "normal" },
  ]);

  assert.deepEqual(kpis, { active: 4, alerts: 1, d45: 2 });
});

run("resolveSelectedStudentId keeps selected when present", () => {
  const selected = resolveSelectedStudentId(
    [{ id: "std_1" }, { id: "std_2" }],
    "std_2"
  );
  assert.equal(selected, "std_2");
});

run("resolveSelectedStudentId falls back to first item", () => {
  const selected = resolveSelectedStudentId(
    [{ id: "std_1" }, { id: "std_2" }],
    "missing"
  );
  assert.equal(selected, "std_1");
});

run("resolveSelectedStudentId returns null for empty list", () => {
  assert.equal(resolveSelectedStudentId([], "std_1"), null);
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F2 command center runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F2 command center runner: PASS");
