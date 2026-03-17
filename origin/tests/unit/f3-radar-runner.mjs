import assert from "node:assert/strict";

import { adaptRadarPayload } from "../../adapters/radarAdapter.js";
import {
  normalizeRadarAxisScores,
  simulateRadar,
  getRadarInsight,
} from "../../lib/radarUtils.js";

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

run("normalizeRadarAxisScores parses numbers and fallback projected", () => {
  const axes = normalizeRadarAxisScores([
    { axisKey: "energia", axisLabel: "Energia", baseline: "40", current: "60" },
  ]);

  assert.equal(axes.length, 1);
  assert.equal(axes[0].baseline, 40);
  assert.equal(axes[0].current, 60);
  assert.equal(axes[0].projected, 60);
  assert.equal(axes[0].insight, null);
});

run("simulateRadar interpolates active values by slider", () => {
  const simulation = simulateRadar(
    [
      { axisKey: "energia", axisLabel: "Energia", baseline: 40, current: 60, projected: 80 },
      { axisKey: "foco", axisLabel: "Foco", baseline: 30, current: 50, projected: 70 },
    ],
    50
  );

  assert.deepEqual(simulation.active, [70, 60]);
  assert.equal(simulation.avgBaseline, 35);
  assert.equal(simulation.avgCurrent, 55);
  assert.equal(simulation.avgProjected, 75);
  assert.equal(simulation.activeScore, 65);
  assert.equal(simulation.deltaScore, 30);
});

run("simulateRadar clamps slider range", () => {
  const belowZero = simulateRadar(
    [{ axisKey: "a1", axisLabel: "A1", baseline: 10, current: 20, projected: 40 }],
    -20
  );
  const aboveHundred = simulateRadar(
    [{ axisKey: "a1", axisLabel: "A1", baseline: 10, current: 20, projected: 40 }],
    140
  );

  assert.equal(belowZero.slider, 0);
  assert.deepEqual(belowZero.active, [20]);
  assert.equal(aboveHundred.slider, 100);
  assert.deepEqual(aboveHundred.active, [40]);
});

run("getRadarInsight returns optional axis insight when present", () => {
  const insight = getRadarInsight(
    [{ axisKey: "foco", axisLabel: "Foco", baseline: 10, current: 20, projected: 30, insight: "Priorizar rotina de foco." }],
    true
  );

  assert.equal(insight, "Priorizar rotina de foco.");
});

run("getRadarInsight fallback is deterministic without optional insight", () => {
  const projectionInsight = getRadarInsight([], true);
  const currentInsight = getRadarInsight([], false);

  assert.equal(
    projectionInsight,
    "O proximo ciclo reforca os pilares com maior alavanca de evolucao."
  );
  assert.equal(
    currentInsight,
    "A evolucao atual abre espaco para consolidacao no proximo ciclo."
  );
});

run("adapter + simulation are compatible for avg and fallback", () => {
  const adapted = adaptRadarPayload({
    studentId: "std_1",
    axisScores: [
      { axisKey: "energia", axisLabel: "Energia", baseline: "45", current: "60", projected: null },
      { axisKey: "foco", axisLabel: "Foco", baseline: "35", current: "55", projected: "75" },
    ],
  });

  const simulation = simulateRadar(adapted.axisScores, 100);

  assert.deepEqual(simulation.projected, [60, 75]);
  assert.equal(simulation.avgProjected, 67.5);
  assert.equal(simulation.activeScore, 67.5);
});

if (process.exitCode && process.exitCode !== 0) {
  console.error("F3 radar runner finished with failures.");
  process.exit(process.exitCode);
}

console.log("F3 radar runner: PASS");
