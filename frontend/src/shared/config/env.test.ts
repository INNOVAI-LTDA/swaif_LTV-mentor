import { afterEach, describe, expect, it, vi } from "vitest";

async function importEnvModule() {
  vi.resetModules();
  return import("./env");
}

async function importEnvContractModule() {
  vi.resetModules();
  return import("./envContract");
}

describe("shared env config", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.resetModules();
  });

  it("normaliza o base path para a raiz ou subpaths com barra final", async () => {
    const { normalizeBasePath } = await importEnvContractModule();

    expect(normalizeBasePath(undefined)).toBe("/");
    expect(normalizeBasePath("/")).toBe("/");
    expect(normalizeBasePath("cliente")).toBe("/cliente/");
    expect(normalizeBasePath("/cliente/app/")).toBe("/cliente/app/");
  });

  it("exige VITE_API_BASE_URL explicito para qualquer deploy target", async () => {
    const { normalizeApiBaseUrl } = await importEnvContractModule();

    expect(() => normalizeApiBaseUrl("", "local")).toThrow("VITE_API_BASE_URL is required for all deploy targets.");
    expect(() => normalizeApiBaseUrl("", "client")).toThrow("VITE_API_BASE_URL is required for all deploy targets.");
  });

  it("valida deploy target e exige URL absoluta para builds de cliente", async () => {
    const { normalizeApiBaseUrl, normalizeDeployTarget, normalizeClientCode } = await importEnvContractModule();

    expect(normalizeDeployTarget("client")).toBe("client");
    expect(() => normalizeDeployTarget(undefined)).toThrow("VITE_DEPLOY_TARGET is required");
    expect(() => normalizeDeployTarget("preview")).toThrow("VITE_DEPLOY_TARGET must be either 'local' or 'client'.");
    expect(() => normalizeApiBaseUrl("api.example.com", "client")).toThrow("VITE_API_BASE_URL must be an absolute http(s) URL.");
    expect(() => normalizeApiBaseUrl("https://api.example.com?tenant=x", "client")).toThrow(
      "VITE_API_BASE_URL must not include query strings or fragments."
    );
    expect(() => normalizeApiBaseUrl("https://user:pass@api.example.com", "client")).toThrow(
      "VITE_API_BASE_URL must not include credentials."
    );
    expect(normalizeApiBaseUrl("https://api.example.com/base/", "client")).toBe("https://api.example.com/base");
    expect(() => normalizeClientCode("", "client")).toThrow("VITE_CLIENT_CODE is required for client deploys.");
    expect(() => normalizeClientCode("cliente x", "client")).toThrow(
      "VITE_CLIENT_CODE must contain only letters, numbers, hyphen, or underscore."
    );
    expect(normalizeClientCode("accmed-client", "client")).toBe("accmed-client");
  });

  it("bloqueia demo mode em deploy target client e mantem branding/base path", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "client");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com/");
    vi.stubEnv("VITE_APP_BASE_PATH", "/cliente");
    vi.stubEnv("VITE_ENABLE_DEMO_MODE", "true");
    vi.stubEnv("VITE_ENABLE_INTERNAL_MENTOR_DEMO", "true");
    vi.stubEnv("VITE_THEME_ACCENT_PRIMARY", "#123456");
    vi.stubEnv("VITE_CLIENT_CODE", "cliente-123");

    const { env } = await importEnvModule();

    expect(env.demoModeEnabled).toBe(false);
    expect(env.internalMentorDemoEnabled).toBe(false);
    expect(env.deployTarget).toBe("client");
    expect(env.apiBaseUrl).toBe("https://api.example.com");
    expect(env.brandingLogoUrl).toBe("/cliente/branding/app-logo.png");
    expect(env.routerBasePath).toBe("/cliente");
    expect(env.themeColors.accentPrimary).toBe("#123456");
  });

  it("mantem a superficie interna de mentor apenas em deploy local explicito", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.stubEnv("VITE_ENABLE_INTERNAL_MENTOR_DEMO", "true");

    const { env } = await importEnvModule();

    expect(env.internalMentorDemoEnabled).toBe(true);
  });

  it("permite clientCode opcional em deploy local mas valida quando presente", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.stubEnv("VITE_CLIENT_CODE", "cliente_01");

    const { env } = await importEnvModule();

    expect(env.clientCode).toBe("cliente_01");
  });

  it("falha ao carregar o runtime sem VITE_DEPLOY_TARGET explicito", async () => {
    vi.unstubAllEnvs();
    vi.stubEnv("VITE_DEPLOY_TARGET", "");
    vi.stubEnv("VITE_API_BASE_URL", "");

    await expect(importEnvModule()).rejects.toThrow("VITE_DEPLOY_TARGET is required");
  });
});
