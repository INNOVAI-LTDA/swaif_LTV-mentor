import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../../../app/providers/AuthProvider";
import { useCommandCenterStudentDetail, useCommandCenterTimeline } from "../../../domain/hooks/useCommandCenter";
import { useStudentRadar } from "../../../domain/hooks/useRadar";
import type { StudentMetric, TimelineItem } from "../../../domain/models";
import { RadarChart } from "../../radar/components/RadarChart";
import { StudentShell } from "../components/StudentShell";
import "../student.css";

type StudentView = "radar" | "jornada" | "timeline" | "indicadores";
type HelpView = Exclude<StudentView, "jornada">;

const TAB_HELP: Record<HelpView, { title: string; body: string }> = {
  radar: {
    title: "Leitura do radar",
    body: "Aqui voce entende rapidamente quais pilares estao mais fortes no seu momento atual e onde ainda existe espaco para evolucao."
  },
  timeline: {
    title: "Leitura da linha do tempo",
    body: "Aqui voce acompanha os marcos do seu ciclo e identifica qual e o proximo ponto relevante da sua jornada."
  },
  indicadores: {
    title: "Leitura dos indicadores",
    body: "Aqui voce compara sinais atuais, base e projecao para entender o que esta sustentando o seu resultado."
  }
};

const DEFAULT_STUDENT_ID = "std_1";

const STUDENT_PREVIEW_BY_EMAIL: Record<string, string> = {
  "aline.rocha@swaif.demo": "std_1",
  "aluno@aceleradormedico.demo": "std_1"
};

const STATUS_CLASSNAME: Record<TimelineItem["status"], string> = {
  green: "is-green",
  yellow: "is-yellow",
  red: "is-red"
};

