import { useCallback } from "react";
import { useAsyncResource } from "./useAsyncResource";
import { getRenewalMatrix } from "../services/matrixService";
import { adaptMatrixPayload, normalizeMatrixFilter } from "../adapters/matrixAdapter";
import type { MatrixPayload } from "../models";

const EMPTY_MATRIX = adaptMatrixPayload({});

export function useRenewalMatrix(filter = "all") {
  const safeFilter = normalizeMatrixFilter(filter);

  const loader = useCallback(() => getRenewalMatrix(safeFilter), [safeFilter]);

  return useAsyncResource<MatrixPayload>(loader, [loader], {
    enabled: true,
    initialData: { ...EMPTY_MATRIX, filter: safeFilter },
    isEmpty: (data) => data.items.length === 0,
    resourceName: "matriz de renovação"
  });
}
