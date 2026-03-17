import { useState, useEffect, useRef } from "react";
import { useStudents } from "./hooks/useStudents";
import { useStudentRadar } from "./hooks/useStudentRadar";
import { resolveSelectedStudentId } from "./lib/commandCenterUtils.js";
import {
  simulateRadar,
  getRadarInsight,
} from "./lib/radarUtils.js";

// SC-021: All patient data is now loaded from the API via useStudents / useStudentRadar


// â”€â”€ RADAR GEOMETRY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function polarToXY(angle, radius, cx, cy) {
  const rad = (angle - 90) * (Math.PI / 180);
  return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
}

function buildPath(values, maxVal, radius, cx, cy, count) {
  const points = values.map((v, i) => {
    const angle = (360 / count) * i;
    const r = (v / maxVal) * radius;
    return polarToXY(angle, r, cx, cy);
  });
  return points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
}

// â”€â”€ CUSTOM RADAR SVG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function LongevityRadar({ baseline, current, projected, sliderVal, width = 520, height = 520, labels = [] }) {
  const cx = width / 2;
  const cy = height / 2;
  const R = Math.min(width, height) * 0.37;
  const count = labels.length || 1;
  const rings = [20, 40, 60, 80, 100];

  // Interpolate current â†’ projected based on slider (0â€“100)
  const t = sliderVal / 100;
  const active = current.map((c, i) => c + (projected[i] - c) * t);

  const gridPts = rings.map((r) =>
    labels.map((_, i) => polarToXY((360 / count) * i - 90, (r / 100) * R, cx, cy))
  );

  const spokes = labels.map((_, i) => {
    const end = polarToXY((360 / count) * i - 90, R * 1.05, cx, cy);
    return end;
  });

  const baselinePath = buildPath(baseline, 100, R, cx, cy, count);
  const activePath = buildPath(active, 100, R, cx, cy, count);

  const labelPositions = labels.map((_, i) => {
    const angle = (360 / count) * i - 90;
    return polarToXY(angle, R * 1.28, cx, cy);
  });

  // Gold shimmer gradient stops
  const goldOpacity = 0.18 + t * 0.2;

  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <defs>
        <radialGradient id="baseGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#c8a96e" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#c8a96e" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="activeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#d4af37" stopOpacity={goldOpacity + 0.1} />
          <stop offset="100%" stopColor="#d4af37" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="goldFill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#d4af37" stopOpacity={0.28 + t * 0.15} />
          <stop offset="100%" stopColor="#c8963e" stopOpacity={0.18 + t * 0.12} />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="softglow">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Background rings */}
      {gridPts.map((ring, ri) => (
        <polygon
          key={ri}
          points={ring.map((p) => `${p.x},${p.y}`).join(" ")}
          fill="none"
          stroke={ri === 4 ? "#d4af3722" : "#00000008"}
          strokeWidth={ri === 4 ? 1.5 : 1}
          strokeDasharray={ri < 4 ? "3 4" : "none"}
        />
      ))}

      {/* Spokes */}
      {spokes.map((end, i) => (
        <line key={i} x1={cx} y1={cy} x2={end.x} y2={end.y} stroke="#00000010" strokeWidth={1} />
      ))}

      {/* Baseline shape (gray) */}
      <path d={baselinePath} fill="#1a1a1a0d" stroke="#9e9e9e" strokeWidth={1.5} strokeDasharray="5 4" />

      {/* Active glow blob behind */}
      <path d={activePath} fill="url(#activeGlow)" stroke="none" style={{ filter: "blur(18px)" }} />

      {/* Active shape (gold) */}
      <path
        d={activePath}
        fill="url(#goldFill)"
        stroke="#d4af37"
        strokeWidth={2.5}
        style={{ filter: "url(#glow)", transition: "d 0.4s cubic-bezier(.4,0,.2,1)" }}
      />

      {/* Active vertex dots */}
      {active.map((v, i) => {
        const angle = (360 / count) * i - 90;
        const r = (v / 100) * R;
        const pt = polarToXY(angle, r, cx, cy);
        return (
          <circle
            key={i}
            cx={pt.x}
            cy={pt.y}
            r={4}
            fill="#d4af37"
            stroke="#fff8e8"
            strokeWidth={1.5}
            style={{ filter: "url(#glow)", transition: "cx 0.4s, cy 0.4s" }}
          />
        );
      })}

      {/* Axis labels */}
      {labels.map((p, i) => {
        const pos = labelPositions[i];
        const isRight = pos.x > cx + 10;
        const isLeft = pos.x < cx - 10;
        const anchor = isRight ? "start" : isLeft ? "end" : "middle";
        const delta = active[i] - baseline[i];
        return (
          <g key={i}>
            <text
              x={pos.x}
              y={pos.y - 5}
              textAnchor={anchor}
              fill="#1a1208"
              fontSize={11}
              fontFamily="'Cormorant Garamond', Georgia, serif"
              fontWeight={600}
              letterSpacing={0.5}
            >
              {p.label}
            </text>
            <text
              x={pos.x}
              y={pos.y + 9}
              textAnchor={anchor}
              fill="#a08060"
              fontSize={9}
              fontFamily="'Cormorant Garamond', Georgia, serif"
            >
              +{delta.toFixed(0)} pts
            </text>
          </g>
        );
      })}

      {/* Center dot */}
      <circle cx={cx} cy={cy} r={4} fill="#d4af37" opacity={0.6} />
    </svg>
  );
}

