import type { MatrixFilter, MatrixResponseDto } from "../../contracts/matrix";
import type { MatrixPayload } from "../models";
import { coerceNumber, normalizePerson, normalizeProgramName, normalizeUrgency } from "./domainAdapter";

const ALLOWED_FILTERS: MatrixFilter[] = ["all", "topRight", "critical", "rescue"];

export function normalizeMatrixFilter(filter: string): MatrixFilter {
  if (ALLOWED_FILTERS.includes(filter as MatrixFilter)) {
    return filter as MatrixFilter;
  }
  return "all";
}

export function matrixQuadrant(item: { progress: number; engagement: number; quadrant?: string }) {
  if (
    item.quadrant === "topRight" ||
    item.quadrant === "topLeft" ||
    item.quadrant === "bottomRight" ||
    item.quadrant === "bottomLeft"
  ) {
    return item.quadrant;
  }

  if (item.progress >= 0.6 && item.engagement >= 0.6) {
    return "topRight";
  }
  if (item.progress < 0.6 && item.engagement >= 0.6) {
    return "topLeft";
  }
  if (item.progress >= 0.6 && item.engagement < 0.6) {
    return "bottomRight";
  }
  return "bottomLeft";
}

export function adaptMatrixPayload(payload: unknown): MatrixPayload {
  const dto = (payload ?? {}) as Partial<MatrixResponseDto>;
  const items = Array.isArray(dto.items) ? dto.items : [];

  return {
    filter: normalizeMatrixFilter(String(dto.filter ?? "all")),
    items: items.map((item) => {
      const person = normalizePerson(item as unknown as Record<string, unknown>);
      const programName = normalizeProgramName(item as unknown as Record<string, unknown>);
      const progress = coerceNumber(item.progress);
      const engagement = coerceNumber(item.engagement);
      return {
        id: person.id,
        name: person.name,
        initials: person.initials,
        programName,
        progress,
        engagement,
        daysLeft: coerceNumber(item.daysLeft),
        urgency: normalizeUrgency(item.urgency),
        ltv: coerceNumber(item.ltv),
        renewalReason: String(item.renewalReason ?? ""),
        suggestion: String(item.suggestion ?? ""),
        markers: Array.isArray(item.markers)
          ? item.markers.map((marker) => ({
              label: String(marker.label ?? ""),
              value: marker.value ?? "",
              target: marker.target ?? "",
              pct: coerceNumber(marker.pct),
              improving:
                marker.improving === undefined || marker.improving === null
                  ? null
                  : Boolean(marker.improving)
            }))
          : [],
        quadrant: matrixQuadrant({
          progress,
          engagement,
          quadrant: item.quadrant
        })
      };
    }),
    kpis: {
      totalLTV: coerceNumber(dto.kpis?.totalLTV),
      criticalRenewals: coerceNumber(dto.kpis?.criticalRenewals),
      rescueCount: coerceNumber(dto.kpis?.rescueCount),
      avgEngagement: coerceNumber(dto.kpis?.avgEngagement)
    }
  };
}

export function deriveMatrixKpis(matrix: MatrixPayload) {
  const items = Array.isArray(matrix.items) ? matrix.items : [];
  return {
    totalLTV: items.reduce((sum, item) => sum + item.ltv, 0),
    criticalRenewals: items.filter((item) => item.daysLeft <= 45 && item.quadrant === "topRight").length,
    rescueCount: items.filter((item) => item.urgency === "rescue").length,
    avgEngagement: items.length > 0 ? items.reduce((sum, item) => sum + item.engagement, 0) / items.length : 0
  };
}
