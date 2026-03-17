import { httpClient } from "../lib/httpClient.js";
import { adaptCenterListItem, adaptStudentDetail } from "../adapters/studentAdapter.js";
import { logContractMismatch } from "../lib/integrationLogger.js";

export async function listCommandCenterStudents() {
  const payload = await httpClient.get("/admin/centro-comando/alunos");
  if (!Array.isArray(payload)) {
    logContractMismatch({
      scope: "command-center.list",
      expected: "array",
      received: typeof payload,
      payload,
    });
    return [];
  }
  return payload.map(adaptCenterListItem);
}

export async function getCommandCenterStudentDetail(studentId) {
  const payload = await httpClient.get(
    `/admin/centro-comando/alunos/${encodeURIComponent(studentId)}`
  );
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    logContractMismatch({
      scope: "command-center.detail",
      expected: "object",
      received: Array.isArray(payload) ? "array" : typeof payload,
      payload,
    });
    return adaptStudentDetail({});
  }
  return adaptStudentDetail(payload);
}
