import { useEffect, useMemo, useState } from "react";
import { deriveCommandCenterTopKpis } from "../../../domain/adapters/commandCenterAdapter";
import {
  useCommandCenterStudentCollection,
  useCommandCenterStudentDetail,
  useCommandCenterTimeline
} from "../../../domain/hooks/useCommandCenter";
import type { StudentListItem, TimelineAnomaly } from "../../../domain/models";
import { formatCurrencyBRL } from "../../../shared/formatters/currency";
import { formatPercent01 } from "../../../shared/formatters/percent";
import { MentorShell } from "../../mentor/components/MentorShell";
import "../command-center.css";

const URGENCY_META: Record<
  StudentListItem["urgency"],
  { label: string; className: string }
> = {
  normal: { label: "Estável", className: "cc-urgency--normal" },
  watch: { label: "Atenção", className: "cc-urgency--watch" },
  critical: { label: "Crítico", className: "cc-urgency--critical" },
  rescue: { label: "Resgate", className: "cc-urgency--rescue" }
};

export function CommandCenterPage() {
  const studentsResource = useCommandCenterStudentCollection();
  const [activeTab, setActiveTab] = useState<"top" | "bottom">("top");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailResource = useCommandCenterStudentDetail(selectedId);
  const timelineResource = useCommandCenterTimeline(selectedId);
  const [selectedAnomaly, setSelectedAnomaly] = useState<TimelineAnomaly | null>(null);

  const allStudents = studentsResource.data.items;
  const topStudents = studentsResource.data.topItems;
  const bottomStudents = studentsResource.data.bottomItems;
  const hasRankingTabs = studentsResource.data.rankingMode === "top_bottom";
  const visibleStudents = hasRankingTabs ? (activeTab === "top" ? topStudents : bottomStudents) : allStudents;

  useEffect(() => {
    if (visibleStudents.length > 0 && !selectedId) {
      setSelectedId(visibleStudents[0].id);
    }
  }, [visibleStudents, selectedId]);

  useEffect(() => {
    if (visibleStudents.length === 0) {
      return;
    }
    if (!selectedId || !visibleStudents.some((student) => student.id === selectedId)) {
      setSelectedId(visibleStudents[0].id);
    }
  }, [visibleStudents, selectedId]);

  useEffect(() => {
    setSelectedAnomaly(null);
  }, [selectedId]);

  const selectedStudent = useMemo(
    () => allStudents.find((student) => student.id === selectedId) ?? null,
    [allStudents, selectedId]
  );
  const mentorLabel = studentsResource.data.context?.mentorName || "Mentor";
  const protocolLabel = studentsResource.data.context?.protocolName || selectedStudent?.programName || undefined;

  const kpis = useMemo(() => deriveCommandCenterTopKpis(allStudents), [allStudents]);

  const detail = detailResource.data;
  const anomalies = timelineResource.data?.anomalies ?? [];
  const timelineItems = timelineResource.data?.timeline ?? [];

  return (
    <MentorShell
      activeView="command-center"
      brandLabel={mentorLabel}
      brandTitle={protocolLabel}
      metrics={[
        { label: "Alunos ativos", value: String(kpis.active), tone: "accent" },
        { label: "Alertas de resgate", value: String(kpis.alerts), tone: "warning" },
        { label: "Renovações D-45", value: String(kpis.d45) },
        {
          label: "LTV monitorado",
          value: formatCurrencyBRL(allStudents.reduce((acc, item) => acc + item.ltv, 0)),
          tone: "success"
        }
      ]}
    >
      <section className="cc-page">
        <section className="cc-grid">
          <article className="cc-panel cc-panel--list">
            <header className="cc-panel-header">
              <h2>Alunos monitorados</h2>
              <p>{studentsResource.data.totalStudents} monitorados</p>
            </header>

            {hasRankingTabs && (
              <div className="cc-tabs" role="tablist" aria-label="Ranking dos alunos monitorados">
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === "top"}
                  className={activeTab === "top" ? "cc-tab is-active" : "cc-tab"}
                  onClick={() => setActiveTab("top")}
                >
                  Top 10
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === "bottom"}
                  className={activeTab === "bottom" ? "cc-tab is-active" : "cc-tab"}
                  onClick={() => setActiveTab("bottom")}
                >
                  Bottom 10
                </button>
              </div>
            )}

            {studentsResource.loading && allStudents.length === 0 && <p>Carregando alunos...</p>}
            {!studentsResource.loading && studentsResource.error && allStudents.length === 0 && (
              <div className="cc-error-box">
                <p>{studentsResource.error}</p>
                <button type="button" onClick={() => void studentsResource.refresh()}>
                  Tentar novamente
                </button>
              </div>
            )}
            {!studentsResource.loading && !studentsResource.error && allStudents.length === 0 && (
              <p>Nenhum aluno encontrado para o Centro de Comando.</p>
            )}

            {visibleStudents.length > 0 && (
              <ul className="cc-student-list">
                {visibleStudents.map((student) => {
                  const urgency = URGENCY_META[student.urgency];
                  const progressWidth = `${Math.max(0, Math.min(100, student.progress * 100))}%`;
                  return (
                    <li key={student.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedId(student.id)}
                        className={student.id === selectedId ? "cc-student-row is-active" : "cc-student-row"}
                      >
                        <div className="cc-student-main">
                          <p className="cc-student-name">{student.name}</p>
                          <p className="cc-student-program">{student.programName || "Programa não informado"}</p>
                        </div>
                        <div className="cc-student-stats">
                          <span className={`cc-urgency ${urgency.className}`}>{urgency.label}</span>
                          <span>D-{student.daysLeft}</span>
                        </div>
                        <div className="cc-progress-track" aria-hidden="true">
                          <div className="cc-progress-fill" style={{ width: progressWidth }} />
                        </div>
                        <div className="cc-row-footer">
                          <span>Progresso {formatPercent01(student.progress)}</span>
                          <span>Engajamento {formatPercent01(student.engagement)}</span>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>

          <article className="cc-panel cc-panel--detail">
            <header className="cc-panel-header">
              <h2>Painel do aluno</h2>
              <p>{selectedStudent ? selectedStudent.name : "Sem seleção"}</p>
            </header>

            {!selectedStudent && <p>Selecione um aluno para abrir o detalhe operacional.</p>}
            {selectedStudent && (
              <>
                <section className="cc-student-overview">
                  <h3>{selectedStudent.name}</h3>
                  <p>{selectedStudent.programName || "Programa não informado"}</p>
                  <div className="cc-inline-metrics">
                    <span>Engajamento: {formatPercent01(selectedStudent.engagement)}</span>
                    <span>Progresso: {formatPercent01(selectedStudent.progress)}</span>
                    <span>Hormozi: {selectedStudent.hormoziScore.toFixed(1)}</span>
                  </div>
                </section>

                <section>
                  <h4>Indicadores da jornada</h4>
                  {detailResource.loading && <p>Carregando indicadores...</p>}
                  {detailResource.error && <p className="cc-inline-error">{detailResource.error}</p>}
                  {!detailResource.loading && !detailResource.error && (
                    <>
                      {detail && detail.metricValues.length > 0 ? (
                        <ul className="cc-metric-list">
                          {detail.metricValues.map((metric) => (
                            <li key={metric.id}>
                              <div>
                                <strong>{metric.metricLabel}</strong>
                                <small>
                                  baseline {metric.valueBaseline}
                                  {metric.unit ? ` ${metric.unit}` : ""}
                                </small>
                              </div>
                              <div className="cc-metric-right">
                                <span>
                                  atual {metric.valueCurrent}
                                  {metric.unit ? ` ${metric.unit}` : ""}
                                </span>
                                {metric.valueProjected != null && (
                                  <span>
                                    proj. {metric.valueProjected}
                                    {metric.unit ? ` ${metric.unit}` : ""}
                                  </span>
                                )}
                              </div>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>Nenhum indicador disponível para este aluno.</p>
                      )}
                    </>
                  )}
                </section>

                <section>
                  <h4>Timeline e anomalias</h4>
                  {timelineResource.loading && <p>Carregando timeline...</p>}
                  {timelineResource.error && <p className="cc-inline-error">{timelineResource.error}</p>}
                  {!timelineResource.loading && !timelineResource.error && (
                    <>
                      {timelineItems.length > 0 ? (
                        <ul className="cc-timeline-list">
                          {timelineItems.map((item, index) => (
                            <li key={`${item.week}-${index}`}>
                              <span className={`cc-dot cc-dot--${item.status}`} />
                              <div>
                                <p>
                                  Semana {item.week}: {item.label || "checkpoint"}
                                </p>
                                {item.anomaly && (
                                  <button type="button" onClick={() => setSelectedAnomaly(item.anomaly)}>
                                    Ver anomalia ({item.anomaly.marker})
                                  </button>
                                )}
                              </div>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>Sem timeline registrada para este aluno.</p>
                      )}

                      {anomalies.length > 0 && (
                        <p className="cc-anomaly-count">Anomalias detectadas: {anomalies.length}</p>
                      )}
                    </>
                  )}
                </section>

                {detail && detail.checkpoints.length > 0 && (
                  <section>
                    <h4>Checkpoints</h4>
                    <ul className="cc-checkpoints">
                      {detail.checkpoints.map((checkpoint) => (
                        <li key={checkpoint.id} className={`cc-checkpoint cc-checkpoint--${checkpoint.status}`}>
                          <span>W{checkpoint.week}</span>
                          <small>{checkpoint.label || "checkpoint"}</small>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
              </>
            )}
          </article>
        </section>

        {selectedAnomaly && (
          <div className="cc-modal-backdrop" onClick={() => setSelectedAnomaly(null)}>
            <div className="cc-modal" onClick={(event) => event.stopPropagation()}>
              <header>
                <h3>Hipótese de bloqueio</h3>
                <button type="button" onClick={() => setSelectedAnomaly(null)}>
                  Fechar
                </button>
              </header>
              <p>
                <strong>Indicador:</strong> {selectedAnomaly.marker}
              </p>
              <p>
                <strong>Valor:</strong> {selectedAnomaly.value} (ref: {selectedAnomaly.ref})
              </p>
              <p>
                <strong>Causa:</strong> {selectedAnomaly.cause}
              </p>
              <p>
                <strong>Ação sugerida:</strong> {selectedAnomaly.action}
              </p>
            </div>
          </div>
        )}
      </section>
    </MentorShell>
  );
}
