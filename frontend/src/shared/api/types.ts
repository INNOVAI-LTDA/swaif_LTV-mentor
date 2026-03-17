export type ErrorPayload = {
  error?: {
    status?: number;
    code?: string;
    message?: string;
    details?: unknown;
  };
};

export class AppError extends Error {
  readonly httpStatus: number;
  readonly code: string;
  readonly details: unknown;
  readonly isNetworkError: boolean;

  constructor(params: {
    message: string;
    httpStatus?: number;
    code?: string;
    details?: unknown;
    isNetworkError?: boolean;
  }) {
    super(params.message);
    this.name = "AppError";
    this.httpStatus = params.httpStatus ?? 0;
    this.code = params.code ?? "UNKNOWN_ERROR";
    this.details = params.details ?? null;
    this.isNetworkError = params.isNetworkError ?? false;
  }
}

const STATUS_MESSAGES: Record<number, string> = {
  401: "Sessão expirada ou token inválido. Faça login novamente.",
  403: "Você não tem permissão para acessar este recurso.",
  404: "Recurso não encontrado.",
  409: "Conflito de regra de negócio.",
  422: "Dados inválidos para esta operação."
};

export function getHttpStatus(error: unknown): number {
  const status =
    error instanceof AppError
      ? error.httpStatus
      : Number((error as { httpStatus?: number } | null)?.httpStatus ?? 0);
  return Number.isFinite(status) ? status : 0;
}

export function toUserErrorMessage(error: unknown, fallback = "Falha ao carregar recurso."): string {
  const status = getHttpStatus(error);
  if (STATUS_MESSAGES[status]) {
    return STATUS_MESSAGES[status];
  }

  if (error instanceof AppError && error.message.trim()) {
    return error.message;
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}
