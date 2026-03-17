import type {
  CommandCenterStudentDetailDto,
  CommandCenterStudentListItemDto,
  CommandCenterTimelineAnomaliesDto
} from "../../contracts/commandCenter";
import type { StudentDetail, StudentListItem, TimelineAnomalies } from "../models";
import { coerceNumber, normalizePerson, normalizeProgramName, normalizeRisk, normalizeUrgency } from "./domainAdapter";

export function adaptCommandCenterListItem(raw: CommandCenterStudentListItemDto): StudentListItem {
  const person = normalizePerson(raw as unknown as Record<string, unknown>);
  const programName = normalizeProgramName(raw as unknown as Record<string, unknown>);

  return {
    id: person.id,
    name: person.name,
    initials: person.initials,
    programName,
    urgency: normalizeUrgency(raw.urgency),
    risk: normalizeRisk(raw.risk),
    daysLeft: coerceNumber(raw.daysLeft),
    day: coerceNumber(raw.day),
    totalDays: coerceNumber(raw.totalDays),
    engagement: coerceNumber(raw.engagement),
    progress: coerceNumber(raw.progress),
    d45: Boolean(raw.d45),
    hormoziScore: coerceNumber(raw.hormoziScore),
    ltv: coerceNumber(raw.ltv)
  };
}

export function adaptCommandCenterListPayload(payload: unknown): StudentListItem[] {
  if (!Array.isArray(payload)) {
    return [];
  }
  return payload.map((item) => adaptCommandCenterListItem(item as CommandCenterStudentListItemDto));
}

export function adaptCommandCenterDetail(payload: unknown): StudentDetail | null {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return null;
  }
  const dto = payload as CommandCenterStudentDetailDto;
  const base = adaptCommandCenterListItem(dto);

  return {
    ...base,
    metricValues: Array.isArray(dto.metricValues)
      ? dto.metricValues.map((metric) => ({
          id: String(metric.id ?? ""),
          metricLabel: String(metric.metricLabel ?? ""),
          valueCurrent: coerceNumber(metric.valueCurrent),
          valueBaseline: coerceNumber(metric.valueBaseline),
          valueProjected:
            metric.valueProjected === undefined || metric.valueProjected === null
              ? null
              : coerceNumber(metric.valueProjected),
          improvingTrend:
            metric.improvingTrend === undefined || metric.improvingTrend === null
              ? null
              : Boolean(metric.improvingTrend),
          unit: String(metric.unit ?? ""),
          optimal: metric.optimal == null ? null : String(metric.optimal)
        }))
      : [],
    checkpoints: Array.isArray(dto.checkpoints)
      ? dto.checkpoints.map((checkpoint) => ({
          id: String(checkpoint.id ?? ""),
          week: coerceNumber(checkpoint.week),
          status:
            checkpoint.status === "yellow" || checkpoint.status === "red" ? checkpoint.status : "green",
          label: String(checkpoint.label ?? "")
        }))
      : []
  };
}

export function adaptTimelineAnomalies(payload: unknown): TimelineAnomalies | null {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return null;
  }
  const dto = payload as CommandCenterTimelineAnomaliesDto;

  return {
    studentId: String(dto.studentId ?? ""),
    timeline: Array.isArray(dto.timeline)
      ? dto.timeline.map((entry) => ({
          week: coerceNumber(entry.week),
          label: String(entry.label ?? ""),
          status: entry.status === "yellow" || entry.status === "red" ? entry.status : "green",
          anomaly: entry.anomaly
            ? {
                marker: String(entry.anomaly.marker ?? ""),
                value: String(entry.anomaly.value ?? ""),
                ref: String(entry.anomaly.ref ?? ""),
                cause: String(entry.anomaly.cause ?? ""),
                action: String(entry.anomaly.action ?? "")
              }
            : null
        }))
      : [],
    anomalies: Array.isArray(dto.anomalies)
      ? dto.anomalies.map((anomaly) => ({
          marker: String(anomaly.marker ?? ""),
          value: String(anomaly.value ?? ""),
          ref: String(anomaly.ref ?? ""),
          cause: String(anomaly.cause ?? ""),
          action: String(anomaly.action ?? "")
        }))
      : [],
    summary: {
      anomalyCount: coerceNumber(dto.summary?.anomalyCount),
      hasAnomalies: Boolean(dto.summary?.hasAnomalies),
      currentWeek: coerceNumber(dto.summary?.currentWeek),
      lastWeek: coerceNumber(dto.summary?.lastWeek)
    }
  };
}

export function deriveCommandCenterTopKpis(students: StudentListItem[]) {
  const items = Array.isArray(students) ? students : [];
  return {
    active: items.length,
    alerts: items.filter((item) => item.urgency === "rescue").length,
    d45: items.filter((item) => item.daysLeft <= 45).length
  };
}
