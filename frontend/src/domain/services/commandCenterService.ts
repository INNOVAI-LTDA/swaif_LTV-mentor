import { adaptCommandCenterDetail, adaptCommandCenterListPayload, adaptTimelineAnomalies } from "../adapters/commandCenterAdapter";
import { httpClient } from "../../shared/api/httpClient";
import type { StudentDetail, StudentListItem, TimelineAnomalies } from "../models";

export async function listCommandCenterStudents(): Promise<StudentListItem[]> {
  const payload = await httpClient.get<unknown>("/mentor/centro-comando/alunos");
  return adaptCommandCenterListPayload(payload);
}

export async function getCommandCenterStudentDetail(studentId: string): Promise<StudentDetail | null> {
  const payload = await httpClient.get<unknown>(`/mentor/centro-comando/alunos/${encodeURIComponent(studentId)}`);
  return adaptCommandCenterDetail(payload);
}

export async function getCommandCenterTimelineAnomalies(studentId: string): Promise<TimelineAnomalies | null> {
  const payload = await httpClient.get<unknown>(
    `/mentor/centro-comando/alunos/${encodeURIComponent(studentId)}/timeline-anomalias`
  );
  return adaptTimelineAnomalies(payload);
}
