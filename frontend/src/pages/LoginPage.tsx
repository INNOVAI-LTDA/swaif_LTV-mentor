import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../app/providers/AuthProvider";
import { getDefaultRouteForRole, isKnownUserRole } from "../shared/auth/roleRouting";
import { env } from "../shared/config/env";

type PreviewRole = "admin" | "mentor" | "aluno";

const ROLE_PRESETS: Record<
  PreviewRole,
  {
    label: string;
    eyebrow: string;
    description: string;
    destination: string;
    summary: string;
  }
> = {
  admin: {
    label: "Admin",
    eyebrow: "Operacao central",
    description: "Acompanha governanca, cadastros principais e leitura administrativa da operacao.",
    destination: "/app/admin",
    summary: "Usa a autenticacao real configurada para a superficie administrativa."
  },
  mentor: {
    label: "Mentor",
    eyebrow: "Decisao e acompanhamento",
    description: "Acompanha carteira, sinais de risco e decisoes de acompanhamento.",
    destination: "/app/matriz-renovacao",
    summary: "Usa a autenticacao real configurada para navegar nas visoes operacionais disponiveis."
  },
  aluno: {
    label: "Aluno",
    eyebrow: "Progresso individual",
    description: "Acompanha a experiencia individual com foco em radar, jornada e proximos marcos.",
    destination: "/app/aluno",
    summary: "Segue restrito ao modo interno enquanto a experiencia autenticada do aluno evolui."
  }
};

