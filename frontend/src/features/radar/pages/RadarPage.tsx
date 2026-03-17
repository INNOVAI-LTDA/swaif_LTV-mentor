import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { simulateRadar } from "../../../domain/adapters/radarAdapter";
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

export function RadarPage() {
  const studentsResource = useCommandCenterStudents();
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [slider, setSlider] = useState(50);

  useEffect(() => {
    if (!selectedStudentId && studentsResource.data.length > 0) {
      setSelectedStudentId(studentsResource.data[0].id);
    }
  }, [selectedStudentId, studentsResource.data]);

  useEffect(() => {
    setSlider(50);
  }, [selectedStudentId]);

  const radarResource = useStudentRadar(selectedStudentId);
  const simulation = useMemo(() => simulateRadar(radarResource.data, slider), [radarResource.data, slider]);

  const radarPoints = simulation.axisScores.map((axis) => ({
    axisLabel: axis.axisLabel,
    baseline: axis.baseline,
    current: axis.current,
    projected: axis.projected,
    active: axis.active
  }));

  const topGainAxis = useMemo(() => {
    if (simulation.axisScores.length === 0) {
      return null;
    }

    const sorted = [...simulation.axisScores].sort((a, b) => b.active - b.baseline - (a.active - a.baseline));
    return sorted[0];
  }, [simulation.axisScores]);

  const activeValues = simulation.axisScores.map((axis) => axis.active);
  const baselineValues = simulation.axisScores.map((axis) => axis.baseline);
  const currentValues = simulation.axisScores.map((axis) => axis.current);
  const projectedValues = simulation.axisScores.map((axis) => axis.projected);

  const avgBaseline = average(baselineValues);
  const avgCurrent = average(currentValues);
  const avgProjected = average(projectedValues);
  const avgActive = average(activeValues);
  const deltaActiveVsBaseline = avgActive - avgBaseline;

  const selectedStudent = studentsResource.data.find((student) => student.id === selectedStudentId) ?? null;

  return (
    <MentorShell
      activeView="radar"
      eyebrow="Mentor | Radar de Evolução"
      title="Evolução por pilares para sustentar renovação e valor percebido"
      description="Simule o próximo ciclo, compare baseline, estado atual e projeção, e transforme leitura analítica em narrativa clara para o mentorado."
      actions={
        <>
          <button type="button" onClick={() => void Promise.all([studentsResource.refresh(), radarResource.refresh()])}>
            Atualizar leitura
          </button>
          <Link to="/app/centro-comando">Abrir centro</Link>
        </>
      }
      metrics={[
        { label: "Eixos ativos", value: String(simulation.axisScores.length), tone: "accent" },
        { label: "Média baseline", value: avgBaseline.toFixed(1) },
        { label: "Média atual", value: avgCurrent.toFixed(1), tone: "success" },
        { label: "Média projetada", value: avgProjected.toFixed(1), tone: "warning" }
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

          <div className="radar-slider-wrap">
            <div className="radar-slider-header">
              <span>Simulador de projeção</span>
              <strong>{slider}%</strong>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={slider}
              onChange={(event) => setSlider(Number(event.target.value))}
              disabled={!selectedStudentId}
            />
          </div>

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
            <span>Média ativa simulada</span>
            <strong>{avgActive.toFixed(1)}</strong>
          </article>
          <article>
            <span>Delta ativo vs baseline</span>
            <strong>
              {deltaActiveVsBaseline >= 0 ? "+" : ""}
              {deltaActiveVsBaseline.toFixed(1)} pts
            </strong>
          </article>
          <article>
            <span>Aluno em foco</span>
            <strong>{selectedStudent ? selectedStudent.initials : "--"}</strong>
          </article>
        </section>

        <section className="radar-main-grid">
          <article className="radar-panel radar-panel--chart">
            {radarResource.loading && simulation.axisScores.length === 0 && <p className="radar-state">Carregando radar...</p>}
            {!radarResource.loading && radarResource.error && simulation.axisScores.length === 0 && (
              <div className="radar-state radar-state--error">
                <p>{radarResource.error}</p>
                <button type="button" onClick={() => void radarResource.refresh()}>
                  Tentar novamente
                </button>
              </div>
            )}
            {!radarResource.loading && !radarResource.error && simulation.axisScores.length === 0 && (
              <p className="radar-state">Sem dados de radar para este aluno.</p>
            )}

            {simulation.axisScores.length > 0 && (
              <RadarChart points={radarPoints} title="Baseline, atual, projetado e ativo" />
            )}
          </article>

          <article className="radar-panel radar-panel--axis-list">
            <header>
              <h2>Pilares de transformação</h2>
              <p>Deltas calculados pelo simulador</p>
            </header>

            {simulation.axisScores.length > 0 ? (
              <ul className="radar-axis-list">
                {simulation.axisScores.map((axis) => {
                  const delta = axis.active - axis.baseline;
                  return (
                    <li key={axis.axisKey}>
                      <div className="radar-axis-top">
                        <strong>{axis.axisLabel}</strong>
                        <span>
                          {delta >= 0 ? "+" : ""}
                          {delta.toFixed(1)} pts
                        </span>
                      </div>
                      {axis.axisSub && <p className="radar-axis-sub">{axis.axisSub}</p>}
                      <div className="radar-axis-values">
                        <span>baseline {axis.baseline.toFixed(1)}</span>
                        <span>atual {axis.current.toFixed(1)}</span>
                        <span>projetado {axis.projected.toFixed(1)}</span>
                        <span>ativo {axis.active.toFixed(1)}</span>
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
          {!topGainAxis && <p>Selecione um aluno com dados de radar para gerar insight.</p>}
          {topGainAxis && (
            <>
              <p>
                O pilar com maior ganho simulado é <strong>{topGainAxis.axisLabel}</strong>, com delta de{" "}
                <strong>{(topGainAxis.active - topGainAxis.baseline).toFixed(1)} pontos</strong>.
              </p>
              <p>
                Progresso de simulação: <strong>{formatPercent01(slider / 100)}</strong>. Mensagem do contrato:{" "}
                <em>{topGainAxis.insight ?? "Sem insight textual para este eixo."}</em>
              </p>
            </>
          )}
        </section>
      </section>
    </MentorShell>
  );
}
