import { useCallback } from "react";
import type { AdminMentorDto } from "../../contracts/adminMentor";
import { useAsyncResource } from "./useAsyncResource";
import { createAdminMentor, listAdminMentors } from "../services/adminMentorService";

export function useAdminMentors(productId: string | null) {
  const loader = useCallback(() => {
    if (!productId) {
      return Promise.resolve([]);
    }
    return listAdminMentors(productId);
  }, [productId]);

  return useAsyncResource<AdminMentorDto[]>(loader, [loader], {
    enabled: Boolean(productId),
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista de mentores"
  });
}

export { createAdminMentor };
