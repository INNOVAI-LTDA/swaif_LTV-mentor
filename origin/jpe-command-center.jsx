import { useState, useEffect } from "react";
import { useStudents } from "./hooks/useStudents";
import { useStudentDetail } from "./hooks/useStudentDetail";
import { formatPercent01 } from "./lib/formatters.js";
import {
  deriveCommandCenterKpis,
  resolveSelectedStudentId,
  safeProgressPercent,
} from "./lib/commandCenterUtils.js";

// â”€â”€ DATA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// SC-016: All patient data is now loaded from the API via useStudents / useStudentDetail

// PILLAR_LABELS removed; checkpoints from API are used instead
const MARKER_CONFIG = {
  insulin: { label: "Insulina", unit: "ÂµU/mL", optimal: "< 7", icon: "âš¡" },
  pcr: { label: "PCR-us", unit: "mg/L", optimal: "< 1.0", icon: "ðŸ”¥" },
  cortisol: { label: "Cortisol", unit: "Âµg/dL", optimal: "< 18", icon: "ðŸŒ€" },
  testosterone: { label: "Testosterona", unit: "ng/dL", optimal: "> 500", icon: "âš™ï¸" },
  hrv: { label: "HRV", unit: "ms", optimal: "> 50", icon: "ðŸ’“" },
  glucose: { label: "Glicemia", unit: "mg/dL", optimal: "< 90", icon: "ðŸ©¸" },
  vitD: { label: "Vitamina D", unit: "ng/mL", optimal: "> 60", icon: "â˜€ï¸" },
};

// â”€â”€ HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const statusColor = {
  green: { dot: "#00ff87", line: "#00ff8766", glow: "0 0 8px #00ff87" },
  yellow: { dot: "#ffd60a", line: "#ffd60a88", glow: "0 0 8px #ffd60a" },
  red: { dot: "#ff3a3a", line: "#ff3a3a88", glow: "0 0 12px #ff3a3a" },
};

function getRisk(p) {
  return p.urgency === 'rescue' ? 'red'
    : (p.urgency === 'watch' || p.urgency === 'critical') ? 'yellow'
      : 'green';
}

function getProgress(p) {
  return safeProgressPercent(p);
}

function getBioAgeDelta(p) {
  return formatPercent01(p.engagement || 0);
}

// â”€â”€ COMPONENTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function Scanline() {
  return (
    <div style={{
      position: "fixed", inset: 0, pointerEvents: "none", zIndex: 9999,
      background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)"
    }} />
  );
}

function TopBar({ kpis = { active: 0, alerts: 0, d45: 0 } }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t); }, []);

  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 28px", height: 56, borderBottom: "1px solid #0ff2",
      background: "linear-gradient(90deg, #000a0f 0%, #001a2f 100%)",
      fontFamily: "'Courier New', monospace"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%", background: "#00ff87",
          boxShadow: "0 0 10px #00ff87", animation: "pulse 2s infinite"
        }} />
        <span style={{ color: "#00ff87", fontSize: 13, letterSpacing: 3, fontWeight: 700 }}>
          CEREBRO JPE - CENTRO DE COMANDO
        </span>
        <span style={{ color: "#0088aa", fontSize: 11, marginLeft: 8, letterSpacing: 2 }}>
          GESTAO DE MENTORIA HIGH TICKET
        </span>
      </div>
      <div style={{ display: "flex", gap: 28, alignItems: "center" }}>
        <Stat label="ALUNOS ATIVOS" value={String(kpis.active)} color="#00ff87" />
        <Stat label="ALERTAS CRITICOS" value={String(kpis.alerts)} color="#ff3a3a" />
        <Stat label="RENOVACOES D-45" value={String(kpis.d45)} color="#ffd60a" />
        <div style={{ color: "#0088aa", fontSize: 11, letterSpacing: 2 }}>
          {time.toLocaleTimeString("pt-BR")} | {time.toLocaleDateString("pt-BR")}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ color, fontSize: 18, fontWeight: 900, fontFamily: "'Courier New', monospace", lineHeight: 1 }}>{value}</div>
      <div style={{ color: "#446", fontSize: 9, letterSpacing: 2, marginTop: 2 }}>{label}</div>
    </div>
  );
}

