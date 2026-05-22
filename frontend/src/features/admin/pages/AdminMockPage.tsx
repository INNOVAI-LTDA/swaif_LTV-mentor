import { Link, useLocation } from "react-router-dom";
import { AdminShell } from "../components/AdminShell";

type PanelKey = "provider" | "clientes" | "database" | "api";

const PANELS: Array<{ key: PanelKey; label: string }> = [
  { key: "provider", label: "Provider View" },
  { key: "clientes", label: "Client View" },
  { key: "database", label: "Database View" },
  { key: "api", label: "API View" }
];

const MOCK_CLIENTS = ["Clínica Alpha", "Instituto Beta", "Grupo Gama"];
const MOCK_AXES = [
  { name: "Aquisição", baseline: 62, current: 70, projected: 74 },
  { name: "Vendas", baseline: 58, current: 66, projected: 71 },
  { name: "Mindset", baseline: 73, current: 79, projected: 82 }
];

const MOCK_TABLES = ["clients", "products", "mentors", "students"];
const MOCK_API = [
  { method: "GET", endpoint: "/admin/provider-view", status: "200 mock" },
  { method: "GET", endpoint: "/admin/client-view", status: "200 mock" },
  { method: "GET", endpoint: "/admin/database-view/tables", status: "200 mock" },
  { method: "POST", endpoint: "/admin/api/operations/run", status: "202 mock" }
];

function getPanel(search: string): PanelKey {
  const panel = new URLSearchParams(search).get("panel");
  return PANELS.some((item) => item.key === panel) ? (panel as PanelKey) : "provider";
}

export function AdminMockPage() {
  const location = useLocation();
  const activePanel = getPanel(location.search);

  return (
    <AdminShell
      eyebrow="Admin | Mock Preview"
      title="Centro Institucional (Mock)"
      description="Tela de validação de conteúdo e navegação das quatro views administrativas com dados simulados."
      metrics={[
        { label: "Clientes mock", value: String(MOCK_CLIENTS.length), tone: "accent" },
        { label: "Tabelas mock", value: String(MOCK_TABLES.length), tone: "warning" },
        { label: "Requests mock", value: String(MOCK_API.length), tone: "success" }
      ]}
    >
      <section className="admin-page">
        <article className="admin-module">
          <p className="admin-module__eyebrow">Navegação de views</p>
          <ul className="admin-client-grid" aria-label="Mock view navigation">
            {PANELS.map((panel) => (
              <li key={panel.key}>
                <Link
                  to={{ pathname: location.pathname, search: `?panel=${panel.key}` }}
                  className={activePanel === panel.key ? "admin-client-card is-active" : "admin-client-card"}
                >
                  <strong>{panel.label}</strong>
                </Link>
              </li>
            ))}
          </ul>
        </article>

        {activePanel === "provider" ? (
          <article className="admin-module" aria-label="Provider View">
            <p className="admin-module__eyebrow">Provider View</p>
            <h2>Resumo operacional do provedor</h2>
            <p className="admin-module__muted">Dados simulados para validar leitura geral da visão administrativa.</p>
            <ul className="admin-client-grid">
              {MOCK_CLIENTS.map((client) => (
                <li key={client}><article className="admin-student-card"><strong>{client}</strong><p>Saúde do portfólio: estável</p></article></li>
              ))}
            </ul>
          </article>
        ) : null}

        {activePanel === "clientes" ? (
          <article className="admin-module" aria-label="Client View">
            <p className="admin-module__eyebrow">Client View</p>
            <h2>Radar em modo leitura</h2>
            <div className="admin-provider-view-edit-grid">
              {MOCK_AXES.map((axis) => (
                <label key={axis.name}>
                  {axis.name}
                  <input type="text" readOnly value={`baseline ${axis.baseline} | current ${axis.current} | projected ${axis.projected}`} />
                </label>
              ))}
            </div>
          </article>
        ) : null}

        {activePanel === "database" ? (
          <article className="admin-module" aria-label="Database View">
            <p className="admin-module__eyebrow">Database View</p>
            <h2>Tabelas permitidas (mock)</h2>
            <ul className="admin-client-grid">
              {MOCK_TABLES.map((table) => (
                <li key={table}><article className="admin-student-card"><strong>{table}</strong><p>10 registros simulados</p></article></li>
              ))}
            </ul>
          </article>
        ) : null}

        {activePanel === "api" ? (
          <article className="admin-module" aria-label="API View">
            <p className="admin-module__eyebrow">API View</p>
            <h2>Catálogo de requests monitoráveis</h2>
            <ul className="admin-student-list">
              {MOCK_API.map((item) => (
                <li key={item.endpoint} className="admin-student-card">
                  <strong>{item.method} {item.endpoint}</strong>
                  <p>Status: {item.status}</p>
                </li>
              ))}
            </ul>
          </article>
        ) : null}
      </section>
    </AdminShell>
  );
}
