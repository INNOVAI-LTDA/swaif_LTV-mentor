import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getAdminClientDetail, listAdminClients } from "../services/adminClientService";
import type { AdminClientDto } from "../../contracts/adminClient";

export function useAdminClients(enabled = true) {
  const loader = useCallback(() => listAdminClients(), []);
  return useAsyncResource<AdminClientDto[]>(loader, [loader], {
    enabled,
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista de clientes"
  });
}

export function useAdminClientDetail(clientId: string | null, enabled = true) {
  const loader = useCallback(() => {
    if (!clientId) {
      return Promise.resolve(null);
    }
    return getAdminClientDetail(clientId);
  }, [clientId]);

  return useAsyncResource<AdminClientDto | null>(loader, [loader], {
    enabled: enabled && Boolean(clientId),
    initialData: null,
    isEmpty: (data) => data === null,
    resourceName: "detalhe do cliente"
  });
}
