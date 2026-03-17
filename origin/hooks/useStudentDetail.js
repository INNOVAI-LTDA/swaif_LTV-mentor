import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getUnifiedStudentDetail } from "../services/studentsService.js";

export function useStudentDetail(studentId) {
  const loader = useCallback(() => {
    if (!studentId) return Promise.resolve(null);
    return getUnifiedStudentDetail(studentId);
  }, [studentId]);

  const resource = useAsyncResource(loader, [loader], {
    enabled: Boolean(studentId),
    initialData: null,
    resourceName: "detalhe do aluno",
  });

  return {
    data: resource.data,
    loading: resource.loading,
    error: resource.error,
    refresh: resource.refresh,
  };
}
