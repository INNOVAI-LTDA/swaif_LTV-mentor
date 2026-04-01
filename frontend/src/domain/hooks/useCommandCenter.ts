import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import {
  getCommandCenterStudentCollection,
  getCommandCenterStudentDetail,
  getCommandCenterTimelineAnomalies,
  listCommandCenterStudents
} from "../services/commandCenterService";
import type { CommandCenterStudentCollection, StudentDetail, StudentListItem, TimelineAnomalies } from "../models";

export function useCommandCenterStudents() {
  const loader = useCallback(() => listCommandCenterStudents(), []);
  return useAsyncResource<StudentListItem[]>(loader, [loader], {
    enabled: true,
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista do centro de comando"
  });
}

export function useCommandCenterStudentCollection() {
  const loader = useCallback(() => getCommandCenterStudentCollection(), []);
  return useAsyncResource<CommandCenterStudentCollection>(loader, [loader], {
    enabled: true,
    initialData: {
      items: [],
      topItems: [],
      bottomItems: [],
      totalStudents: 0,
      rankingMode: "full",
      context: {
        mentorName: "",
        mentorId: "",
        protocolName: "",
        protocolId: ""
      }
    },
    isEmpty: (data) => data.items.length === 0,
    resourceName: "ranking do centro de comando"
  });
}

export function useCommandCenterStudentDetail(studentId: string | null) {
  const loader = useCallback(() => {
    if (!studentId) {
      return Promise.resolve(null);
    }
    return getCommandCenterStudentDetail(studentId);
  }, [studentId]);

  return useAsyncResource<StudentDetail | null>(loader, [loader], {
    enabled: Boolean(studentId),
    initialData: null,
    isEmpty: (data) => data === null,
    resourceName: "detalhe do aluno"
  });
}

export function useCommandCenterTimeline(studentId: string | null) {
  const loader = useCallback(() => {
    if (!studentId) {
      return Promise.resolve(null);
    }
    return getCommandCenterTimelineAnomalies(studentId);
  }, [studentId]);

  return useAsyncResource<TimelineAnomalies | null>(loader, [loader], {
    enabled: Boolean(studentId),
    initialData: null,
    isEmpty: (data) => data === null,
    resourceName: "timeline de anomalias"
  });
}
