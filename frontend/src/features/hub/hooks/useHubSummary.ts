import { useMemo } from "react";
import { deriveCommandCenterTopKpis } from "../../../domain/adapters/commandCenterAdapter";
import { deriveMatrixKpis } from "../../../domain/adapters/matrixAdapter";
import { useCommandCenterStudents } from "../../../domain/hooks/useCommandCenter";
import { useRenewalMatrix } from "../../../domain/hooks/useMatrix";

export function useHubSummary() {
  const studentsResource = useCommandCenterStudents();
  const matrixResource = useRenewalMatrix("all");

  const commandKpis = useMemo(
    () => deriveCommandCenterTopKpis(studentsResource.data),
    [studentsResource.data]
  );

  const matrixKpis = useMemo(() => deriveMatrixKpis(matrixResource.data), [matrixResource.data]);

  const loading = studentsResource.loading || matrixResource.loading;
  const hasError = Boolean(studentsResource.error || matrixResource.error);
  const error = studentsResource.error || matrixResource.error;

  return {
    loading,
    hasError,
    error,
    studentsCount: studentsResource.data.length,
    matrixItemsCount: matrixResource.data.items.length,
    commandKpis,
    matrixKpis,
    refresh: async () => {
      await Promise.all([studentsResource.refresh(), matrixResource.refresh()]);
    }
  };
}
