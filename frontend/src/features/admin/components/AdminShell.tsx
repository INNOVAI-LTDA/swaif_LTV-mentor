import type { ReactNode } from "react";
import { Link, NavLink, useLocation, useSearchParams } from "react-router-dom";
import "../admin-shell.css";
import { env } from "../../../shared/config/env";

type AdminShellProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
  metrics?: Array<{ label: string; value: string; tone?: "neutral" | "accent" | "success" | "warning" }>;
  children: ReactNode;
};

const SUPPORT_PANELS = {
  provider: { label: "Provider View" },
  client: { label: "Client View" },
  database: { label: "Database View" },
  api: { label: "API" }
} as const;

type SupportPanelKey = keyof typeof SUPPORT_PANELS;

function isSupportPanel(value: string | null): value is SupportPanelKey {
  return value === "provider" || value === "client" || value === "database" || value === "api";
}

export function AdminShell({ eyebrow, title, description, actions, metrics = [], children }: AdminShellProps) {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const searchPanel = searchParams.get("panel");
  const panelKey = isSupportPanel(searchPanel) ? searchPanel : null;

  return (
    <section className="admin-shell">
      <div className="admin-shell__backdrop" />
      <div className="admin-shell__layout">
        <aside className="admin-sidebar">
          <div className="admin-sidebar__brand">
            <img src={env.brandingIconUrl} alt="" aria-hidden="true" />
            <div>
              <p>Admin</p>
              <strong>{env.clientName}</strong>
            </div>
          </div>

          <div className="admin-sidebar__block">
            <span className="admin-sidebar__label">Areas de Apoio</span>
            <div className="admin-sidebar__nav admin-sidebar__nav--secondary">
              {(Object.keys(SUPPORT_PANELS) as SupportPanelKey[]).map((key) => (
                <Link
                  key={key}
                  to={{ pathname: location.pathname, search: `?panel=${key}` }}
                  className={panelKey === key ? "admin-sidebar__link is-secondary-active" : "admin-sidebar__link is-secondary"}
                >
                  {SUPPORT_PANELS[key].label}
                </Link>
              ))}
            </div>
          </div>

        </aside>

        <div className="admin-main">
          <header className="admin-header">
            <div>
              {eyebrow ? <p className="admin-header__eyebrow">{eyebrow}</p> : null}
              <h1>{title}</h1>
              <p>{description}</p>
            </div>
            {actions && <div className="admin-header__actions">{actions}</div>}
          </header>

          {metrics.length > 0 && (
            <section className="admin-metrics">
              {metrics.map((metric) => (
                <article
                  key={`${metric.label}-${metric.value}`}
                  className={metric.tone ? `admin-metric admin-metric--${metric.tone}` : "admin-metric"}
                >
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </article>
              ))}
            </section>
          )}

          <div className="admin-main__content">{children}</div>
        </div>
      </div>
    </section>
  );
}
