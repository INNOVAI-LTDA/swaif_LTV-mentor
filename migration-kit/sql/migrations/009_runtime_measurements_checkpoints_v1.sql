-- Story 1.2 - Runtime stores for initial indicator load without JSON fallback

CREATE TABLE IF NOT EXISTS public.deva_accmed_runtime_measurements (
  id TEXT PRIMARY KEY,
  enrollment_id TEXT NOT NULL,
  metric_id TEXT NOT NULL,
  value_baseline DOUBLE PRECISION NOT NULL,
  value_current DOUBLE PRECISION NOT NULL,
  value_projected DOUBLE PRECISION NULL,
  improving_trend BOOLEAN NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deva_accmed_runtime_measurements_enrollment
  ON public.deva_accmed_runtime_measurements (enrollment_id);

CREATE TABLE IF NOT EXISTS public.deva_accmed_runtime_checkpoints (
  id TEXT PRIMARY KEY,
  enrollment_id TEXT NOT NULL,
  week INTEGER NOT NULL,
  status TEXT NOT NULL,
  label TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deva_accmed_runtime_checkpoints_enrollment
  ON public.deva_accmed_runtime_checkpoints (enrollment_id);

