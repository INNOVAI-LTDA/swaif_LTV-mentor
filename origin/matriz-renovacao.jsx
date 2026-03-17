import { useState, useEffect, useRef } from "react";
import { useRenewalMatrix } from "./hooks/useRenewalMatrix";
import { formatCurrencyBRL, formatPercent01 } from "./lib/formatters.js";
import { matrixQuadrant, resolveMatrixKpis } from "./lib/matrixUtils.js";

// ─────────────────────────────────────────────────────────────────────────────
// DATA — SC-022: hardcoded PATIENTS removed, using useStudents() API hook
// ─────────────────────────────────────────────────────────────────────────────
const _REMOVED = [
  {
    id: 1, name: "Renata Souza", initials: "RS", age: 47,
    progress: 0.82, engagement: 0.88, daysLeft: 18, totalDays: 180,
    plan: "Longevidade Elite", ltv: 28400,
    bioAgeDelta: -8.8, risk: "low",
    renewalReason: "Testosterona em 72 ng/dL — ainda 32% abaixo do alvo ideal de 105 ng/dL. Protocolo de reposição hormonal bioidêntica incompleto.",
    suggestion: "Plano Pro — Hormônios + Biohacking",
    pillars: { progress: 82, engagement: 88 },
    markers: [
      { label: "Testosterona", value: "72 ng/dL", target: "105 ng/dL", pct: 69, improving: true },
      { label: "PCR-us", value: "1.1 mg/L", target: "< 0.8 mg/L", pct: 78, improving: true },
      { label: "HRV", value: "61 ms", target: "75+ ms", pct: 81, improving: true },
    ],
    urgency: "critical",
  },
  {
    id: 2, name: "Carlos Mendes", initials: "CM", age: 54,
    progress: 0.55, engagement: 0.79, daysLeft: 72, totalDays: 180,
    plan: "Performance & Hormônios", ltv: 19800,
    bioAgeDelta: -5.3, risk: "medium",
    renewalReason: "Resistência insulínica ainda presente — Insulina em 9.4 µU/mL, meta < 7. Protocolo metabólico exige continuidade de pelo menos 90 dias.",
    suggestion: "Plano Metabólico Avançado",
    pillars: { progress: 55, engagement: 79 },
    markers: [
      { label: "Insulina", value: "9.4 µU/mL", target: "< 7 µU/mL", pct: 52, improving: true },
      { label: "Testosterona", value: "310 ng/dL", target: "500+ ng/dL", pct: 62, improving: true },
      { label: "Cortisol", value: "19 µg/dL", target: "< 18 µg/dL", pct: 58, improving: true },
    ],
    urgency: "watch",
  },
  {
    id: 3, name: "Beatriz Alves", initials: "BA", age: 39,
    progress: 0.91, engagement: 0.94, daysLeft: 12, totalDays: 180,
    plan: "Longevidade Premium", ltv: 34600,
    bioAgeDelta: -7.7, risk: "low",
    renewalReason: "Resultados excepcionais em todos os pilares. Candidata ideal para protocolo de Longevidade Extrema com peptídeos e NAD+ IV.",
    suggestion: "Longevidade Extrema — Biohacking Elite",
    pillars: { progress: 91, engagement: 94 },
    markers: [
      { label: "PCR-us", value: "0.4 mg/L", target: "< 0.5 mg/L", pct: 96, improving: true },
      { label: "HRV", value: "82 ms", target: "75+ ms", pct: 100, improving: true },
      { label: "Vitamina D", value: "74 ng/mL", target: "60+ ng/mL", pct: 98, improving: true },
    ],
    urgency: "critical",
  },
  {
    id: 4, name: "Diego Ferreira", initials: "DF", age: 61,
    progress: 0.38, engagement: 0.41, daysLeft: 95, totalDays: 180,
    plan: "Anti-Aging Básico", ltv: 9200,
    bioAgeDelta: -1.8, risk: "high",
    renewalReason: "Baixa adesao ao plano de execucao. Indicadores com melhora minima. Requer acao de recuperacao de engajamento.",
    suggestion: "Revisão de Protocolo + Sessão de Resultados",
    pillars: { progress: 38, engagement: 41 },
    markers: [
      { label: "Insulina", value: "18.6 µU/mL", target: "< 7 µU/mL", pct: 22, improving: false },
      { label: "PCR-us", value: "4.9 mg/L", target: "< 0.8 mg/L", pct: 16, improving: false },
      { label: "HRV", value: "24 ms", target: "50+ ms", pct: 28, improving: false },
    ],
    urgency: "rescue",
  },
  {
    id: 5, name: "Fernanda Costa", initials: "FC", age: 44,
    progress: 0.73, engagement: 0.52, daysLeft: 38, totalDays: 180,
    plan: "Hormônios & Energia", ltv: 15600,
    bioAgeDelta: -4.1, risk: "medium",
    renewalReason: "Progresso de transformacao solido, mas o engajamento digital caiu nos ultimos 21 dias. Tangibilizar resultados para reforcar percepcao de valor.",
    suggestion: "Consulta de Resultados + Plano Energia Pro",
    pillars: { progress: 73, engagement: 52 },
    markers: [
      { label: "Cortisol", value: "15 µg/dL", target: "< 15 µg/dL", pct: 74, improving: true },
      { label: "Testosterona", value: "88 ng/dL", target: "105+ ng/dL", pct: 69, improving: true },
      { label: "Vitamina D", value: "48 ng/mL", target: "60+ ng/mL", pct: 66, improving: true },
    ],
    urgency: "watch",
  },
  {
    id: 6, name: "Gustavo Lima", initials: "GL", age: 52,
    progress: 0.67, engagement: 0.71, daysLeft: 55, totalDays: 180,
    plan: "Performance Executiva", ltv: 22100,
    bioAgeDelta: -6.2, risk: "low",
    renewalReason: "HRV em recuperação consistente. Faltam 55 dias — momento estratégico para apresentar Ciclo 2 com foco em Mitocôndria e Sono.",
    suggestion: "Plano Executivo Avançado — Sono + Mitocôndria",
    pillars: { progress: 67, engagement: 71 },
    markers: [
      { label: "HRV", value: "54 ms", target: "70+ ms", pct: 72, improving: true },
      { label: "Cortisol noturno", value: "8 µg/dL", target: "< 6 µg/dL", pct: 68, improving: true },
      { label: "Glicemia", value: "89 mg/dL", target: "< 85 mg/dL", pct: 75, improving: true },
    ],
    urgency: "normal",
  },
];

