import { afterEach, describe, expect, it, vi } from "vitest";

async function importHttpClientModule() {
  vi.resetModules();
  return import("../shared/api/httpClient");
}

describe("http client hardening", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("resolve requisicoes relativas a partir de VITE_API_BASE_URL", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const { httpClient } = await importHttpClientModule();

    await httpClient.get("/me");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/me",
      expect.objectContaining({
        method: "GET"
      })
    );
  });

  it("limpa sessao e emite unauthorized quando o backend responde 401", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            status: 401,
            code: "AUTH_INVALID",
            message: "Sessao expirada.",
            details: null
          }
        }),
        {
          status: 401,
          headers: { "Content-Type": "application/json" }
        }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const { httpClient } = await importHttpClientModule();
    const { onUnauthorized } = await import("../shared/auth/authEvents");
    const { getAccessToken, setAccessToken } = await import("../shared/auth/tokenStorage");
    const handler = vi.fn();
    const unsubscribe = onUnauthorized(handler);
    setAccessToken("token-expirado");

    await expect(httpClient.get("/me")).rejects.toMatchObject({
      httpStatus: 401,
      code: "AUTH_INVALID"
    });

    expect(getAccessToken()).toBeNull();
    expect(handler).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 401,
        code: "AUTH_INVALID",
        method: "GET",
        path: "/me"
      })
    );

    unsubscribe();
  });
});
