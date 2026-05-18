import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { createAdminProduct, getAdminProductDetail, listAdminProducts } from "../services/adminProductService";
import type { AdminProductDto } from "../../contracts/adminProduct";

export function useAdminProducts(clientId: string | null) {
  const loader = useCallback(() => {
    if (!clientId) {
      return Promise.resolve([]);
    }
    return listAdminProducts(clientId);
  }, [clientId]);

  return useAsyncResource<AdminProductDto[]>(loader, [loader], {
    enabled: Boolean(clientId),
    initialData: [],
    isEmpty: (data) => data.length === 0,
    resourceName: "lista de produtos"
  });
}

export function useAdminProductDetail(clientId: string | null, productId: string | null) {
  const loader = useCallback(() => {
    if (!clientId || !productId) {
      return Promise.resolve(null);
    }
    return getAdminProductDetail(clientId, productId);
  }, [clientId, productId]);

  return useAsyncResource<AdminProductDto | null>(loader, [loader], {
    enabled: Boolean(clientId && productId),
    initialData: null,
    isEmpty: (data) => data === null,
    resourceName: "detalhe do produto"
  });
}

export { createAdminProduct };
