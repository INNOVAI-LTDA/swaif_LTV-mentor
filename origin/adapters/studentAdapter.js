import {
  coerceNumber,
  normalizePersonEntity,
  normalizeProgramName,
  normalizeUrgency,
} from "./domainAdapter.js";

function toInitials(name) {
  if (!name) return "";
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] || ""}${parts[parts.length - 1][0] || ""}`.toUpperCase();
}

export function adaptCenterListItem(raw) {
  const person = normalizePersonEntity(raw);
  const programName = normalizeProgramName(raw);

  return {
    id: person.id,
    name: person.name,
    initials: person.initials || toInitials(person.name),
    programName,
    plan: raw?.plan || programName,
    urgency: normalizeUrgency(raw.urgency),
    risk: raw.risk || "low",
    daysLeft: coerceNumber(raw.daysLeft),
    day: coerceNumber(raw.day),
    totalDays: coerceNumber(raw.totalDays),
    engagement: coerceNumber(raw.engagement),
    progress: coerceNumber(raw.progress),
    d45: Boolean(raw.d45),
    hormoziScore: coerceNumber(raw.hormoziScore),
    ltv: coerceNumber(raw.ltv),
    renewalReason: raw.renewalReason || "",
    suggestion: raw.suggestion || "",
    markers: Array.isArray(raw.markers) ? raw.markers : [],
  };
}

export function mergeCenterAndMatrix(centerItems, matrixItems) {
  const matrixById = new Map(
    (matrixItems || []).map((item) => [String(item.id), item])
  );

  return (centerItems || []).map((centerItem) => {
    const matrixItem = matrixById.get(String(centerItem.id));
    const merged = { ...centerItem, ...(matrixItem || {}) };
    return adaptCenterListItem(merged);
  });
}

export function adaptStudentDetail(raw, fallbackItem = null) {
  const base = adaptCenterListItem({ ...(fallbackItem || {}), ...(raw || {}) });

  return {
    ...base,
    metricValues: Array.isArray(raw?.metricValues)
      ? raw.metricValues.map((metric) => ({
          id: metric.id,
          metricLabel: metric.metricLabel || "",
          valueCurrent: coerceNumber(metric.valueCurrent),
          valueBaseline: coerceNumber(metric.valueBaseline),
          valueProjected:
            metric.valueProjected === undefined || metric.valueProjected === null
              ? null
              : coerceNumber(metric.valueProjected),
          improvingTrend:
            metric.improvingTrend === undefined
              ? null
              : Boolean(metric.improvingTrend),
          unit: metric.unit || "",
          optimal: metric.optimal || null,
        }))
      : [],
    checkpoints: Array.isArray(raw?.checkpoints)
      ? raw.checkpoints.map((checkpoint) => ({
          id: checkpoint.id,
          week: coerceNumber(checkpoint.week),
          status: checkpoint.status || "green",
          label: checkpoint.label || "",
        }))
      : [],
  };
}
