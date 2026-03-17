import { useCallback } from "react";
import type { AdminMetricDto } from "../../contracts/adminMetric";
import { useAsyncResource } from "./useAsyncResource";
import { createAdminMetric, listAdminMetrics } from "../services/adminMetricService";

export function useAdminMetrics(pillarId: string | null) {
  const loader = useCallback(() => {
    if (!pillarId) {
      return Promise.resolve([]);
    }
    return listAdminMetrics(pillarId);
  }, [pillarId]);

  return useAsyncResource<AdminMetricDto[]>(loader, [loader], {
    enabled: Boolean(pillarId),
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista de metricas"
  });
}

export { createAdminMetric };
