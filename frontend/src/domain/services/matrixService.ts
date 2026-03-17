import { adaptMatrixPayload, normalizeMatrixFilter } from "../adapters/matrixAdapter";
import { httpClient } from "../../shared/api/httpClient";
import type { MatrixPayload } from "../models";

export async function getRenewalMatrix(filter = "all"): Promise<MatrixPayload> {
  const safeFilter = normalizeMatrixFilter(filter);
  const payload = await httpClient.get<unknown>(`/mentor/matriz-renovacao?filter=${encodeURIComponent(safeFilter)}`);
  return adaptMatrixPayload(payload);
}