// Patient Timeline Row
function PatientRow({ patient, onAnomalyClick, selected, onClick }) {
  const risk = getRisk(patient);
  const progress = getProgress(patient);
  const delta = getBioAgeDelta(patient);
  const sc = statusColor[risk];

  return (
    <div
      onClick={onClick}
      style={{
        display: "grid",
        gridTemplateColumns: "220px 1fr 180px",
        alignItems: "center",
        padding: "18px 28px",
        borderBottom: "1px solid #0ff1",
        cursor: "pointer",
        background: selected ? "linear-gradient(90deg, #001a2f 0%, #00111f 100%)" : "transparent",
        transition: "background 0.2s",
        position: "relative",
      }}
    >
      {/* Left: Patient info */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: sc.dot, boxShadow: sc.glow }} />
          <span style={{ color: "#e0f4ff", fontSize: 14, fontWeight: 700, letterSpacing: 0.5 }}>{patient.name}</span>
        </div>
        <div style={{ color: "#446688", fontSize: 11, letterSpacing: 1, marginLeft: 18, marginBottom: 2 }}>
          {patient.programName}
        </div>
        <div style={{ display: "flex", gap: 10, marginLeft: 18 }}>
          <Tag color="#00ff87">âš¡{delta} engaj.</Tag>
          {(patient.daysLeft <= 45) && <Tag color="#ffd60a">ðŸ”„ D-45</Tag>}
          {(patient.urgency === 'watch') && <Tag color="#ff6b35">âš  Tangibilizar</Tag>}
        </div>
      </div>

      {/* Center: Progress timeline */}
      <div style={{ padding: "0 24px" }}>
        <div style={{ position: "relative", height: 4, borderRadius: 2, background: "#0a1a2a", overflow: "hidden", margin: "16px 0" }}>
          <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${progress}%`, background: `linear-gradient(90deg, ${sc.dot}88, ${sc.dot})`, borderRadius: 2, transition: "width 1s ease" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          {["M1", "M2", "M3", "M4", "M5", "M6"].map((m, i) => (
            <span key={i} style={{ color: "#334455", fontSize: 9, letterSpacing: 1 }}>{m}</span>
          ))}
        </div>
      </div>

      {/* Right: Engagement + progress */}
      <div style={{ textAlign: "right" }}>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "flex-end", gap: 4 }}>
          <span style={{ color: "#446688", fontSize: 11 }}>Engaj.</span>
          <span style={{ color: "#00ff87", fontSize: 22, fontWeight: 900, fontFamily: "'Courier New', monospace", lineHeight: 1 }}>{delta}</span>
        </div>
        <div style={{ marginTop: 8, position: "relative", height: 4, borderRadius: 2, background: "#0a1a2a", overflow: "hidden" }}>
          <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${progress}%`, background: `linear-gradient(90deg, ${sc.dot}88, ${sc.dot})`, borderRadius: 2, transition: "width 1s ease" }} />
        </div>
        <div style={{ color: "#446688", fontSize: 10, marginTop: 4, letterSpacing: 1 }}>
          DIA {patient.day} / {patient.totalDays} Â· {progress}%
        </div>
      </div>
    </div>
  );
}

function Tag({ color, children }) {
  return (
    <span style={{
      color, fontSize: 9, fontWeight: 700, letterSpacing: 1,
      border: `1px solid ${color}44`, padding: "2px 6px", borderRadius: 3,
      background: `${color}11`, fontFamily: "'Courier New', monospace"
    }}>{children}</span>
  );
}

