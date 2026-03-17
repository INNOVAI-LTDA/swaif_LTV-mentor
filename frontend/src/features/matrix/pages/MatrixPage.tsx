import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { MatrixFilter } from "../../../contracts/matrix";
import { useRenewalMatrix } from "../../../domain/hooks/useMatrix";
import type { MatrixItem, Urgency } from "../../../domain/models";
import { formatCurrencyBRL } from "../../../shared/formatters/currency";
import { formatPercent01 } from "../../../shared/formatters/percent";
import { MentorShell } from "../../mentor/components/MentorShell";
import { MatrixBoard } from "../components/MatrixBoard";
import "../matrix.css";

const FILTER_OPTIONS: Array<{ value: MatrixFilter; label: string }> = [
  { value: "all", label: "Todos" },
  { value: "topRight", label: "Renovar" },
  { value: "critical", label: "D-45" },
  { value: "rescue", label: "Resgate" }
];

const URGENCY_LABEL: Record<Urgency, string> = {
  normal: "Estável",
  watch: "Atenção",
  critical: "Crítico",
  rescue: "Resgate"
};

function clampPct(value: number) {
  const safe = Number.isFinite(value) ? value : 0;
  return Math.max(0, Math.min(100, safe));
}

function formatPercentKpi(avgEngagement: number) {
  const safe = Number.isFinite(avgEngagement) ? avgEngagement : 0;
  if (safe > 1) {
    return `${safe.toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    })}%`;
  }
  return formatPercent01(safe, 1);
}

function markerValue(value: string | number) {
  if (typeof value === "number") {
    return value.toLocaleString("pt-BR");
  }
  return String(value ?? "");
}

export function MatrixPage() {
  const [filter, setFilter] = useState<MatrixFilter>("all");
  const resource = useRenewalMatrix(filter);
  const items = resource.data.items;
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (items.length === 0) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !items.some((item) => item.id === selectedId)) {
      setSelectedId(items[0].id);
    }
  }, [items, selectedId]);

  const selected = useMemo(
    () => items.find((item) => item.id === selectedId) ?? null,
    [items, selectedId]
  );

  const sortedItems = useMemo(() => [...items].sort((a, b) => a.daysLeft - b.daysLeft), [items]);

  const d45Ltv = useMemo(
    () => items.filter((item) => item.daysLeft <= 45).reduce((sum, item) => sum + item.ltv, 0),
    [items]
  );

  const kpis = resource.data.kpis;

  function select(item: MatrixItem) {
    setSelectedId(item.id);
  }

  return (
    <MentorShell
      activeView="matrix"
      eyebrow="Mentor | Matriz de Decisão"
      title="Renovações, resgates e prioridades da carteira"
      description="Organize os alunos por progresso e engajamento para decidir onde renovar, onde recuperar valor e onde ajustar o plano de mentoria."
      actions={
        <>
          <button type="button" onClick={() => void resource.refresh()}>
            Atualizar leitura
          </button>
          <Link to="/app">Visão geral</Link>
        </>
      }
      metrics={[
        { label: "Pipeline LTV total", value: formatCurrencyBRL(kpis.totalLTV), tone: "accent" },
        { label: "Renovações críticas D-45", value: String(kpis.criticalRenewals), tone: "warning" },
        { label: "Alertas de resgate", value: String(kpis.rescueCount) },
        { label: "Engajamento médio", value: formatPercentKpi(kpis.avgEngagement), tone: "success" }
      ]}
    >
      <section className="mx-page">
        <section className="mx-filter-row">
          {FILTER_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setFilter(option.value)}
              className={filter === option.value ? "is-active" : ""}
            >
              {option.label}
            </button>
          ))}
        </section>

        {resource.loading && items.length === 0 && <p className="mx-state">Carregando matriz...</p>}
        {resource.error && items.length === 0 && (
          <div className="mx-state mx-state--error">
            <p>{resource.error}</p>
            <button type="button" onClick={() => void resource.refresh()}>
              Tentar novamente
            </button>
          </div>
        )}
        {!resource.loading && !resource.error && items.length === 0 && (
          <p className="mx-state">Nenhum aluno encontrado para a matriz neste momento.</p>
        )}

        {items.length > 0 && (
          <section className="mx-main-grid">
            <div>
              <MatrixBoard items={items} selectedId={selectedId} onSelect={select} />

              <article className="mx-opportunity">
                <span>Oportunidade em contratos D-45</span>
                <strong>{formatCurrencyBRL(d45Ltv)}</strong>
                <p>Soma dos alunos em janela de renovação nos próximos 45 dias.</p>
              </article>
            </div>

            <aside className="mx-side">
              <section className="mx-panel">
                <header>
                  <h2>Painel de ação rápida</h2>
                  <p>{sortedItems.length} alunos no filtro atual</p>
                </header>

                <ul className="mx-quick-list">
                  {sortedItems.map((item) => (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={item.id === selectedId ? "is-selected" : ""}
                        onClick={() => setSelectedId(item.id)}
                      >
                        <div>
                          <strong>{item.name}</strong>
                          <span>{item.programName || "Programa não informado"}</span>
                        </div>
                        <div>
                          <small>D-{item.daysLeft}</small>
                          <span className={`mx-urgency mx-urgency--${item.urgency}`}>
                            {URGENCY_LABEL[item.urgency]}
                          </span>
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>

              <section className="mx-panel">
                <header>
                  <h2>Contexto de renovação</h2>
                  <p>{selected ? selected.name : "Sem seleção"}</p>
                </header>

                {!selected && <p className="mx-state-inline">Selecione um aluno para abrir os detalhes.</p>}

                {selected && (
                  <div className="mx-detail">
                    <div className="mx-detail-kpis">
                      <article>
                        <span>Progresso</span>
                        <strong>{formatPercent01(selected.progress)}</strong>
                      </article>
                      <article>
                        <span>Engajamento</span>
                        <strong>{formatPercent01(selected.engagement)}</strong>
                      </article>
                      <article>
                        <span>Dias restantes</span>
                        <strong>D-{selected.daysLeft}</strong>
                      </article>
                      <article>
                        <span>LTV</span>
                        <strong>{formatCurrencyBRL(selected.ltv)}</strong>
                      </article>
                    </div>

                    <article className="mx-detail-card">
                      <h3>Motivo de renovação</h3>
                      <p>{selected.renewalReason || "Sem motivo registrado."}</p>
                    </article>

                    <article className="mx-detail-card mx-detail-card--accent">
                      <h3>Ação sugerida</h3>
                      <p>{selected.suggestion || "Sem sugestão registrada."}</p>
                    </article>

                    <article className="mx-detail-card">
                      <h3>Indicadores do aluno</h3>
                      {selected.markers.length === 0 && (
                        <p className="mx-state-inline">Nenhum indicador carregado para este aluno.</p>
                      )}

                      {selected.markers.length > 0 && (
                        <ul className="mx-marker-list">
                          {selected.markers.map((marker, index) => (
                            <li key={`${marker.label}-${index}`}>
                              <div className="mx-marker-header">
                                <strong>{marker.label}</strong>
                                <span>
                                  {markerValue(marker.value)} / {markerValue(marker.target)}
                                </span>
                              </div>
                              <div className="mx-marker-track">
                                <div className="mx-marker-fill" style={{ width: `${clampPct(marker.pct)}%` }} />
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </article>
                  </div>
                )}
              </section>
            </aside>
          </section>
        )}
      </section>
    </MentorShell>
  );
}
