function safeSerialize(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function buildMeta(meta = {}) {
  return {
    ts: new Date().toISOString(),
    ...meta,
  };
}

export function logHttpFailure({
  phase = "http",
  path = "",
  method = "GET",
  status = 0,
  code = "UNKNOWN_ERROR",
  message = "Erro inesperado.",
  details = null,
} = {}) {
  const payload = buildMeta({
    phase,
    method,
    path,
    status,
    code,
    message,
    details: safeSerialize(details),
  });
  console.error("[frontend-integration][http-failure]", payload);
}

export function logContractMismatch({
  scope = "unknown",
  expected = "unknown",
  received = "unknown",
  payload = null,
} = {}) {
  const meta = buildMeta({
    scope,
    expected,
    received,
    payloadPreview: safeSerialize(payload)?.slice(0, 240) || null,
  });
  console.warn("[frontend-integration][contract-mismatch]", meta);
}

export function logResourceFailure({
  resource = "resource",
  status = 0,
  code = "UNKNOWN_ERROR",
  message = "Falha ao carregar recurso.",
} = {}) {
  const meta = buildMeta({
    resource,
    status,
    code,
    message,
  });
  console.error("[frontend-integration][resource-failure]", meta);
}