function average(values: number[]) {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function resolveStudentId(email: string | null | undefined) {
  if (!email) {
    return DEFAULT_STUDENT_ID;
  }

  return STUDENT_PREVIEW_BY_EMAIL[email.trim().toLowerCase()] ?? DEFAULT_STUDENT_ID;
}

function resolveView(value: string | null): StudentView {
  if (value === "jornada" || value === "timeline" || value === "indicadores") {
    return value;
  }

  return "radar";
}

type TabHelpPopoverProps = {
  view: HelpView;
  openView: HelpView | null;
  onToggle: (view: HelpView) => void;
  onClose: () => void;
};

function TabHelpPopover({ view, openView, onToggle, onClose }: TabHelpPopoverProps) {
  const help = TAB_HELP[view];
  const isOpen = openView === view;

  return (
    <div className={isOpen ? "student-help is-open" : "student-help"} onMouseLeave={onClose}>
      <button
        type="button"
        className="student-help__button"
        aria-label={help.title}
        aria-expanded={isOpen}
        onClick={() => onToggle(view)}
      >
        ?
      </button>
      {isOpen && (
        <div className="student-help__popover" role="note">
          <strong>{help.title}</strong>
          <p>{help.body}</p>
        </div>
      )}
    </div>
  );
}

function TimelineStatusChart({ items }: { items: TimelineItem[] }) {
  if (items.length === 0) {
    return <p className="student-state">Sem dados visuais da linha do tempo.</p>;
  }

  return (
    <div className="student-timeline-chart" aria-label="Resumo visual da linha do tempo">
      {items.map((item) => (
        <article key={`${item.week}-${item.label}`} className={`student-timeline-chart__step ${STATUS_CLASSNAME[item.status]}`}>
          <span className="student-timeline-chart__week">S{item.week}</span>
          <div className="student-timeline-chart__marker" aria-hidden="true" />
          <strong>{item.label}</strong>
          <small>{item.anomaly ? item.anomaly.value : "Fluxo estavel"}</small>
        </article>
      ))}
    </div>
  );
}

function IndicatorBars({ metrics }: { metrics: StudentMetric[] }) {
  const items = metrics.slice(0, 4);
  const maxValue = Math.max(
    1,
    ...items.flatMap((metric) => [
      metric.valueBaseline,
      metric.valueCurrent,
      metric.valueProjected ?? 0
    ])
  );

  if (items.length === 0) {
    return <p className="student-state">Sem dados visuais dos indicadores.</p>;
  }

  return (
    <div className="student-indicator-chart" aria-label="Grafico comparativo de indicadores">
      {items.map((metric) => (
        <article key={metric.id} className="student-indicator-chart__group">
          <div className="student-indicator-chart__bars" aria-hidden="true">
            <span className="student-indicator-chart__bar is-baseline" style={{ height: `${(metric.valueBaseline / maxValue) * 120}px` }} />
            <span className="student-indicator-chart__bar is-current" style={{ height: `${(metric.valueCurrent / maxValue) * 120}px` }} />
            <span
              className="student-indicator-chart__bar is-projected"
              style={{ height: `${((metric.valueProjected ?? 0) / maxValue) * 120}px` }}
            />
          </div>
          <strong>{metric.metricLabel}</strong>
          <small>Base | Atual | Proj.</small>
        </article>
      ))}
    </div>
  );
}

export function StudentPage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [openHelp, setOpenHelp] = useState<HelpView | null>(null);
  const activeView = resolveView(searchParams.get("view"));
  const studentId = resolveStudentId(user?.email);
  const detailResource = useCommandCenterStudentDetail(studentId);
  const timelineResource = useCommandCenterTimeline(studentId);
  const radarResource = useStudentRadar(studentId);

  const selectedStudent = detailResource.data;
  const timelineItems = timelineResource.data?.timeline ?? [];
  const indicatorItems = detailResource.data?.metricValues ?? [];

  const radarPoints = radarResource.data.axisScores.map((axis) => ({
    axisLabel: axis.axisLabel,
    baseline: axis.baseline,
    current: axis.current,
    projected: axis.projected,
    active: axis.current
  }));

  const strongestAxis = useMemo(() => {
    if (radarResource.data.axisScores.length === 0) {
      return null;
    }

    return [...radarResource.data.axisScores].sort((a, b) => b.current - a.current)[0];
  }, [radarResource.data.axisScores]);

  const weakestAxis = useMemo(() => {
    if (radarResource.data.axisScores.length === 0) {
      return null;
    }

    return [...radarResource.data.axisScores].sort((a, b) => a.current - b.current)[0];
  }, [radarResource.data.axisScores]);

  const nextCheckpoint =
    detailResource.data?.checkpoints.find((checkpoint) => checkpoint.status !== "green") ??
    detailResource.data?.checkpoints[0] ??
    null;

  const avgCurrent = average(radarResource.data.axisScores.map((axis) => axis.current));
  const avgProjected = average(radarResource.data.axisScores.map((axis) => axis.projected));

  const viewCopy = {
    radar: {
      eyebrow: "Aluno | Radar de Evolucao",
      title: selectedStudent ? `${selectedStudent.name}, acompanhe seu radar de evolucao` : "Acompanhe seu radar de evolucao",
      description: "Leitura visual principal do aluno, mostrando de forma imediata os pilares que estao puxando ou travando a sua evolucao.",
      secondaryHref: "/app/aluno?view=timeline",
      secondaryLabel: "Ver linha do tempo"
    },
    timeline: {
      eyebrow: "Aluno | Linha do Tempo",
      title: selectedStudent ? `${selectedStudent.name}, acompanhe seu ciclo por marcos` : "Acompanhe seu ciclo por marcos",
      description: "Visao da jornada organizada pela progressao do programa, com destaque para os marcos ja percorridos e o proximo ponto de atencao.",
      secondaryHref: "/app/aluno?view=indicadores",
      secondaryLabel: "Ver indicadores"
    },
    indicadores: {
      eyebrow: "Aluno | Indicadores",
      title: selectedStudent ? `${selectedStudent.name}, entenda o que sustenta seu resultado` : "Entenda o que sustenta seu resultado",
      description: "Visao comparativa dos sinais que explicam seu momento atual, combinando resumo visual e leitura detalhada dos indicadores.",
      secondaryHref: "/app/aluno?view=jornada",
      secondaryLabel: "Ver sua jornada"
    },
    jornada: {
      eyebrow: "Aluno | Sua Jornada",
      title: selectedStudent ? `${selectedStudent.name}, veja sua jornada atual` : "Veja sua jornada atual",
      description: "Visao textual e contextual da sua experiencia, sem grafico, focada em momento atual, proximos passos e leitura de programa.",
      secondaryHref: "/app/aluno?view=radar",
      secondaryLabel: "Ver radar"
    }
  } as const;

  const headerCopy = viewCopy[activeView];

  function toggleHelp(view: HelpView) {
    setOpenHelp((current) => (current === view ? null : view));
  }

  useEffect(() => {
    if (!openHelp) {
      return;
    }

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (target instanceof HTMLElement && target.closest(".student-help")) {
        return;
      }

      setOpenHelp(null);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [openHelp]);

  return (
    <StudentShell
      eyebrow={headerCopy.eyebrow}
      title={headerCopy.title}
      description={headerCopy.description}
      actions={
        <>
          <button
            type="button"
            onClick={() =>
              void Promise.all([detailResource.refresh(), timelineResource.refresh(), radarResource.refresh()])
            }
          >
            Atualizar leitura
          </button>
          <Link to={headerCopy.secondaryHref}>{headerCopy.secondaryLabel}</Link>
        </>
      }
    >
      <section className="student-page">
        <section className="student-tab-panel">
          {activeView === "jornada" && (
            <div className="student-view-stack">
              <section className="student-grid student-grid--balanced">
                <article className="student-module student-module--summary">
                  <div className="student-module__header">
                    <div>
                      <p className="student-module__eyebrow">Seu momento</p>
                      <h2>{selectedStudent?.name ?? "Carregando jornada"}</h2>
                    </div>
                    <div className="student-identity-chip">
                      <span>Perfil autenticado</span>
                      <strong>{user?.email ?? "preview-aluno"}</strong>
                    </div>
                  </div>

                  {selectedStudent ? (
                    <>
                      <p className="student-summary-copy">
                        Esta visao organiza a leitura mais pessoal da sua experiencia. O foco aqui e entender onde voce
                        esta no programa, o que ja ganhou tracao e qual deve ser o proximo passo.
                      </p>

                      <div className="student-summary-grid">
                        <article>
                          <span>Programa</span>
                          <strong>{selectedStudent.programName}</strong>
                        </article>
                        <article>
                          <span>Hoje no ciclo</span>
                          <strong>
                            Dia {selectedStudent.day} de {selectedStudent.totalDays}
                          </strong>
                        </article>
                        <article>
                          <span>Dias restantes</span>
                          <strong>{selectedStudent.daysLeft}</strong>
                        </article>
                        <article>
                          <span>Ritmo de acompanhamento</span>
                          <strong>{selectedStudent.engagement}%</strong>
                        </article>
                      </div>
                    </>
                  ) : (
                    <p className="student-state">Nao foi possivel carregar a sua jornada agora.</p>
                  )}
                </article>

                <article className="student-module student-module--checkpoint">
                  <p className="student-module__eyebrow">Seu proximo marco</p>
                  <h2>{nextCheckpoint ? `Semana ${nextCheckpoint.week}` : "Sem checkpoint"}</h2>
                  <p>{nextCheckpoint?.label ?? "Nao ha checkpoints configurados para este aluno."}</p>
                  <div className="student-checkpoint-pill">
                    <span>Status</span>
                    <strong>{nextCheckpoint?.status ?? "indefinido"}</strong>
                  </div>
                </article>
              </section>

              <section className="student-grid student-grid--balanced">
                <article className="student-module">
                  <p className="student-module__eyebrow">Leitura da fase</p>
                  <h2>Como voce entra nesta etapa do programa</h2>
                  <div className="student-copy-stack">
                    <p>
                      Sua Jornada nao mostra grafico. Ela existe para resumir seu momento de forma direta, com linguagem
                      clara e foco no que muda seu acompanhamento.
                    </p>
                    <p>
                      Use esta visao quando quiser uma leitura contextual: onde voce esta, quanto ainda falta e qual e
                      o proximo marco mais importante.
                    </p>
                  </div>
                </article>

                <article className="student-module">
                  <p className="student-module__eyebrow">Proximo passo</p>
                  <h2>O que merece atencao agora</h2>
                  <div className="student-copy-stack">
                    <p>
                      {nextCheckpoint
                        ? `Seu proximo checkpoint relevante esta na semana ${nextCheckpoint.week}, com foco em ${nextCheckpoint.label}.`
                        : "Assim que houver um checkpoint priorizado, ele vai aparecer aqui como seu proximo passo."}
                    </p>
                    <p>
                      Se quiser uma leitura mais visual do momento, volte para Radar de Evolucao ou abra Linha do Tempo
                      para ver a progressao do ciclo.
                    </p>
                  </div>
                </article>
              </section>
            </div>
          )}

          {activeView === "radar" && (
            <div className="student-view-stack">
              <article className="student-module student-module--radar">
                <div className="student-module__eyebrow-row">
                  <p className="student-module__eyebrow">Radar de evolucao</p>
                  <TabHelpPopover
                    view="radar"
                    openView={openHelp}
                    onToggle={toggleHelp}
                    onClose={() => setOpenHelp(null)}
                  />
                </div>
                <div className="student-module__header">
                  <div>
                    <h2>Leitura central da sua jornada</h2>
                  </div>
                  {strongestAxis && (
                    <div className="student-highlight-chip">
                      <span>Pilar mais forte</span>
                      <strong>{strongestAxis.axisLabel}</strong>
                    </div>
                  )}
                </div>

                {radarResource.loading && radarResource.data.axisScores.length === 0 && (
                  <p className="student-state">Carregando radar...</p>
                )}
                {radarResource.error && radarResource.data.axisScores.length === 0 && (
                  <div className="student-state student-state--error">
                    <p>{radarResource.error}</p>
                    <button type="button" onClick={() => void radarResource.refresh()}>
                      Tentar novamente
                    </button>
                  </div>
                )}
                {!radarResource.loading && !radarResource.error && radarPoints.length === 0 && (
                  <p className="student-state">Sem dados de radar para este aluno.</p>
                )}
                {radarPoints.length > 0 && <RadarChart points={radarPoints} title="Baseline, atual e projecao do aluno" />}
              </article>

              <section className="student-grid student-grid--balanced">
                <article className="student-module">
                  <p className="student-module__eyebrow">Leitura do momento</p>
                  <h2>Onde sua tracao ja aparece</h2>
                  <div className="student-copy-stack">
                    <p>
                      {strongestAxis
                        ? `${strongestAxis.axisLabel} aparece como seu eixo mais forte no momento atual.`
                        : "Assim que os eixos forem carregados, esta secao vai destacar o ponto mais forte da sua leitura."}
                    </p>
                    <p>
                      A media atual do radar esta em {avgCurrent.toFixed(1)}, com potencial projetado de {avgProjected.toFixed(1)}.
                    </p>
                  </div>
                </article>

                <article className="student-module">
                  <p className="student-module__eyebrow">Ponto de atencao</p>
                  <h2>Onde ainda existe espaco para evoluir</h2>
                  <div className="student-copy-stack">
                    <p>
                      {weakestAxis
                        ? `${weakestAxis.axisLabel} e o eixo que hoje pede mais energia e consistencia.`
                        : "Quando o radar estiver completo, esta secao vai destacar o eixo com mais margem de evolucao."}
                    </p>
                    <p>
                      Use esta visao para entender rapidamente o equilibrio entre seus pilares, antes de aprofundar em
                      Linha do Tempo e Indicadores.
                    </p>
                  </div>
                </article>
              </section>
            </div>
          )}

          {activeView === "timeline" && (
            <div className="student-view-stack">
              <article className="student-module">
                <div className="student-module__eyebrow-row">
                  <p className="student-module__eyebrow">Sua linha do tempo</p>
                  <TabHelpPopover
                    view="timeline"
                    openView={openHelp}
                    onToggle={toggleHelp}
                    onClose={() => setOpenHelp(null)}
                  />
                </div>
                <h2>Grafico visual do seu ciclo</h2>
                <TimelineStatusChart items={timelineItems} />
              </article>

              <section className="student-grid">
                <article className="student-module">
                  <p className="student-module__eyebrow">Marcos do programa</p>
                  <h2>Detalhamento da sua progressao</h2>
                  {timelineItems.length > 0 ? (
                    <ul className="student-timeline-list">
                      {timelineItems.map((item) => (
                        <li key={`${item.week}-${item.label}`}>
                          <strong>Semana {item.week}</strong>
                          <span>{item.label}</span>
                          <small>{item.anomaly ? item.anomaly.action : "Sem anomalia relevante para este marco."}</small>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="student-state">Sem timeline disponivel.</p>
                  )}
                </article>

                <article className="student-module">
                  <p className="student-module__eyebrow">Leitura do ciclo</p>
                  <h2>O que o fluxo mostra agora</h2>
                  <div className="student-copy-stack">
                    <p>
                      {nextCheckpoint
                        ? `Seu proximo ponto de atencao esta na semana ${nextCheckpoint.week}: ${nextCheckpoint.label}.`
                        : "Quando houver um checkpoint definido, ele vai aparecer aqui como o proximo passo prioritario."}
                    </p>
                    <p>
                      A Linha do Tempo ajuda a entender ritmo, marcos e desvios do programa sem perder a clareza visual
                      do ciclo completo.
                    </p>
                  </div>
                </article>
              </section>
            </div>
          )}

          {activeView === "indicadores" && (
            <div className="student-view-stack">
              <article className="student-module student-module--metrics">
                <div className="student-module__eyebrow-row">
                  <p className="student-module__eyebrow">Indicadores da sua jornada</p>
                  <TabHelpPopover
                    view="indicadores"
                    openView={openHelp}
                    onToggle={toggleHelp}
                    onClose={() => setOpenHelp(null)}
                  />
                </div>
                <h2>Grafico comparativo dos seus indicadores</h2>
                <div className="student-metrics student-metrics--embedded">
                  <article className="student-metric student-metric--accent">
                    <span>Seu progresso</span>
                    <strong>{selectedStudent ? `${selectedStudent.progress}%` : "--"}</strong>
                  </article>
                  <article className="student-metric student-metric--success">
                    <span>Seu engajamento</span>
                    <strong>{selectedStudent ? `${selectedStudent.engagement}%` : "--"}</strong>
                  </article>
                  <article className="student-metric">
                    <span>Media atual</span>
                    <strong>{avgCurrent.toFixed(1)}</strong>
                  </article>
                  <article className="student-metric student-metric--warning">
                    <span>Potencial projetado</span>
                    <strong>{avgProjected.toFixed(1)}</strong>
                  </article>
                </div>
                <IndicatorBars metrics={indicatorItems} />
              </article>

              <section className="student-grid">
                <article className="student-module">
                  <p className="student-module__eyebrow">Detalhamento dos indicadores</p>
                  <h2>Leitura completa dos sinais</h2>
                  {indicatorItems.length > 0 ? (
                    <ul className="student-indicator-list">
                      {indicatorItems.slice(0, 6).map((metric) => (
                        <li key={metric.id}>
                          <div>
                            <strong>{metric.metricLabel}</strong>
                            <span>{metric.optimal ?? "Faixa de referencia em definicao"}</span>
                          </div>
                          <div className="student-indicator-values">
                            <small>
                              Atual {metric.valueCurrent}
                              {metric.unit}
                            </small>
                            <small>
                              Base {metric.valueBaseline}
                              {metric.unit}
                            </small>
                            <small>
                              Proj. {metric.valueProjected !== null ? `${metric.valueProjected}${metric.unit}` : "--"}
                            </small>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="student-state">Sem indicadores disponiveis.</p>
                  )}
                </article>

                <article className="student-module">
                  <p className="student-module__eyebrow">Leitura do resultado</p>
                  <h2>Quais sinais mais pesam hoje</h2>
                  <div className="student-copy-stack">
                    <p>
                      Esta visao mostra o que esta sustentando ou limitando seu resultado com base na comparacao entre
                      valor atual, baseline e projecao.
                    </p>
                    <p>
                      Use este quadro quando quiser aprofundar a leitura que o Radar ja sugeriu de forma mais sintetica.
                    </p>
                  </div>
                </article>
              </section>
            </div>
          )}
        </section>
      </section>
    </StudentShell>
  );
}
