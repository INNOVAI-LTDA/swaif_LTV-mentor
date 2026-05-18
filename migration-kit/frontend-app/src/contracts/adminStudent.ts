export type AdminStudentDto = {
  id: string;
  full_name: string;
  initials: string;
  email: string | null;
  cpf: string | null;
  phone: string | null;
  notes: string | null;
  status: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  mentor_id: string | null;
  organization_id: string | null;
  enrollment_id: string | null;
};

export type AdminStudentCreateDto = {
  full_name: string;
  cpf: string;
  email?: string;
  phone?: string;
  notes?: string;
};

export type AdminStudentReassignDto = {
  target_mentor_id: string;
  justificativa: string;
};

export type AdminStudentUnlinkDto = {
  justificativa: string;
};

export type AdminEnrollmentDto = {
  id: string;
  student_id: string;
  organization_id: string;
  mentor_id: string | null;
  is_active: boolean;
  deactivated_reason: string | null;
};

export type AdminIndicatorValueInputDto = {
  metric_id: string;
  value_baseline: number;
  value_current: number;
  value_projected?: number;
  improving_trend?: boolean;
};

export type AdminCheckpointInputDto = {
  week: number;
  status: "green" | "yellow" | "red";
  label?: string;
};

export type AdminIndicatorLoadDto = {
  metric_values: AdminIndicatorValueInputDto[];
  checkpoints: AdminCheckpointInputDto[];
};

export type AdminIndicatorLoadResultDto = {
  student_id: string;
  enrollment_id: string;
  measurement_count: number;
  checkpoint_count: number;
};