function Timeline({ segments, totalDays, currentDay, onAnomalyClick }) {
  const trackW = "100%";
  return (
    <div style={{ padding: "0 24px", position: "relative" }}>
      {/* Track line */}
      <div style={{
        position: "relative", height: 4, borderRadius: 2,
        background: "linear-gradient(90deg, #0a1a2a 0%, #0a1a2a 100%)",
        margin: "16px 0"
      }}>
        {/* Colored segments */}
        {segments.map((seg, i) => {
          const x1 = ((seg.week - 1) / 24) * 100;
          const x2 = i < segments.length - 1 ? (((segments[i + 1].week - 1) / 24) * 100) : ((currentDay / totalDays) * 100);
          const sc = statusColor[seg.status];
          return (
            <div key={i} style={{
              position: "absolute", left: `${x1}%`, width: `${x2 - x1}%`,
              height: "100%", background: sc.dot, opacity: 0.6, borderRadius: 2
            }} />
          );
        })}
        {/* Current position indicator */}
        <div style={{
          position: "absolute",
          left: `${(currentDay / totalDays) * 100}%`,
          top: "50%", transform: "translate(-50%, -50%)",
          width: 10, height: 10, borderRadius: "50%",
          background: "#00eeff",
          boxShadow: "0 0 12px #00eeff, 0 0 24px #00eeff44",
          zIndex: 2,
        }} />
        {/* Anomaly dots */}
        {segments.filter(s => s.anomaly).map((seg, i) => {
          const x = ((seg.week - 1) / 24) * 100;
          const sc = statusColor[seg.status];
          return (
            <AnomalyDot key={i} x={x} color={sc.dot} glow={sc.glow} seg={seg} onAnomalyClick={onAnomalyClick} />
          );
        })}
      </div>
      {/* Week labels */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        {["M1", "M2", "M3", "M4", "M5", "M6"].map((m, i) => (
          <span key={i} style={{ color: "#334455", fontSize: 9, letterSpacing: 1 }}>{m}</span>
        ))}
      </div>
    </div>
  );
}

function AnomalyDot({ x, color, glow, seg, onAnomalyClick }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={(e) => { e.stopPropagation(); onAnomalyClick(seg.anomaly, { x, color }); }}
      style={{
        position: "absolute", left: `${x}%`, top: "50%",
        transform: "translate(-50%, -50%)",
        width: hovered ? 16 : 12, height: hovered ? 16 : 12,
        borderRadius: "50%", background: color,
        boxShadow: glow,
        cursor: "pointer", zIndex: 3, transition: "all 0.15s",
        border: `2px solid ${color}`,
        animation: "anomalyPulse 2s infinite"
      }}
    />
  );
}

// Insight Card (floating popup)
function InsightCard({ anomaly, onClose, style }) {
  if (!anomaly) return null;
  return (
    <div style={{
      position: "fixed", top: "50%", left: "50%",
      transform: "translate(-50%, -50%)",
      width: 420, zIndex: 1000,
      background: "linear-gradient(145deg, #000d1a 0%, #001525 100%)",
      border: "1px solid #00eeff44",
      borderRadius: 8,
      boxShadow: "0 0 40px #00eeff22, 0 24px 80px #000a",
      padding: 28,
      fontFamily: "'Courier New', monospace",
      animation: "cardIn 0.2s ease-out",
    }}>
      {/* Close */}
      <button onClick={onClose} style={{
        position: "absolute", top: 12, right: 16,
        background: "none", border: "none", color: "#446688",
        fontSize: 18, cursor: "pointer"
      }}>âœ•</button>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <div style={{ width: 6, height: 6, borderRadius: "50%", background: style?.color || "#ff3a3a", boxShadow: `0 0 8px ${style?.color || "#ff3a3a"}` }} />
        <span style={{ color: "#0088cc", fontSize: 9, letterSpacing: 3, textTransform: "uppercase" }}>
          Insight Card Â· Metodo de Mentoria
        </span>
      </div>

      {/* Data anomaly */}
      <div style={{ background: "#00060f", borderRadius: 6, padding: "14px 16px", marginBottom: 16, border: `1px solid ${style?.color || "#ff3a3a"}33` }}>
        <div style={{ color: "#446688", fontSize: 9, letterSpacing: 2, marginBottom: 6 }}>DADO ANÃ”MALO</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ color: "#e0f4ff", fontSize: 16, fontWeight: 700 }}>{anomaly.marker}</span>
          <div style={{ textAlign: "right" }}>
            <span style={{ color: style?.color || "#ff3a3a", fontSize: 20, fontWeight: 900 }}>{anomaly.value}</span>
            <div style={{ color: "#446688", fontSize: 10 }}>Ref: {anomaly.ref}</div>
          </div>
        </div>
      </div>

      {/* Cause */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ color: "#446688", fontSize: 9, letterSpacing: 2, marginBottom: 8 }}>HIPOTESE DE BLOQUEIO Â· METODO DE MENTORIA</div>
        <p style={{ color: "#8ab0cc", fontSize: 12, lineHeight: 1.7, margin: 0 }}>{anomaly.cause}</p>
      </div>

      {/* Action Button */}
      <button style={{
        width: "100%", padding: "12px 0",
        background: "linear-gradient(90deg, #00eeff22, #00ff8722)",
        border: "1px solid #00eeff88",
        borderRadius: 6, color: "#00eeff",
        fontSize: 12, fontWeight: 700, letterSpacing: 2,
        cursor: "pointer", fontFamily: "'Courier New', monospace",
        transition: "all 0.2s",
      }}
        onMouseEnter={e => { e.target.style.background = "linear-gradient(90deg, #00eeff44, #00ff8744)"; e.target.style.boxShadow = "0 0 20px #00eeff44"; }}
        onMouseLeave={e => { e.target.style.background = "linear-gradient(90deg, #00eeff22, #00ff8722)"; e.target.style.boxShadow = "none"; }}
      >
        âš¡ {anomaly.action}
      </button>
    </div>
  );
}

