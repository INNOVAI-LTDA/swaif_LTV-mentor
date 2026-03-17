import { useCallback } from "react";
import type { AdminStudentDto } from "../../contracts/adminStudent";
import { useAsyncResource } from "./useAsyncResource";
import { createAdminStudent, listAdminStudentsByMentor } from "../services/adminStudentService";

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

export { createAdminStudent };
