import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getStudentRadar } from "../services/radarService";
import { adaptRadarPayload } from "../adapters/radarAdapter";
import type { StudentRadar } from "../models";

const EMPTY_RADAR = adaptRadarPayload({});

export function useStudentRadar(studentId: string | null) {
  const loader = useCallback(() => {
    if (!studentId) {
      return Promise.resolve(EMPTY_RADAR);
    }
    return getStudentRadar(studentId);
  }, [studentId]);

  return useAsyncResource<StudentRadar>(loader, [loader], {
    enabled: true,
    initialData: EMPTY_RADAR,
    isEmpty: (data) => data.axisScores.length === 0,
    resourceName: "radar do aluno"
  });
}
