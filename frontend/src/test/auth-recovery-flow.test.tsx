import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Outlet, RouterProvider, createMemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { appRoutes } from "../app/routes";
import { AppError } from "../shared/api/types";
import { setAccessToken } from "../shared/auth/tokenStorage";

const { getMeMock, loginServiceMock, logoutServiceMock, envState } = vi.hoisted(() => ({
  getMeMock: vi.fn(),
  loginServiceMock: vi.fn(),
  logoutServiceMock: vi.fn(),
  envState: {
    routerBasePath: "/",
    internalMentorDemoEnabled: true
  }
}));

vi.mock("../domain/services/authService", () => ({
  getMe: getMeMock,
  login: loginServiceMock,
  logout: logoutServiceMock
}));

vi.mock("../shared/config/env", () => ({
  env: {
    deployTarget: "local",
    isLocalDeployTarget: true,
    appBasePath: "/",
    routerBasePath: envState.routerBasePath,
    apiBaseUrl: "http://127.0.0.1:8000",
    httpTimeoutMs: 15000,
    demoModeEnabled: false,
    internalMentorDemoEnabled: envState.internalMentorDemoEnabled,
    clientName: "Cliente",
    appName: "Plataforma de Mentoria",
    appTagline: "Acompanhamento com visao operacional",
    shellSubtitle: "Operacao, acompanhamento e governanca",
    brandingIconUrl: "/branding/app-icon.png",
    brandingLogoUrl: "/branding/app-logo.png",
    brandingLoginHeroUrl: "/branding/login-hero.png"
  }
}));

vi.mock("../app/layout/AppLayout", () => ({
  AppLayout: () => (
    <div data-testid="app-shell">
      <main>
        <Outlet />
      </main>
    </div>
  )
}));

vi.mock("../features/hub/pages/HubPage", () => ({
  HubPage: () => <h1>Hub</h1>
}));

vi.mock("../features/command-center/pages/CommandCenterPage", () => ({
  CommandCenterPage: () => <h1>Centro de comando</h1>
}));

vi.mock("../features/radar/pages/RadarPage", () => ({
  RadarPage: () => <h1>Radar</h1>
}));

vi.mock("../features/matrix/pages/MatrixPage", () => ({
  MatrixPage: () => <h1>Matriz</h1>
}));

vi.mock("../features/student/pages/StudentPage", () => ({
  StudentPage: () => <h1>Aluno</h1>
}));

vi.mock("../features/admin/pages/AdminPage", () => ({
  AdminPage: () => <h1>Admin</h1>
}));

describe("auth recovery flow", () => {
  beforeEach(() => {
    localStorage.clear();
    loginServiceMock.mockReset();
    getMeMock.mockReset();
    logoutServiceMock.mockReset();
    envState.internalMentorDemoEnabled = true;
    envState.routerBasePath = "/";
    vi.stubEnv("VITE_DEPLOY_TARGET", "local");
    loginServiceMock.mockImplementation(async () => {
      setAccessToken("token-recovery");
      throw new AppError({
        message: "Autenticacao concluida, mas nao foi possivel validar seu perfil. Tente novamente.",
        code: "AUTH_BOOTSTRAP_RETRYABLE",
        isNetworkError: true
      });
    });
    getMeMock
      .mockRejectedValueOnce(
        new AppError({
          message: "Falha de rede ao chamar o backend.",
          code: "NETWORK_ERROR",
          isNetworkError: true
        })
      )
      .mockResolvedValue({
        id: "usr_mentor",
        email: "mentor@cliente.test",
        role: "mentor"
      });
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("bloqueia rota protegida, mostra banner de recuperacao e recupera a sessao apos retry", async () => {
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/login"]
    });

    const { AuthProvider } = await import("../app/providers/AuthProvider");

    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: /Decisao e acompanhamento Mentor/i }));
    fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "mentor@cliente.test" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-mentor-segura" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar como Mentor" }));

    expect(await screen.findByText("Sessao pendente de validacao")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Matriz" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Matriz" })).toBeInTheDocument();
    });
  });
});
