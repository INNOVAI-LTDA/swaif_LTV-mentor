import { coerceNumber } from "../adapters/domainAdapter.js";

function clampSlider(value) {
  const numeric = coerceNumber(value, 0);
  if (numeric < 0) return 0;
  if (numeric > 100) return 100;
  return numeric;
}

export function normalizeRadarAxisScores(axisScores = []) {
  const items = Array.isArray(axisScores) ? axisScores : [];

  return items.map((axis, index) => {
    const axisKey = axis?.axisKey || `axis_${index + 1}`;
    const axisLabel = axis?.axisLabel || axisKey;
    const baseline = coerceNumber(axis?.baseline, 0);
    const current = coerceNumber(axis?.current, 0);
    const projectedRaw = axis?.projected;
    const projected =
      projectedRaw === undefined || projectedRaw === null
        ? current
        : coerceNumber(projectedRaw, current);

    return {
      axisKey,
      axisLabel,
      axisSub: axis?.axisSub || "",
      baseline,
      current,
      projected,
      insight: axis?.insight || null,
    };
  });
}

export function simulateRadar(axisScores = [], sliderValue = 0) {
  const normalized = normalizeRadarAxisScores(axisScores);
  const slider = clampSlider(sliderValue);
  const t = slider / 100;

  const baseline = normalized.map((axis) => axis.baseline);
  const current = normalized.map((axis) => axis.current);
  const projected = normalized.map((axis) => axis.projected);
  const active = normalized.map(
    (axis) => axis.current + (axis.projected - axis.current) * t
  );

  const count = normalized.length;
  const avgBaseline = count > 0 ? baseline.reduce((sum, value) => sum + value, 0) / count : 0;
  const avgCurrent = count > 0 ? current.reduce((sum, value) => sum + value, 0) / count : 0;
  const avgProjected = count > 0 ? projected.reduce((sum, value) => sum + value, 0) / count : 0;
  const activeScore = avgCurrent + (avgProjected - avgCurrent) * t;

  return {
    axisScores: normalized,
    slider,
    t,
    count,
    baseline,
    current,
    projected,
    active,
    avgBaseline,
    avgCurrent,
    avgProjected,
    activeScore,
    deltaScore: activeScore - avgBaseline,
  };
}

export function getRadarInsight(axisScores = [], isProjectionMode = false) {
  const normalized = normalizeRadarAxisScores(axisScores);
  const withInsight = normalized.find((axis) => axis.insight);

  if (withInsight) {
    return withInsight.insight;
  }

  if (isProjectionMode) {
    return "O proximo ciclo reforca os pilares com maior alavanca de evolucao.";
  }

  return "A evolucao atual abre espaco para consolidacao no proximo ciclo.";
}