// â”€â”€ HORMOZI VALUE METER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function HormoziMeter({ patient }) {
  const totalDays = Math.max(Number(patient.totalDays) || 0, 1);
  const day = Math.max(Number(patient.day) || 0, 0);
  const progress = Math.min(day / totalDays, 1);
  const engagement = Math.max(Math.min(Number(patient.engagement) || 0, 1), 0);
  const daysLeft = Math.max(totalDays - day, 0);
  const td = daysLeft / totalDays;
  const eff = 1 - engagement;
  const denominator = (td + 0.2) * (eff + 0.2);
  const raw = denominator > 0 ? (progress * engagement) / denominator : 0;
  const safeRaw = Number.isFinite(raw) && raw > 0 ? raw : 0;
  const score = Math.min(Math.sqrt(safeRaw) * 25, 100);
  const label = score >= 70 ? "Alta" : score >= 40 ? "MÃ©dia" : "Baixa";
  const tc = score >= 70 ? "#3b82f6" : score >= 40 ? "#ffd60a" : "#ff3a3a";
  const factors = [
    { l: "RESULTADO", v: Math.round(progress * 100) },
    { l: "PROBABILIDADE", v: Math.round(engagement * 100) },
    { l: "TEMPO", v: Math.round((1 - td) * 100) },
    { l: "ESFORÃ‡O", v: Math.round(engagement * 100) },
  ];
  return (
    <div style={{ marginBottom: 24, background: "#00060f", border: "1px solid #0088cc22", borderRadius: 8, padding: "14px 16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ color: "#0088cc", fontSize: 9, letterSpacing: 3, textTransform: "uppercase" }}>TermÃ´metro de Valor Â· Hormozi</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: tc, fontSize: 14, fontWeight: 900, fontFamily: "'Courier New', monospace" }}>{score.toFixed(0)}</span>
          <span style={{ color: "#446688", fontSize: 9, letterSpacing: 1 }}>{label}</span>
        </div>
      </div>
      <div style={{ position: "relative", height: 8, borderRadius: 4, background: "linear-gradient(90deg, #ff3a3a 0%, #ffd60a 35%, #8b5cf6 65%, #00eeff 100%)", marginBottom: 10 }}>
        <div style={{ position: "absolute", left: `${score}%`, top: "50%", transform: "translate(-50%, -50%)", width: 14, height: 14, borderRadius: "50%", background: "#e0f4ff", boxShadow: `0 0 0 2px ${tc}, 0 0 12px ${tc}66`, transition: "left .6s ease" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        {factors.map((f) => (
          <div key={f.l} style={{ textAlign: "center" }}>
            <div style={{ color: "#446688", fontSize: 8, letterSpacing: 1, marginBottom: 2 }}>{f.l}</div>
            <div style={{ color: "#8ab0cc", fontSize: 10, fontWeight: 700, fontFamily: "'Courier New', monospace" }}>{f.v}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Detailed student panel
function PatientDetail({ patient, loading = false, error = null, onRetry, hasSelection = false }) {
  if (!hasSelection) {
    return (
      <ResourceState
        title="SELECAO PENDENTE"
        message="Selecione um aluno para ver os detalhes da mentoria."
      />
    );
  }

  if (loading && !patient) {
    return <ResourceState title="CARREGANDO DETALHES" message="Buscando dados mais recentes do aluno." />;
  }

  if (error && !patient) {
    return (
      <ResourceState
        title="FALHA AO CARREGAR DETALHE"
        message={error}
        actionLabel="Tentar novamente"
        onAction={onRetry}
      />
    );
  }

  if (!patient) {
    return (
      <ResourceState
        title="DETALHE INDISPONIVEL"
        message="Nao foi possivel obter o detalhe do aluno selecionado."
        actionLabel="Recarregar"
        onAction={onRetry}
      />
    );
  }

  const delta = getBioAgeDelta(patient);
  const progress = getProgress(patient);
  const totalWeeks = Math.max((Number(patient.totalDays) || 0) / 7, 1);

  return (
    <div style={{ padding: "24px 28px", overflowY: "auto", height: "100%" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <h2 style={{ color: "#e0f4ff", fontSize: 20, margin: 0, fontFamily: "'Courier New', monospace", letterSpacing: 2 }}>{patient.name}</h2>
          <div style={{ color: "#446688", fontSize: 11, letterSpacing: 1, marginTop: 4 }}>{patient.programName}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: "#00ff87", fontSize: 32, fontWeight: 900, fontFamily: "'Courier New', monospace", lineHeight: 1 }}>{(patient.hormoziScore || 0).toFixed(0)}</div>
          <div style={{ color: "#446688", fontSize: 10 }}>SCORE HORMOZI</div>
          <div style={{ color: "#00ff87", fontSize: 13, fontWeight: 700, marginTop: 4 }}>âš¡ {delta} engajamento</div>
        </div>
      </div>

      {loading && (
        <div style={{ color: "#446688", fontSize: 10, marginBottom: 12, letterSpacing: 1 }}>
          Atualizando detalhe do aluno...
        </div>
      )}

      {error && (
        <div style={{ marginBottom: 16, background: "#1a0a0a", border: "1px solid #ff3a3a55", borderRadius: 6, padding: "10px 12px" }}>
          <div style={{ color: "#ffb0b0", fontSize: 10, marginBottom: 8 }}>{error}</div>
          {onRetry && (
            <button
              onClick={onRetry}
              style={{
                padding: "6px 10px",
                border: "1px solid #ff3a3a88",
                background: "transparent",
                borderRadius: 4,
                color: "#ff8080",
                fontSize: 10,
                letterSpacing: 1,
                cursor: "pointer",
                fontFamily: "'Courier New', monospace",
              }}
            >
              Recarregar detalhe
            </button>
          )}
        </div>
      )}

      {/* Progress ring + key stats */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24 }}>
        <MiniStat label="DIA DO CICLO" value={`${patient.day}/${patient.totalDays}`} color="#00eeff" />
        <MiniStat label="PROGRESSO" value={`${progress}%`} color="#ffd60a" />
        <MiniStat label="RISCO" value={getRisk(patient).toUpperCase()} color={statusColor[getRisk(patient)].dot} />
      </div>

      {/* Performance indicators grid */}
      <div style={{ marginBottom: 24 }}>
        <SectionTitle>INDICADORES DE EVOLUCAO · DELTA vs BASELINE</SectionTitle>
        {patient.metricValues?.length > 0 ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {patient.metricValues.map((mv) => {
              const curr = parseFloat(mv.valueCurrent || '0');
              const base = parseFloat(mv.valueBaseline || '0');
              const pct = base !== 0 ? ((curr - base) / base * 100).toFixed(1) : '0.0';
              const improved = mv.improvingTrend ?? (curr > base);
              return (
                <div key={mv.id} style={{ background: "#00060f", borderRadius: 6, padding: "10px 14px", border: `1px solid ${improved ? "#00ff8722" : "#ff3a3a22"}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ color: "#8ab0cc", fontSize: 10, letterSpacing: 1 }}>{mv.metricLabel}</span>
                    <span style={{ color: improved ? "#00ff87" : "#ff3a3a", fontSize: 10, fontWeight: 700 }}>
                      {parseFloat(pct) > 0 ? "â†‘" : "â†“"}{Math.abs(parseFloat(pct))}%
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: 4 }}>
                    <span style={{ color: "#e0f4ff", fontSize: 16, fontWeight: 700, fontFamily: "'Courier New', monospace" }}>
                      {curr.toFixed(1)}
                    </span>
                    <span style={{ color: "#334455", fontSize: 10 }}>{base.toFixed(1)} â†’ {curr.toFixed(1)} {mv.unit || ''}</span>
                  </div>
                  {mv.optimal && <div style={{ color: "#334455", fontSize: 9, letterSpacing: 1 }}>IDEAL: {mv.optimal}</div>}
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ color: "#334455", fontSize: 11, letterSpacing: 1, textAlign: "center", padding: "16px 0" }}>Sem indicadores registrados</div>
        )}
      </div>

      {/* Checkpoints timeline */}
      <div style={{ marginBottom: 24 }}>
        <SectionTitle>CHECKPOINTS DA JORNADA</SectionTitle>
        {patient.checkpoints?.length > 0 ? (
          patient.checkpoints.map((cp, i) => {
            const cpColor = cp.status === 'red' ? '#ff3a3a' : cp.status === 'yellow' ? '#ffd60a' : '#00ff87';
            return (
              <div key={cp.id} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ color: "#8ab0cc", fontSize: 10, letterSpacing: 1 }}>{cp.label || `SEMANA ${cp.week}`}</span>
                  <span style={{ color: cpColor, fontSize: 10, fontWeight: 700, fontFamily: "'Courier New', monospace" }}>{cp.status.toUpperCase()}</span>
                </div>
                <div style={{ height: 3, background: "#0a1a2a", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${Math.min((cp.week / totalWeeks) * 100, 100)}%`, background: cpColor, borderRadius: 2 }} />
                </div>
              </div>
            );
          })
        ) : (
          <div style={{ color: "#334455", fontSize: 11, letterSpacing: 1, textAlign: "center", padding: "16px 0" }}>
            Sem checkpoints registrados. Timeline de anomalias indisponivel no contrato atual.
          </div>
        )}
      </div>

      <HormoziMeter patient={patient} />

      {/* D-45 Renewal alert */}
      {(patient.daysLeft || 0) <= 45 && (
        <div style={{
          background: "linear-gradient(135deg, #1a1000, #0a0800)",
          border: "1px solid #ffd60a44",
          borderRadius: 8, padding: "16px 18px",
        }}>
          <div style={{ color: "#ffd60a", fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 8 }}>
            ðŸ”„ GATILHO D-45 Â· RENOVAÃ‡ÃƒO ANTECIPADA
          </div>
          <p style={{ color: "#8a7a44", fontSize: 11, lineHeight: 1.7, margin: "0 0 14px" }}>
            Resultados atuais justificam apresentaÃ§Ã£o do Ciclo 2.{" "}
            {patient.name} tem {delta} de engajamento com o programa.
            Argumento de renovaÃ§Ã£o: consolidar ganhos e maximizar ROI do ciclo atual.
          </p>
          <button style={{
            padding: "8px 16px",
            background: "linear-gradient(90deg, #ffd60a22, #ff990022)",
            border: "1px solid #ffd60a66",
            borderRadius: 5, color: "#ffd60a",
            fontSize: 11, fontWeight: 700, letterSpacing: 2,
            cursor: "pointer", fontFamily: "'Courier New', monospace",
          }}>
            âš¡ GERAR PROPOSTA CICLO 2
          </button>
        </div>
      )}

      {/* Value gap alert */}
      {patient.urgency === 'watch' && (
        <div style={{
          marginTop: 12,
          background: "linear-gradient(135deg, #1a0800, #0a0500)",
          border: "1px solid #ff6b3544",
          borderRadius: 8, padding: "16px 18px",
        }}>
          <div style={{ color: "#ff6b35", fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 8 }}>
            âš  ALERTA: TANGIBILIZAR O INVISÃVEL
          </div>
          <p style={{ color: "#8a5a44", fontSize: 11, lineHeight: 1.7, margin: "0 0 14px" }}>
            Nenhum entregÃ¡vel de alto valor nos Ãºltimos 21 dias.
            Recomendar: relatÃ³rio de progresso visual + revisÃ£o de metas + sessÃ£o estratÃ©gica de mentoria.
          </p>
          <button style={{
            padding: "8px 16px",
            background: "linear-gradient(90deg, #ff6b3522, #ff3a0022)",
            border: "1px solid #ff6b3566",
            borderRadius: 5, color: "#ff6b35",
            fontSize: 11, fontWeight: 700, letterSpacing: 2,
            cursor: "pointer", fontFamily: "'Courier New', monospace",
          }}>
            ðŸ“Š ACIONAR PROTOCOLO DE VALOR
          </button>
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value, color }) {
  return (
    <div style={{ background: "#00060f", borderRadius: 6, padding: "10px 14px", border: "1px solid #0ff1" }}>
      <div style={{ color: "#446688", fontSize: 9, letterSpacing: 2, marginBottom: 4 }}>{label}</div>
      <div style={{ color, fontSize: 16, fontWeight: 900, fontFamily: "'Courier New', monospace" }}>{value}</div>
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{ color: "#0088cc", fontSize: 9, letterSpacing: 3, marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 1, background: "linear-gradient(90deg, #0088cc44, transparent)" }} />
      {children}
      <div style={{ flex: 1, height: 1, background: "linear-gradient(90deg, transparent, #0088cc44)" }} />
    </div>
  );
}

function ResourceState({ title, message, actionLabel, onAction }) {
  return (
    <div
      style={{
        padding: "30px 28px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 12,
        minHeight: 180,
      }}
    >
      <div style={{ color: "#00eeff", fontSize: 11, letterSpacing: 2, fontWeight: 700 }}>{title}</div>
      <div style={{ color: "#446688", fontSize: 11, textAlign: "center", lineHeight: 1.6 }}>{message}</div>
      {onAction && (
        <button
          onClick={onAction}
          style={{
            padding: "8px 14px",
            border: "1px solid #00eeff66",
            background: "linear-gradient(90deg, #00eeff22, #00ff8722)",
            borderRadius: 6,
            color: "#00eeff",
            fontSize: 10,
            letterSpacing: 1.5,
            fontWeight: 700,
            cursor: "pointer",
            fontFamily: "'Courier New', monospace",
          }}
        >
          {actionLabel || "Tentar novamente"}
        </button>
      )}
    </div>
  );
}

// Overlay backdrop
function Backdrop({ onClick }) {
  return <div onClick={onClick} style={{ position: "fixed", inset: 0, background: "#000a", zIndex: 999 }} />;
}

// â”€â”€ MAIN APP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function App() {
  const {
    data: studentList,
    loading: listLoading,
    error: listError,
    refresh: refreshList,
  } = useStudents();
  const [selectedId, setSelectedId] = useState(null);
  const {
    data: detail,
    loading: detailLoading,
    error: detailError,
    refresh: refreshDetail,
  } = useStudentDetail(selectedId);
  const [anomaly, setAnomaly] = useState(null);
  const [anomalyStyle, setAnomalyStyle] = useState(null);

  useEffect(() => {
    setSelectedId((prevId) => resolveSelectedStudentId(studentList, prevId));
  }, [studentList]);

  useEffect(() => {
    setAnomaly(null);
    setAnomalyStyle(null);
  }, [selectedId]);

  const students = studentList ?? [];
  const kpis = deriveCommandCenterKpis(students);
  const detailForSelected =
    detail && String(detail.id) === String(selectedId) ? detail : null;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;700;900&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #000811; overflow: hidden; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
        @keyframes anomalyPulse {
          0%,100% { box-shadow: 0 0 6px currentColor; transform: translate(-50%,-50%) scale(1); }
          50% { box-shadow: 0 0 16px currentColor, 0 0 30px currentColor44; transform: translate(-50%,-50%) scale(1.25); }
        }
        @keyframes cardIn {
          from { opacity:0; transform: translate(-50%,-50%) scale(0.94); }
          to { opacity:1; transform: translate(-50%,-50%) scale(1); }
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #000811; }
        ::-webkit-scrollbar-thumb { background: #0088cc44; border-radius: 2px; }
      `}</style>

      <Scanline />

      <div style={{
        display: "flex", flexDirection: "column",
        height: "100vh", background: "#000811",
        fontFamily: "'Share Tech Mono', 'Courier New', monospace",
        color: "#e0f4ff"
      }}>
        <TopBar kpis={kpis} />

        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Main Timeline Column */}
          <div style={{ flex: 1, overflowY: "auto", borderRight: "1px solid #0ff1" }}>
            {/* Column Headers */}
            <div style={{
              display: "grid", gridTemplateColumns: "220px 1fr 180px",
              padding: "10px 28px", borderBottom: "1px solid #0ff1",
              background: "#00060f"
            }}>
              <span style={{ color: "#0088cc", fontSize: 9, letterSpacing: 3 }}>ALUNO · STATUS</span>
              <span style={{ color: "#0088cc", fontSize: 9, letterSpacing: 3, paddingLeft: 24 }}>
                JORNADA DO ALUNO - PROGRESSO DO CICLO
              </span>
              <span style={{ color: "#0088cc", fontSize: 9, letterSpacing: 3, textAlign: "right" }}>ENGAJ. · PROGRESSO</span>
            </div>

            {listLoading && students.length > 0 && (
              <div style={{ color: "#446688", fontSize: 10, letterSpacing: 1, padding: "8px 28px", borderBottom: "1px solid #0ff1" }}>
                Atualizando lista de alunos...
              </div>
            )}

            {listLoading && students.length === 0 && (
              <ResourceState
                title="CARREGANDO LISTA"
                message="Buscando alunos do Centro de Comando."
              />
            )}

            {!listLoading && listError && (
              <ResourceState
                title="FALHA AO CARREGAR LISTA"
                message={listError}
                actionLabel="Atualizar lista"
                onAction={refreshList}
              />
            )}

            {!listLoading && !listError && students.length === 0 && (
              <ResourceState
                title="SEM ALUNOS"
                message="Nao existem alunos para exibir neste momento."
                actionLabel="Recarregar"
                onAction={refreshList}
              />
            )}

            {!listError && students.map((p) => (
              <PatientRow
                key={p.id}
                patient={p}
                selected={selectedId === p.id}
                onClick={() => setSelectedId(p.id)}
                onAnomalyClick={(a, s) => {
                  setAnomaly(a);
                  setAnomalyStyle(s);
                }}
              />
            ))}

            {students.length > 0 && (
              <div style={{ padding: "20px 28px", borderTop: "1px solid #0ff1", display: "flex", gap: 24 }}>
                {[["green", "Indicadores dentro do alvo"], ["yellow", "Desvio monitorado"], ["red", "Acao de recuperacao urgente"], ["#00eeff", "Posicao atual"]].map(([c, l]) => (
                  <div key={c} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: statusColor[c]?.dot || c, boxShadow: `0 0 6px ${statusColor[c]?.dot || c}` }} />
                    <span style={{ color: "#446688", fontSize: 10, letterSpacing: 1 }}>{l}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Detail Panel */}
          <div style={{ width: 380, overflowY: "auto", background: "linear-gradient(180deg, #000811 0%, #000a14 100%)" }}>
            <PatientDetail
              patient={detailForSelected}
              loading={detailLoading}
              error={detailError}
              onRetry={refreshDetail}
              hasSelection={Boolean(selectedId)}
            />
          </div>
        </div>
      </div>

      {/* Anomaly Insight Card */}
      {anomaly && (
        <>
          <Backdrop onClick={() => setAnomaly(null)} />
          <InsightCard anomaly={anomaly} style={anomalyStyle} onClose={() => setAnomaly(null)} />
        </>
      )}
    </>
  );
}

