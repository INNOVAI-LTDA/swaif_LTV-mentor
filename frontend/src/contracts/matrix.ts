import type { UrgencyStatus } from "./common";

export type MatrixFilter = "all" | "topRight" | "critical" | "rescue";

export type MatrixMarkerDto = {
  label: string;
  value: string | number;
  target: string | number;
  pct: number;
  improving?: boolean | null;
};

export type MatrixItemDto = {
  id: string;
  name: string;
  initials?: string;
  programName?: string;
  plan?: string;
  progress: number;
  engagement: number;
  daysLeft: number;
  urgency: UrgencyStatus;
  ltv: number;
  renewalReason?: string;
  suggestion?: string;
  markers?: MatrixMarkerDto[];
  quadrant?: "topRight" | "topLeft" | "bottomRight" | "bottomLeft";
};

export type MatrixKpisDto = {
  totalLTV: number;
  criticalRenewals: number;
  rescueCount: number;
  avgEngagement: number;
};

export type MatrixResponseDto = {
  filter: MatrixFilter;
  items: MatrixItemDto[];
  kpis: MatrixKpisDto;
};
