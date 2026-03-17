import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getStudentRadar } from "../services/radarService.js";

export function useStudentRadar(studentId) {
  const loader = useCallback(() => {
    if (!studentId) return Promise.resolve({ axisScores: [] });
    return getStudentRadar(studentId);
  }, [studentId]);

  const resource = useAsyncResource(loader, [loader], {
    enabled: Boolean(studentId),
    initialData: { axisScores: [] },
    resourceName: "radar do aluno",
  });

  return {
    data: resource.data || { axisScores: [] },
    loading: resource.loading,
    error: resource.error,
    refresh: resource.refresh,
  };
}
