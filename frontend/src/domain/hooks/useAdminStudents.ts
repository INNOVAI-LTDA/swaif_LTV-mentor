import { useCallback } from "react";
import type { AdminStudentDto } from "../../contracts/adminStudent";
import type { StudentRadar } from "../models";
import { useAsyncResource } from "./useAsyncResource";
import { adaptRadarPayload } from "../adapters/radarAdapter";
import { createAdminStudent, getAdminStudentRadar, listAdminStudentsByMentor } from "../services/adminStudentService";

const EMPTY_RADAR = adaptRadarPayload({});

export function useAdminStudents(mentorId: string | null) {
  const loader = useCallback(() => {
    if (!mentorId) {
      return Promise.resolve([]);
    }
    return listAdminStudentsByMentor(mentorId);
  }, [mentorId]);

  return useAsyncResource<AdminStudentDto[]>(loader, [loader], {
    enabled: Boolean(mentorId),
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista de alunos"
  });
}

export function useAdminStudentRadar(mentorId: string | null, studentId: string | null) {
  const loader = useCallback(() => {
    if (!mentorId || !studentId) {
      return Promise.resolve(EMPTY_RADAR);
    }
    return getAdminStudentRadar(mentorId, studentId);
  }, [mentorId, studentId]);

  return useAsyncResource<StudentRadar>(loader, [loader], {
    enabled: Boolean(mentorId && studentId),
    initialData: EMPTY_RADAR,
    isEmpty: (data) => data.axisScores.length === 0,
    resourceName: "radar do aluno"
  });
}

export { createAdminStudent };
