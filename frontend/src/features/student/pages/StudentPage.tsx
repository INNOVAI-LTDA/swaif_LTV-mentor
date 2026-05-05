import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { RadarChart } from "../../radar/components/RadarChart";
import { StudentShell } from "../components/StudentShell";
import { useSelfPillarMetrics, useSelfRadar } from "../../../domain/hooks/useStudentWorkspace";
import { getSelfPillarMetrics, updateSelfMeasurementValueCurrent } from "../../../domain/services/studentWorkspaceService";
import { AppError, toUserErrorMessage } from "../../../shared/api/types";
import "../student.css";

type StudentView = "radar" | "indicadores";

type PillarMetricsPanelState = {
  loading: boolean;
  error: string | null;
  byPillarId: Record<string, { pillarName: string; items: Array<{ measurementId: string; metricLabel: string; valueBaseline: number; valueCurrent: number; valueProjected: number | null; unit: string | null }> }>;
};

function resolveView(value: string | null): StudentView {
  if (value === "indicadores") {
    return value;
  }
  return "radar";
}

function parseNumericInput(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value.replace(",", "."));
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return parsed;
}

export function StudentPage() {
  const [searchParams] = useSearchParams();
  const activeView = resolveView(searchParams.get("view"));
  const [selectedPillarId, setSelectedPillarId] = useState<string | null>(null);
  const [editingMeasurementId, setEditingMeasurementId] = useState<string | null>(null);
  const [draftValue, setDraftValue] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; message: string } | null>(null);
  const [pillarMetricsPanel, setPillarMetricsPanel] = useState<PillarMetricsPanelState>({ loading: false, error: null, byPillarId: {} });

  const radarResource = useSelfRadar();
  const pillars = radarResource.data.axisScores;
  const pillarMetricsResource = useSelfPillarMetrics(selectedPillarId);

  useEffect(() => {
    if (!selectedPillarId && pillars.length > 0) {
      setSelectedPillarId(pillars[0].axisId || pillars[0].axisKey);
    }
  }, [selectedPillarId, pillars]);

  useEffect(() => {
    setEditingMeasurementId(null);
    setDraftValue("");
  }, [selectedPillarId]);


  useEffect(() => {
    let active = true;

    async function loadPillarMetricsPanel() {
      if (pillars.length === 0) {
        if (active) {
          setPillarMetricsPanel({ loading: false, error: null, byPillarId: {} });
        }
        return;
      }

      if (active) {
        setPillarMetricsPanel((current) => ({ ...current, loading: true, error: null }));
      }

      try {
        const results = await Promise.all(
          pillars.map(async (pillar) => {
            const pillarId = pillar.axisId || pillar.axisKey;
            const response = await getSelfPillarMetrics(pillarId);
            return [
              pillarId,
              {
                pillarName: response.pillar.name || pillar.axisLabel,
                items: response.items.map((item) => ({
                  measurementId: item.measurementId,
                  metricLabel: item.metricLabel,
                  valueBaseline: item.valueBaseline,
                  valueCurrent: item.valueCurrent,
                  valueProjected: item.valueProjected,
                  unit: item.unit
                }))
              }
            ] as const;
          })
        );

        if (!active) {
          return;
        }

        setPillarMetricsPanel({ loading: false, error: null, byPillarId: Object.fromEntries(results) });
      } catch (error) {
        if (!active) {
          return;
        }
        setPillarMetricsPanel({ loading: false, error: toUserErrorMessage(error, "Não foi possível carregar as métricas por pilar."), byPillarId: {} });
      }
    }

    void loadPillarMetricsPanel();

    return () => {
      active = false;
    };
  }, [pillars]);

  const radarPoints = useMemo(
    () =>
      pillars.map((axis) => ({
        axisLabel: axis.axisLabel,
        baseline: axis.baseline,
        current: axis.current,
        projected: axis.projected
      })),
    [pillars]
  );

  async function persistMeasurement(measurementId: string) {
    const parsed = parseNumericInput(draftValue);
    if (parsed === null) {
      setFeedback({ tone: "error", message: "Informe um número válido para salvar." });
      return;
    }

    const confirmed = window.confirm("Confirmar atualização do valor atual desta métrica?");
    if (!confirmed) {
      return;
    }

    setSaving(true);
    setFeedback(null);
    try {
      await updateSelfMeasurementValueCurrent(measurementId, parsed);
      await Promise.all([radarResource.refresh(), pillarMetricsResource.refresh()]);
      setEditingMeasurementId(null);
      setDraftValue("");
      setFeedback({ tone: "success", message: "Valor atualizado com sucesso." });
    } catch (error) {
      setFeedback({ tone: "error", message: toUserErrorMessage(error, "Não foi possível salvar a métrica.") });
      if (error instanceof AppError && error.code === "MEASUREMENT_VALUE_INVALID") {
        return;
      }
    } finally {
      setSaving(false);
    }
  }

  const headerCopy =
    activeView === "indicadores"
      ? {
          eyebrow: "Aluno | Indicadores por Pilar",
          title: "Atualize seu valor real por indicador",
          description: "Selecione um pilar do radar para visualizar e editar apenas o campo atual de cada métrica.",
          secondaryHref: "/app/aluno?view=radar",
          secondaryLabel: "Voltar ao radar"
        }
      : {
          eyebrow: "Aluno | Radar de Evolução",
          title: "Acompanhe o seu radar",
          description: "Veja seus pilares e siga para os indicadores para registrar o valor atual da sua evolução.",
          secondaryHref: "/app/aluno?view=indicadores",
          secondaryLabel: "Abrir indicadores"
        };

  return (
    <StudentShell
      eyebrow={headerCopy.eyebrow}
      title={headerCopy.title}
      description={headerCopy.description}
      actions={
        <>
          <button
            type="button"
            onClick={() => void Promise.all([radarResource.refresh(), pillarMetricsResource.refresh()])}
            disabled={saving}
          >
            Atualizar leitura
          </button>
          <Link to={headerCopy.secondaryHref}>{headerCopy.secondaryLabel}</Link>
        </>
      }
    >
      <section className="student-page">
        {feedback && <p className={feedback.tone === "success" ? "student-state student-state--success" : "student-state student-state--error"}>{feedback.message}</p>}

        {activeView === "radar" ? (
          <section className="student-radar-grid">
            <article className="student-card student-card--radar" aria-label="Radar do aluno">
            {radarResource.loading && <p className="student-state">Carregando radar...</p>}
            {radarResource.error && <p className="student-state">{radarResource.error}</p>}
            {!radarResource.loading && !radarResource.error && radarPoints.length === 0 && <p className="student-state">Sem dados de radar para este aluno.</p>}
            {radarPoints.length > 0 && <RadarChart points={radarPoints} title="Radar do aluno" />}
            </article>

            <article className="student-card student-card--pillar-panel" aria-label="Métricas por pilar">
              <header className="student-card__header">
                <div>
                  <h2>Painel de métricas por pilar</h2>
                  <p>Visualize base, atual e projetado em cada indicador.</p>
                </div>
              </header>

              {pillarMetricsPanel.loading && <p className="student-state">Carregando métricas por pilar...</p>}
              {pillarMetricsPanel.error && <p className="student-state">{pillarMetricsPanel.error}</p>}

              {!pillarMetricsPanel.loading && !pillarMetricsPanel.error && (
                <div className="student-pillar-panel-list">
                  {pillars.map((pillar) => {
                    const pillarId = pillar.axisId || pillar.axisKey;
                    const panel = pillarMetricsPanel.byPillarId[pillarId];
                    const panelItems = panel?.items ?? [];
                    return (
                      <section key={pillarId} className="student-pillar-panel-item">
                        <h3>{panel?.pillarName || pillar.axisLabel}</h3>
                        {panelItems.length === 0 ? (
                          <p className="student-state">Sem métricas para este pilar.</p>
                        ) : (
                          <ul className="student-pillar-metric-list">
                            {panelItems.map((metric) => (
                              <li key={metric.measurementId}>
                                <strong>{metric.metricLabel}</strong>
                                <span>Base: {metric.valueBaseline}{metric.unit ? ` ${metric.unit}` : ""}</span>
                                <span>Atual: {metric.valueCurrent}{metric.unit ? ` ${metric.unit}` : ""}</span>
                                <span>Projetado: {metric.valueProjected ?? "-"}{metric.unit ? ` ${metric.unit}` : ""}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </section>
                    );
                  })}
                </div>
              )}
            </article>
          </section>
        ) : (
          <article className="student-card" aria-label="Métricas do pilar selecionado">
            <header className="student-card__header">
              <div>
                <h2>{pillarMetricsResource.data.pillar.name || "Selecione um pilar"}</h2>
                <p>Edição permitida apenas no valor atual.</p>
              </div>

              <div className="student-pillars" role="tablist" aria-label="Seleção de pilar para indicadores">
                {pillars.map((pillar) => (
                  <button
                    key={pillar.axisId || pillar.axisKey}
                    type="button"
                    role="tab"
                    aria-selected={selectedPillarId === (pillar.axisId || pillar.axisKey)}
                    className={selectedPillarId === (pillar.axisId || pillar.axisKey) ? "student-pillars__item is-active" : "student-pillars__item"}
                    onClick={() => setSelectedPillarId(pillar.axisId || pillar.axisKey)}
                  >
                    <strong>{pillar.axisLabel}</strong>
                  </button>
                ))}
              </div>
            </header>

            {pillarMetricsResource.loading && <p className="student-state">Carregando métricas do pilar...</p>}
            {pillarMetricsResource.error && <p className="student-state">{pillarMetricsResource.error}</p>}
            {!pillarMetricsResource.loading && !pillarMetricsResource.error && pillarMetricsResource.data.items.length === 0 && (
              <p className="student-state">Nenhuma métrica encontrada para o pilar selecionado.</p>
            )}

            {pillarMetricsResource.data.items.length > 0 && (
              <ul className="student-metrics-list">
                {pillarMetricsResource.data.items.map((metric) => {
                  const isEditing = editingMeasurementId === metric.measurementId;
                  return (
                    <li key={metric.measurementId} className="student-metrics-list__item">
                      <div>
                        <strong>{metric.metricLabel}</strong>
                        <p>
                          Base: {metric.valueBaseline} | Projetado: {metric.valueProjected ?? "-"}
                        </p>
                      </div>
                      <div className="student-metrics-list__editor">
                        {isEditing ? (
                          <>
                            <input
                              type="text"
                              value={draftValue}
                              onChange={(event) => setDraftValue(event.target.value)}
                              aria-label={`Valor atual de ${metric.metricLabel}`}
                              disabled={saving}
                            />
                            <button type="button" onClick={() => void persistMeasurement(metric.measurementId)} disabled={saving}>
                              Confirmar
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setEditingMeasurementId(null);
                                setDraftValue("");
                              }}
                              disabled={saving}
                            >
                              Cancelar
                            </button>
                          </>
                        ) : (
                          <>
                            <span>Atual: {metric.valueCurrent}</span>
                            <button
                              type="button"
                              onClick={() => {
                                setEditingMeasurementId(metric.measurementId);
                                setDraftValue(String(metric.valueCurrent));
                                setFeedback(null);
                              }}
                            >
                              Editar atual
                            </button>
                          </>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        )}
      </section>
    </StudentShell>
  );
}
