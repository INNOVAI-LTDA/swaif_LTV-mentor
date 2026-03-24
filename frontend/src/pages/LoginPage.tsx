import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../app/providers/AuthProvider";
import { getDefaultRouteForRole, isKnownUserRole } from "../shared/auth/roleRouting";
import { env } from "../shared/config/env";

export function LoginPage() {
  const navigate = useNavigate();
  const {
    error,
    errorCode,
    loading,
    login,
    isAuthenticated,
    isPreviewSession,
    user,
    logout,
    sessionRecoveryPending,
    retrySessionValidation,
    clearPendingSession
  } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (isAuthenticated && user && isKnownUserRole(user.role)) {
      navigate(getDefaultRouteForRole(user.role), { replace: true });
    }
  }, [isAuthenticated, navigate, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const authenticatedUser = await login(email.trim(), password);
    if (authenticatedUser && isKnownUserRole(authenticatedUser.role)) {
      navigate(getDefaultRouteForRole(authenticatedUser.role));
    }
  }

  const loginErrorMessage =
    errorCode === "AUTH_ROLE_INVALID"
      ? "A autenticação foi concluída, mas o backend retornou um perfil incompatível com esta entrega."
      : error;

  return (
    <section className="login-shell">
      <div className="login-shell__backdrop" />
      <div className="login-shell__overlay" />
      <div className="login-grid">
        <aside className="login-hero">
          <img className="login-hero__logo" src={env.brandingLogoUrl} alt={env.clientName} />
        </aside>

        <div className="login-panel">
          <div className="login-panel__frame">
            <div className="login-panel__header">
              <img className="login-panel__icon" src={env.brandingIconUrl} alt="" aria-hidden="true" />
              <div className="login-panel__header-copy">
                <p className="login-panel__eyebrow">{env.appName}</p>
                <p className="login-panel__client">{env.clientName}</p>
              </div>
            </div>

            <form className="login-form" onSubmit={(event) => void handleSubmit(event)}>
              {sessionRecoveryPending ? (
                <div className="login-session-banner" role="alert">
                  <div>
                    <p className="login-session-banner__label">Sessão pendente de validação</p>
                    <strong>A autenticação foi concluída, mas a validação do perfil falhou temporariamente.</strong>
                    <p>Use Tentar novamente para validar sua sessão atual ou Limpar sessão para reiniciar o acesso.</p>
                  </div>
                  <div className="login-session-banner__actions">
                    <button type="button" onClick={() => void retrySessionValidation()} disabled={loading}>
                      Tentar novamente
                    </button>
                    <button type="button" onClick={clearPendingSession} disabled={loading}>
                  Limpar sessão
                    </button>
                  </div>
                </div>
              ) : null}
              <label className="login-form__field">
                <span>Usuário</span>
                <input
                  type="text"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="username"
                  disabled={sessionRecoveryPending}
                />
              </label>
              <label className="login-form__field">
                <span>Senha</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  autoComplete="current-password"
                  disabled={sessionRecoveryPending}
                />
              </label>
              {loginErrorMessage ? (
                <p className="login-form__hint" role="alert">
                  {loginErrorMessage}
                </p>
              ) : null}
              <button className="login-form__submit" type="submit" disabled={loading || sessionRecoveryPending}>
                {loading ? "Entrando..." : "Entrar"}
              </button>
            </form>

            {isAuthenticated && isPreviewSession && (
              <div className="login-session-banner" role="status">
                  <div>
                    <p className="login-session-banner__label">Sessão interna ativa</p>
                    <strong>{user?.email}</strong>
                  </div>
                  <button type="button" onClick={logout}>
                    Encerrar sessão interna
                  </button>
                </div>
              )}
          </div>
        </div>
      </div>
    </section>
  );
}