const QUADRANT_META = {
  topRight: { label: "Foco em Renovação", sublabel: "Alto resultado · Alto engajamento", bg: "rgba(16,185,129,0.04)", border: "rgba(16,185,129,0.15)" },
  topLeft: { label: "Resgatar Valor", sublabel: "Baixo resultado · Alto engajamento", bg: "rgba(245,158,11,0.04)", border: "rgba(245,158,11,0.15)" },
  bottomRight: { label: "Ajustar Protocolo", sublabel: "Alto resultado · Baixo engajamento", bg: "rgba(99,102,241,0.04)", border: "rgba(99,102,241,0.15)" },
  bottomLeft: { label: "Acao de Recuperacao Urgente", sublabel: "Baixo resultado · Baixo engajamento", bg: "rgba(239,68,68,0.04)", border: "rgba(239,68,68,0.15)" },
};

const URGENCY_CFG = {
  critical: { color: "#10b981", glow: "0 0 0 3px rgba(16,185,129,.25), 0 0 20px rgba(16,185,129,.35)", ring: "#10b981" },
  watch: { color: "#f59e0b", glow: "0 0 0 2px rgba(245,158,11,.2),  0 0 12px rgba(245,158,11,.2)", ring: "#f59e0b" },
  rescue: { color: "#ef4444", glow: "0 0 0 2px rgba(239,68,68,.25),  0 0 14px rgba(239,68,68,.3)", ring: "#ef4444" },
  normal: { color: "#6366f1", glow: "0 0 0 1px rgba(99,102,241,.2),  0 0 8px  rgba(99,102,241,.1)", ring: "#6366f1" },
};

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────
function quadrant(p) {
  return matrixQuadrant(p);
}

function fmtLTV(v) {
  return formatCurrencyBRL(v);
}

// ─────────────────────────────────────────────────────────────────────────────
// SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

