import { env } from "../config/env";
import { AppError, type ErrorPayload } from "./types";
import { emitUnauthorized } from "../auth/authEvents";
import { clearAccessToken, getAccessToken } from "../auth/tokenStorage";

function buildUrl(path: string): string {
  if (!path || !path.trim()) {
    throw new AppError({
      message: "Path HTTP inválido.",
      code: "HTTP_PATH_INVALID"
    });
  }

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${env.apiBaseUrl}${normalizedPath}`;
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function normalizeError(parsed: unknown, fallbackStatus: number): AppError {
  const payload = parsed as ErrorPayload;

  if (payload?.error && typeof payload.error === "object") {
    return new AppError({
      message: payload.error.message || "Erro inesperado.",
      httpStatus: payload.error.status ?? fallbackStatus,
      code: payload.error.code ?? "UNKNOWN_ERROR",
      details: payload.error.details ?? null
    });
  }

  return new AppError({
    message: "Erro inesperado.",
    httpStatus: fallbackStatus,
    code: "UNKNOWN_ERROR",
    details: null
  });
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
  token?: string | null;
  timeoutMs?: number;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = buildUrl(path);
  const method = options.method ?? "GET";
  const timeoutMs = options.timeoutMs ?? env.httpTimeoutMs;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    ...(options.headers ?? {})
  };
  const token = options.token === undefined ? getAccessToken() : options.token;

  if (options.body !== undefined && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal
    });

    const parsed = await parseBody(response);

    if (!response.ok) {
      const appError = normalizeError(parsed, response.status);
      if (appError.httpStatus === 401 && token) {
        clearAccessToken();
        emitUnauthorized({
          status: appError.httpStatus,
          code: appError.code,
          message: appError.message,
          method,
          path
        });
      }
      throw appError;
    }

    return parsed as T;
  } catch (error) {
    if (error instanceof AppError) {
      throw error;
    }

    const isAbort = error instanceof Error && error.name === "AbortError";
    throw new AppError({
      message: isAbort ? "Tempo limite de requisição excedido." : "Falha de rede ao chamar o backend.",
      code: isAbort ? "HTTP_TIMEOUT" : "NETWORK_ERROR",
      isNetworkError: true
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

export const httpClient = {
  get<T>(path: string, options: Omit<RequestOptions, "method" | "body"> = {}) {
    return request<T>(path, { ...options, method: "GET" });
  },
  post<T>(path: string, body: unknown, options: Omit<RequestOptions, "method" | "body"> = {}) {
    return request<T>(path, { ...options, method: "POST", body });
  },
  put<T>(path: string, body: unknown, options: Omit<RequestOptions, "method" | "body"> = {}) {
    return request<T>(path, { ...options, method: "PUT", body });
  },
  delete<T>(path: string, options: Omit<RequestOptions, "method" | "body"> = {}) {
    return request<T>(path, { ...options, method: "DELETE" });
  }
};
