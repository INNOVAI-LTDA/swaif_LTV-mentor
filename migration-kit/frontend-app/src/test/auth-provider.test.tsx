import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AppError } from "../shared/api/types";

const getMeMock = vi.fn();
const loginServiceMock = vi.fn();
const logoutServiceMock = vi.fn();

vi.mock("../domain/services/authService", () => ({
  getMe: getMeMock,
  login: loginServiceMock,
  logout: logoutServiceMock
}));

async function renderAuthProbe() {
  const { AuthProvider, useAuth } = await import("../app/providers/AuthProvider");

  function AuthProbe() {
    const auth = useAuth();

    return (
      <div>
        <span data-testid="auth-state">{auth.isAuthenticated ? "authenticated" : "unauthenticated"}</span>
        <span data-testid="preview-state">{auth.isPreviewSession ? "preview" : "real"}</span>
        <span data-testid="error-state">{auth.error ?? ""}</span>
        <span data-testid="error-code">{auth.errorCode ?? ""}</span>
        <span data-testid="recovery-state">{auth.sessionRecoveryPending ? "pending" : "clear"}</span>
      </div>
    );
  }

  await act(async () => {
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>
    );
  });
}

describe("auth provider hardening", () => {
  beforeEach(() => {
    localStorage.clear();
    getMeMock.mockReset();
    loginServiceMock.mockReset();
    logoutServiceMock.mockReset();
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("bloqueia sessao real nao validada quando /me falha por rede", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    localStorage.setItem("swaif_mvp_access_token", "token-pendente");
    getMeMock.mockRejectedValue(
      new AppError({
        message: "Falha de rede ao chamar o backend.",
        code: "NETWORK_ERROR",
        isNetworkError: true
      })
    );

    await renderAuthProbe();

    await waitFor(() => {
      expect(screen.getByTestId("auth-state").textContent).toBe("unauthenticated");
    });
    expect(screen.getByTestId("error-state").textContent).toBe("Falha de rede ao chamar o backend.");
    expect(screen.getByTestId("error-code").textContent).toBe("NETWORK_ERROR");
    expect(screen.getByTestId("recovery-state").textContent).toBe("pending");
  });

  it("remove preview salvo quando demo mode esta desligado ou invalido", async () => {
    vi.stubEnv("VITE_DEPLOY_TARGET", "client");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com");
    localStorage.setItem("swaif_mvp_preview_session", JSON.stringify({ email: "", role: "guest", token: "" }));

    await renderAuthProbe();

    await waitFor(() => {
      expect(screen.getByTestId("preview-state").textContent).toBe("real");
    });
    expect(localStorage.getItem("swaif_mvp_preview_session")).toBeNull();
  });
});
