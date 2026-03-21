import type { ReactNode } from "react";
import { Link, NavLink, useLocation, useSearchParams } from "react-router-dom";
import "../mentor-shell.css";
import { env } from "../../../shared/config/env";

type MentorShellProps = {
  activeView: "matrix" | "command-center" | "radar";
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  metrics?: Array<{ label: string; value: string; tone?: "neutral" | "accent" | "success" | "warning" }>;
  children: ReactNode;
};

const MAIN_NAV = [
  { key: "matrix", label: "Matriz de Decisao", to: "/app/matriz-renovacao" },
  { key: "command-center", label: "Centro de Comando", to: "/app/centro-comando" },
  { key: "radar", label: "Radar de Evolucao", to: "/app/radar" }
] as const;

const SUPPORT_PANELS = {
  produtos: {
    label: "Produtos",
    title: "Portfolio acompanhado",
    description: "Resumo dos programas e estruturas atualmente vinculados ao acompanhamento do mentor.",
    items: [
      { title: "Programa principal", meta: "Carteira ativa", detail: "Leitura executiva conectada a centro, radar e matriz." },
      { title: "Mentor responsavel", meta: "Conta autenticada", detail: "Contexto operacional da carteira vinculada ao acesso atual." },
      { title: "Pilares e metricas", meta: "Estrutura do metodo", detail: "Base usada para acompanhamento, evolucao e recorrencia." }
    ]
  },
  alunos: {
    label: "Alunos",
    title: "Carteira do mentor",
    description: "Distribuicao atual da carteira para leitura de decisao, risco e oportunidade.",
    items: [
      { title: "Renovacoes prioritarias", meta: "Quadrante superior direito", detail: "Base forte para continuidade e ampliacao de contrato." },
      { title: "Aderencia alta", meta: "Quadrante superior esquerdo", detail: "Engajamento bom, com progresso ainda abaixo do ideal." },
      { title: "Watch e resgate", meta: "Quadrantes inferiores", detail: "Espaco claro para acao consultiva e narrativa de recuperacao." }
    ]
  },
  usuario: {
    label: "Usuario",
    title: "Contexto do mentor",
    description: "Resumo do acesso autenticado e do recorte operacional associado a ele.",
    items: [
      { title: "Acesso autenticado", meta: "Conta do mentor", detail: "A carteira apresentada respeita o contexto do acesso atual." },
      { title: "Visoes integradas", meta: "Centro, Radar e Matriz", detail: "Leitura coerente entre operacao, evolucao e decisao." },
      { title: "Escopo protegido", meta: "Admin preservado", detail: "As superficies administrativas seguem separadas do fluxo do mentor." }
    ]
  }
} as const;

type SupportPanelKey = keyof typeof SUPPORT_PANELS;

function isSupportPanel(value: string | null): value is SupportPanelKey {
  return value === "produtos" || value === "alunos" || value === "usuario";
}

export function MentorShell({ activeView, eyebrow, title, description, actions, metrics = [], children }: MentorShellProps) {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const searchPanel = searchParams.get("panel");
  const panelKey = isSupportPanel(searchPanel) ? searchPanel : null;
  const panel = panelKey ? SUPPORT_PANELS[panelKey] : null;

  return (
    <section className="mentor-shell">
      <div className="mentor-shell__backdrop" />
      <div className={panel ? "mentor-shell__layout mentor-shell__layout--with-rail" : "mentor-shell__layout"}>
        <aside className="mentor-sidebar">
          <div className="mentor-sidebar__brand">
            <img src={env.brandingIconUrl} alt="" aria-hidden="true" />
            <div>
              <p>Mentor</p>
              <strong>{env.clientName}</strong>
            </div>
          </div>

          <div className="mentor-sidebar__block">
            <span className="mentor-sidebar__label">Visoes principais</span>
            <nav className="mentor-sidebar__nav" aria-label="Navegacao do mentor">
              {MAIN_NAV.map((item) => (
                <NavLink
                  key={item.key}
                  to={item.to}
                  className={item.key === activeView ? "mentor-sidebar__link is-active" : "mentor-sidebar__link"}
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="mentor-sidebar__block">
            <span className="mentor-sidebar__label">Areas de Apoio</span>
            <div className="mentor-sidebar__nav mentor-sidebar__nav--secondary">
              {(Object.keys(SUPPORT_PANELS) as SupportPanelKey[]).map((key) => (
                <Link
                  key={key}
                  to={{ pathname: location.pathname, search: `?panel=${key}` }}
                  className={panelKey === key ? "mentor-sidebar__link is-secondary-active" : "mentor-sidebar__link is-secondary"}
                >
                  {SUPPORT_PANELS[key].label}
                </Link>
              ))}
            </div>
          </div>

          <div className="mentor-sidebar__spotlight">
            <span className="mentor-sidebar__label">Leitura da carteira</span>
            <strong>Visao executiva com foco em renovacao, resgate e crescimento da carteira.</strong>
            <p>Leitura operacional voltada a acompanhamento, priorizacao e sustentacao da carteira.</p>
          </div>
        </aside>

        <div className="mentor-main">
          <header className="mentor-header">
            <div>
              <p className="mentor-header__eyebrow">{eyebrow}</p>
              <h1>{title}</h1>
              <p>{description}</p>
            </div>
            {actions && <div className="mentor-header__actions">{actions}</div>}
          </header>

          {metrics.length > 0 && (
            <section className="mentor-metrics">
              {metrics.map((metric) => (
                <article
                  key={`${metric.label}-${metric.value}`}
                  className={metric.tone ? `mentor-metric mentor-metric--${metric.tone}` : "mentor-metric"}
                >
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </article>
              ))}
            </section>
          )}

          <div className="mentor-main__content">{children}</div>
        </div>

        <aside className={panel ? "mentor-rail is-open" : "mentor-rail"}>
          <div className={panel ? "mentor-rail__panel is-open" : "mentor-rail__panel"}>
            {panel && (
              <>
                <p className="mentor-rail__eyebrow">{panel.label}</p>
                <h2>{panel.title}</h2>
                <p className="mentor-rail__description">{panel.description}</p>
                <ul className="mentor-rail__list">
                  {panel.items.map((item) => (
                    <li key={item.title}>
                      <strong>{item.title}</strong>
                      <span>{item.meta}</span>
                      <small>{item.detail}</small>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
