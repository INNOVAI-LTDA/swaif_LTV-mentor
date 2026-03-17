export type ApiErrorResponse = {
  error: {
    status: number;
    code: string;
    message: string;
    details: unknown;
  };
};

export type UrgencyStatus = "normal" | "watch" | "critical" | "rescue";
export type RiskStatus = "low" | "medium" | "high";
