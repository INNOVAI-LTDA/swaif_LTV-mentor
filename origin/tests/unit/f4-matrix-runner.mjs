import assert from "node:assert/strict";

import { adaptMatrixPayload } from "../../adapters/matrixAdapter.js";
import {
  normalizeMatrixFilter,
  matrixQuadrant,
  deriveMatrixKpis,
  resolveMatrixKpis,
} from "../../lib/matrixUtils.js";

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

run("normalizeMatrixFilter accepts contract filters", () => {
  assert.equal(normalizeMatrixFilter("all"), "all");
  assert.equal(normalizeMatrixFilter("topRight"), "topRight");
  assert.equal(normalizeMatrixFilter("critical"), "critical");
  assert.equal(normalizeMatrixFilter("rescue"), "rescue");
});

run("normalizeMatrixFilter falls back to all for invalid values", () => {
  assert.equal(normalizeMatrixFilter("invalid"), "all");
  assert.equal(normalizeMatrixFilter(""), "all");
  assert.equal(normalizeMatrixFilter(null), "all");
});

run("matrixQuadrant prefers backend quadrant when provided", () => {
  assert.equal(matrixQuadrant({ quadrant: "bottomLeft", progress: 0.9, engagement: 0.9 }), "bottomLeft");
});

run("matrixQuadrant derives quadrant from progress and engagement", () => {
  assert.equal(matrixQuadrant({ progress: 0.8, engagement: 0.7 }), "topRight");
  assert.equal(matrixQuadrant({ progress: 0.4, engagement: 0.7 }), "topLeft");
  assert.equal(matrixQuadrant({ progress: 0.8, engagement: 0.3 }), "bottomRight");
  assert.equal(matrixQuadrant({ progress: 0.4, engagement: 0.3 }), "bottomLeft");
});

run("deriveMatrixKpis computes totals and counts", () => {
  const kpis = deriveMatrixKpis([
    { ltv: 10000, daysLeft: 20, progress: 0.8, engagement: 0.8, urgency: "watch" },
    { ltv: 5000, daysLeft: 80, progress: 0.4, engagement: 0.4, urgency: "rescue" },
  ]);

  assert.equal(kpis.totalLTV, 15000);
  assert.equal(kpis.criticalRenewals, 1);
  assert.equal(kpis.rescueCount, 1);
  assert.ok(Math.abs(kpis.avgEngagement - 0.6) < 1e-9);
});

run("resolveMatrixKpis keeps backend KPIs when present", () => {
  const kpis = resolveMatrixKpis(
    { totalLTV: 40000, criticalRenewals: 3, rescueCount: 2, avgEngagement: 0.74 },
    [{ ltv: 1 }]
  );

  assert.deepEqual(kpis, {
    totalLTV: 40000,
    criticalRenewals: 3,
    rescueCount: 2,
    avgEngagement: 0.74,
  });
});

run("resolveMatrixKpis falls back to derived when payload is zeroed", () => {
  const kpis = resolveMatrixKpis(
    { totalLTV: 0, criticalRenewals: 0, rescueCount: 0, avgEngagement: 0 },
    [{ ltv: 9000, daysLeft: 35, progress: 0.9, engagement: 0.7, urgency: "rescue" }]
  );

  assert.equal(kpis.totalLTV, 9000);
  assert.equal(kpis.criticalRenewals, 1);
  assert.equal(kpis.rescueCount, 1);
  assert.equal(kpis.avgEngagement, 0.7);
});

run("adaptMatrixPayload normalizes aliases and marker defaults", () => {
  const payload = adaptMatrixPayload({
    filter: "critical",
    items: [
      {
        id: "s-1",
        full_name: "Aluno Matriz",
        plan: "Mentoria Scale",
        progress: "0.62",
        engagement: "0.71",
        daysLeft: "21",
        urgency: "critical",
        ltv: "25000",
        markers: [{ label: "Indicador", value: "12", target: "20", pct: "60", improving: 1 }],
      },
    ],
    kpis: { totalLTV: "25000", criticalRenewals: "1", rescueCount: "0", avgEngagement: "0.71" },
  });

  assert.equal(payload.filter, "critical");
  assert.equal(payload.items[0].programName, "Mentoria Scale");
  assert.equal(payload.items[0].plan, "Mentoria Scale");
  assert.equal(payload.items[0].markers[0].pct, 60);
  assert.equal(payload.items[0].markers[0].improving, true);
  assert.equal(payload.kpis.totalLTV, 25000);
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F4 matrix runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F4 matrix runner: PASS");
