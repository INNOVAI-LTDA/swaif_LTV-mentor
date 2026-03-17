import { coerceNumber } from "../adapters/domainAdapter.js";

export function safeProgressPercent(student) {
  const day = coerceNumber(student?.day, 0);
  const totalDays = coerceNumber(student?.totalDays, 0);
  const progress01 = coerceNumber(student?.progress, 0);

  if (totalDays > 0) {
    return Math.round((day / totalDays) * 100);
  }
  return Math.round(progress01 * 100);
}

export function deriveCommandCenterKpis(students = []) {
  const items = Array.isArray(students) ? students : [];
  return {
    active: items.length,
    alerts: items.filter((student) => student?.urgency === "rescue").length,
    d45: items.filter(
      (student) => coerceNumber(student?.daysLeft, Number.POSITIVE_INFINITY) <= 45
    ).length,
  };
}

export function resolveSelectedStudentId(students = [], selectedId = null) {
  const items = Array.isArray(students) ? students : [];
  if (items.length === 0) return null;

  if (selectedId !== null && selectedId !== undefined) {
    const exists = items.some((item) => String(item.id) === String(selectedId));
    if (exists) return selectedId;
  }

  return items[0].id;
}
