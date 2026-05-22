import type { Risk, Urgency } from "../models";

export function coerceNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function pickFirstDefined<T>(...values: Array<T | null | undefined>): T | undefined {
  for (const value of values) {
    if (value !== undefined && value !== null) {
      return value;
    }
  }
  return undefined;
}

export function normalizeUrgency(value: unknown): Urgency {
  const text = String(value ?? "normal");
  if (text === "watch" || text === "critical" || text === "rescue") {
    return text;
  }
  return "normal";
}

export function normalizeRisk(value: unknown): Risk {
  const text = String(value ?? "low");
  if (text === "medium" || text === "high") {
    return text;
  }
  return "low";
}

export function normalizeProgramName(raw: Record<string, unknown>): string {
  const value = pickFirstDefined(raw.programName, raw.plan, "");
  return String(value ?? "");
}

export function normalizePerson(raw: Record<string, unknown>): { id: string; name: string; initials: string } {
  const id = String(pickFirstDefined(raw.id, raw.studentId, raw.clientId, raw.patientId, "") ?? "");
  const name = String(pickFirstDefined(raw.name, raw.full_name, raw.fullName, "") ?? "");
  const initials = String(pickFirstDefined(raw.initials, buildInitials(name), "") ?? "");

  return { id, name, initials };
}

function buildInitials(name: string): string {
  const parts = String(name)
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length === 0) {
    return "";
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return `${parts[0][0] ?? ""}${parts[parts.length - 1][0] ?? ""}`.toUpperCase();
}
