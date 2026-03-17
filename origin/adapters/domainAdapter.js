export function coerceNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function pickFirstDefined(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null) return value;
  }
  return undefined;
}

export function normalizePersonEntity(raw) {
  const person = pickFirstDefined(raw?.student, raw?.client, raw?.patient, raw) || {};

  const id = pickFirstDefined(person.id, raw?.studentId, raw?.clientId, raw?.patientId);
  const name = pickFirstDefined(person.name, person.full_name, person.fullName, raw?.name, raw?.full_name, "");
  const initials = pickFirstDefined(person.initials, raw?.initials, "");

  return {
    id,
    name: String(name || ""),
    initials: String(initials || ""),
  };
}

export function normalizeProgramName(raw) {
  const programName = pickFirstDefined(
    raw?.programName,
    raw?.plan,
    raw?.program,
    raw?.mentoriaName,
    ""
  );
  return String(programName || "");
}

export function normalizeUrgency(value) {
  const urgency = String(value || "normal");
  if (["normal", "watch", "critical", "rescue"].includes(urgency)) {
    return urgency;
  }
  return "normal";
}

