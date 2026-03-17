const envFromImportMeta = (() => {
  try {
    return import.meta && import.meta.env ? import.meta.env : {};
  } catch {
    return {};
  }
})();

const envFromProcess =
  typeof process !== "undefined" && process && process.env ? process.env : {};

function asNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const API_BASE_URL =
  envFromImportMeta.VITE_API_BASE_URL ||
  envFromProcess.VITE_API_BASE_URL ||
  envFromProcess.API_BASE_URL ||
  "http://127.0.0.1:8000";

export const HTTP_TIMEOUT_MS = asNumber(
  envFromImportMeta.VITE_HTTP_TIMEOUT_MS || envFromProcess.HTTP_TIMEOUT_MS,
  15000
);

