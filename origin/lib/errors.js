export class AppError extends Error {
  constructor({
    message,
    httpStatus = 0,
    code = "UNKNOWN_ERROR",
    details = null,
    isNetworkError = false,
    cause = null,
  }) {
    super(message || "Erro inesperado.");
    this.name = "AppError";
    this.httpStatus = httpStatus;
    this.code = code;
    this.details = details;
    this.isNetworkError = isNetworkError;
    this.cause = cause;
  }
}

const STATUS_MESSAGES = {
  401: "Sessao expirada ou token invalido. Faca login novamente.",
  403: "Voce nao tem permissao para acessar este recurso.",
  404: "Recurso nao encontrado.",
  409: "Conflito de dados. Atualize e tente novamente.",
  422: "Dados invalidos para esta operacao.",
};

const AUTH_ERROR_CODES = new Set([
  "AUTH_INVALID_TOKEN",
  "AUTH_EXPIRED_TOKEN",
  "INVALID_TOKEN",
  "TOKEN_EXPIRED",
  "UNAUTHORIZED",
]);

export function normalizeErrorPayload(payload, fallbackStatus = 0) {
  if (payload && payload.error && typeof payload.error === "object") {
    return {
      httpStatus: payload.error.status || fallbackStatus,
      code: payload.error.code || "UNKNOWN_ERROR",
      message: payload.error.message || "Erro inesperado.",
      details:
        payload.error.details === undefined ? null : payload.error.details,
    };
  }

  if (payload && typeof payload === "object") {
    return {
      httpStatus: fallbackStatus,
      code: payload.code || "UNKNOWN_ERROR",
      message: payload.message || "Erro inesperado.",
      details: payload.details === undefined ? null : payload.details,
    };
  }

  return {
    httpStatus: fallbackStatus,
    code: "UNKNOWN_ERROR",
    message: "Erro inesperado.",
    details: null,
  };
}

export function getHttpStatus(error) {
  const status = Number(error?.httpStatus || 0);
  return Number.isFinite(status) ? status : 0;
}

export function toUserErrorMessage(error, fallbackMessage = "Falha ao carregar recurso.") {
  const status = getHttpStatus(error);
  if (STATUS_MESSAGES[status]) {
    return STATUS_MESSAGES[status];
  }
  if (error && typeof error.message === "string" && error.message.trim()) {
    return error.message;
  }
  return fallbackMessage;
}

export function shouldForceLogout(error) {
  const status = getHttpStatus(error);
  if (status === 401) return true;
  const code = typeof error?.code === "string" ? error.code.toUpperCase() : "";
  return AUTH_ERROR_CODES.has(code);
}
