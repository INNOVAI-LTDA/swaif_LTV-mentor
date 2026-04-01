import { useEffect, useMemo, useState } from "react";
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
  { value: "critical", label: "D-45" },
];

const DENSITY_OPTIONS = [
  { value: 5, label: "5 por quadrante" },
  { value: 10, label: "10 por quadrante" },
  { value: 20, label: "20 por quadrante" },
  { value: "all", label: "Todos" },
] as const;

type BubbleDensity = (typeof DENSITY_OPTIONS)[number]["value"];

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
  const [density, setDensity] = useState<BubbleDensity>(10);
  const resource = useRenewalMatrix(filter);
  const items = resource.data.items;
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const visibleItems = useMemo(() => {
    if (density === "all") {
      return items;
    }

    const byQuadrant = {
      topRight: [] as MatrixItem[],
      topLeft: [] as MatrixItem[],
      bottomRight: [] as MatrixItem[],
      bottomLeft: [] as MatrixItem[],
    };

    for (const item of items) {
      byQuadrant[item.quadrant].push(item);
    }

    return [
      ...byQuadrant.topRight.slice(0, density),
      ...byQuadrant.topLeft.slice(0, density),
      ...byQuadrant.bottomRight.slice(0, density),
      ...byQuadrant.bottomLeft.slice(0, density),
    ];
  }, [density, items]);

  useEffect(() => {
    if (selectedId && !visibleItems.some((item) => item.id === selectedId)) {
      setSelectedId(null);
    }
  }, [selectedId, visibleItems]);

  useEffect(() => {
    if (!selectedId) {
      return undefined;
    }

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      if (target.closest(".mx-bubble") || target.closest(".mx-panel")) {
        return;
      }
      setSelectedId(null);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [selectedId]);

  const selected = useMemo(
    () => visibleItems.find((item) => item.id === selectedId) ?? null,
    [selectedId, visibleItems]
  );

  const d45Ltv = useMemo(
    () => items.filter((item) => item.daysLeft <= 45).reduce((sum, item) => sum + item.ltv, 0),
    [items]
  );

  const kpis = resource.data.kpis;

  function select(item: MatrixItem) {
    setSelectedId(item.id);
  }

  const mentorLabel = resource.data.context.mentorName || "Mentor";
  const protocolLabel = resource.data.context.protocolName || visibleItems[0]?.programName || undefined;

  return (
    <MentorShell
      activeView="matrix"
      brandLabel={mentorLabel}
      brandTitle={protocolLabel}
      showSpotlight={false}
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

        <section className="mx-density-row" aria-label="Quantidade de bolhas por quadrante">
          <span>Bolhas por quadrante</span>
          <div className="mx-density-row__actions">
            {DENSITY_OPTIONS.map((option) => (
              <button
                key={String(option.value)}
                type="button"
                onClick={() => setDensity(option.value)}
                className={density === option.value ? "is-active" : ""}
              >
                {option.label}
              </button>
            ))}
          </div>
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
          <section className={`mx-main-grid ${selected ? "" : "mx-main-grid--solo"}`.trim()}>
            <div>
              <MatrixBoard items={visibleItems} selectedId={selectedId} onSelect={select} />

              <article className="mx-opportunity">
                <span>Oportunidade em contratos D-45</span>
                <strong>{formatCurrencyBRL(d45Ltv)}</strong>
                <p>Soma dos alunos em janela de renovação nos próximos 45 dias.</p>
              </article>
            </div>

            {selected && (
              <aside className="mx-side">
                <section className="mx-panel">
                  <header>
                    <h2>Contexto de Renovação</h2>
                    <p>{selected.name}</p>
                  </header>

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
                </section>
              </aside>
            )}
          </section>
        )}
      </section>
    </MentorShell>
  );
}
