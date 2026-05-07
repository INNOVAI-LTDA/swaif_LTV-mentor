import { httpClient } from "../../shared/api/httpClient";
import type { StudentWorkspacePillarMetrics } from "../models";

function toNumberOrNull(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return null;
}

function adaptPillarMetricsPayload(payload: unknown): StudentWorkspacePillarMetrics {
  if (!payload || typeof payload !== "object") {
    return { studentId: "", enrollmentId: "", pillar: { id: "", name: "", code: "" }, items: [] };
  }
  const raw = payload as Record<string, unknown>;
  const pillarRaw = (raw.pillar && typeof raw.pillar === "object" ? raw.pillar : {}) as Record<string, unknown>;
  const rawItems = Array.isArray(raw.items) ? raw.items : [];
  return {
    studentId: String(raw.studentId ?? ""),
    enrollmentId: String(raw.enrollmentId ?? ""),
    pillar: { id: String(pillarRaw.id ?? ""), name: String(pillarRaw.name ?? "Pilar"), code: String(pillarRaw.code ?? "") },
    items: rawItems.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object")).map((item) => ({
      measurementId: String(item.measurementId ?? ""),
      metricId: String(item.metricId ?? ""),
      metricLabel: String(item.metricLabel ?? "Indicador"),
      direction: String(item.direction ?? "higher_better"),
      unit: typeof item.unit === "string" ? item.unit : null,
      valueBaseline: Number(item.valueBaseline ?? 0),
      valueCurrent: Number(item.valueCurrent ?? 0),
      valueProjected: toNumberOrNull(item.valueProjected),
      improvingTrend: typeof item.improvingTrend === "boolean" ? item.improvingTrend : null,
      minScore: toNumberOrNull(item.minScore),
      maxScore: toNumberOrNull(item.maxScore)
    }))
  };
}

export async function getMentorStudentPillarMetrics(studentId: string, pillarId: string): Promise<StudentWorkspacePillarMetrics> {
  if (!studentId || !pillarId) {
    return { studentId: "", enrollmentId: "", pillar: { id: "", name: "", code: "" }, items: [] };
  }
  const payload = await httpClient.get<unknown>(`/mentor/radar/alunos/${encodeURIComponent(studentId)}/pilares/${encodeURIComponent(pillarId)}/metricas`);
  return adaptPillarMetricsPayload(payload);
}
