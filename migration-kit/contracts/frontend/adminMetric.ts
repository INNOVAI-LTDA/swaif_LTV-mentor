export type AdminMetricDirection = "higher_better" | "lower_better" | "target_range";

export type AdminMetricDto = {
  id: string;
  protocol_id: string;
  pillar_id: string;
  name: string;
  code: string;
  direction: AdminMetricDirection;
  unit: string | null;
  is_active: boolean;
  pillar_name?: string;
};

export type AdminMetricCreateDto = {
  name: string;
  code?: string;
  direction?: AdminMetricDirection;
  unit?: string;
};
