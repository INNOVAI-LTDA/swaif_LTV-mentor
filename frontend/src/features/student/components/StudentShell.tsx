import type { ReactNode } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import "../student-shell.css";
import { env } from "../../../shared/config/env";
import { useStudentProducts } from "../hooks/useStudentProducts";
import { useStudentMentors } from "../hooks/useStudentMentors";
import { useStudentProfile } from "../hooks/useStudentProfile";

type StudentShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  metrics?: Array<{ label: string; value: string; tone?: "neutral" | "accent" | "success" | "warning" }>;
  children: ReactNode;
};

type SupportPanelKey = "produtos" | "mentores" | "usuario";

type SupportPanelItem = {
  title: string;
  meta: string;
  detail: string;
  section?: string;
  cta?: string;
};

type MainViewKey = "radar" | "timeline" | "indicadores" | "jornada";

const MAIN_NAV: Array<{ key: MainViewKey; label: string; to: string }> = [
  { key: "radar", label: "Radar de Evolucao", to: "/app/aluno" },
  { key: "timeline", label: "Linha do Tempo", to: "/app/aluno" },
  { key: "indicadores", label: "Indicadores", to: "/app/aluno" },
  { key: "jornada", label: "Sua Jornada", to: "/app/aluno" }
];

const SUPPORT_PANELS: Record<SupportPanelKey, { label: string; title: string; description: string; items: SupportPanelItem[] }> = {
  produtos: {
    label: "Produtos",
    title: "Produtos vinculados a voce",
    description: "Lista dos programas e modulos em que voce esta ativo dentro da sua jornada atual.",
    items: []
  },
  mentores: {
    label: "Mentores",
    title: "Mentores vinculados a voce",
    description: "Profissionais que acompanham sua jornada e sustentam os proximos avancos do programa.",
    items: []
  },
  usuario: {
    label: "Minha Conta",
    title: "Minha Conta",
    description: "Atalhos pessoais da sua conta para acesso futuro a configuracoes e dados do seu perfil.",
    items: [
      {
        title: "Perfil",
        meta: "Dados da sua conta",
        detail: "Informacoes pessoais e de acesso.",
        section: "perfil",
        cta: "Abrir"
      }
    ]
  }
};



function isSupportPanel(value: string | null): value is SupportPanelKey {
  return value === "produtos" || value === "mentores" || value === "usuario";
}

