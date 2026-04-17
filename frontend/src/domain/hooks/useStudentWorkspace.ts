import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import type { StudentRadar, StudentWorkspacePillarMetrics } from "../models";
import { getSelfPillarMetrics, getSelfRadar } from "../services/studentWorkspaceService";

const EMPTY_PILLAR_METRICS: StudentWorkspacePillarMetrics = {
  studentId: "",
  enrollmentId: "",
  pillar: {
    id: "",
    name: "",
    code: ""
  },
  items: []
};

export function useSelfRadar() {
  const loader = useCallback(() => getSelfRadar(), []);
  return useAsyncResource<StudentRadar>(loader, [loader], {
    enabled: true,
    initialData: {
      studentId: "",
      axisScores: [],
      avgBaseline: 0,
      avgCurrent: 0,
      avgProjected: 0,
      context: {
        mentorName: "",
        mentorId: "",
        protocolName: "",
        protocolId: ""
      }
    },
    isEmpty: (data) => data.axisScores.length === 0,
    resourceName: "radar do aluno"
  });
}

export function useSelfPillarMetrics(pillarId: string | null) {
  const loader = useCallback(() => {
    if (!pillarId) {
      return Promise.resolve(EMPTY_PILLAR_METRICS);
    }
    return getSelfPillarMetrics(pillarId);
  }, [pillarId]);

  return useAsyncResource<StudentWorkspacePillarMetrics>(loader, [loader], {
    enabled: Boolean(pillarId),
    initialData: EMPTY_PILLAR_METRICS,
    isEmpty: (data) => data.items.length === 0,
    resourceName: "metricas do pilar"
  });
}
