import { coerceNumber } from "./domainAdapter.js";

export function adaptRadarPayload(raw) {
  const axisScores = Array.isArray(raw?.axisScores)
    ? raw.axisScores.map((axis) => {
        const current = coerceNumber(axis.current);
        const projected =
          axis.projected === undefined || axis.projected === null
            ? current
            : coerceNumber(axis.projected, current);

        return {
          axisKey: axis.axisKey || "",
          axisLabel: axis.axisLabel || "",
          axisSub: axis.axisSub || "",
          baseline: coerceNumber(axis.baseline),
          current,
          projected,
          insight: axis.insight || null,
        };
      })
    : [];

  return {
    studentId: raw?.studentId || raw?.clientId || raw?.patientId || "",
    axisScores,
    avgBaseline: coerceNumber(raw?.avgBaseline),
    avgCurrent: coerceNumber(raw?.avgCurrent),
    avgProjected: coerceNumber(raw?.avgProjected),
  };
}