export function StudentShell({ eyebrow, title, description, actions, metrics = [], children }: StudentShellProps) {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const searchPanel = searchParams.get("panel");
  const searchSection = searchParams.get("section");
  const searchView = searchParams.get("view");
  const panelKey = isSupportPanel(searchPanel) ? searchPanel : null;
  // Fetch data for support panels
  const { products, loading: loadingProducts, error: errorProducts } = useStudentProducts();
  const { mentors, loading: loadingMentors, error: errorMentors } = useStudentMentors();
  const { profile, loading: loadingProfile, error: errorProfile } = useStudentProfile();

  const panel = panelKey ? SUPPORT_PANELS[panelKey] : null;
  const activePanelKey = panelKey ?? "produtos";
  const activeView: MainViewKey =
    searchView === "timeline" || searchView === "indicadores" || searchView === "jornada" ? searchView : "radar";

  function buildJourneySearch(defaultView = "radar") {
    const params = new URLSearchParams(searchParams);
    params.set("view", defaultView);
    params.delete("panel");
    params.delete("section");
    const nextSearch = params.toString();
    return nextSearch ? `?${nextSearch}` : "";
  }

  function buildSearch(panelValue: SupportPanelKey, sectionValue?: string) {
    const params = new URLSearchParams(searchParams);
    params.set("panel", panelValue);

    if (panelValue === "usuario" && sectionValue) {
      params.set("section", sectionValue);
    } else {
      params.delete("section");
    }

    return `?${params.toString()}`;
  }

  return (
    <section className="student-shell">
      <div className="student-shell__backdrop" />
      <div className={panel ? "student-shell__layout student-shell__layout--with-rail" : "student-shell__layout"}>
        <aside className="student-sidebar">
          <div className="student-sidebar__brand">
            <img src={env.brandingIconUrl} alt="" aria-hidden="true" />
            <div>
              <p>Aluno</p>
              <strong>{env.clientName}</strong>
            </div>
          </div>

          <div className="student-sidebar__block">
            <span className="student-sidebar__label">Visao principal</span>
            <nav className="student-sidebar__nav" aria-label="Navegacao do aluno">
              {MAIN_NAV.map((item) => (
                <Link
                  key={item.key}
                  to={{ pathname: item.to, search: buildJourneySearch(item.key) }}
                  className={activeView === item.key ? "student-sidebar__link is-active" : "student-sidebar__link"}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="student-sidebar__block">
            <span className="student-sidebar__label">Areas de apoio</span>
            <div className="student-sidebar__nav student-sidebar__nav--secondary">
              {(Object.keys(SUPPORT_PANELS) as SupportPanelKey[]).map((key) => (
                <Link
                  key={key}
                  to={{ pathname: location.pathname, search: buildSearch(key) }}
                  className={panelKey === key ? "student-sidebar__link is-secondary-active" : "student-sidebar__link is-secondary"}
                >
                  {SUPPORT_PANELS[key].label}
                </Link>
              ))}
            </div>
          </div>

          <div className="student-sidebar__spotlight">
            <span className="student-sidebar__label">Jornada do aluno</span>
            <strong>Visao integrada para acompanhar evolucao, indicadores e proximos passos.</strong>
            <p>Leitura orientada para progresso continuo e acao taticamente priorizada.</p>
          </div>
        </aside>

        <div className="student-main">
          <header className="student-header">
            <div>
              <p className="student-header__eyebrow">{eyebrow}</p>
              <h1>{title}</h1>
              <p>{description}</p>
            </div>
            {actions ? <div className="student-header__actions">{actions}</div> : null}
          </header>

          {metrics.length > 0 && (
            <section className="student-metrics">
              {metrics.map((metric) => (
                <article
                  key={`${metric.label}-${metric.value}`}
                  className={metric.tone ? `student-metric student-metric--${metric.tone}` : "student-metric"}
                >
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </article>
              ))}
            </section>
          )}

          <div className="student-main__content">{children}</div>
        </div>

        <aside className={panel ? "student-rail is-open" : "student-rail"}>
          <div className={panel ? "student-rail__panel is-open" : "student-rail__panel"}>
            {panel && (
              <>
                <p className="student-rail__eyebrow">{panel.label}</p>
                <h2>{panel.title}</h2>
                <p className="student-rail__description">{panel.description}</p>
                <ul className="student-rail__list">
                  {panelKey === "produtos" && (
                    loadingProducts ? (
                      <li>Carregando produtos...</li>
                    ) : errorProducts ? (
                      <li>Erro: {errorProducts}</li>
                    ) : products.length === 0 ? (
                      <li>Nenhum produto encontrado.</li>
                    ) : (
                      products.map((product) => (
                        <li key={product.id}>
                          <strong>{product.name}</strong>
                          <span>{product.code}</span>
                          <small>Status: {product.status}</small>
                        </li>
                      ))
                    )
                  )}
                  {panelKey === "mentores" && (
                    loadingMentors ? (
                      <li>Carregando mentores...</li>
                    ) : errorMentors ? (
                      <li>Erro: {errorMentors}</li>
                    ) : mentors.length === 0 ? (
                      <li>Nenhum mentor encontrado.</li>
                    ) : (
                      mentors.map((mentor) => (
                        <li key={mentor.id}>
                          <strong>{mentor.name}</strong>
                          <span>{mentor.role}</span>
                          {mentor.email && <small>{mentor.email}</small>}
                        </li>
                      ))
                    )
                  )}
                  {panelKey === "usuario" && (
                    loadingProfile ? (
                      <li>Carregando perfil...</li>
                    ) : errorProfile ? (
                      <li>Erro: {errorProfile}</li>
                    ) : !profile ? (
                      <li>Perfil nao encontrado.</li>
                    ) : (
                      panel.items.map((item) => {
                        const isSelected = searchSection === item.section;
                        return (
                          <li key={`${panelKey}-${item.title}`} className={isSelected ? "is-selected" : undefined}>
                            {item.section ? (
                              <Link
                                to={{ pathname: location.pathname, search: buildSearch(activePanelKey, item.section) }}
                                className="student-rail__action"
                              >
                                <strong>{item.title}</strong>
                                <span>{item.meta}</span>
                                <small>{item.detail}</small>
                                <em>{item.cta}</em>
                              </Link>
                            ) : null}
                            <strong>{profile.name}</strong>
                            <span>{profile.email}</span>
                          </li>
                        );
                      })
                    )
                  )}
                </ul>
              </>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