// â”€â”€ BIO AGE COUNTER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function BioAgeCounter({ target, label, size = "lg", secondary = false }) {
  const [display, setDisplay] = useState(target + 8);
  const rafRef = useRef(null);
  const startRef = useRef(null);
  const startValRef = useRef(target + 8);

  useEffect(() => {
    startValRef.current = display;
    startRef.current = null;
    const duration = 1800;

    const animate = (ts) => {
      if (!startRef.current) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const val = startValRef.current + (target - startValRef.current) * ease;
      setDisplay(val);
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target]);

  const fontSize = size === "lg" ? 64 : 42;
  const color = secondary ? "#a08060" : "#1a1208";
  const goldColor = secondary ? "#c8963e" : "#d4af37";

  return (
    <div style={{ textAlign: "center", lineHeight: 1 }}>
      <div style={{
        fontFamily: "'Cormorant Garamond', Georgia, serif",
        fontSize,
        fontWeight: 300,
        color,
        letterSpacing: -1,
        lineHeight: 1,
        transition: "color 0.5s"
      }}>
        {display.toFixed(1)}
        <span style={{ fontSize: fontSize * 0.35, color: goldColor, marginLeft: 2, fontWeight: 400 }}>a</span>
      </div>
      <div style={{
        fontSize: 10,
        letterSpacing: 3,
        color: "#a08060",
        marginTop: 6,
        fontFamily: "'Cormorant Garamond', Georgia, serif",
        textTransform: "uppercase"
      }}>
        {label}
      </div>
    </div>
  );
}

