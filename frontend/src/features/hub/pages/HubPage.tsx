import { formatCurrencyBRL } from "../../../shared/formatters/currency";
import { formatPercent01 } from "../../../shared/formatters/percent";
import { HubKpiStrip } from "../components/HubKpiStrip";
import { HubModuleCard } from "../components/HubModuleCard";
import { HUB_MODULES } from "../constants";
import { useHubSummary } from "../hooks/useHubSummary";
import "../hub.css";

export function HubPage() {
  const summary = useHubSummary();

  const kpis = [
    {
      label: "Alunos ativos",
      value: String(summary.commandKpis.active),
      tone: "success" as const
    },
    {
      label: "Alertas de resgate",
      value: String(summary.commandKpis.alerts),
      tone: "danger" as const
    },
    {
      label: "Renovações D-45",
      value: String(summary.matrixKpis.criticalRenewals),
      tone: "warning" as const
    },
    {
      label: "LTV em pipeline",
      value: formatCurrencyBRL(summary.matrixKpis.totalLTV),
      tone: "neutral" as const
    },
    {
      label: "Engajamento médio",
      value: formatPercent01(summary.matrixKpis.avgEngagement),
      tone: "neutral" as const
    }
  ];

  return (
    <section className="hub-page">
      <div className="hub-bg-shape hub-bg-shape--one" />
      <div className="hub-bg-shape hub-bg-shape--two" />
      <div className="hub-bg-shape hub-bg-shape--three" />

      <header className="hub-hero">
        <p className="hub-hero__eyebrow">Mentoria Intelligence Hub</p>
        <h1 className="hub-hero__title">Platafoma Inteligência para Mentorias</h1>
        <p className="hub-hero__description">
          Visão executiva para acompanhar risco, evolução e renovação. O hub conecta os contratos v1 e prepara a
          navegação completa das visões Centro, Radar e Matriz.
        </p>

        <div className="hub-hero__meta">
          <span>Contratos ativos: v1</span>
          <span>Alunos sincronizados: {summary.studentsCount}</span>
          <span>Itens de matriz: {summary.matrixItemsCount}</span>
        </div>
      </header>

      <HubKpiStrip items={kpis} />

      {(summary.loading || summary.hasError) && (
        <div className="hub-state-card">
          {summary.loading && <p>Atualizando indicadores do hub...</p>}
          {summary.hasError && (
            <p>
              Falha de sincronização: {summary.error}{" "}
              <button type="button" onClick={() => void summary.refresh()}>
                tentar novamente
              </button>
            </p>
          )}
        </div>
      )}

      <section className="hub-modules-grid" aria-label="Módulos principais do hub">
        {HUB_MODULES.map((module, index) => (
          <HubModuleCard key={module.id} module={module} index={index} />
        ))}
      </section>
    </section>
  );
}