export function LoginPage() {
  const navigate = useNavigate();
  const {
    error,
    errorCode,
    loading,
    login,
    loginPreview,
    isAuthenticated,
    isPreviewSession,
    user,
    logout,
    canUsePreviewLogin,
    sessionRecoveryPending,
    retrySessionValidation,
    clearPendingSession
  } = useAuth();
  const [selectedRole, setSelectedRole] = useState<PreviewRole>("admin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const availableRoles = [
    "admin",
    ...(env.internalMentorDemoEnabled ? (["mentor"] as const) : []),
    ...(canUsePreviewLogin ? (["aluno"] as const) : [])
  ] as PreviewRole[];
  const usesInternalAlunoPreview = canUsePreviewLogin && selectedRole === "aluno";
  const usesInternalMentorWorkspace = env.internalMentorDemoEnabled && selectedRole === "mentor";

  function selectRole(role: PreviewRole) {
    setSelectedRole(role);
    setEmail("");
    setPassword("");
  }

  useEffect(() => {
    if (!availableRoles.includes(selectedRole)) {
      setSelectedRole(availableRoles[0]);
    }
  }, [availableRoles, selectedRole]);

  useEffect(() => {
    if (isAuthenticated && user && isKnownUserRole(user.role)) {
      navigate(getDefaultRouteForRole(user.role), { replace: true });
    }
  }, [isAuthenticated, navigate, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (usesInternalAlunoPreview) {
      loginPreview(selectedRole);
      navigate(ROLE_PRESETS[selectedRole].destination);
      return;
    }

    const authenticatedUser = await login(email.trim(), password);
    if (authenticatedUser && isKnownUserRole(authenticatedUser.role)) {
      navigate(getDefaultRouteForRole(authenticatedUser.role));
    }
  }

  const loginErrorMessage =
    errorCode === "AUTH_ROLE_INVALID"
      ? "A autenticacao foi concluida, mas o backend retornou um perfil incompativel com esta entrega."
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
                <p className="login-panel__eyebrow">{env.appTagline}</p>
                <h2 className="login-panel__title">Entrar em {env.appName}</h2>
              </div>
            </div>

            <p className="login-panel__intro">
              {canUsePreviewLogin
                ? env.internalMentorDemoEnabled
                  ? "Admin usa a autenticacao publicada. Mentor e Aluno permanecem disponiveis apenas no modo interno para validacao controlada, sem credenciais predefinidas na interface."
                  : "Admin usa a autenticacao publicada. O perfil Aluno permanece disponivel apenas no modo interno para validacao controlada, sem credenciais predefinidas na interface."
                : env.internalMentorDemoEnabled
                  ? "Use as credenciais do ambiente configurado. A superficie de mentor permanece restrita ao modo interno local."
                  : "Use as credenciais do ambiente configurado para acessar as superficies protegidas publicadas."}
            </p>

            <div className="login-role-picker" role="tablist" aria-label="Selecao de perfil">
              {availableRoles.map((role) => {
                const preset = ROLE_PRESETS[role];
                const isActive = role === selectedRole;

                return (
                  <button
                    key={role}
                    type="button"
                    className={isActive ? "login-role-card is-active" : "login-role-card"}
                    onClick={() => selectRole(role)}
                    aria-pressed={isActive}
                  >
                    <span className="login-role-card__eyebrow">{preset.eyebrow}</span>
                    <strong>{preset.label}</strong>
                    <small>{preset.description}</small>
                  </button>
                );
              })}
            </div>

            <div className="login-profile-summary">
              <p className="login-profile-summary__label">Destino da validacao</p>
              <strong>{ROLE_PRESETS[selectedRole].label}</strong>
              <span>{ROLE_PRESETS[selectedRole].summary}</span>
            </div>

            <form className="login-form" onSubmit={(event) => void handleSubmit(event)}>
              {sessionRecoveryPending ? (
                <div className="login-session-banner" role="alert">
                  <div>
                    <p className="login-session-banner__label">Sessao pendente de validacao</p>
                    <strong>A autenticacao foi concluida, mas a validacao do perfil falhou temporariamente.</strong>
                    <p>Use Tentar novamente para validar sua sessao atual ou Limpar sessao para reiniciar o acesso.</p>
                  </div>
                  <div className="login-session-banner__actions">
                    <button type="button" onClick={() => void retrySessionValidation()} disabled={loading}>
                      Tentar novamente
                    </button>
                    <button type="button" onClick={clearPendingSession} disabled={loading}>
                      Limpar sessao
                    </button>
                  </div>
                </div>
              ) : null}
              {usesInternalAlunoPreview ? (
                <div className="login-session-banner" role="note">
                  <div>
                    <p className="login-session-banner__label">Acesso interno controlado</p>
                    <strong>O perfil Aluno usa uma sessao interna temporaria neste modo.</strong>
                    <p>Nenhuma credencial de demonstracao e exibida na interface para iniciar essa validacao.</p>
                  </div>
                </div>
              ) : (
                <>
                  <label className="login-form__field">
                    <span>Usuario</span>
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
                </>
              )}
              <p className="login-form__hint">
                {usesInternalAlunoPreview
                  ? "Esse caminho interno existe apenas para validacao controlada e nao representa o acesso publicado ao cliente."
                  : usesInternalMentorWorkspace
                    ? "A superficie de mentor segue disponivel apenas para validacao local controlada e nao faz parte do caminho publicado ao cliente."
                    : canUsePreviewLogin
                      ? "Admin usa a autenticacao configurada para o ambiente. O perfil Aluno segue restrito ao modo interno."
                      : "As credenciais deste ambiente sao geridas fora da interface. Nenhum usuario ou senha de demonstracao e exposto ao cliente."}
              </p>
              {loginErrorMessage ? (
                <p className="login-form__hint" role="alert">
                  {loginErrorMessage}
                </p>
              ) : null}
              <button className="login-form__submit" type="submit" disabled={loading || sessionRecoveryPending}>
                {loading ? "Entrando..." : `Entrar como ${ROLE_PRESETS[selectedRole].label}`}
              </button>
            </form>

            {isAuthenticated && isPreviewSession && (
              <div className="login-session-banner" role="status">
                  <div>
                    <p className="login-session-banner__label">Sessao interna ativa</p>
                    <strong>{user?.email}</strong>
                  </div>
                  <button type="button" onClick={logout}>
                    Encerrar sessao interna
                  </button>
                </div>
              )}
          </div>
        </div>
      </div>
    </section>
  );
}
