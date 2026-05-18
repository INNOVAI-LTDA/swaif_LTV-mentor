import { env } from "../shared/config/env";

export function HomePage() {
  return (
    <section className="page">
      <h1>Frontend MVP Mentoria</h1>
      <p>Bootstrap inicial pronto. As telas funcionais serão implementadas nos próximos marcos.</p>
      <div className="card">
        <h2>Configuração ativa</h2>
        <p>
          <strong>API_BASE_URL:</strong> {env.apiBaseUrl}
        </p>
        <p>
          <strong>HTTP_TIMEOUT_MS:</strong> {env.httpTimeoutMs}
        </p>
      </div>
    </section>
  );
}
