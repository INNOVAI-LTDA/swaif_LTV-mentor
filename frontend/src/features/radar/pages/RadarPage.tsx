import { useEffect, useMemo, useState } from "react";
import { useCommandCenterStudents } from "../../../domain/hooks/useCommandCenter";
import { useStudentRadar } from "../../../domain/hooks/useRadar";
import { formatPercent01 } from "../../../shared/formatters/percent";
import { MentorShell } from "../../mentor/components/MentorShell";
import { RadarChart } from "../components/RadarChart";
import "../radar.css";

function average(values: number[]) {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function formatPercentPointDelta(value: number, fractionDigits = 1) {
  const safe = Number.isFinite(value) ? value : 0;
  return `${safe >= 0 ? "+" : ""}${(safe * 100).toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  })} pp`;
}

export function RadarPage() {
  const studentsResource = useCommandCenterStudents();
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedStudentId && studentsResource.data.length > 0) {
      setSelectedStudentId(studentsResource.data[0].id);
    }
  }, [selectedStudentId, studentsResource.data]);

  const radarResource = useStudentRadar(selectedStudentId);

  const radarPoints = radarResource.data.axisScores.map((axis) => ({
    axisLabel: axis.axisLabel,
    baseline: axis.baseline,
    current: axis.current,
    projected: axis.projected
  }));

  const topGapAxis = useMemo(() => {
    if (radarResource.data.axisScores.length === 0) {
      return null;
    }

    const sorted = [...radarResource.data.axisScores].sort((a, b) => b.projected - b.current - (a.projected - a.current));
    return sorted[0];
  }, [radarResource.data.axisScores]);

  const baselineValues = radarResource.data.axisScores.map((axis) => axis.baseline);
  const currentValues = radarResource.data.axisScores.map((axis) => axis.current);
  const projectedValues = radarResource.data.axisScores.map((axis) => axis.projected);

  const avgBaseline = average(baselineValues);
  const avgCurrent = average(currentValues);
  const avgProjected = average(projectedValues);
  const deltaCurrentVsBaseline = avgCurrent - avgBaseline;
  const gapGoalVsCurrent = avgProjected - avgCurrent;

  const selectedStudent = studentsResource.data.find((student) => student.id === selectedStudentId) ?? null;
  const mentorLabel = radarResource.data.context?.mentorName || "Mentor";
  const protocolLabel = radarResource.data.context?.protocolName || selectedStudent?.programName || undefined;

  return (
    <MentorShell
      activeView="radar"
      brandLabel={mentorLabel}
      brandTitle={protocolLabel}
      metrics={[
        { label: "Eixos ativos", value: String(radarResource.data.axisScores.length), tone: "accent" },
        { label: "Média base", value: formatPercent01(avgBaseline, 1) },
        { label: "Média real", value: formatPercent01(avgCurrent, 1), tone: "success" },
        { label: "Média meta", value: formatPercent01(avgProjected, 1), tone: "warning" }
      ]}
    >
      <section className="radar-page">
        <section className="radar-control-row">
          <label className="radar-select-wrap">
            <span>Aluno</span>
            <select
              value={selectedStudentId ?? ""}
              onChange={(event) => setSelectedStudentId(event.target.value || null)}
              disabled={studentsResource.loading || studentsResource.data.length === 0}
            >
              {studentsResource.data.length === 0 && <option value="">Sem alunos</option>}
              {studentsResource.data.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.name}
                </option>
              ))}
            </select>
          </label>

          <article className="radar-student-chip">
            <p>Aluno selecionado</p>
            <strong>{selectedStudent?.name ?? "Sem seleção"}</strong>
            <span>{selectedStudent?.programName ?? "Programa não informado"}</span>
          </article>
        </section>

        {studentsResource.loading && studentsResource.data.length === 0 && (
          <p className="radar-state">Carregando alunos para o Radar...</p>
        )}
        {studentsResource.error && studentsResource.data.length === 0 && (
          <div className="radar-state radar-state--error">
            <p>{studentsResource.error}</p>
            <button type="button" onClick={() => void studentsResource.refresh()}>
              Tentar novamente
            </button>
          </div>
        )}

        <section className="radar-kpi-grid">
          <article>
            <span>Média real</span>
            <strong>{formatPercent01(avgCurrent, 1)}</strong>
          </article>
          <article>
            <span>Delta real vs base</span>
            <strong>{formatPercentPointDelta(deltaCurrentVsBaseline, 1)}</strong>
          </article>
          <article>
            <span>Gap meta x real</span>
            <strong>{formatPercentPointDelta(gapGoalVsCurrent, 1)}</strong>
          </article>
        </section>

        <section className="radar-main-grid">
          <article className="radar-panel radar-panel--chart">
            {radarResource.loading && radarResource.data.axisScores.length === 0 && <p className="radar-state">Carregando radar...</p>}
            {!radarResource.loading && radarResource.error && radarResource.data.axisScores.length === 0 && (
              <div className="radar-state radar-state--error">
                <p>{radarResource.error}</p>
                <button type="button" onClick={() => void radarResource.refresh()}>
                  Tentar novamente
                </button>
              </div>
            )}
            {!radarResource.loading && !radarResource.error && radarResource.data.axisScores.length === 0 && (
              <p className="radar-state">Sem dados de radar para este aluno.</p>
            )}

            {radarResource.data.axisScores.length > 0 && (
              <RadarChart points={radarPoints} title="Base, real e meta do primeiro carregamento" />
            )}
          </article>

          <article className="radar-panel radar-panel--axis-list">
            <header>
              <h2>Pilares de transformação</h2>
              <p>Leitura base, real e meta por pilar</p>
            </header>

            {radarResource.data.axisScores.length > 0 ? (
              <ul className="radar-axis-list">
                {radarResource.data.axisScores.map((axis) => {
                  const delta = axis.current - axis.baseline;
                  return (
                    <li key={axis.axisKey}>
                      <div className="radar-axis-top">
                        <strong>{axis.axisLabel}</strong>
                        <span>{formatPercentPointDelta(delta, 1)}</span>
                      </div>
                      {axis.axisSub && <p className="radar-axis-sub">{axis.axisSub}</p>}
                      <div className="radar-axis-values">
                        <span>base {formatPercent01(axis.baseline, 1)}</span>
                        <span>real {formatPercent01(axis.current, 1)}</span>
                        <span>meta {formatPercent01(axis.projected, 1)}</span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="radar-state">Sem eixos para exibir.</p>
            )}
          </article>
        </section>

        <section className="radar-insight">
          <h2>Insight principal do ciclo</h2>
          {!topGapAxis && <p>Selecione um aluno com dados de radar para gerar insight.</p>}
          {topGapAxis && (
            <>
              <p>
                O pilar com maior distância até a meta é <strong>{topGapAxis.axisLabel}</strong>, com gap de{" "}
                <strong>{formatPercentPointDelta(topGapAxis.projected - topGapAxis.current, 1)}</strong>.
              </p>
              <p>
                Mensagem do contrato: <em>{topGapAxis.insight ?? "Sem insight textual para este eixo."}</em>
              </p>
            </>
          )}
        </section>
      </section>
    </MentorShell>
  );
}
