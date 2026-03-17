import { adaptRadarPayload } from "../adapters/radarAdapter";
import { httpClient } from "../../shared/api/httpClient";
import type { StudentRadar } from "../models";

export async function getStudentRadar(studentId: string): Promise<StudentRadar> {
  if (!studentId) {
    return adaptRadarPayload({});
  }

  const payload = await httpClient.get<unknown>(`/mentor/radar/alunos/${encodeURIComponent(studentId)}`);
  return adaptRadarPayload(payload);
}