// â”€â”€ PILLAR DELTA ROW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function PillarRow({ pillar, sliderVal, index, total }) {
  const t = sliderVal / 100;
  const active = pillar.current + (pillar.projected - pillar.current) * t;
  const delta = active - pillar.baseline;

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "140px 1fr 60px",
      alignItems: "center",
      gap: 16,
      padding: "9px 0",
      borderBottom: index < total - 1 ? "1px solid #d4af3710" : "none",
      animation: `fadeSlideUp 0.5s ${index * 0.06}s both ease-out`
    }}>
      <div>
        <div style={{ fontSize: 11, color: "#1a1208", fontFamily: "'Cormorant Garamond', Georgia, serif", fontWeight: 600 }}>
          {pillar.label}
        </div>
        <div style={{ fontSize: 9, color: "#a08060", letterSpacing: 0.5, marginTop: 1 }}>{pillar.sub}</div>
      </div>
      <div style={{ position: "relative", height: 3, background: "#f0ead0", borderRadius: 2, overflow: "hidden" }}>
        {/* Baseline */}
        <div style={{
          position: "absolute", left: 0, top: 0, height: "100%",
          width: `${pillar.baseline}%`,
          background: "#c0b090",
          borderRadius: 2
        }} />
        {/* Active */}
        <div style={{
          position: "absolute", left: 0, top: 0, height: "100%",
          width: `${active}%`,
          background: "linear-gradient(90deg, #d4af37, #c8963e)",
          borderRadius: 2,
          boxShadow: "0 0 6px #d4af3744",
          transition: "width 0.4s cubic-bezier(.4,0,.2,1)"
        }} />
      </div>
      <div style={{
        textAlign: "right",
        fontSize: 13,
        fontFamily: "'Cormorant Garamond', Georgia, serif",
        color: "#d4af37",
        fontWeight: 700
      }}>
        +{delta.toFixed(0)}
      </div>
    </div>
  );
}

function RadarResourceState({ title, message, actionLabel, onAction }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#faf6ec",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 560,
          background: "#fff8e8",
          border: "1px solid #d4af3730",
          borderRadius: 12,
          padding: "24px 28px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "'Cinzel', serif",
            fontSize: 11,
            letterSpacing: 3,
            color: "#d4af37",
            marginBottom: 10,
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 14,
            color: "#7a5c30",
            lineHeight: 1.7,
            marginBottom: onAction ? 16 : 0,
          }}
        >
          {message}
        </div>
        {onAction && (
          <button
            onClick={onAction}
            style={{
              padding: "10px 14px",
              borderRadius: 6,
              border: "1px solid #d4af3766",
              background: "linear-gradient(135deg, #d4af3722, #c8860b22)",
              color: "#d4af37",
              fontFamily: "'Cinzel', serif",
              fontSize: 10,
              letterSpacing: 2,
              textTransform: "uppercase",
              cursor: "pointer",
            }}
          >
            {actionLabel || "Tentar novamente"}
          </button>
        )}
      </div>
    </div>
  );
}

