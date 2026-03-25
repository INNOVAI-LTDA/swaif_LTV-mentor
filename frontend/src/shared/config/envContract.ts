export type DeployTarget = "local" | "client";

export function normalizeDeployTarget(raw: string | undefined): DeployTarget {
  const candidate = (raw || "").trim().toLowerCase();
  if (!candidate) {
    throw new Error("VITE_DEPLOY_TARGET is required and must be either 'local' or 'client'.");
  }
  if (candidate === "local" || candidate === "client") {
    return candidate;
  }
  throw new Error("VITE_DEPLOY_TARGET must be either 'local' or 'client'.");
}

export function normalizeBasePath(raw: string | undefined): string {
  const candidate = (raw || "").trim();
  if (!candidate || candidate === "/") {
    return "/";
  }
  return `/${candidate.replace(/^\/+|\/+$/g, "")}/`;
}

export function normalizeApiBaseUrl(raw: string | undefined, deployTarget: DeployTarget): string {
  const candidate = (raw || "").trim();
  if (!candidate) {
    if (deployTarget === "local") {
      return "http://127.0.0.1:8000";
    }
    throw new Error("VITE_API_BASE_URL is required for client deploys.");
  }

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error("VITE_API_BASE_URL must be an absolute http(s) URL.");
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("VITE_API_BASE_URL must use http or https.");
  }

  if (parsed.username || parsed.password) {
    throw new Error("VITE_API_BASE_URL must not include credentials.");
  }

  if (parsed.search || parsed.hash) {
    throw new Error("VITE_API_BASE_URL must not include query strings or fragments.");
  }

  return `${parsed.origin}${parsed.pathname}`.replace(/\/+$/, "");
}

function isValidClientCode(candidate: string): boolean {
  return /^[A-Za-z0-9_-]+$/.test(candidate);
}

export function normalizeClientCode(raw: string | undefined, deployTarget: DeployTarget): string | null {
  const candidate = (raw || "").trim();
  if (!candidate) {
    if (deployTarget === "client") {
      throw new Error("VITE_CLIENT_CODE is required for client deploys.");
    }
    return null;
  }
  if (!isValidClientCode(candidate)) {
    throw new Error("VITE_CLIENT_CODE must contain only letters, numbers, hyphen, or underscore.");
  }
  return candidate;
}
