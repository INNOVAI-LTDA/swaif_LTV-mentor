import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getRenewalMatrix } from "../services/matrixService.js";
import { normalizeMatrixFilter } from "../lib/matrixUtils.js";

export function useRenewalMatrix(filter = "all") {
  const safeFilter = normalizeMatrixFilter(filter);

  const loader = useCallback(() => getRenewalMatrix(safeFilter), [safeFilter]);
  const resource = useAsyncResource(loader, [loader], {
    enabled: true,
    initialData: {
      filter: safeFilter,
      items: [],
      kpis: {
        totalLTV: 0,
        criticalRenewals: 0,
        rescueCount: 0,
        avgEngagement: 0,
      },
    },
    resourceName: "matriz de renovacao",
  });

  return {
    data: resource.data || {
      filter: safeFilter,
      items: [],
      kpis: {
        totalLTV: 0,
        criticalRenewals: 0,
        rescueCount: 0,
        avgEngagement: 0,
      },
    },
    loading: resource.loading,
    error: resource.error,
    refresh: resource.refresh,
  };
}
