import {
  coerceNumber,
  normalizePersonEntity,
  normalizeProgramName,
  normalizeUrgency,
} from "./domainAdapter.js";

function adaptMarker(marker) {
  return {
    label: marker?.label || "",
    value: marker?.value ?? "",
    target: marker?.target ?? "",
    pct: coerceNumber(marker?.pct),
    improving:
      marker?.improving === undefined ? null : Boolean(marker.improving),
  };
}

function adaptMatrixItem(item) {
  const person = normalizePersonEntity(item);
  const programName = normalizeProgramName(item);

  return {
    id: person.id,
    name: person.name,
    initials: person.initials || "",
    programName,
    plan: item?.plan || programName,
    progress: coerceNumber(item.progress),
    engagement: coerceNumber(item.engagement),
    daysLeft: coerceNumber(item.daysLeft),
    urgency: normalizeUrgency(item.urgency),
    ltv: coerceNumber(item.ltv),
    renewalReason: item.renewalReason || "",
    suggestion: item.suggestion || "",
    markers: Array.isArray(item.markers)
      ? item.markers.map(adaptMarker)
      : [],
    quadrant: item.quadrant || "",
  };
}

export function adaptMatrixPayload(raw) {
  return {
    filter: raw?.filter || "all",
    items: Array.isArray(raw?.items) ? raw.items.map(adaptMatrixItem) : [],
    kpis: {
      totalLTV: coerceNumber(raw?.kpis?.totalLTV),
      criticalRenewals: coerceNumber(raw?.kpis?.criticalRenewals),
      rescueCount: coerceNumber(raw?.kpis?.rescueCount),
      avgEngagement: coerceNumber(raw?.kpis?.avgEngagement),
    },
  };
}