function TopMetric({ label, value, sub, accent }) {
  return (
    <div style={{
      background: "linear-gradient(135deg,#0f172a,#0c1424)",
      border: "1px solid rgba(255,255,255,.06)",
      borderRadius: 10, padding: "16px 20px",
    }}>
      <div style={{ fontSize: 10, letterSpacing: 3, color: "#475569", textTransform: "uppercase", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700, color: accent || "#f1f5f9", fontFamily: "'DM Mono', monospace", lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "#475569", marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function QuadrantLabel({ qKey }) {
  const meta = QUADRANT_META[qKey];
  return (
    <div style={{ position: "absolute", ...quadrantLabelPos(qKey), pointerEvents: "none", zIndex: 1 }}>
      <div style={{ fontSize: 9, letterSpacing: 2, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>{meta.label}</div>
      <div style={{ fontSize: 8, color: "#1e293b", marginTop: 2, letterSpacing: 0.5 }}>{meta.sublabel}</div>
    </div>
  );
}

function quadrantLabelPos(key) {
  switch (key) {
    case "topRight": return { top: 12, right: 16, textAlign: "right" };
    case "topLeft": return { top: 12, left: 16 };
    case "bottomRight": return { bottom: 12, right: 16, textAlign: "right" };
    case "bottomLeft": return { bottom: 12, left: 16 };
  }
}

function PatientBubble({ patient, onClick, selected }) {
  const [hovered, setHovered] = useState(false);
  const urg = URGENCY_CFG[patient.urgency] || URGENCY_CFG.normal;
  const isHighlight = patient.daysLeft <= 45 && quadrant(patient) === "topRight";
  const active = hovered || selected;

  // pulse for critical renewals
  const pulseAnim = isHighlight ? "bubblePulse 2.4s ease-in-out infinite" : "none";

  return (
    <div
      onClick={() => onClick(patient)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: "absolute",
        left: `${patient.progress * 100}%`,
        bottom: `${patient.engagement * 100}%`,
        transform: "translate(-50%, 50%)",
        zIndex: selected ? 20 : hovered ? 15 : 10,
        cursor: "pointer",
        transition: "transform 0.2s, z-index 0s",
      }}
    >
      {/* Outer pulse ring (only highlight bubbles) */}
      {isHighlight && (
        <div style={{
          position: "absolute",
          inset: -8,
          borderRadius: "50%",
          border: `1px solid ${urg.color}`,
          animation: pulseAnim,
          opacity: 0.6,
          pointerEvents: "none"
        }} />
      )}

      {/* Bubble */}
      <div style={{
        width: active ? 52 : 44,
        height: active ? 52 : 44,
        borderRadius: "50%",
        background: `radial-gradient(circle at 35% 35%, ${urg.color}55, ${urg.color}22)`,
        border: `2px solid ${urg.color}`,
        boxShadow: active ? urg.glow : `0 0 0 1px ${urg.color}55`,
        display: "flex", alignItems: "center", justifyContent: "center",
        transition: "all 0.18s ease",
        position: "relative",
      }}>
        <span style={{
          fontSize: active ? 11 : 10,
          fontWeight: 700,
          color: "#f1f5f9",
          letterSpacing: 0.5,
          fontFamily: "'DM Mono', monospace",
        }}>
          {patient.initials}
        </span>

        {/* D-45 badge */}
        {patient.daysLeft <= 45 && (
          <div style={{
            position: "absolute",
            top: -8, right: -8,
            background: patient.daysLeft <= 20 ? "#ef4444" : "#f59e0b",
            color: "#fff",
            fontSize: 8,
            fontWeight: 800,
            borderRadius: 10,
            padding: "2px 5px",
            letterSpacing: 0.5,
            boxShadow: "0 2px 8px rgba(0,0,0,.4)",
            fontFamily: "'DM Mono', monospace",
            whiteSpace: "nowrap",
          }}>
            D-{patient.daysLeft}
          </div>
        )}
      </div>

      {/* Tooltip on hover */}
      {hovered && !selected && (
        <div style={{
          position: "absolute",
          bottom: "calc(100% + 10px)",
          left: "50%",
          transform: "translateX(-50%)",
          background: "#0f172a",
          border: "1px solid rgba(255,255,255,.1)",
          borderRadius: 6,
          padding: "8px 12px",
          whiteSpace: "nowrap",
          pointerEvents: "none",
          boxShadow: "0 8px 32px rgba(0,0,0,.6)",
          zIndex: 100,
          animation: "fadeUp 0.15s ease-out",
        }}>
          <div style={{ color: "#f1f5f9", fontSize: 12, fontWeight: 600 }}>{patient.name}</div>
          <div style={{ color: "#64748b", fontSize: 10, marginTop: 2 }}>{patient.programName}</div>
          <div style={{ color: "#10b981", fontSize: 10, marginTop: 2 }}>{Math.round((patient.engagement || 0) * 100)}% eng · LTV {fmtLTV(patient.ltv)}</div>
        </div>
      )}
    </div>
  );
}

function MarkerBar({ marker }) {
  const color = marker.pct >= 80 ? "#10b981" : marker.pct >= 55 ? "#f59e0b" : "#ef4444";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ color: "#94a3b8", fontSize: 10, letterSpacing: 0.5 }}>{marker.label}</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ color: color, fontSize: 10, fontFamily: "'DM Mono', monospace", fontWeight: 700 }}>{marker.value}</span>
          <span style={{ color: "#334155", fontSize: 9 }}>→ {marker.target}</span>
        </div>
      </div>
      <div style={{ height: 3, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${marker.pct}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          borderRadius: 2, transition: "width 0.6s ease"
        }} />
      </div>
    </div>
  );
}

