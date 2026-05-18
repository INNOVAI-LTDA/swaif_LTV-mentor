
import type { ReactNode } from "react";
import { Link, NavLink, useLocation, useSearchParams } from "react-router-dom";
import "../mentor-shell.css";
import { env } from "../../../shared/config/env";
import { useMentorProducts } from "../hooks/useMentorProducts";

type MentorShellProps = {
  activeView: "matrix" | "command-center" | "radar";
  eyebrow?: string;
  title?: string;
  description?: string;
  brandLabel?: string;
  brandTitle?: string;
  actions?: ReactNode;
  metrics?: Array<{ label: string; value: string; tone?: "neutral" | "accent" | "success" | "warning" }>;
  showSpotlight?: boolean;
  children: ReactNode;
};

const MAIN_NAV = [
  { key: "matrix", label: "Matriz de Decisão", to: "/app/matriz-renovacao" },
  { key: "command-center", label: "Centro de Comando", to: "/app/centro-comando" },
  { key: "radar", label: "Radar de Evolução", to: "/app/radar" }
] as const;

const SUPPORT_PANELS = {
  produtos: {
    label: "Produtos",
    title: "Portfólio acompanhado",
    description: "Resumo dos programas e estruturas atualmente vinculados ao acompanhamento do mentor.",
    items: []
  },
  alunos: {
    label: "Alunos",
    title: "Carteira do mentor",
    description: "Distribuição atual da carteira para leitura de decisão, risco e oportunidade.",
    items: [
      { title: "Renovações prioritárias", meta: "Quadrante superior direito", detail: "Base forte para continuidade e ampliação de contrato." },
      { title: "Aderência alta", meta: "Quadrante superior esquerdo", detail: "Engajamento bom, com progresso ainda abaixo do ideal." },
      { title: "Watch e resgate", meta: "Quadrantes inferiores", detail: "Espaço claro para ação consultiva e narrativa de recuperação." }
    ]
  },
  usuario: {
    label: "Usuário",
    title: "Contexto do mentor",
    description: "Resumo do acesso autenticado e do recorte operacional associado a ele.",
    items: [
      { title: "Acesso autenticado", meta: "Conta do mentor", detail: "A carteira apresentada respeita o contexto do acesso atual." },
      { title: "Visões integradas", meta: "Centro, Radar e Matriz", detail: "Leitura coerente entre operação, evolução e decisão." },
      { title: "Escopo protegido", meta: "Admin preservado", detail: "As superfícies administrativas seguem separadas do fluxo do mentor." }
    ]
  }
} as const;

type SupportPanelKey = keyof typeof SUPPORT_PANELS;

function isSupportPanel(value: string | null): value is SupportPanelKey {
  return value === "produtos" || value === "alunos" || value === "usuario";
}

function MentorProductsPanel({ label, title, description }: { label: string; title: string; description: string }) {
  const { products, loading, error } = useMentorProducts();

  return (
    <>
      <p className="mentor-rail__eyebrow">{label}</p>
      <h2>{title}</h2>
      <p className="mentor-rail__description">{description}</p>
      {loading ? (
        <div className="mentor-rail__list"><em>Carregando produtos...</em></div>
      ) : error ? (
        <div className="mentor-rail__list"><em style={{ color: "#c00" }}>{error}</em></div>
      ) : products.length === 0 ? (
        <div className="mentor-rail__list"><em>Nenhum produto encontrado.</em></div>
      ) : (
        <ul className="mentor-rail__list">
          {products.map((product) => (
            <li key={product.id}>
              <strong>{product.name}</strong>
              <span>{product.code}</span>
              <small>{typeof product.metadata?.narrative === "string" ? product.metadata.narrative : ""}</small>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export function MentorShell({
  activeView,
  eyebrow,
  title,
  description,
  brandLabel = "Mentor",
  brandTitle = env.clientName,
  actions,
  metrics = [],
  showSpotlight = true,
  children,
}: MentorShellProps) {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const searchPanel = searchParams.get("panel");
  const panelKey = isSupportPanel(searchPanel) ? searchPanel : null;
  const panel = panelKey ? SUPPORT_PANELS[panelKey] : null;
  const hasHeaderCopy = Boolean(eyebrow || title || description);

  return (
    <section className="mentor-shell">
      <div className="mentor-shell__backdrop" />
      <div className={panel ? "mentor-shell__layout mentor-shell__layout--with-rail" : "mentor-shell__layout"}>
        <aside className="mentor-sidebar">
          <div className="mentor-sidebar__brand">
            <img src={env.brandingIconUrl} alt="" aria-hidden="true" />
            <div>
              <p>{brandLabel}</p>
              <strong>{brandTitle}</strong>
            </div>
          </div>

          <div className="mentor-sidebar__block">
            <span className="mentor-sidebar__label">Visões principais</span>
            <nav className="mentor-sidebar__nav" aria-label="Navegação do mentor">
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
            <span className="mentor-sidebar__label">Áreas de Apoio</span>
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

          {showSpotlight ? (
            <div className="mentor-sidebar__spotlight">
              <span className="mentor-sidebar__label">Leitura da carteira</span>
              <strong>Visão executiva com foco em renovação, resgate e crescimento da carteira.</strong>
              <p>Leitura operacional voltada a acompanhamento, priorização e sustentação da carteira.</p>
            </div>
          ) : null}
        </aside>

        <div className="mentor-main">
          {(hasHeaderCopy || actions) && (
            <header className="mentor-header">
              {hasHeaderCopy ? (
                <div>
                  {eyebrow ? <p className="mentor-header__eyebrow">{eyebrow}</p> : null}
                  {title ? <h1>{title}</h1> : null}
                  {description ? <p>{description}</p> : null}
                </div>
              ) : (
                <div />
              )}
              {actions && <div className="mentor-header__actions">{actions}</div>}
            </header>
          )}

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
            {panelKey === "produtos" ? (
              <MentorProductsPanel label={SUPPORT_PANELS.produtos.label} title={SUPPORT_PANELS.produtos.title} description={SUPPORT_PANELS.produtos.description} />
            ) : panel ? (
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
            ) : null}
          </div>
        </aside>
      </div>
    </section>
  );
}
