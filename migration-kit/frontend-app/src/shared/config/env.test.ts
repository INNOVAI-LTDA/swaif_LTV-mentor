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

  it("mantem fallback localhost quando o helper permite ambiente local", async () => {
    const { normalizeApiBaseUrl } = await importEnvContractModule();

    expect(normalizeApiBaseUrl("", "local")).toBe("http://127.0.0.1:8000");
  });

  it("falha quando o helper recebe build client-safe sem api definida", async () => {
    const { normalizeApiBaseUrl } = await importEnvContractModule();

    expect(() => normalizeApiBaseUrl("", "client")).toThrow("VITE_API_BASE_URL is required for client deploys.");
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
    vi.stubEnv("VITE_ENABLE_INTERNAL_MENTOR_SURFACE", "true");
    vi.stubEnv("VITE_THEME_ACCENT_PRIMARY", "#123456");
    vi.stubEnv("VITE_CLIENT_CODE", "cliente-123");

    const { env } = await importEnvModule();

    expect(env.demoModeEnabled).toBe(false);
    expect(env.internalMentorSurfaceEnabled).toBe(false);
    expect(env.deployTarget).toBe("client");
    expect(env.apiBaseUrl).toBe("https://api.example.com");
    expect(env.brandingLogoUrl).toBe("/cliente/branding/app-logo.png");
    expect(env.routerBasePath).toBe("/cliente");
    expect(env.themeColors.accentPrimary).toBe("#123456");
  });

  it("mantem a superficie interna de mentor apenas em deploy local explicito", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.stubEnv("VITE_ENABLE_INTERNAL_MENTOR_SURFACE", "true");

    const { env } = await importEnvModule();

    expect(env.internalMentorSurfaceEnabled).toBe(true);
  });

  it("permite clientCode opcional em deploy local mas valida quando presente", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.stubEnv("VITE_CLIENT_CODE", "cliente_01");

    const { env } = await importEnvModule();

    expect(env.clientCode).toBe("cliente_01");
  });

  it("BrandPack: contrato de marca tem todos os campos obrigatorios preenchidos", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "client");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("VITE_CLIENT_CODE", "testclient");
    vi.stubEnv("VITE_APP_BASE_PATH", "/");
    vi.stubEnv("VITE_CLIENT_NAME", "Cliente Teste");
    vi.stubEnv("VITE_APP_NAME", "Plataforma Teste");
    vi.stubEnv("VITE_APP_TAGLINE", "Tagline de teste");
    vi.stubEnv("VITE_SHELL_SUBTITLE", "Subtitulo de teste");
    vi.stubEnv("VITE_BRANDING_ICON_PATH", "branding/icon.png");
    vi.stubEnv("VITE_BRANDING_LOGO_PATH", "branding/logo.png");
    vi.stubEnv("VITE_BRANDING_LOGIN_HERO_PATH", "branding/hero.png");
    vi.stubEnv("VITE_THEME_ACCENT_PRIMARY", "#0070f3");
    vi.stubEnv("VITE_THEME_BG_PRIMARY", "#0a0a0a");

    const { env } = await importEnvModule();

    // All BrandPack fields must be present and non-empty
    expect(env.clientCode).toBe("testclient");
    expect(env.clientName).toBe("Cliente Teste");
    expect(env.appName).toBe("Plataforma Teste");
    expect(env.appTagline).toBe("Tagline de teste");
    expect(env.shellSubtitle).toBe("Subtitulo de teste");
    expect(env.brandingIconUrl).toBe("/branding/icon.png");
    expect(env.brandingLogoUrl).toBe("/branding/logo.png");
    expect(env.brandingLoginHeroUrl).toBe("/branding/hero.png");
    // Theme color tokens override correctly
    expect(env.themeColors.accentPrimary).toBe("#0070f3");
    expect(env.themeColors.bgPrimary).toBe("#0a0a0a");
    // Remaining tokens fall back to defaults
    expect(env.themeColors.textPrimary).toBe("#ffffff");
    expect(env.themeColors.textSecondary).toBe("#bfbfbf");
  });

  it("BrandPack: campos de tema tem valores padrao quando env nao define tokens", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");

    const { env } = await importEnvModule();

    expect(env.themeColors.bgPrimary).toBe("#090909");
    expect(env.themeColors.bgSecondary).toBe("#121212");
    expect(env.themeColors.accentPrimary).toBe("#fab800");
    expect(env.themeColors.accentSecondary).toBe("#ffbd00");
    expect(env.themeColors.success).toBe("#39b56a");
    expect(env.themeColors.warning).toBe("#d9a100");
    expect(env.themeColors.danger).toBe("#d64545");
  });

  it("BrandPack: base path e resolvido corretamente nos asset paths de branding", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "client");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com");
    vi.stubEnv("VITE_CLIENT_CODE", "testclient");
    vi.stubEnv("VITE_APP_BASE_PATH", "/cliente/");
    vi.stubEnv("VITE_BRANDING_ICON_PATH", "branding/custom-icon.png");

    const { env } = await importEnvModule();

    expect(env.brandingIconUrl).toBe("/cliente/branding/custom-icon.png");
    expect(env.appBasePath).toBe("/cliente/");
  });

  it("carrega o runtime com a baseline local quando nao ha stub explicito", async () => {
    vi.unstubAllEnvs();

    const { env } = await importEnvModule();

    expect(env.deployTarget).toBe("local");
    expect(env.isLocalDeployTarget).toBe(true);
    expect(env.clientCode).toBe("local");
    expect(env.apiBaseUrl).toBe("http://127.0.0.1:8000");
  });
});