function PatientDrawer({ patient, onClose }) {
  const urg = URGENCY_CFG[patient.urgency] || URGENCY_CFG.normal;
  const q = quadrant(patient);
  const [proposed, setProposed] = useState(false);

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      zIndex: 500,
      display: "flex",
      alignItems: "flex-end",
      justifyContent: "flex-end",
      pointerEvents: "none",
    }}>
      {/* Scrim */}
      <div
        onClick={onClose}
        style={{
          position: "absolute", inset: 0,
          background: "rgba(2,6,23,.7)",
          backdropFilter: "blur(2px)",
          pointerEvents: "all",
          animation: "fadeIn .2s ease",
        }}
      />

      {/* Panel */}
      <div style={{
        position: "relative",
        width: 440,
        height: "100vh",
        background: "linear-gradient(180deg, #0c1424 0%, #090f1a 100%)",
        borderLeft: "1px solid rgba(255,255,255,.07)",
        overflowY: "auto",
        pointerEvents: "all",
        animation: "slideInRight .25s cubic-bezier(.4,0,.2,1)",
        boxShadow: "-24px 0 80px rgba(0,0,0,.8)",
        display: "flex",
        flexDirection: "column",
      }}>
        {/* Close */}
        <button
          onClick={onClose}
          style={{
            position: "absolute", top: 20, right: 20,
            background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)",
            color: "#64748b", width: 32, height: 32, borderRadius: 8,
            cursor: "pointer", fontSize: 14, display: "flex", alignItems: "center", justifyContent: "center"
          }}
        >✕</button>

        <div style={{ padding: "28px 28px 0" }}>
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
            <div style={{
              width: 48, height: 48, borderRadius: "50%",
              background: `radial-gradient(circle at 35% 35%, ${urg.color}55, ${urg.color}22)`,
              border: `2px solid ${urg.color}`,
              boxShadow: urg.glow,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13, fontWeight: 800, color: "#f1f5f9",
              fontFamily: "'DM Mono', monospace",
            }}>{patient.initials}</div>
            <div>
              <div style={{ color: "#f1f5f9", fontSize: 18, fontWeight: 700, letterSpacing: -0.3 }}>{patient.name}</div>
              <div style={{ color: "#475569", fontSize: 11, marginTop: 2 }}>{patient.programName}</div>
            </div>
          </div>

          {/* KPI strip */}
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 24,
          }}>
            {[
              { l: "Dias Restantes", v: patient.daysLeft + "d", c: patient.daysLeft <= 20 ? "#ef4444" : "#f59e0b" },
              { l: "Engajamento", v: Math.round((patient.engagement || 0) * 100) + "%", c: "#10b981" },
              { l: "LTV", v: fmtLTV(patient.ltv), c: "#6366f1" },
            ].map((k, i) => (
              <div key={i} style={{
                background: "#0f172a", border: "1px solid rgba(255,255,255,.05)",
                borderRadius: 8, padding: "10px 12px", textAlign: "center"
              }}>
                <div style={{ fontSize: 9, color: "#334155", letterSpacing: 2, textTransform: "uppercase", marginBottom: 4 }}>{k.l}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: k.c, fontFamily: "'DM Mono', monospace" }}>{k.v}</div>
              </div>
            ))}
          </div>

          {/* Divider */}
          <div style={{ height: 1, background: "linear-gradient(90deg, transparent, rgba(255,255,255,.07), transparent)", marginBottom: 22 }} />

          {/* Reason block */}
          <div style={{ marginBottom: 22 }}>
            <div style={{ fontSize: 9, letterSpacing: 3, color: "#334155", textTransform: "uppercase", marginBottom: 12 }}>
              Motivo para Renovação
            </div>
            <div style={{
              background: "rgba(16,185,129,.06)",
              border: "1px solid rgba(16,185,129,.2)",
              borderLeft: `3px solid ${urg.color}`,
              borderRadius: "0 8px 8px 0",
              padding: "14px 16px",
            }}>
              <p style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.75, margin: 0 }}>
                {patient.renewalReason}
              </p>
            </div>
          </div>

          {/* Markers */}
          <div style={{ marginBottom: 22 }}>
            <div style={{ fontSize: 9, letterSpacing: 3, color: "#334155", textTransform: "uppercase", marginBottom: 14 }}>
              Indicadores · Progresso Atual
            </div>
            {(patient.markers || []).map((m, i) => <MarkerBar key={i} marker={m} />)}
          </div>

          {/* Progress bars */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 9, letterSpacing: 3, color: "#334155", textTransform: "uppercase", marginBottom: 14 }}>
              Posição na Matriz
            </div>
            {[
              { label: "Progresso de Transformacao", val: patient.progress * 100, color: "#6366f1" },
              { label: "Engajamento", val: patient.engagement * 100, color: "#f59e0b" },
            ].map((b, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ color: "#64748b", fontSize: 10 }}>{b.label}</span>
                  <span style={{ color: b.color, fontSize: 10, fontFamily: "'DM Mono', monospace", fontWeight: 700 }}>{b.val.toFixed(0)}%</span>
                </div>
                <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${b.val}%`, background: b.color, borderRadius: 2 }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Suggestion + CTA — sticky bottom */}
        <div style={{ marginTop: "auto", padding: "0 28px 32px" }}>
          <div style={{
            background: "linear-gradient(135deg, rgba(99,102,241,.1), rgba(16,185,129,.08))",
            border: "1px solid rgba(99,102,241,.25)",
            borderRadius: 10, padding: "14px 16px", marginBottom: 16,
          }}>
            <div style={{ fontSize: 9, letterSpacing: 3, color: "#6366f1", textTransform: "uppercase", marginBottom: 6 }}>
              Sugestão de Plano
            </div>
            <div style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600 }}>{patient.suggestion}</div>
          </div>

          {!proposed ? (
            <button
              onClick={() => setProposed(true)}
              style={{
                width: "100%",
                padding: "15px 0",
                background: "linear-gradient(135deg, #6366f1, #4f46e5)",
                border: "none",
                borderRadius: 10,
                color: "#fff",
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: 1,
                cursor: "pointer",
                boxShadow: "0 4px 24px rgba(99,102,241,.45)",
                transition: "all .15s",
                fontFamily: "inherit",
              }}
              onMouseEnter={e => { e.target.style.transform = "translateY(-1px)"; e.target.style.boxShadow = "0 8px 32px rgba(99,102,241,.55)"; }}
              onMouseLeave={e => { e.target.style.transform = "translateY(0)"; e.target.style.boxShadow = "0 4px 24px rgba(99,102,241,.45)"; }}
            >
              ◆ Gerar Proposta Baseada em Dados
            </button>
          ) : (
            <div style={{
              padding: "16px",
              background: "rgba(16,185,129,.1)",
              border: "1px solid rgba(16,185,129,.3)",
              borderRadius: 10,
              textAlign: "center",
              animation: "fadeIn .3s ease"
            }}>
              <div style={{ color: "#10b981", fontSize: 13, fontWeight: 700, marginBottom: 4 }}>✓ Proposta gerada com sucesso</div>
              <div style={{ color: "#64748b", fontSize: 11 }}>Enviada para o painel do mentor · Ciclo 2 · {patient.suggestion}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MATRIX CHART
// ─────────────────────────────────────────────────────────────────────────────
function Matrix({ onSelectPatient, selectedId, patients = [] }) {
  const [size, setSize] = useState({ w: 600, h: 480 });
  const wrapRef = useRef(null);

  useEffect(() => {
    const obs = new ResizeObserver(entries => {
      for (const e of entries) {
        const { width } = e.contentRect;
        setSize({ w: width, h: Math.min(480, width * 0.75) });
      }
    });
    if (wrapRef.current) obs.observe(wrapRef.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={wrapRef} style={{ width: "100%", position: "relative" }}>
      <div style={{
        position: "relative",
        width: "100%",
        height: size.h,
        background: "linear-gradient(135deg, #070d1a 0%, #0a1120 100%)",
        borderRadius: 14,
        border: "1px solid rgba(255,255,255,.05)",
        overflow: "hidden",
      }}>
        {/* Grid lines */}
        <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
          {/* Center axes */}
          <line x1="50%" y1="0" x2="50%" y2="100%" stroke="rgba(255,255,255,.07)" strokeWidth={1} strokeDasharray="4 4" />
          <line x1="0" y1="50%" x2="100%" y2="50%" stroke="rgba(255,255,255,.07)" strokeWidth={1} strokeDasharray="4 4" />
          {/* Grid */}
          {[25, 75].map(p => (
            <g key={p}>
              <line x1={`${p}%`} y1="0" x2={`${p}%`} y2="100%" stroke="rgba(255,255,255,.03)" strokeWidth={1} />
              <line x1="0" y1={`${p}%`} x2="100%" y2={`${p}%`} stroke="rgba(255,255,255,.03)" strokeWidth={1} />
            </g>
          ))}
          {/* Axis ticks */}
          {[0, 25, 50, 75, 100].map(p => (
            <g key={p}>
              <text x={`${p}%`} y="98%" textAnchor="middle" fill="rgba(255,255,255,.15)" fontSize={9} fontFamily="DM Mono, monospace">{p}%</text>
              <text x="1.5%" y={`${100 - p}%`} dominantBaseline="middle" fill="rgba(255,255,255,.15)" fontSize={9} fontFamily="DM Mono, monospace">{p}%</text>
            </g>
          ))}
        </svg>

        {/* Quadrant backgrounds */}
        {[
          { left: "50%", top: "0", width: "50%", height: "50%", qKey: "topRight" },
          { left: "0", top: "0", width: "50%", height: "50%", qKey: "topLeft" },
          { left: "50%", top: "50%", width: "50%", height: "50%", qKey: "bottomRight" },
          { left: "0", top: "50%", width: "50%", height: "50%", qKey: "bottomLeft" },
        ].map(({ left, top, width, height, qKey }) => (
          <div key={qKey} style={{
            position: "absolute", left, top, width, height,
            background: QUADRANT_META[qKey].bg,
            borderTop: qKey.includes("bottom") ? `1px solid ${QUADRANT_META[qKey].border}` : "none",
            borderBottom: qKey.includes("top") ? `1px solid ${QUADRANT_META[qKey].border}` : "none",
            borderLeft: qKey.includes("Right") ? `1px solid ${QUADRANT_META[qKey].border}` : "none",
            borderRight: qKey.includes("Left") ? `1px solid ${QUADRANT_META[qKey].border}` : "none",
          }}>
            <QuadrantLabel qKey={qKey} />
          </div>
        ))}

        {/* Bubbles */}
        {patients.map(p => (
          <PatientBubble
            key={p.id}
            patient={p}
            selected={selectedId === p.id}
            onClick={onSelectPatient}
          />
        ))}

        {/* Axis labels */}
        <div style={{ position: "absolute", bottom: 6, left: "50%", transform: "translateX(-50%)", fontSize: 9, color: "#334155", letterSpacing: 3, textTransform: "uppercase" }}>
          Progresso de Transformacao →
        </div>
        <div style={{
          position: "absolute", left: 6, top: "50%",
          transform: "translateY(-50%) rotate(-90deg)",
          fontSize: 9, color: "#334155", letterSpacing: 3, textTransform: "uppercase",
          transformOrigin: "center",
        }}>
          ↑ Engajamento
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN APP
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [filter, setFilter] = useState("all");
  const { data: matrixData } = useRenewalMatrix(filter);
  const students = matrixData?.items ?? [];
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    setSelected((prev) => {
      if (!prev) return prev;
      const exists = students.some((item) => String(item.id) === String(prev.id));
      return exists ? prev : null;
    });
  }, [students]);

  const kpis = resolveMatrixKpis(matrixData?.kpis, students);
  const rescueCount = kpis.rescueCount;
  const avgEngagement = formatPercent01(kpis.avgEngagement, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  const filteredView = students;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Sora:wght@300;400;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #020817; color: #e2e8f0; font-family: 'Sora', sans-serif; min-height: 100vh; }

        @keyframes fadeIn       { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fadeUp       { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0); } }
        @keyframes bubblePulse  {
          0%, 100% { transform: scale(1); opacity: .6; }
          50%       { transform: scale(1.6); opacity: 0; }
        }
        @keyframes staggerIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #020817; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,.08); border-radius: 2px; }
      `}</style>

      <div style={{ minHeight: "100vh", padding: "28px 28px 40px", maxWidth: 1280, margin: "0 auto" }}>

        {/* ── HEADER ── */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "flex-end",
          marginBottom: 32, animation: "staggerIn .5s ease both"
        }}>
          <div>
            <div style={{ fontSize: 10, letterSpacing: 5, color: "#334155", textTransform: "uppercase", marginBottom: 8 }}>
              Cérebro JPE · Inteligência de Negócio
            </div>
            <h1 style={{ fontSize: 28, fontWeight: 800, color: "#f1f5f9", letterSpacing: -0.5, lineHeight: 1 }}>
              Matriz de Renovação Antecipada
            </h1>
            <p style={{ color: "#475569", fontSize: 13, marginTop: 6, fontWeight: 300 }}>
              Posicionamento de alunos por resultado de transformacao x engajamento · Foco em LTV e retencao
            </p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {[
              { key: "all", label: "Todos" },
              { key: "topRight", label: "Renovar" },
              { key: "critical", label: "D-45" },
              { key: "rescue", label: "Resgatar" },
            ].map(f => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                style={{
                  padding: "7px 16px",
                  background: filter === f.key ? "rgba(99,102,241,.2)" : "rgba(255,255,255,.03)",
                  border: `1px solid ${filter === f.key ? "rgba(99,102,241,.5)" : "rgba(255,255,255,.07)"}`,
                  borderRadius: 8, color: filter === f.key ? "#a5b4fc" : "#475569",
                  fontSize: 11, fontWeight: 600, cursor: "pointer", letterSpacing: 0.5,
                  transition: "all .15s", fontFamily: "'Sora', sans-serif",
                }}
              >{f.label}</button>
            ))}
          </div>
        </div>

        {/* ── TOP KPIs ── */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14,
          marginBottom: 28, animation: "staggerIn .5s .1s ease both"
        }}>
          <TopMetric label="Pipeline LTV Total" value={fmtLTV(kpis.totalLTV)} sub={students.length + " alunos ativos"} accent="#10b981" />
          <TopMetric label="Renovações Críticas D-45" value={kpis.criticalRenewals} sub="Prontos para proposta" accent="#f59e0b" />
          <TopMetric label="Alerta de Resgate" value={rescueCount} sub="Risco de churn" accent="#ef4444" />
          <TopMetric label="Eng. Médio" value={avgEngagement} sub="Engajamento médio da turma" accent="#6366f1" />
        </div>

        {/* ── MAIN GRID ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 20, alignItems: "start" }}>

          {/* Matrix */}
          <div style={{ animation: "staggerIn .6s .15s ease both" }}>
            <Matrix onSelectPatient={setSelected} selectedId={selected?.id} patients={filteredView} />

            {/* Legend */}
            <div style={{
              display: "flex", gap: 20, marginTop: 14, flexWrap: "wrap",
              paddingLeft: 2
            }}>
              {[
                { color: "#10b981", label: "Renovação Imediata (D-45 + quadrante top-right)" },
                { color: "#f59e0b", label: "Monitorar" },
                { color: "#ef4444", label: "Resgate Urgente" },
                { color: "#6366f1", label: "Em Progressão" },
              ].map((l, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                  <div style={{ width: 9, height: 9, borderRadius: "50%", background: l.color, boxShadow: `0 0 6px ${l.color}` }} />
                  <span style={{ color: "#334155", fontSize: 10, letterSpacing: 0.3 }}>{l.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Patient list */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10, animation: "staggerIn .6s .2s ease both" }}>
            <div style={{ fontSize: 9, letterSpacing: 3, color: "#334155", textTransform: "uppercase", marginBottom: 4 }}>
              Painel de Ação Rápida
            </div>
            {[...filteredView].sort((a, b) => a.daysLeft - b.daysLeft).map(p => {
              const urg = URGENCY_CFG[p.urgency] || URGENCY_CFG.normal;
              return (
                <div
                  key={p.id}
                  onClick={() => setSelected(p)}
                  style={{
                    background: selected?.id === p.id
                      ? "linear-gradient(135deg, rgba(99,102,241,.1), rgba(16,185,129,.06))"
                      : "rgba(255,255,255,.02)",
                    border: selected?.id === p.id
                      ? "1px solid rgba(99,102,241,.35)"
                      : "1px solid rgba(255,255,255,.05)",
                    borderRadius: 10, padding: "12px 14px",
                    cursor: "pointer", transition: "all .15s",
                    display: "grid", gridTemplateColumns: "auto 1fr auto",
                    gap: 12, alignItems: "center",
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(255,255,255,.1)"}
                  onMouseLeave={e => e.currentTarget.style.borderColor = selected?.id === p.id ? "rgba(99,102,241,.35)" : "rgba(255,255,255,.05)"}
                >
                  {/* Avatar */}
                  <div style={{
                    width: 36, height: 36, borderRadius: "50%",
                    background: `radial-gradient(circle at 35% 35%, ${urg.color}44, ${urg.color}11)`,
                    border: `1.5px solid ${urg.color}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, fontWeight: 800, color: "#f1f5f9", fontFamily: "'DM Mono', monospace",
                    flexShrink: 0,
                  }}>{p.initials}</div>

                  {/* Info */}
                  <div>
                    <div style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 600 }}>{p.name}</div>
                    <div style={{ color: "#334155", fontSize: 10, marginTop: 1 }}>{p.programName || p.plan}</div>
                  </div>

                  {/* Days badge */}
                  <div style={{ textAlign: "right" }}>
                    <div style={{
                      fontSize: 11, fontWeight: 800, color: p.daysLeft <= 20 ? "#ef4444" : p.daysLeft <= 45 ? "#f59e0b" : "#475569",
                      fontFamily: "'DM Mono', monospace"
                    }}>D-{p.daysLeft}</div>
                    <div style={{ fontSize: 9, color: "#1e293b", marginTop: 1 }}>{quadrant(p) === "topRight" ? "Renovar" : p.urgency === "rescue" ? "Resgatar" : "Monitorar"}</div>
                  </div>
                </div>
              );
            })}

            {/* Summary box */}
            <div style={{
              marginTop: 8,
              background: "rgba(16,185,129,.05)",
              border: "1px solid rgba(16,185,129,.15)",
              borderRadius: 10, padding: "14px 16px"
            }}>
              <div style={{ fontSize: 9, letterSpacing: 3, color: "#10b981", textTransform: "uppercase", marginBottom: 8 }}>
                Oportunidade de Receita
              </div>
              <div style={{ color: "#6ee7b7", fontSize: 22, fontWeight: 800, fontFamily: "'DM Mono', monospace", lineHeight: 1 }}>
                {fmtLTV(filteredView.filter(p => p.daysLeft <= 45).reduce((s, p) => s + parseFloat(String(p.ltv || 0)), 0))}
              </div>
              <div style={{ color: "#334155", fontSize: 10, marginTop: 4 }}>
                Em contratos com vencimento em 45 dias
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: 32, paddingTop: 20,
          borderTop: "1px solid rgba(255,255,255,.04)",
          display: "flex", justifyContent: "space-between",
          color: "#1e293b", fontSize: 10, letterSpacing: 1
        }}>
          <span>Metodo de Mentoria LTV · 7 Pilares do Metodo</span>
          <span>JPE · Jornada do Aluno Estruturada · Mentoria High Ticket</span>
        </div>
      </div>

      {/* Drawer */}
      {selected && <PatientDrawer patient={selected} onClose={() => setSelected(null)} />}
    </>
  );
}


