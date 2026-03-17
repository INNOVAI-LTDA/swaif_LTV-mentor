import { coerceNumber, normalizeUrgency } from "../adapters/domainAdapter.js";

export const MATRIX_FILTERS = ["all", "topRight", "critical", "rescue"];

export function normalizeMatrixFilter(filter) {
  const value = String(filter || "all");
  return MATRIX_FILTERS.includes(value) ? value : "all";
}

export function matrixQuadrant(item) {
  if (item?.quadrant && ["topRight", "topLeft", "bottomRight", "bottomLeft"].includes(item.quadrant)) {
    return item.quadrant;
  }

  const progress = coerceNumber(item?.progress, 0);
  const engagement = coerceNumber(item?.engagement, 0);

  if (progress >= 0.6 && engagement >= 0.6) return "topRight";
  if (progress < 0.6 && engagement >= 0.6) return "topLeft";
  if (progress >= 0.6 && engagement < 0.6) return "bottomRight";
  return "bottomLeft";
}

export function deriveMatrixKpis(items = []) {
  const safeItems = Array.isArray(items) ? items : [];
  const totalLTV = safeItems.reduce((sum, item) => sum + coerceNumber(item?.ltv, 0), 0);
  const criticalRenewals = safeItems.filter(
    (item) => coerceNumber(item?.daysLeft, Number.POSITIVE_INFINITY) <= 45 && matrixQuadrant(item) === "topRight"
  ).length;
  const rescueCount = safeItems.filter(
    (item) => normalizeUrgency(item?.urgency) === "rescue"
  ).length;
  const avgEngagement =
    safeItems.length > 0
      ? safeItems.reduce((sum, item) => sum + coerceNumber(item?.engagement, 0), 0) / safeItems.length
      : 0;

  return {
    totalLTV,
    criticalRenewals,
    rescueCount,
    avgEngagement,
  };
}

export function resolveMatrixKpis(payloadKpis, items = []) {
  const provided = {
    totalLTV: coerceNumber(payloadKpis?.totalLTV, 0),
    criticalRenewals: coerceNumber(payloadKpis?.criticalRenewals, 0),
    rescueCount: coerceNumber(payloadKpis?.rescueCount, 0),
    avgEngagement: coerceNumber(payloadKpis?.avgEngagement, 0),
  };

  const hasOnlyZeros =
    provided.totalLTV === 0 &&
    provided.criticalRenewals === 0 &&
    provided.rescueCount === 0 &&
    provided.avgEngagement === 0;

  if (hasOnlyZeros && Array.isArray(items) && items.length > 0) {
    return deriveMatrixKpis(items);
  }

  return provided;
}

