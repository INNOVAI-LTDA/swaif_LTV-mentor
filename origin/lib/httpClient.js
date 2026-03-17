import { API_BASE_URL, HTTP_TIMEOUT_MS } from "./apiConfig.js";
import { AppError, normalizeErrorPayload, shouldForceLogout } from "./errors.js";
import { clearAccessToken, getAccessToken } from "./authStorage.js";
import { emitUnauthorized } from "./httpEvents.js";
import { logHttpFailure } from "./integrationLogger.js";

function buildUrl(path) {
  if (!path) {
    throw new AppError({
      message: "Path HTTP invalido.",
      code: "HTTP_PATH_INVALID",
    });
  }
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseResponseBody(response) {
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function buildHeaders(headers, hasBody, token) {
  const normalized = { ...headers };
  if (hasBody && !normalized["Content-Type"]) {
    normalized["Content-Type"] = "application/json";
  }
  if (token) {
    normalized.Authorization = `Bearer ${token}`;
  }
  return normalized;
}

async function request(path, options = {}) {
  const {
    method = "GET",
    body,
    headers = {},
    token = getAccessToken(),
    signal,
    timeoutMs = HTTP_TIMEOUT_MS,
  } = options;

  const url = buildUrl(path);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  const mergedSignal = signal || controller.signal;

  try {
    const response = await fetch(url, {
      method,
      headers: buildHeaders(headers, body !== undefined, token),
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: mergedSignal,
    });

    const parsed = await parseResponseBody(response);

    if (!response.ok) {
      const normalized = normalizeErrorPayload(parsed, response.status);
      const appError = new AppError({
        message: normalized.message,
        httpStatus: normalized.httpStatus,
        code: normalized.code,
        details: normalized.details,
      });

      logHttpFailure({
        phase: "response",
        method,
        path,
        status: appError.httpStatus,
        code: appError.code,
        message: appError.message,
        details: appError.details,
      });

      if (token && shouldForceLogout(appError)) {
        clearAccessToken();
        emitUnauthorized({
          status: appError.httpStatus,
          code: appError.code,
          message: appError.message,
          method,
          path,
        });
      }

      throw appError;
    }

    return parsed;
  } catch (error) {
    if (error instanceof AppError) throw error;

    const aborted = error && error.name === "AbortError";
    const appError = new AppError({
      message: aborted
        ? "Tempo limite de requisicao excedido."
        : "Falha de rede ao chamar o backend.",
      httpStatus: 0,
      code: aborted ? "HTTP_TIMEOUT" : "NETWORK_ERROR",
      details: null,
      isNetworkError: true,
      cause: error,
    });

    logHttpFailure({
      phase: aborted ? "timeout" : "network",
      method,
      path,
      status: appError.httpStatus,
      code: appError.code,
      message: appError.message,
      details: appError.details,
    });

    throw appError;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const httpClient = {
  get(path, options = {}) {
    return request(path, { ...options, method: "GET" });
  },
  post(path, body, options = {}) {
    return request(path, { ...options, method: "POST", body });
  },
  put(path, body, options = {}) {
    return request(path, { ...options, method: "PUT", body });
  },
  delete(path, options = {}) {
    return request(path, { ...options, method: "DELETE" });
  },
};
