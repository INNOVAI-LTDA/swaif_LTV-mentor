import { afterEach, describe, expect, it, vi } from "vitest";

const postMock = vi.fn();
const getMock = vi.fn();

vi.mock("../shared/api/httpClient", () => ({
  httpClient: {
    post: postMock,
    get: getMock
  }
}));

async function importAuthServiceModule() {
  vi.resetModules();
  return import("../domain/services/authService");
}

describe("auth service hardening", () => {
  afterEach(() => {
    localStorage.clear();
    postMock.mockReset();
    getMock.mockReset();
    vi.resetModules();
  });

  it("mantem o token para retry quando o bootstrap do perfil falha por rede", async () => {
    const { login } = await importAuthServiceModule();
    const { AppError } = await import("../shared/api/types");
    postMock.mockResolvedValue({
      access_token: "token-retry",
      token_type: "bearer"
    });
    getMock.mockRejectedValue(
      new AppError({
        message: "Falha de rede ao chamar o backend.",
        code: "NETWORK_ERROR",
        isNetworkError: true
      })
    );

    const { getAccessToken } = await import("../shared/auth/tokenStorage");

    await expect(login({ email: "mentor@cliente.test", password: "senha-mentor-segura" })).rejects.toMatchObject({
      code: "AUTH_BOOTSTRAP_RETRYABLE",
      isNetworkError: true
    });
    expect(postMock).toHaveBeenCalledWith("/auth/login", { email: "mentor@cliente.test", password: "senha-mentor-segura" }, { token: null });
    expect(getAccessToken()).toBe("token-retry");
  });

  it("falha fechado e limpa token quando o backend devolve uma role desconhecida", async () => {
    const { login } = await importAuthServiceModule();
    postMock.mockResolvedValue({
      access_token: "token-invalido",
      token_type: "bearer"
    });
    getMock.mockResolvedValue({
      id: "usr_unknown",
      email: "unknown@swaif.local",
      role: "guest"
    });
    const { getAccessToken } = await import("../shared/auth/tokenStorage");

    await expect(login({ email: "unknown@swaif.local", password: "guest123" })).rejects.toMatchObject({
      code: "AUTH_ROLE_INVALID"
    });
    expect(getAccessToken()).toBeNull();
  });
});
