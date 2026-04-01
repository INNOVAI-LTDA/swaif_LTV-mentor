import type { RiskStatus, UrgencyStatus } from "./common";

export type CommandCenterStudentListItemDto = {
  id: string;
  name: string;
  programName?: string;
  plan?: string;
  urgency: UrgencyStatus;
  risk?: RiskStatus;
  daysLeft: number;
  day: number;
  totalDays: number;
  engagement: number;
  progress: number;
  d45?: boolean;
  hormoziScore: number;
  ltv: number;
};

export type CommandCenterStudentListPayloadDto = {
  items: CommandCenterStudentListItemDto[];
  topItems?: CommandCenterStudentListItemDto[];
  bottomItems?: CommandCenterStudentListItemDto[];
  totalStudents?: number;
  rankingMode?: "full" | "top_bottom";
  context?: {
    mentorName?: string;
    mentorId?: string;
    protocolName?: string;
    protocolId?: string;
  };
};

export type CommandCenterMetricValueDto = {
  id: string;
  metricLabel: string;
  valueCurrent: number;
  valueBaseline: number;
  valueProjected?: number | null;
  improvingTrend?: boolean | null;
  unit?: string;
  optimal?: string | null;
};

export type CommandCenterCheckpointDto = {
  id: string;
  week: number;
  status: "green" | "yellow" | "red";
  label: string;
};

export type CommandCenterStudentDetailDto = CommandCenterStudentListItemDto & {
  metricValues: CommandCenterMetricValueDto[];
  checkpoints: CommandCenterCheckpointDto[];
};

export type TimelineEntryDto = {
  week: number;
  label: string;
  status: "green" | "yellow" | "red";
  anomaly?: {
    marker: string;
    value: string;
    ref: string;
    cause: string;
    action: string;
  } | null;
};

export type TimelineAnomalyDto = {
  marker: string;
  value: string;
  ref: string;
  cause: string;
  action: string;
};

export type CommandCenterTimelineAnomaliesDto = {
  studentId: string;
  timeline: TimelineEntryDto[];
  anomalies: TimelineAnomalyDto[];
  summary: {
    anomalyCount: number;
    hasAnomalies: boolean;
    currentWeek: number;
    lastWeek: number;
  };
};
