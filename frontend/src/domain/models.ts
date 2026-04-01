export type Urgency = "normal" | "watch" | "critical" | "rescue";
export type Risk = "low" | "medium" | "high";

export type StudentListItem = {
  id: string;
  name: string;
  initials: string;
  programName: string;
  urgency: Urgency;
  risk: Risk;
  daysLeft: number;
  day: number;
  totalDays: number;
  engagement: number;
  progress: number;
  d45: boolean;
  hormoziScore: number;
  ltv: number;
};

export type StudentMetric = {
  id: string;
  metricLabel: string;
  valueCurrent: number;
  valueBaseline: number;
  valueProjected: number | null;
  improvingTrend: boolean | null;
  unit: string;
  optimal: string | null;
};

export type StudentCheckpoint = {
  id: string;
  week: number;
  status: "green" | "yellow" | "red";
  label: string;
};

export type StudentDetail = StudentListItem & {
  metricValues: StudentMetric[];
  checkpoints: StudentCheckpoint[];
};

export type CommandCenterStudentCollection = {
  items: StudentListItem[];
  topItems: StudentListItem[];
  bottomItems: StudentListItem[];
  totalStudents: number;
  rankingMode: "full" | "top_bottom";
  context: {
    mentorName: string;
    mentorId: string;
    protocolName: string;
    protocolId: string;
  };
};

export type TimelineAnomaly = {
  marker: string;
  value: string;
  ref: string;
  cause: string;
  action: string;
};

export type TimelineItem = {
  week: number;
  label: string;
  status: "green" | "yellow" | "red";
  anomaly: TimelineAnomaly | null;
};

export type TimelineAnomalies = {
  studentId: string;
  timeline: TimelineItem[];
  anomalies: TimelineAnomaly[];
  summary: {
    anomalyCount: number;
    hasAnomalies: boolean;
    currentWeek: number;
    lastWeek: number;
  };
};

export type RadarAxis = {
  axisKey: string;
  axisLabel: string;
  axisSub: string;
  baseline: number;
  current: number;
  projected: number;
  insight: string | null;
};

export type StudentRadar = {
  studentId: string;
  axisScores: RadarAxis[];
  avgBaseline: number;
  avgCurrent: number;
  avgProjected: number;
  context: {
    mentorName: string;
    mentorId: string;
    protocolName: string;
    protocolId: string;
  };
};

export type MatrixMarker = {
  label: string;
  value: string | number;
  target: string | number;
  pct: number;
  improving: boolean | null;
};

export type MatrixItem = {
  id: string;
  name: string;
  initials: string;
  programName: string;
  progress: number;
  engagement: number;
  daysLeft: number;
  urgency: Urgency;
  ltv: number;
  renewalReason: string;
  suggestion: string;
  markers: MatrixMarker[];
  quadrant: "topRight" | "topLeft" | "bottomRight" | "bottomLeft";
};

export type MatrixPayload = {
  filter: "all" | "topRight" | "critical" | "rescue";
  items: MatrixItem[];
  kpis: {
    totalLTV: number;
    criticalRenewals: number;
    rescueCount: number;
    avgEngagement: number;
  };
  context: {
    mentorName: string;
    mentorId: string;
    protocolName: string;
    protocolId: string;
  };
};

export type AuthSession = {
  accessToken: string;
  tokenType: string;
  user: {
    id: string;
    email: string;
    role: string;
  } | null;
};

export type AdminClient = {
  id: string;
  name: string;
  brandName: string;
  cnpj: string;
  slug: string;
  status: string;
  isActive: boolean;
  timezone: string;
  currency: string;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
};