// â”€â”€ MAIN APP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function App() {
  const {
    data: studentList,
    loading: studentsLoading,
    error: studentsError,
    refresh: refreshStudents,
  } = useStudents();
  const students = studentList ?? [];
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    setSelectedId((prevId) => resolveSelectedStudentId(students, prevId));
  }, [students]);

  const selectedStudent = students.find(
    (student) => String(student.id) === String(selectedId)
  );
  const studentName = selectedStudent?.name ?? null;

  const {
    data: radarData,
    loading: radarLoading,
    error: radarError,
    refresh: refreshRadar,
  } = useStudentRadar(selectedId);

  const [sliderVal, setSliderVal] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => setMounted(true), 100);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    setSliderVal(0);
  }, [selectedId]);

  const simulation = simulateRadar(radarData?.axisScores ?? [], sliderVal);
  const pillars = simulation.axisScores.map((axis) => ({
    key: axis.axisKey,
    label: axis.axisLabel,
    sub: axis.axisSub || "",
    baseline: axis.baseline,
    current: axis.current,
    projected: axis.projected,
    insight: axis.insight,
  }));

  const baseline = simulation.baseline;
  const current = simulation.current;
  const projected = simulation.projected;

  const avgBaseline = simulation.avgBaseline;
  const avgProjected = simulation.avgProjected;
  const activeScore = simulation.activeScore;
  const isProjectionMode = sliderVal > 5;
  const insightText = getRadarInsight(simulation.axisScores, isProjectionMode);

  if (studentsLoading && students.length === 0) {
    return (
      <RadarResourceState
        title="Carregando alunos"
        message="Buscando alunos da mentoria para abrir o Radar de Transformacao."
      />
    );
  }

  if (!studentsLoading && studentsError) {
    return (
      <RadarResourceState
        title="Falha ao carregar alunos"
        message={studentsError}
        actionLabel="Atualizar alunos"
        onAction={refreshStudents}
      />
    );
  }

  if (!studentsLoading && !studentsError && students.length === 0) {
    return (
      <RadarResourceState
        title="Sem alunos"
        message="Nenhum aluno disponivel para analise no Radar."
        actionLabel="Recarregar"
        onAction={refreshStudents}
      />
    );
  }

  if (!selectedId) {
    return (
      <RadarResourceState
        title="Selecao pendente"
        message="Selecione um aluno para analisar os eixos de transformacao."
      />
    );
  }

  if (radarLoading && simulation.count === 0) {
    return (
      <RadarResourceState
        title="Carregando radar"
        message="Buscando os eixos de transformacao do aluno selecionado."
      />
    );
  }

  if (!radarLoading && radarError && simulation.count === 0) {
    return (
      <RadarResourceState
        title="Falha ao carregar radar"
        message={radarError}
        actionLabel="Atualizar radar"
        onAction={refreshRadar}
      />
    );
  }

  if (!radarLoading && !radarError && simulation.count === 0) {
    return (
      <RadarResourceState
        title="Sem dados de radar"
        message="Este aluno ainda nao possui eixos avaliados para o Radar de Transformacao."
        actionLabel="Atualizar radar"
        onAction={refreshRadar}
      />
    );
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Cinzel:wght@400;500&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #faf6ec;
          min-height: 100vh;
        }

        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }

        @keyframes goldReveal {
          from { opacity: 0; transform: scaleX(0); transform-origin: left; }
          to   { opacity: 1; transform: scaleX(1); transform-origin: left; }
        }

        input[type=range] {
          -webkit-appearance: none;
          appearance: none;
          width: 100%;
          height: 2px;
          background: linear-gradient(90deg, #d4af37 0%, #d4af37 var(--progress, 0%), #d4c88044 var(--progress, 0%), #d4c88044 100%);
          border-radius: 2px;
          outline: none;
          cursor: pointer;
        }
        input[type=range]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: radial-gradient(circle at 35% 35%, #f0d060, #b8860b);
          box-shadow: 0 2px 12px #d4af3766;
          border: 2px solid #fff8e8;
          cursor: pointer;
          transition: transform 0.15s;
        }
        input[type=range]::-webkit-slider-thumb:active {
          transform: scale(1.3);
        }
        input[type=range]::-moz-range-thumb {
          width: 18px; height: 18px; border-radius: 50%;
          background: radial-gradient(circle at 35% 35%, #f0d060, #b8860b);
          box-shadow: 0 2px 12px #d4af3766;
          border: 2px solid #fff8e8;
          cursor: pointer;
        }

        .pillar-hover:hover {
          background: #fdf6de !important;
          transition: background 0.2s;
        }
      `}</style>

      <div style={{
        minHeight: "100vh",
        background: "#faf6ec",
        padding: "48px 40px 40px",
        display: "flex",
        flexDirection: "column",
        gap: 0,
        opacity: mounted ? 1 : 0,
        transition: "opacity 0.6s ease",
        maxWidth: 1200,
        margin: "0 auto"
      }}>

        {/* â”€â”€ HEADER â”€â”€ */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: 48,
          animation: "fadeSlideUp 0.7s ease-out both"
        }}>
          <div>
            <div style={{
              fontFamily: "'Cinzel', Georgia, serif",
              fontSize: 11,
              letterSpacing: 5,
              color: "#a08060",
              marginBottom: 8,
              textTransform: "uppercase"
            }}>
              Jornada do Aluno Estruturada · Radar de Transformacao
            </div>
            <h1 style={{
              fontFamily: "'Cormorant Garamond', Georgia, serif",
              fontSize: 38,
              fontWeight: 300,
              color: "#1a1208",
              letterSpacing: -0.5,
              lineHeight: 1
            }}>
              {studentName ?? 'Carregando...'}
            </h1>
            <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 14, color: "#a08060", marginTop: 4 }}>
              Radar de Transformacao · {pillars.length} eixos avaliados
            </div>
          </div>

          {/* Thin gold rule right side */}
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-end",
            gap: 4
          }}>
            <div style={{
              fontFamily: "'Cinzel', serif",
              fontSize: 9,
              letterSpacing: 4,
              color: "#d4af37",
              textTransform: "uppercase"
            }}>
              {isProjectionMode ? "Projecao · Ciclo 2" : "Resultado · Ciclo 1"}
            </div>
            <div style={{
              width: isProjectionMode ? 120 : 60,
              height: 1,
              background: "linear-gradient(90deg, transparent, #d4af37)",
              transition: "width 0.6s ease",
              animation: "goldReveal 1s 0.4s both"
            }} />
          </div>
        </div>

        {radarLoading && simulation.count > 0 && (
          <div style={{ marginBottom: 16, color: "#a08060", fontSize: 11, fontFamily: "'Cormorant Garamond', serif" }}>
            Atualizando eixos do radar...
          </div>
        )}

        {radarError && simulation.count > 0 && (
          <div
            style={{
              marginBottom: 16,
              background: "#fff1ec",
              border: "1px solid #c8860b55",
              borderRadius: 8,
              padding: "10px 12px",
              color: "#7a4f1a",
              fontSize: 11,
              fontFamily: "'Cormorant Garamond', serif",
            }}
          >
            {radarError}
          </div>
        )}

        {/* â”€â”€ MAIN GRID â”€â”€ */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 340px",
          gap: 48,
          alignItems: "start"
        }}>

          {/* LEFT: Radar + Slider */}
          <div style={{ display: "flex", flexDirection: "column", gap: 36 }}>

            {/* Radar chart */}
            <div style={{
              position: "relative",
              display: "flex",
              justifyContent: "center",
              animation: "fadeIn 1s 0.3s both"
            }}>
              {/* Subtle paper texture ring */}
              <div style={{
                position: "absolute",
                inset: 0,
                background: "radial-gradient(circle at 50% 50%, #fff8e844 0%, transparent 70%)",
                borderRadius: "50%",
                pointerEvents: "none"
              }} />

              <LongevityRadar
                baseline={baseline}
                current={current}
                projected={projected}
                sliderVal={sliderVal}
                labels={pillars}
                width={520}
                height={520}
              />

              {/* Legend overlay */}
              <div style={{
                position: "absolute",
                bottom: 12,
                left: "50%",
                transform: "translateX(-50%)",
                display: "flex",
                gap: 24,
                background: "#faf6ecee",
                padding: "8px 18px",
                borderRadius: 32,
                border: "1px solid #d4af3722"
              }}>
                <LegendItem color="#9e9e9e" dash label="InÃ­cio do Ciclo" />
                <LegendItem color="#d4af37" label={isProjectionMode ? "Projecao · Ciclo 2" : "Resultado · Ciclo 1"} />
              </div>
            </div>

            {/* â”€â”€ PROJECTION SLIDER â”€â”€ */}
            <div style={{
              background: "#fff8e8",
              border: "1px solid #d4af3730",
              borderRadius: 12,
              padding: "24px 28px",
              animation: "fadeSlideUp 0.7s 0.5s both"
            }}>
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 20
              }}>
                <div>
                  <div style={{
                    fontFamily: "'Cinzel', serif",
                    fontSize: 10,
                    letterSpacing: 4,
                    color: "#d4af37",
                    textTransform: "uppercase",
                    marginBottom: 4
                  }}>
                    Zona de ProjeÃ§Ã£o Â· Ciclo 2
                  </div>
                  <div style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 14,
                    color: "#a08060",
                    fontStyle: "italic"
                  }}>
                    Arraste para visualizar sua projecao de transformacao
                  </div>
                </div>
                {isProjectionMode && (
                  <div style={{
                    background: "linear-gradient(135deg, #d4af3720, #c8963e20)",
                    border: "1px solid #d4af3744",
                    borderRadius: 6,
                    padding: "4px 12px",
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 12,
                    color: "#d4af37",
                    letterSpacing: 1,
                    animation: "fadeIn 0.3s"
                  }}>
                    +{sliderVal.toFixed(0)}% simulado
                  </div>
                )}
              </div>

              <div style={{ position: "relative", paddingBottom: 20 }}>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={sliderVal}
                  onChange={(e) => setSliderVal(+e.target.value)}
                  style={{ "--progress": `${sliderVal}%` }}
                />
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: 12
                }}>
                  <span style={{ fontSize: 10, color: "#a08060", fontFamily: "'Cormorant Garamond', serif", letterSpacing: 1 }}>
                    Resultado Atual
                  </span>
                  <span style={{ fontSize: 10, color: "#d4af37", fontFamily: "'Cormorant Garamond', serif", letterSpacing: 1 }}>
                    â—† ProjeÃ§Ã£o Ciclo 2 Completo
                  </span>
                </div>
              </div>

              {isProjectionMode && (
                <div style={{
                  marginTop: 8,
                  padding: "12px 16px",
                  background: "linear-gradient(135deg, #1a120800, #d4af370a)",
                  borderRadius: 8,
                  borderLeft: "2px solid #d4af37",
                  animation: "fadeSlideUp 0.4s ease-out"
                }}>
                  <p style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 13,
                    color: "#5a4020",
                    fontStyle: "italic",
                    lineHeight: 1.7
                  }}>
                    Com o Ciclo 2, o score mÃ©dio pode chegar a{" "}
                    <strong style={{ color: "#d4af37", fontStyle: "normal" }}>
                      {avgProjected.toFixed(0)} pts
                    </strong>{" "}
                    â€” <strong style={{ color: "#d4af37", fontStyle: "normal" }}>
                      +{(avgProjected - avgBaseline).toFixed(0)} pts acima
                    </strong> do baseline.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: KPIs + Pillar Details */}
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: 0,
            animation: "fadeSlideUp 0.7s 0.2s both"
          }}>

            {/* Bio Age KPIs */}
            <div style={{
              background: "#fff8e8",
              border: "1px solid #d4af3728",
              borderRadius: 12,
              padding: "28px 24px",
              marginBottom: 24
            }}>
              <div style={{
                fontFamily: "'Cinzel', serif",
                fontSize: 9,
                letterSpacing: 4,
                color: "#a08060",
                textTransform: "uppercase",
                textAlign: "center",
                marginBottom: 24
              }}>
                Score de TransformaÃ§Ã£o
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 8 }}>
                <div style={{ textAlign: "center", opacity: 0.5 }}>
                  <div style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 44,
                    fontWeight: 300,
                    color: "#1a1208",
                    lineHeight: 1
                  }}>
                    {avgBaseline.toFixed(0)}
                    <span style={{ fontSize: 16, color: "#9e9e9e", marginLeft: 1 }}>pts</span>
                  </div>
                  <div style={{ fontSize: 9, letterSpacing: 3, color: "#9e9e9e", marginTop: 6, fontFamily: "'Cormorant Garamond', serif" }}>
                    BASELINE
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                  <div style={{ width: 1, height: 28, background: "linear-gradient(#d4af3700, #d4af37, #d4af3700)" }} />
                  <div style={{ fontSize: 9, color: "#d4af37", letterSpacing: 1, fontFamily: "'Cormorant Garamond', serif" }}>â†’</div>
                  <div style={{ width: 1, height: 28, background: "linear-gradient(#d4af37, #d4af3700)" }} />
                </div>

                <BioAgeCounter target={activeScore} label={isProjectionMode ? "Projecao · Ciclo 2" : "Resultado · Ciclo 1"} />
              </div>

              {/* Delta badge */}
              <div style={{
                marginTop: 20,
                textAlign: "center",
                padding: "10px 0",
                borderTop: "1px solid #d4af3720"
              }}>
                <span style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 13,
                  color: "#d4af37",
                  fontStyle: "italic"
                }}>
                  ↑ {simulation.deltaScore.toFixed(0)} pontos de evolucao de transformacao
                </span>
              </div>
            </div>

            {/* Divider */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 18,
              paddingLeft: 4
            }}>
              <div style={{ fontFamily: "'Cinzel', serif", fontSize: 9, letterSpacing: 4, color: "#a08060", textTransform: "uppercase", whiteSpace: "nowrap" }}>
                {simulation.count} pilares do metodo
              </div>
              <div style={{ flex: 1, height: 1, background: "linear-gradient(90deg, #d4af3330, transparent)" }} />
            </div>

            {/* Pillars */}
            <div style={{ paddingLeft: 4 }}>
              {pillars.map((pillar, i) => (
                <PillarRow key={pillar.key} pillar={pillar} sliderVal={sliderVal} index={i} total={pillars.length} />
              ))}
            </div>

            {/* Insight of hovered pillar or static CTA */}
            <div style={{
              marginTop: 24,
              padding: "16px 18px",
              borderTop: "1px solid #d4af3720",
              borderBottom: "1px solid #d4af3720",
              animation: "fadeIn 0.7s 0.8s both"
            }}>
              <div style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 13,
                color: "#7a5c30",
                fontStyle: "italic",
                lineHeight: 1.7,
                marginBottom: 14
              }}>
                {insightText}
              </div>

              <button
                onClick={() => { }}
                style={{
                  width: "100%",
                  padding: "13px 0",
                  background: "linear-gradient(135deg, #d4af37 0%, #c8860b 100%)",
                  border: "none",
                  borderRadius: 6,
                  color: "#fff8e8",
                  fontFamily: "'Cinzel', serif",
                  fontSize: 11,
                  letterSpacing: 3,
                  cursor: "pointer",
                  textTransform: "uppercase",
                  boxShadow: "0 4px 20px #d4af3744, inset 0 1px 0 #fff8e833",
                  transition: "transform 0.15s, box-shadow 0.15s"
                }}
                onMouseEnter={e => {
                  e.target.style.transform = "translateY(-1px)";
                  e.target.style.boxShadow = "0 8px 28px #d4af3766, inset 0 1px 0 #fff8e833";
                }}
                onMouseLeave={e => {
                  e.target.style.transform = "translateY(0)";
                  e.target.style.boxShadow = "0 4px 20px #d4af3744, inset 0 1px 0 #fff8e833";
                }}
              >
                â—† Apresentar Proposta Ciclo 2
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: 40,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingTop: 20,
          borderTop: "1px solid #d4af3718",
          animation: "fadeIn 1s 1s both"
        }}>
          <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 11, color: "#c0b090", fontStyle: "italic" }}>
            Analise orientada por indicadores do metodo de mentoria.
          </div>
          <div style={{ fontFamily: "'Cinzel', serif", fontSize: 9, letterSpacing: 4, color: "#d4af3788", textTransform: "uppercase" }}>
            JPE Â· Jornada do Aluno Estruturada · Radar de Transformacao
          </div>
        </div>
      </div>
    </>
  );
}

function LegendItem({ color, dash, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
      <svg width={24} height={2}>
        <line
          x1={0} y1={1} x2={24} y2={1}
          stroke={color}
          strokeWidth={2}
          strokeDasharray={dash ? "4 3" : "none"}
        />
      </svg>
      <span style={{ fontSize: 10, color: "#7a5c30", fontFamily: "'Cormorant Garamond', serif" }}>{label}</span>
    </div>
  );
}

