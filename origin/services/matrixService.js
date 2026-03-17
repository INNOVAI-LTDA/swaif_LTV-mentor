import { httpClient } from "../lib/httpClient.js";
import { adaptMatrixPayload } from "../adapters/matrixAdapter.js";
import { normalizeMatrixFilter } from "../lib/matrixUtils.js";
import { logContractMismatch } from "../lib/integrationLogger.js";

export async function getRenewalMatrix(filter = "all") {
  const safeFilter = normalizeMatrixFilter(filter);
  const payload = await httpClient.get(
    `/admin/matriz-renovacao?filter=${encodeURIComponent(safeFilter)}`
  );
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    logContractMismatch({
      scope: "matrix.renewal",
      expected: "object",
      received: Array.isArray(payload) ? "array" : typeof payload,
      payload,
    });
    return adaptMatrixPayload({});
  }
  return adaptMatrixPayload(payload);
}
