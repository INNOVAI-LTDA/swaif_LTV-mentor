import { httpClient } from "../lib/httpClient.js";
import { adaptRadarPayload } from "../adapters/radarAdapter.js";
import { logContractMismatch } from "../lib/integrationLogger.js";

export async function getStudentRadar(studentId) {
  if (!studentId) return adaptRadarPayload({});
  const payload = await httpClient.get(
    `/admin/radar/alunos/${encodeURIComponent(studentId)}`
  );
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    logContractMismatch({
      scope: "radar.student",
      expected: "object",
      received: Array.isArray(payload) ? "array" : typeof payload,
      payload,
    });
    return adaptRadarPayload({});
  }
  return adaptRadarPayload(payload);
}
