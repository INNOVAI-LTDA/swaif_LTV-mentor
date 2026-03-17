import assert from "node:assert/strict";

import {
  coerceNumber,
  normalizePersonEntity,
  normalizeProgramName,
  normalizeUrgency,
} from "../../adapters/domainAdapter.js";
import {
  adaptCenterListItem,
  adaptStudentDetail,
  mergeCenterAndMatrix,
} from "../../adapters/studentAdapter.js";
import { adaptRadarPayload } from "../../adapters/radarAdapter.js";
import { adaptMatrixPayload } from "../../adapters/matrixAdapter.js";
import { formatPercent01, formatCurrencyBRL } from "../../lib/formatters.js";

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

run("domain/coerceNumber parses valid values", () => {
  assert.equal(coerceNumber("12.5"), 12.5);
  assert.equal(coerceNumber(8), 8);
});

run("domain/coerceNumber fallback", () => {
  assert.equal(coerceNumber("abc", 7), 7);
  assert.equal(coerceNumber(undefined, 3), 3);
});

run("domain/normalizePersonEntity supports legacy aliases", () => {
  const raw = { client: { id: "c1", name: "Ana Silva", initials: "AS" } };
  assert.deepEqual(normalizePersonEntity(raw), {
    id: "c1",
    name: "Ana Silva",
    initials: "AS",
  });
});

run("domain/normalizeProgramName fallback programName->plan", () => {
  assert.equal(normalizeProgramName({ programName: "Mentoria Alpha" }), "Mentoria Alpha");
  assert.equal(normalizeProgramName({ plan: "Plano Pro" }), "Plano Pro");
  assert.equal(normalizeProgramName({}), "");
});

run("domain/normalizeUrgency defaults unknown", () => {
  assert.equal(normalizeUrgency("watch"), "watch");
  assert.equal(normalizeUrgency("invalid"), "normal");
});

run("student/adaptCenterListItem normalizes aliases and numbers", () => {
  const item = adaptCenterListItem({
    id: "std_1",
    full_name: "Bruna Costa",
    plan: "Mentoria Scale",
    progress: "0.7",
    engagement: "0.8",
    ltv: "12000",
  });

  assert.equal(item.name, "Bruna Costa");
  assert.equal(item.programName, "Mentoria Scale");
  assert.equal(item.plan, "Mentoria Scale");
  assert.equal(item.progress, 0.7);
  assert.equal(item.engagement, 0.8);
  assert.equal(item.ltv, 12000);
});

run("student/mergeCenterAndMatrix merges by id", () => {
  const merged = mergeCenterAndMatrix(
    [{ id: "1", name: "A", programName: "P1", progress: 0.5, engagement: 0.4 }],
    [{ id: "1", renewalReason: "Motivo", suggestion: "Oferta", markers: [] }]
  );

  assert.equal(merged.length, 1);
  assert.equal(merged[0].renewalReason, "Motivo");
  assert.equal(merged[0].suggestion, "Oferta");
});

run("student/adaptStudentDetail keeps optional safe", () => {
  const detail = adaptStudentDetail({
    id: "1",
    name: "Aluno",
    programName: "Mentoria",
    metricValues: [{ id: "m1", metricLabel: "Engajamento", valueCurrent: "10", valueBaseline: "8" }],
    checkpoints: [{ id: "c1", week: "2", status: "yellow", label: "Semana 2" }],
  });

  assert.equal(detail.metricValues[0].valueCurrent, 10);
  assert.equal(detail.metricValues[0].valueProjected, null);
  assert.equal(detail.checkpoints[0].week, 2);
});

run("radar/adaptRadarPayload fallback projected=current", () => {
  const result = adaptRadarPayload({
    studentId: "std_1",
    axisScores: [{ axisKey: "energia", axisLabel: "Energia", baseline: "40", current: "60" }],
  });

  assert.equal(result.axisScores[0].baseline, 40);
  assert.equal(result.axisScores[0].current, 60);
  assert.equal(result.axisScores[0].projected, 60);
});

run("radar/adaptRadarPayload supports clientId alias", () => {
  const result = adaptRadarPayload({ clientId: "c_10", axisScores: [] });
  assert.equal(result.studentId, "c_10");
});

run("matrix/adaptMatrixPayload normalizes item and kpis", () => {
  const result = adaptMatrixPayload({
    filter: "all",
    items: [
      {
        id: "1",
        full_name: "Carlos Melo",
        plan: "Mentoria Growth",
        progress: "0.63",
        engagement: "0.51",
        daysLeft: "30",
        urgency: "watch",
        ltv: "15000",
      },
    ],
    kpis: {
      totalLTV: "15000",
      criticalRenewals: "2",
      rescueCount: "1",
      avgEngagement: "0.62",
    },
  });

  assert.equal(result.items[0].name, "Carlos Melo");
  assert.equal(result.items[0].programName, "Mentoria Growth");
  assert.equal(result.items[0].progress, 0.63);
  assert.equal(result.kpis.totalLTV, 15000);
});

run("formatters/formatPercent01", () => {
  assert.equal(formatPercent01(0.42), "42%");
  assert.equal(
    formatPercent01("0.155", { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
    "15,5%"
  );
});

run("formatters/formatCurrencyBRL", () => {
  const value = formatCurrencyBRL(12345);
  assert.ok(value.includes("R$"));
  assert.ok(value.includes("12.345"));
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F1 unit runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F1 unit runner: PASS");

