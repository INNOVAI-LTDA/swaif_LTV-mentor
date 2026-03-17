import { useCallback } from "react";
import type { AdminPillarDto } from "../../contracts/adminPillar";
import { useAsyncResource } from "./useAsyncResource";
import { createAdminPillar, listAdminPillars } from "../services/adminPillarService";

export function useAdminPillars(productId: string | null) {
  const loader = useCallback(() => {
    if (!productId) {
      return Promise.resolve([]);
    }
    return listAdminPillars(productId);
  }, [productId]);

  return useAsyncResource<AdminPillarDto[]>(loader, [loader], {
    enabled: Boolean(productId),
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista de pilares"
  });
}

export { createAdminPillar };
