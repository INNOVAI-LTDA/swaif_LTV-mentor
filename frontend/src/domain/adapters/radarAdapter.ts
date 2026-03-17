import type { RadarResponseDto } from "../../contracts/radar";
import type { StudentRadar } from "../models";
import { coerceNumber } from "./domainAdapter";

export function adaptRadarPayload(payload: unknown): StudentRadar {
  const dto = (payload ?? {}) as Partial<RadarResponseDto>;
  const axisScores = Array.isArray(dto.axisScores) ? dto.axisScores : [];

  return {
    studentId: String(dto.studentId ?? ""),
    axisScores: axisScores.map((axis, index) => {
      const current = coerceNumber(axis.current);
      const projected =
        axis.projected === undefined || axis.projected === null
          ? current
          : coerceNumber(axis.projected, current);

      return {
        axisKey: String(axis.axisKey ?? `axis_${index + 1}`),
        axisLabel: String(axis.axisLabel ?? `Eixo ${index + 1}`),
        axisSub: String(axis.axisSub ?? ""),
        baseline: coerceNumber(axis.baseline),
        current,
        projected,
        insight: axis.insight == null ? null : String(axis.insight)
      };
    }),
    avgBaseline: coerceNumber(dto.avgBaseline),
    avgCurrent: coerceNumber(dto.avgCurrent),
    avgProjected: coerceNumber(dto.avgProjected)
  };
}

export function simulateRadar(radar: StudentRadar, slider: number) {
  const safe = Math.max(0, Math.min(100, coerceNumber(slider)));
  const t = safe / 100;
  const activeAxisScores = radar.axisScores.map((axis) => ({
    ...axis,
    active: axis.current + (axis.projected - axis.current) * t
  }));

  const count = activeAxisScores.length || 1;
  const activeScore = activeAxisScores.reduce((sum, axis) => sum + axis.active, 0) / count;

  return {
    slider: safe,
    axisScores: activeAxisScores,
    activeScore
  };
}
