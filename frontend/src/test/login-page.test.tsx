import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginPage } from "../pages/LoginPage";

const { navigateMock, loginMock, loginPreviewMock, logoutMock, retrySessionValidationMock, clearPendingSessionMock, authState, envState } =
  vi.hoisted(() => ({
    navigateMock: vi.fn(),
    loginMock: vi.fn(),
    loginPreviewMock: vi.fn(),
    logoutMock: vi.fn(),
    retrySessionValidationMock: vi.fn(),
    clearPendingSessionMock: vi.fn(),
    authState: {
      error: null as string | null,
      errorCode: null as string | null,
      loading: false,
      isAuthenticated: false,
      isPreviewSession: false,
      sessionRecoveryPending: false,
      user: null as { email: string } | null,
      canUsePreviewLogin: false
    },
    envState: {
      appName: "Gamma",
      appTagline: "Operacao segura",
      brandingIconUrl: "/branding/app-icon.png",
      brandingLogoUrl: "/branding/app-logo.png",
      clientName: "AccMed",
      internalMentorDemoEnabled: false
    }
  }));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock
  };
});

vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({
    error: authState.error,
    errorCode: authState.errorCode,
    loading: authState.loading,
    login: loginMock,
    loginPreview: loginPreviewMock,
    isAuthenticated: authState.isAuthenticated,
    isPreviewSession: authState.isPreviewSession,
    sessionRecoveryPending: authState.sessionRecoveryPending,
    user: authState.user,
    logout: logoutMock,
    canUsePreviewLogin: authState.canUsePreviewLogin,
    retrySessionValidation: retrySessionValidationMock,
    clearPendingSession: clearPendingSessionMock,
    refreshMe: vi.fn(),
    authReady: true,
    accessToken: null
  })
}));

vi.mock("../shared/config/env", () => ({
  env: envState
}));

function renderLoginPage() {
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe("login page deployment modes", () => {
  beforeEach(() => {
    authState.error = null;
    authState.errorCode = null;
    authState.loading = false;
    authState.isAuthenticated = false;
    authState.isPreviewSession = false;
    authState.sessionRecoveryPending = false;
    authState.user = null;
    authState.canUsePreviewLogin = false;
    envState.internalMentorDemoEnabled = false;
    navigateMock.mockReset();
    loginMock.mockReset();
    loginPreviewMock.mockReset();
    logoutMock.mockReset();
    retrySessionValidationMock.mockReset();
    clearPendingSessionMock.mockReset();
    loginMock.mockResolvedValue({ id: "usr_mentor", email: "mentor@cliente.test", role: "mentor" });
  });

  it("publica apenas o acesso admin quando a superficie mentor-demo interna esta desligada", () => {
    renderLoginPage();

    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
    expect(screen.queryByText("Mentor")).not.toBeInTheDocument();
    expect(screen.queryByText("Aluno")).not.toBeInTheDocument();
    expect(screen.queryByText(/Use as credenciais do ambiente configurado/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Nenhum usuario ou senha de demonstracao/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Usuário")).toBeInTheDocument();
    expect(screen.getByLabelText("Senha")).toBeInTheDocument();
    expect(screen.getByText("AccMed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
  });

  it("mantem apenas a entrada de credenciais mesmo quando a superficie interna local esta habilitada", () => {
    envState.internalMentorDemoEnabled = true;

    renderLoginPage();

    expect(screen.queryByText("Mentor")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Usuário")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
  });

  it("navega pela role autenticada retornada pelo backend", async () => {
    loginMock.mockResolvedValue({ id: "usr_mentor", email: "mentor@cliente.test", role: "mentor" });

    renderLoginPage();

    fireEvent.change(screen.getByLabelText("Usuário"), { target: { value: "mentor@cliente.test" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-mentor-segura" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/app/matriz-renovacao");
    });
  });

  it("nao navega quando a autenticacao nao entrega uma role valida", async () => {
    loginMock.mockResolvedValue(null);
    authState.error = "Perfil da conta nao reconhecido.";
    authState.errorCode = "AUTH_ROLE_INVALID";

    renderLoginPage();

    fireEvent.change(screen.getByLabelText("Usuário"), { target: { value: "admin@cliente.test" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-admin-segura" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalled();
    });
    expect(navigateMock).not.toHaveBeenCalled();
    expect(
      screen.getByText("A autenticação foi concluída, mas o backend retornou um perfil incompatível com esta entrega.")
    ).toBeInTheDocument();
  });

  it("exibe banner de recuperacao de sessao e bloqueia novo submit", () => {
    authState.sessionRecoveryPending = true;
    authState.error = "Falha ao validar seu perfil apos autenticar.";
    authState.errorCode = "AUTH_BOOTSTRAP_RETRYABLE";

    renderLoginPage();

    expect(screen.getByText("Sessão pendente de validação")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tentar novamente" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Limpar sessão" })).toBeInTheDocument();
    expect(screen.getByLabelText("Usuário")).toBeDisabled();
    expect(screen.getByLabelText("Senha")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Entrar" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    fireEvent.click(screen.getByRole("button", { name: "Limpar sessão" }));

    expect(retrySessionValidationMock).toHaveBeenCalled();
    expect(clearPendingSessionMock).toHaveBeenCalled();
  });
});
