function parseTimeout(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return parsed;
}

function normalizeBaseUrl(raw: string | undefined): string {
  const candidate = (raw || "").trim();
  if (!candidate) {
    return "http://127.0.0.1:8000";
  }
  return candidate.replace(/\/+$/, "");
}

export const env = {
  apiBaseUrl: normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL),
  httpTimeoutMs: parseTimeout(import.meta.env.VITE_HTTP_TIMEOUT_MS, 15000)
};
