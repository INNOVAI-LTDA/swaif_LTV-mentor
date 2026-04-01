import type {
  CommandCenterStudentListPayloadDto,
  CommandCenterStudentDetailDto,
  CommandCenterStudentListItemDto,
  CommandCenterTimelineAnomaliesDto
} from "../../contracts/commandCenter";
import type { CommandCenterStudentCollection, StudentDetail, StudentListItem, TimelineAnomalies } from "../models";
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
  if (Array.isArray(payload)) {
    return payload.map((item) => adaptCommandCenterListItem(item as CommandCenterStudentListItemDto));
  }
  if (!payload || typeof payload !== "object") {
    return [];
  }
  const dto = payload as CommandCenterStudentListPayloadDto;
  if (!Array.isArray(dto.items)) {
    return [];
  }
  return dto.items.map((item) => adaptCommandCenterListItem(item));
}

export function adaptCommandCenterCollection(payload: unknown): CommandCenterStudentCollection {
  if (Array.isArray(payload)) {
    const items = payload.map((item) => adaptCommandCenterListItem(item as CommandCenterStudentListItemDto));
    return {
      items,
      topItems: items,
      bottomItems: [],
      totalStudents: items.length,
      rankingMode: "full",
      context: {
        mentorName: "",
        mentorId: "",
        protocolName: "",
        protocolId: ""
      }
    };
  }

  if (!payload || typeof payload !== "object") {
    return {
      items: [],
      topItems: [],
      bottomItems: [],
      totalStudents: 0,
      rankingMode: "full",
      context: {
        mentorName: "",
        mentorId: "",
        protocolName: "",
        protocolId: ""
      }
    };
  }

  const dto = payload as CommandCenterStudentListPayloadDto;
  const items = Array.isArray(dto.items) ? dto.items.map((item) => adaptCommandCenterListItem(item)) : [];
  const topItems = Array.isArray(dto.topItems) ? dto.topItems.map((item) => adaptCommandCenterListItem(item)) : items;
  const bottomItems = Array.isArray(dto.bottomItems)
    ? dto.bottomItems.map((item) => adaptCommandCenterListItem(item))
    : [];

  return {
    items,
    topItems,
    bottomItems,
    totalStudents: coerceNumber(dto.totalStudents ?? items.length),
    rankingMode: dto.rankingMode === "top_bottom" ? "top_bottom" : "full",
    context: {
      mentorName: String(dto.context?.mentorName ?? ""),
      mentorId: String(dto.context?.mentorId ?? ""),
      protocolName: String(dto.context?.protocolName ?? ""),
      protocolId: String(dto.context?.protocolId ?? "")
    }
  };
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
