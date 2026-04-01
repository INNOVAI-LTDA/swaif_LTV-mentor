import { render, screen } from "@testing-library/react";
import { Outlet, createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { authState, envState } = vi.hoisted(() => ({
  authState: {
    authReady: true,
    accessToken: null as string | null,
    isAuthenticated: false,
    user: null as { id: string; email: string; role: "admin" | "mentor" | "aluno" } | null
  },
  envState: {
    routerBasePath: "/",
    internalMentorSurfaceEnabled: false
  }
}));

vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({
    accessToken: authState.accessToken,
    user: authState.user,
    loading: false,
    error: null,
    errorCode: null,
    authReady: authState.authReady,
    isAuthenticated: authState.isAuthenticated,
    isPreviewSession: false,
    canUsePreviewLogin: false,
    sessionRecoveryPending: false,
    login: vi.fn(),
    loginPreview: vi.fn(),
    logout: vi.fn(),
    refreshMe: vi.fn(),
    retrySessionValidation: vi.fn(),
    clearPendingSession: vi.fn()
  })
}));

vi.mock("../app/layout/AppLayout", () => ({
  AppLayout: () => (
    <div>
      <span>shell</span>
      <Outlet />
    </div>
  )
}));

vi.mock("../shared/config/env", () => ({
  env: envState
}));

vi.mock("../pages/LoginPage", () => ({
  LoginPage: () => <h1>Entrar na nova experiencia</h1>
}));

vi.mock("../pages/NotFoundPage", () => ({
  NotFoundPage: () => <h1>Pagina nao encontrada</h1>
}));

vi.mock("../pages/AccessDeniedPage", () => ({
  AccessDeniedPage: () => <h1>Acesso negado</h1>
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
  StudentPage: () => <h1>Acompanhe seu radar de evolucao</h1>
}));

vi.mock("../features/admin/pages/AdminPage", () => ({
  AdminPage: () => <h1>Centro Institucional</h1>
}));

import { appRoutes } from "../app/routes";

function renderRoute(initialEntries: string[], basename?: string) {
  const router = createMemoryRouter(appRoutes, {
    basename,
    initialEntries
  });

  render(<RouterProvider router={router} />);
}

describe("app routes", () => {
  beforeEach(() => {
    authState.authReady = true;
    authState.accessToken = null;
    authState.isAuthenticated = false;
    authState.user = null;
    envState.internalMentorSurfaceEnabled = false;
  });

  it("renderiza a pagina de login", () => {
    renderRoute(["/login"]);

    expect(screen.getByRole("heading", { name: "Entrar na nova experiencia" })).toBeInTheDocument();
  });

  it("renderiza pagina 404 para rota desconhecida", () => {
    renderRoute(["/rota-inexistente"]);

    expect(screen.getByRole("heading", { name: "Pagina nao encontrada" })).toBeInTheDocument();
  });

  it("redireciona rota protegida para login quando nao existe sessao valida", async () => {
    renderRoute(["/app/aluno"]);

    expect(await screen.findByRole("heading", { name: "Entrar na nova experiencia" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Acompanhe seu radar de evolucao" })).not.toBeInTheDocument();
  });

  it("redireciona rota admin para acesso negado quando o usuario autenticado nao e admin", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = true;
    authState.user = { id: "usr_mentor", email: "mentor@cliente.test", role: "mentor" };

    renderRoute(["/app/admin"]);

    expect(await screen.findByRole("heading", { name: "Acesso negado" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Centro Institucional" })).not.toBeInTheDocument();
  });

  it("redireciona /app para a home da role autenticada", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = true;
    authState.user = { id: "usr_admin", email: "admin@cliente.test", role: "admin" };

    renderRoute(["/app"]);

    expect(await screen.findByRole("heading", { name: "Centro Institucional" })).toBeInTheDocument();
  });

  it("permite que mentor autenticado acesse a matriz mesmo com a flag interna desligada", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = true;
    authState.user = { id: "usr_mentor", email: "mentor@cliente.test", role: "mentor" };

    renderRoute(["/app/matriz-renovacao"]);

    expect(await screen.findByRole("heading", { name: "Matriz" })).toBeInTheDocument();
  });

  it("redireciona /app para a home publicada do mentor", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = true;
    authState.user = { id: "usr_mentor", email: "mentor@cliente.test", role: "mentor" };

    renderRoute(["/app"]);

    expect(await screen.findByRole("heading", { name: "Matriz" })).toBeInTheDocument();
  });

  it("renderiza a tela do admin para sessao administrativa valida", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = true;
    authState.user = { id: "usr_admin", email: "admin@cliente.test", role: "admin" };

    renderRoute(["/app/admin"]);

    expect(await screen.findByRole("heading", { name: "Centro Institucional" })).toBeInTheDocument();
  });

  it("resolve navegacao protegida sob um basename configurado", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = true;
    authState.user = { id: "usr_admin", email: "admin@cliente.test", role: "admin" };

    renderRoute(["/cliente/app/admin"], "/cliente");

    expect(await screen.findByRole("heading", { name: "Centro Institucional" })).toBeInTheDocument();
  });

  it("mantem rota protegida bloqueada quando existe token mas o usuario ainda nao foi validado", async () => {
    authState.accessToken = "token";
    authState.isAuthenticated = false;
    authState.user = null;

    renderRoute(["/app/radar"]);

    expect(await screen.findByRole("heading", { name: "Entrar na nova experiencia" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Radar" })).not.toBeInTheDocument();
  });

  it("redireciona /dashboard para a superficie protegida com basename default", async () => {
    renderRoute(["/dashboard"]);

    expect(await screen.findByRole("heading", { name: "Entrar na nova experiencia" })).toBeInTheDocument();
  });

  it("redireciona /dashboard para a superficie protegida respeitando basename", async () => {
    renderRoute(["/cliente/dashboard"], "/cliente");

    expect(await screen.findByRole("heading", { name: "Entrar na nova experiencia" })).toBeInTheDocument();
  });
});
