import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getUnifiedStudents } from "../services/studentsService.js";

export function useStudents() {
  const loader = useCallback(() => getUnifiedStudents(), []);
  const resource = useAsyncResource(loader, [loader], {
    enabled: true,
    initialData: [],
    resourceName: "lista de alunos",
  });

  return {
    data: resource.data || [],
    loading: resource.loading,
    error: resource.error,
    refresh: resource.refresh,
  };
}
