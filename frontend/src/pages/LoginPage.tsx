import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../app/providers/AuthProvider";

type PreviewRole = "admin" | "mentor" | "aluno";

const ROLE_PRESETS: Record<
  PreviewRole,
  {
    label: string;
    eyebrow: string;
    description: string;
    destination: string;
    summary: string;
    email: string;
    password: string;
  }
> = {
  admin: {
    label: "Admin",
    eyebrow: "Operacao central",
    description: "Valida a visao de controle, relacionamento entre entidades e a futura camada de operacoes.",
    destination: "/app/admin",
    summary: "Usa autenticacao real local para destravar a operacao administrativa.",
    email: "admin@swaif.local",
    password: "admin123"
  },
  mentor: {
    label: "Mentor",
    eyebrow: "Decisao e acompanhamento",
    description: "Valida a leitura executiva da carteira, acompanhamento de alunos e tomada de decisao.",
    destination: "/app/matriz-renovacao",
    summary: "Pode usar autenticacao real local para navegar nas visoes operacionais ja integradas.",
    email: "mentor@swaif.local",
    password: "mentor123"
  },
  aluno: {
    label: "Aluno",
    eyebrow: "Progresso individual",
    description: "Valida a experiencia mais pessoal, com foco em radar, jornada e proximos marcos.",
    destination: "/app/aluno",
    summary: "Segue em modo preview para preservar o escopo incremental da fase administrativa.",
    email: "aline.rocha@swaif.demo",
    password: "aluno-preview"
  }
};

export function LoginPage() {
  const navigate = useNavigate();
  const { error, loading, login, loginPreview, isAuthenticated, isPreviewSession, user, logout } = useAuth();
  const [selectedRole, setSelectedRole] = useState<PreviewRole>("mentor");
  const [email, setEmail] = useState(ROLE_PRESETS.mentor.email);
  const [password, setPassword] = useState(ROLE_PRESETS.mentor.password);

  function applyPreset(role: PreviewRole) {
    setSelectedRole(role);
    setEmail(ROLE_PRESETS[role].email);
    setPassword(ROLE_PRESETS[role].password);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (selectedRole === "aluno") {
      loginPreview(email.trim(), selectedRole);
      navigate(ROLE_PRESETS[selectedRole].destination);
      return;
    }

    const success = await login(email.trim(), password);
    if (success) {
      navigate(ROLE_PRESETS[selectedRole].destination);
    }
  }

  return (
    <section className="login-shell">
      <div className="login-shell__backdrop" />
      <div className="login-shell__overlay" />
      <div className="login-grid">
        <aside className="login-hero">
          <img className="login-hero__logo" src="/branding/acelerador-logo.png" alt="Acelerador Medico" />
        </aside>

        <div className="login-panel">
          <div className="login-panel__frame">
            <div className="login-panel__header">
              <img className="login-panel__icon" src="/branding/acelerador-icon.png" alt="" aria-hidden="true" />
              <div className="login-panel__header-copy">
                <p className="login-panel__eyebrow">Acesso da fase 2</p>
                <h2 className="login-panel__title">Entrar na nova experiencia</h2>
              </div>
            </div>

            <p className="login-panel__intro">
              Admin e Mentor agora podem usar autenticacao real local. O perfil Aluno continua disponivel em modo preview
              enquanto a camada administrativa evolui por blocos pequenos.
            </p>

            <div className="login-role-picker" role="tablist" aria-label="Selecao de perfil">
              {(["admin", "mentor", "aluno"] as PreviewRole[]).map((role) => {
                const preset = ROLE_PRESETS[role];
                const isActive = role === selectedRole;

                return (
                  <button
                    key={role}
                    type="button"
                    className={isActive ? "login-role-card is-active" : "login-role-card"}
                    onClick={() => applyPreset(role)}
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
              <label className="login-form__field">
                <span>Usuario</span>
                <input
                  type="text"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="username"
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
                />
              </label>
              <p className="login-form__hint">
                Admin e Mentor usam credenciais locais do backend. Aluno segue em preview para preservar o escopo desta etapa.
              </p>
              {error ? (
                <p className="login-form__hint" role="alert">
                  {error}
                </p>
              ) : null}
              <button className="login-form__submit" type="submit" disabled={loading}>
                {loading ? "Entrando..." : `Entrar como ${ROLE_PRESETS[selectedRole].label}`}
              </button>
            </form>

            {isAuthenticated && isPreviewSession && (
              <div className="login-session-banner" role="status">
                <div>
                  <p className="login-session-banner__label">Sessao simulada ativa</p>
                  <strong>{user?.email}</strong>
                </div>
                <button type="button" onClick={logout}>
                  Limpar preview
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
