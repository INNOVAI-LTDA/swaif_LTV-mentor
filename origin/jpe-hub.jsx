import { useState, useEffect, useRef } from "react";
import { useClients } from './hooks/useClients';
import { useClientRadar } from './hooks/useClientRadar';
import { useRenewalMatrix } from "./hooks/useRenewalMatrix";
import CadastroModal from './CadastroModal';
import { useAuth } from './contexts/AuthContext';
import { simulateRadar, getRadarInsight } from "./lib/radarUtils.js";
import { formatCurrencyBRL, formatPercent01 } from "./lib/formatters.js";
import { matrixQuadrant, resolveMatrixKpis } from "./lib/matrixUtils.js";

// â”€â”€ DATA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// SC-006: All patient data is now loaded from the API (useClients, useClientRadar).
// No static patient arrays remain in this file.

const MODULES_META = [
  {
    id: "comando", label: "Centro de Comando", sub: "Gestao por Excecao",
    desc: "Monitore jornadas de transformacao em tempo real. Detecte desvios em indicadores e acione acoes de mentoria rapidamente.",
    tags: ["Cortisol", "HRV", "PCR-us", "Timeline 6M"], accent: "#00eeff", num: "01"
  },
  {
    id: "radar", label: "Radar de TransformaÃ§Ã£o", sub: "Eu de Ontem vs. Eu de Hoje",
    desc: "Visualize a evoluÃ§Ã£o dos 7 eixos de transformaÃ§Ã£o. Projete resultados futuros e converta dados em argumentos poderosos de renovaÃ§Ã£o.",
    tags: ["7 Eixos", "Radar Chart", "ProjeÃ§Ã£o Ciclo 2"], accent: "#d4af37", num: "02"
  },
  {
    id: "matriz", label: "Matriz de RenovaÃ§Ã£o", sub: "Inteligencia de Mentoria",
    desc: "Quadrante mÃ¡gico por resultado Ã— engajamento. Identifique oportunidades D-45 e gere propostas com um Ãºnico clique.",
    tags: ["Quadrante MÃ¡gico", "LTV", "D-45", "RetenÃ§Ã£o"], accent: "#a78bfa", num: "03"
  },
];

// â”€â”€ UTILS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const SC = {
  green: { dot: "#00ff87", glow: "0 0 8px #00ff87" },
  yellow: { dot: "#ffd60a", glow: "0 0 8px #ffd60a" },
  red: { dot: "#ff3a3a", glow: "0 0 12px #ff3a3a" },
};
const URG = {
  critical: { color: "#10b981", glow: "0 0 0 3px rgba(16,185,129,.25),0 0 20px rgba(16,185,129,.3)" },
  watch: { color: "#f59e0b", glow: "0 0 0 2px rgba(245,158,11,.2),0 0 12px rgba(245,158,11,.2)" },
  rescue: { color: "#ef4444", glow: "0 0 0 2px rgba(239,68,68,.25),0 0 14px rgba(239,68,68,.25)" },
  normal: { color: "#6366f1", glow: "0 0 0 1px rgba(99,102,241,.15)" },
};
const getRisk = p => p.segments.some(s => s.s === "red") ? "red" : p.segments.some(s => s.s === "yellow") ? "yellow" : "green";
const qKey = (p) => matrixQuadrant(p);
const polar = (ang, r, cx, cy) => { const rad = (ang - 90) * Math.PI / 180; return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }; };
const rPath = (vals, R, cx, cy, n) => vals.map((v, i) => { const p = polar((360 / n) * i, (v / 100) * R, cx, cy); return `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`; }).join(" ") + " Z";

// â”€â”€ GLOBAL STYLES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const GS = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,400&family=DM+Mono:wght@300;400;500&family=Sora:wght@300;400;600;700;800&display=swap');
    *{box-sizing:border-box;margin:0;padding:0}
    html,body{height:100%;background:#02060f;overflow:hidden}
    ::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:#02060f}::-webkit-scrollbar-thumb{background:rgba(255,255,255,.09);border-radius:2px}
    @keyframes fadeIn{from{opacity:0}to{opacity:1}}
    @keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
    @keyframes scaleIn{from{opacity:0;transform:scale(.93)}to{opacity:1;transform:scale(1)}}
    @keyframes slideR{from{transform:translateX(100%)}to{transform:translateX(0)}}
    @keyframes gPulse{0%,100%{opacity:.5}50%{opacity:1}}
    @keyframes rotateSlow{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
    @keyframes bPulse{0%,100%{transform:scale(1);opacity:.5}50%{transform:scale(1.7);opacity:0}}
    @keyframes shimmer{0%{background-position:200% center}100%{background-position:-200% center}}
    input[type=range]{-webkit-appearance:none;width:100%;height:2px;
      background:linear-gradient(90deg,#d4af37 var(--p,0%),#d4c88033 var(--p,0%));
      border-radius:2px;outline:none;cursor:pointer}
    input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;
      background:radial-gradient(circle at 35% 35%,#f0d060,#b8860b);
      box-shadow:0 2px 10px #d4af3766;border:2px solid #fff8e8;cursor:pointer}
  `}</style>
);

// â”€â”€ MODULE 1: CENTRO DE COMANDO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function InsightModal({ anomaly, color, onClose }) {
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,.75)", backdropFilter: "blur(4px)" }} />
      <div style={{
        position: "relative", width: 390, background: "linear-gradient(145deg,#000d1a,#001525)",
        border: "1px solid #00eeff33", borderRadius: 12, padding: 26,
        boxShadow: "0 0 40px #00eeff22,0 24px 80px #000c", animation: "scaleIn .2s ease", fontFamily: "'DM Mono',monospace"
      }}>
        <button onClick={onClose} style={{ position: "absolute", top: 12, right: 14, background: "none", border: "none", color: "#446688", fontSize: 18, cursor: "pointer" }}>âœ•</button>
        <div style={{ color: "#0088cc", fontSize: 8, letterSpacing: 3, marginBottom: 14 }}>INSIGHT CARD Â· PROTOCOLO DO ALUNO</div>
        <div style={{ background: "#00060f", borderRadius: 6, padding: "11px 14px", marginBottom: 12, border: `1px solid ${color}33` }}>
          <div style={{ color: "#446688", fontSize: 8, letterSpacing: 2, marginBottom: 4 }}>DADO ANÃ”MALO</div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "#e0f4ff", fontSize: 14, fontWeight: 700 }}>{anomaly.marker}</span>
            <div style={{ textAlign: "right" }}><div style={{ color, fontSize: 18, fontWeight: 900 }}>{anomaly.value}</div><div style={{ color: "#446688", fontSize: 8 }}>Ref: {anomaly.ref}</div></div>
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <div style={{ color: "#446688", fontSize: 8, letterSpacing: 2, marginBottom: 5 }}>HIPOTESE DE BLOQUEIO</div>
          <p style={{ color: "#8ab0cc", fontSize: 11, lineHeight: 1.75, margin: 0 }}>{anomaly.cause}</p>
        </div>
        <button style={{
          width: "100%", padding: "10px 0", background: "linear-gradient(90deg,#00eeff22,#00ff8722)",
          border: "1px solid #00eeff77", borderRadius: 6, color: "#00eeff", fontSize: 10, fontWeight: 700,
          letterSpacing: 2, cursor: "pointer", fontFamily: "'DM Mono',monospace"
        }}>
          âš¡ {anomaly.action}
        </button>
      </div>
    </div>
  );
}

function CommandoModule({ students = [] }) {
  const [sel, setSel] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [aColor, setAColor] = useState("#ff3a3a");
  const [time, setTime] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t); }, []);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", background: "#000811", fontFamily: "'DM Mono',monospace", overflow: "hidden" }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", height: 46,
        borderBottom: "1px solid #0ff2", background: "linear-gradient(90deg,#000a0f,#001a2f)", flexShrink: 0
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#00ff87", boxShadow: "0 0 10px #00ff87", animation: "gPulse 2s infinite" }} />
          <span style={{ color: "#00ff87", fontSize: 11, letterSpacing: 3, fontWeight: 700 }}>JORNADA DE TRANSFORMACAO · GESTAO POR EXCECAO</span>
        </div>
        <div style={{ display: "flex", gap: 18, alignItems: "center" }}>
          {[["ATIVOS", String(students.length), "#00ff87"], ["ALERTAS", String(students.filter(p => p.urgency === 'rescue').length), "#ff3a3a"], ["D-45", String(students.filter(p => p.daysLeft <= 45).length), "#ffd60a"]].map(([l, v, c]) => (
            <div key={l} style={{ textAlign: "center" }}>
              <div style={{ color: c, fontSize: 15, fontWeight: 900, lineHeight: 1 }}>{v}</div>
              <div style={{ color: "#446", fontSize: 7, letterSpacing: 2 }}>{l}</div>
            </div>
          ))}
          <div style={{ color: "#0088aa", fontSize: 9, letterSpacing: 1 }}>{time.toLocaleTimeString("pt-BR")}</div>
        </div>
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden", minHeight: 0 }}>
        <div style={{ flex: 1, overflowY: "auto", borderRight: "1px solid #0ff1" }}>
          <div style={{ display: "grid", gridTemplateColumns: "190px 1fr 150px", padding: "7px 16px", borderBottom: "1px solid #0ff1", background: "#00060f" }}>
            {["ALUNO", "JORNADA 6M â€” CLIQUE NOS PONTOS DE DESVIO", "SCORE EVOL"].map((h, i) => (
              <span key={i} style={{ color: "#0088cc", fontSize: 8, letterSpacing: 3, textAlign: i === 2 ? "right" : "left" }}>{h}</span>
            ))}
          </div>
          {students.map(p => {
            const risk = p.urgency === 'rescue' ? 'red' : (p.urgency === 'watch' || p.urgency === 'critical') ? 'yellow' : 'green';
            const sc = SC[risk]; const prog = Math.round(p.progress * 100);
            return (
              <div key={p.id} onClick={() => setSel(p)} style={{
                display: "grid", gridTemplateColumns: "190px 1fr 150px",
                alignItems: "center", padding: "12px 16px", borderBottom: "1px solid #0ff1", cursor: "pointer",
                background: sel?.id === p.id ? "linear-gradient(90deg,#001a2f,#00111f)" : "transparent", transition: "background .2s"
              }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 3 }}>
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: sc.dot, boxShadow: sc.glow }} />
                    <span style={{ color: "#e0f4ff", fontSize: 12, fontWeight: 700 }}>{p.name}</span>
                  </div>
                  <div style={{ color: "#446688", fontSize: 9, marginLeft: 14 }}>
                    {p.daysLeft <= 45 && <span style={{ color: "#ffd60a", marginRight: 6 }}>ðŸ”„ D-{p.daysLeft}</span>}
                    {p.programName}
                  </div>
                </div>
                <div style={{ padding: "0 14px", position: "relative" }}>
                  <div style={{ position: "relative", height: 4, borderRadius: 2, background: "#0a1a2a", margin: "12px 0" }}>
                    <div style={{ height: "100%", width: `${prog}%`, background: sc.dot, opacity: .65, borderRadius: 2 }} />
                    <div style={{ position: "absolute", left: `${prog}%`, top: "50%", transform: "translate(-50%,-50%)", width: 8, height: 8, borderRadius: "50%", background: "#00eeff", boxShadow: "0 0 10px #00eeff", zIndex: 2 }} />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    {["M1", "M2", "M3", "M4", "M5", "M6"].map(m => <span key={m} style={{ color: "#334455", fontSize: 7, letterSpacing: 1 }}>{m}</span>)}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "#00ff87", fontSize: 20, fontWeight: 900, lineHeight: 1 }}>{prog}%</div>
                  <div style={{ color: "#446688", fontSize: 8, marginTop: 2 }}>progresso</div>
                  <div style={{ marginTop: 5, height: 3, borderRadius: 2, background: "#0a1a2a", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${prog}%`, background: sc.dot, borderRadius: 2 }} />
                  </div>
                  <div style={{ color: "#446688", fontSize: 7, marginTop: 2 }}>D{p.day}/{p.totalDays} Â· {p.daysLeft}d</div>
                </div>
              </div>
            );
          })}
        </div>

        {sel && (
          <div style={{ width: 280, overflowY: "auto", background: "#000a14", padding: "18px 16px", flexShrink: 0 }}>
            <div style={{ color: "#e0f4ff", fontSize: 15, fontWeight: 700, marginBottom: 3, fontFamily: "'Sora',sans-serif" }}>{sel.name}</div>
            <div style={{ color: "#446688", fontSize: 9, letterSpacing: 1, marginBottom: 14 }}>{sel.programName}</div>
            <div style={{ color: "#00ff87", fontSize: 28, fontWeight: 900, lineHeight: 1, fontFamily: "'DM Mono',monospace" }}>{Math.round(sel.engagement * 100)}
              <span style={{ fontSize: 11, color: "#446688", marginLeft: 4 }}>% engaj.</span>
            </div>
            <div style={{ color: "#00ff87", fontSize: 11, marginTop: 3, marginBottom: 18 }}>â†‘ {Math.round(sel.progress * 100)}% de progresso</div>
            <div style={{ color: "#0088cc", fontSize: 7, letterSpacing: 3, marginBottom: 8 }}>MÃ‰TRICAS Â· PROGRESSO</div>
            {[
              { label: "Progresso", v: Math.round(sel.progress * 100) },
              { label: "Engajamento", v: Math.round(sel.engagement * 100) },
              { label: "Hormozi Score", v: Math.round(sel.hormoziScore) },
            ].map((m, i) => {
              const c = m.v >= 80 ? "#00ff87" : m.v >= 55 ? "#ffd60a" : "#ff3a3a";
              return (
                <div key={i} style={{ marginBottom: 9 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ color: "#8ab0cc", fontSize: 9 }}>{m.label}</span>
                    <span style={{ color: c, fontSize: 9, fontWeight: 700 }}>{m.v}%</span>
                  </div>
                  <div style={{ height: 2, background: "#0a1a2a", borderRadius: 1, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${m.v}%`, background: c, borderRadius: 1 }} />
                  </div>
                </div>
              );
            })}
            {sel.daysLeft <= 45 && (
              <div style={{ marginTop: 16, background: "linear-gradient(135deg,#1a1000,#0a0800)", border: "1px solid #ffd60a44", borderRadius: 8, padding: "12px" }}>
                <div style={{ color: "#ffd60a", fontSize: 8, fontWeight: 700, letterSpacing: 2, marginBottom: 5 }}>ðŸ”„ GATILHO D-{sel.daysLeft}</div>
                <p style={{ color: "#8a7a44", fontSize: 10, lineHeight: 1.6, margin: "0 0 10px" }}>{sel.renewalReason}</p>
                <button style={{ width: "100%", padding: "8px 0", background: "linear-gradient(90deg,#ffd60a22,#ff990022)", border: "1px solid #ffd60a66", borderRadius: 5, color: "#ffd60a", fontSize: 9, fontWeight: 700, letterSpacing: 2, cursor: "pointer", fontFamily: "'DM Mono',monospace" }}>
                  âš¡ GERAR PROPOSTA
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      {anomaly && <InsightModal anomaly={anomaly} color={aColor} onClose={() => setAnomaly(null)} />}
    </div>
  );
}

// â”€â”€ MODULE 2: RADAR DE TRANSFORMAÃ‡ÃƒO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function RadarModuleState({ title, message, actionLabel, onAction }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", background: "#faf6ec", padding: 24 }}>
      <div style={{ width: "100%", maxWidth: 520, background: "#fff8e8", border: "1px solid #d4af3730", borderRadius: 10, padding: "18px 22px", textAlign: "center" }}>
        <div style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: 3, color: "#d4af37", textTransform: "uppercase", marginBottom: 8 }}>
          {title}
        </div>
        <div style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 13, color: "#7a5c30", lineHeight: 1.7, marginBottom: onAction ? 14 : 0 }}>
          {message}
        </div>
        {onAction && (
          <button
            onClick={onAction}
            style={{
              padding: "8px 12px",
              borderRadius: 6,
              border: "1px solid #d4af3755",
              background: "linear-gradient(135deg,#d4af3722,#c8860b22)",
              color: "#d4af37",
              fontFamily: "'DM Mono',monospace",
              fontSize: 9,
              letterSpacing: 1.5,
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

function RadarModule({ studentId, studentName }) {
  const {
    data: radarData,
    loading: radarLoading,
    error: radarError,
    refresh: refreshRadar,
  } = useClientRadar(studentId ?? null);
  const [slider, setSlider] = useState(0);

  useEffect(() => {
    setSlider(0);
  }, [studentId]);

  const simulation = simulateRadar(radarData?.axisScores ?? [], slider);
  const pillars = simulation.axisScores;
  const n = simulation.count;
  const W = 460, H = 460, cx = W / 2, cy = H / 2, R = W * .34;
  const t = simulation.t;
  const base = simulation.baseline;
  const activeCurrent = simulation.current;
  const activeProjected = simulation.projected;
  const active = simulation.active;
  const bPath = n > 0 ? rPath(base, R, cx, cy, n) : '';
  const aPath = n > 0 ? rPath(active, R, cx, cy, n) : '';
  const insightText = getRadarInsight(pillars, slider > 5);

  if (!studentId) {
    return (
      <RadarModuleState
        title="Selecao pendente"
        message="Selecione um aluno para carregar o Radar de Transformacao."
      />
    );
  }

  if (radarLoading && n === 0) {
    return (
      <RadarModuleState
        title="Carregando radar"
        message="Buscando eixos de transformacao do aluno selecionado."
      />
    );
  }

  if (!radarLoading && radarError && n === 0) {
    return (
      <RadarModuleState
        title="Falha ao carregar radar"
        message={radarError}
        actionLabel="Atualizar radar"
        onAction={refreshRadar}
      />
    );
  }

  if (!radarLoading && !radarError && n === 0) {
    return (
      <RadarModuleState
        title="Sem dados de radar"
        message="Este aluno ainda nao possui eixos avaliados."
        actionLabel="Atualizar radar"
        onAction={refreshRadar}
      />
    );
  }

  return (
    <div style={{ height: "100%", overflowY: "auto", background: "#faf6ec", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "28px 32px 0" }}>
        <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: 5, color: "#a08060", marginBottom: 5, textTransform: "uppercase" }}>
          Jornada do Aluno · Radar de Transformacao
        </div>
        <h2 style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 30, fontWeight: 300, color: "#1a1208", letterSpacing: -0.5 }}>
          {studentName ?? 'â€”'}
        </h2>
        <div style={{ color: "#a08060", fontSize: 11, fontFamily: "'Cormorant Garamond',serif", marginTop: 2 }}>
          {n > 0 ? `${n} eixos de transformacao` : "Sem dados de radar disponiveis"}
        </div>
      </div>

      {radarLoading && n > 0 && (
        <div style={{ color: "#a08060", fontSize: 10, fontFamily: "'DM Mono',monospace", padding: "8px 32px 0" }}>
          Atualizando eixos do radar...
        </div>
      )}

      {radarError && n > 0 && (
        <div style={{ margin: "8px 32px 0", background: "#fff1ec", border: "1px solid #c8860b55", borderRadius: 6, padding: "8px 10px", color: "#7a4f1a", fontSize: 10, fontFamily: "'DM Mono',monospace" }}>
          {radarError}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 28, padding: "20px 32px", flex: 1, overflow: "hidden" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <svg width={W} height={H} style={{ overflow: "visible" }}>
              <defs>
                <radialGradient id="ag" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#d4af37" stopOpacity={0.15 + t * .15} />
                  <stop offset="100%" stopColor="#d4af37" stopOpacity="0" />
                </radialGradient>
                <filter id="rg"><feGaussianBlur stdDeviation="3" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
              </defs>
              {[20, 40, 60, 80, 100].map((rv, ri) => {
                const pts = pillars.map((_, i) => polar((360 / n) * i - 90, (rv / 100) * R, cx, cy));
                return <polygon key={ri} points={pts.map(p => `${p.x},${p.y}`).join(" ")} fill="none" stroke={ri === 4 ? "#d4af3722" : "rgba(0,0,0,.04)"} strokeWidth={ri === 4 ? 1.5 : 1} strokeDasharray={ri < 4 ? "3 4" : "none"} />;
              })}
              {pillars.map((_, i) => { const e = polar((360 / n) * i - 90, R * 1.04, cx, cy); return <line key={i} x1={cx} y1={cy} x2={e.x} y2={e.y} stroke="rgba(0,0,0,.05)" strokeWidth={1} />; })}
              <path d={bPath} fill="#1a1a1a08" stroke="#9e9e9e" strokeWidth={1.5} strokeDasharray="5 4" />
              <path d={aPath} fill="url(#ag)" stroke="#d4af37" strokeWidth={2.5} style={{ filter: "url(#rg)", transition: "d .4s cubic-bezier(.4,0,.2,1)" }} />
              {active.map((v, i) => {
                const p = polar((360 / n) * i - 90, (v / 100) * R, cx, cy);
                return <circle key={i} cx={p.x} cy={p.y} r={4} fill="#d4af37" stroke="#fff8e8" strokeWidth={1.5} style={{ filter: "url(#rg)", transition: "cx .4s,cy .4s" }} />;
              })}
              {pillars.map((pm, i) => {
                const pos = polar((360 / n) * i - 90, R * 1.27, cx, cy);
                const anchor = pos.x > cx + 10 ? "start" : pos.x < cx - 10 ? "end" : "middle";
                const delta = active[i] - base[i];
                return (<g key={i}>
                  <text x={pos.x} y={pos.y - 4} textAnchor={anchor} fill="#1a1208" fontSize={10} fontFamily="'Cormorant Garamond',serif" fontWeight={600}>{pm.axisLabel}</text>
                  <text x={pos.x} y={pos.y + 9} textAnchor={anchor} fill="#a08060" fontSize={9} fontFamily="'Cormorant Garamond',serif">+{delta.toFixed(0)} pts</text>
                </g>);
              })}
              <circle cx={cx} cy={cy} r={3} fill="#d4af37" opacity={.7} />
            </svg>
          </div>

          <div style={{ background: "#fff8e8", border: "1px solid #d4af3325", borderRadius: 10, padding: "18px 20px" }}>
            <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: 4, color: "#d4af37", marginBottom: 3, textTransform: "uppercase" }}>Zona de ProjeÃ§Ã£o Â· Ciclo 2</div>
              <div style={{ fontFamily: "'Cormorant Garamond',serif", color: "#a08060", fontSize: 11, fontStyle: "italic", marginBottom: 12 }}>Arraste para visualizar sua projecao de transformacao</div>
            <input type="range" min={0} max={100} value={slider} onChange={e => setSlider(+e.target.value)} style={{ "--p": `${slider}%` }} />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
              <span style={{ fontSize: 8, color: "#a08060", fontFamily: "'Cormorant Garamond',serif" }}>Resultado Atual</span>
              <span style={{ fontSize: 8, color: "#d4af37", fontFamily: "'Cormorant Garamond',serif" }}>â—† ProjeÃ§Ã£o Ciclo 2</span>
            </div>
            {slider > 5 && (
              <div style={{ marginTop: 10, padding: "9px 13px", borderLeft: "2px solid #d4af37", borderRadius: "0 6px 6px 0", background: "#d4af370a", animation: "fadeIn .3s" }}>
                <p style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 11, color: "#5a4020", fontStyle: "italic", lineHeight: 1.7, margin: 0 }}>
                  {insightText}
                </p>
              </div>
            )}
          </div>
        </div>

        <div>
          <div style={{ background: "#fff8e8", border: "1px solid #d4af3820", borderRadius: 12, padding: "20px 16px", marginBottom: 18, textAlign: "center" }}>
            <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: 4, color: "#a08060", textTransform: "uppercase", marginBottom: 14 }}>Score MÃ©dio</div>
            <div style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 52, fontWeight: 300, color: "#1a1208", lineHeight: 1 }}>
              {n > 0 ? simulation.activeScore.toFixed(0) : "—"}<span style={{ fontSize: 18, color: "#d4af37", marginLeft: 2 }}>pts</span>
            </div>
            <div style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 8, letterSpacing: 3, color: "#a08060", marginTop: 5, textTransform: "uppercase" }}>{slider > 5 ? "ProjeÃ§Ã£o" : "Atual"}</div>
            {n > 0 && (
              <div style={{ marginTop: 10, padding: "7px 0", borderTop: "1px solid #d4af3815", fontFamily: "'Cormorant Garamond',serif", fontSize: 11, color: "#d4af37", fontStyle: "italic" }}>
                +{simulation.deltaScore.toFixed(0)} pts vs. baseline
              </div>
            )}
          </div>
          <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: 3, color: "#a08060", textTransform: "uppercase", marginBottom: 10 }}>Eixos de Transformacao</div>
          {pillars.map((pm, i) => {
            const v = activeCurrent[i] + (activeProjected[i] - activeCurrent[i]) * t;
            const delta = v - base[i];
            return (
              <div key={i} style={{ marginBottom: 9 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                  <span style={{ color: "#1a1208", fontSize: 10, fontFamily: "'Cormorant Garamond',serif", fontWeight: 600 }}>{pm.axisLabel}</span>
                  <span style={{ color: "#d4af37", fontSize: 10, fontFamily: "'Cormorant Garamond',serif", fontWeight: 700 }}>+{delta.toFixed(0)}</span>
                </div>
                <div style={{ height: 3, background: "#f0ead0", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${v}%`, background: "linear-gradient(90deg,#d4af37,#c8963e)", borderRadius: 2, transition: "width .4s ease" }} />
                </div>
              </div>
            );
          })}
          <button style={{
            marginTop: 18, width: "100%", padding: "12px 0", background: "linear-gradient(135deg,#d4af37,#c8860b)",
            border: "none", borderRadius: 8, color: "#fff8e8", fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: 3,
            cursor: "pointer", boxShadow: "0 4px 18px #d4af3744", textTransform: "uppercase"
          }}>
            â—† Apresentar Proposta Ciclo 2
          </button>
        </div>
      </div>
    </div>
  );
}

// â”€â”€ HORMOZI VALUE METER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function HormoziMeter({ p }) {
  const td = p.daysLeft / p.totalDays;
  const eff = 1 - p.engagement;
  const raw = (p.progress * p.engagement) / ((td + 0.2) * (eff + 0.2));
  const score = Math.min(Math.sqrt(raw) * 25, 100);
  const label = score >= 70 ? "Alta" : score >= 40 ? "MÃ©dia" : "Baixa";
  const tc = score >= 70 ? "#3b82f6" : score >= 40 ? "#f59e0b" : "#ef4444";
  const factors = [
    { l: "RESULTADO", v: Math.round(p.progress * 100) },
    { l: "PROBABILIDADE", v: Math.round(p.engagement * 100) },
    { l: "TEMPO", v: Math.round((1 - td) * 100) },
    { l: "ESFORÃ‡O", v: Math.round(p.engagement * 100) },
  ];
  return (
    <div style={{ background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.07)", borderRadius: 8, padding: "10px 12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 7 }}>
        <div style={{ fontSize: 7, letterSpacing: 2, color: "#64748b", textTransform: "uppercase" }}>TermÃ´metro de Valor Â· Hormozi</div>
        <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ color: tc, fontSize: 13, fontWeight: 800, fontFamily: "'DM Mono',monospace" }}>{score.toFixed(0)}</span>
          <span style={{ color: "#475569", fontSize: 8, letterSpacing: 1 }}>{label}</span>
        </div>
      </div>
      <div style={{ position: "relative", height: 8, borderRadius: 4, background: "linear-gradient(90deg,#ef4444 0%,#f59e0b 35%,#8b5cf6 65%,#3b82f6 100%)", marginBottom: 7 }}>
        <div style={{ position: "absolute", left: `${score}%`, top: "50%", transform: "translate(-50%,-50%)", width: 13, height: 13, borderRadius: "50%", background: "#fff", boxShadow: `0 0 0 2px ${tc},0 2px 8px rgba(0,0,0,.5)`, transition: "left .6s ease" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        {factors.map(f => (
          <div key={f.l} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 7, color: "#334155", letterSpacing: 1, marginBottom: 1 }}>{f.l}</div>
            <div style={{ fontSize: 9, color: "#94a3b8", fontFamily: "'DM Mono',monospace" }}>{f.v}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// â”€â”€ MODULE 3: MATRIZ DE RENOVAÃ‡ÃƒO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const QMETA = {
  topRight: { label: "Foco em RenovaÃ§Ã£o", bg: "rgba(16,185,129,.04)", border: "rgba(16,185,129,.12)" },
  topLeft: { label: "Resgatar Valor", bg: "rgba(245,158,11,.04)", border: "rgba(245,158,11,.12)" },
  bottomRight: { label: "Ajustar Protocolo", bg: "rgba(99,102,241,.04)", border: "rgba(99,102,241,.12)" },
  bottomLeft: { label: "IntervenÃ§Ã£o Urgente", bg: "rgba(239,68,68,.04)", border: "rgba(239,68,68,.12)" },
};

function MatrizModule() {
  const [filter, setFilter] = useState("all");
  const [sel, setSel] = useState(null);
  const [proposed, setProposed] = useState(false);
  const {
    data: matrixData,
    loading: matrixLoading,
    error: matrixError,
    refresh: refreshMatrix,
  } = useRenewalMatrix(filter);

  const students = matrixData?.items ?? [];
  const kpis = resolveMatrixKpis(matrixData?.kpis, students);

  useEffect(() => {
    setSel((prev) => {
      if (!prev) return prev;
      const exists = students.some((item) => String(item.id) === String(prev.id));
      return exists ? prev : null;
    });
  }, [students]);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", background: "#020817", color: "#e2e8f0", fontFamily: "'Sora',sans-serif", overflow: "hidden" }}>
      <div style={{ padding: "16px 22px 0", flexShrink: 0 }}>
        <div style={{ fontSize: 8, letterSpacing: 5, color: "#334155", textTransform: "uppercase", marginBottom: 5 }}>Cerebro JPE · Inteligencia de Mentoria</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 800, color: "#f1f5f9", letterSpacing: -0.5 }}>Matriz de Renovacao Antecipada</h2>
            <p style={{ color: "#475569", fontSize: 11, marginTop: 2 }}>Resultado x Engajamento · LTV e retencao</p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
            <div style={{ display: "flex", gap: 6 }}>
              {[
                ["all", "Todos"],
                ["topRight", "Renovar"],
                ["critical", "D-45"],
                ["rescue", "Resgatar"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 6,
                    border: `1px solid ${filter === key ? "rgba(99,102,241,.45)" : "rgba(255,255,255,.08)"}`,
                    background: filter === key ? "rgba(99,102,241,.18)" : "rgba(255,255,255,.03)",
                    color: filter === key ? "#a5b4fc" : "#64748b",
                    fontSize: 9,
                    cursor: "pointer",
                    fontFamily: "'DM Mono',monospace",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {[
                ["LTV TOTAL", formatCurrencyBRL(kpis.totalLTV), "#10b981"],
                ["D-45 CRITICOS", kpis.criticalRenewals, "#f59e0b"],
                ["RESGATAR", String(kpis.rescueCount), "#ef4444"],
                ["ENG. MEDIO", formatPercent01(kpis.avgEngagement, { minimumFractionDigits: 1, maximumFractionDigits: 1 }), "#6366f1"],
              ].map(([l, v, c]) => (
                <div key={l} style={{ background: "linear-gradient(135deg,#0f172a,#0c1424)", border: "1px solid rgba(255,255,255,.06)", borderRadius: 8, padding: "8px 10px", textAlign: "center", minWidth: 82 }}>
                  <div style={{ color: "#475569", fontSize: 7, letterSpacing: 2, textTransform: "uppercase", marginBottom: 3 }}>{l}</div>
                  <div style={{ color: c, fontSize: 14, fontWeight: 800, fontFamily: "'DM Mono',monospace" }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {matrixLoading && (
        <div style={{ color: "#64748b", fontSize: 10, padding: "8px 22px 0", fontFamily: "'DM Mono',monospace" }}>
          Atualizando dados da matriz...
        </div>
      )}

      {matrixError && (
        <div style={{ margin: "8px 22px 0", padding: "8px 10px", borderRadius: 6, border: "1px solid rgba(239,68,68,.4)", background: "rgba(239,68,68,.08)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
          <span style={{ color: "#fecaca", fontSize: 10 }}>{matrixError}</span>
          <button
            onClick={refreshMatrix}
            style={{ border: "1px solid rgba(239,68,68,.45)", background: "rgba(239,68,68,.12)", borderRadius: 6, color: "#fecaca", fontSize: 9, letterSpacing: 1, padding: "5px 8px", cursor: "pointer", fontFamily: "'DM Mono',monospace" }}
          >
            Recarregar
          </button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 250px", gap: 14, padding: "14px 22px", flex: 1, overflow: "hidden", minHeight: 0 }}>
        <div style={{ position: "relative", background: "linear-gradient(135deg,#070d1a,#0a1120)", borderRadius: 12, border: "1px solid rgba(255,255,255,.05)", overflow: "hidden" }}>
          <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
            <line x1="50%" y1="0" x2="50%" y2="100%" stroke="rgba(255,255,255,.06)" strokeWidth={1} strokeDasharray="4 4" />
            <line x1="0" y1="50%" x2="100%" y2="50%" stroke="rgba(255,255,255,.06)" strokeWidth={1} strokeDasharray="4 4" />
          </svg>
          {[{ left: "50%", top: "0", w: "50%", h: "50%", qk: "topRight" }, { left: "0", top: "0", w: "50%", h: "50%", qk: "topLeft" }, { left: "50%", top: "50%", w: "50%", h: "50%", qk: "bottomRight" }, { left: "0", top: "50%", w: "50%", h: "50%", qk: "bottomLeft" }].map(({ left, top, w, h, qk }) => (
            <div key={qk} style={{ position: "absolute", left, top, width: w, height: h, background: QMETA[qk].bg, pointerEvents: "none" }}>
              <div style={{ padding: "8px 10px", fontSize: 7, letterSpacing: 2, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>{QMETA[qk].label}</div>
            </div>
          ))}
          {students.map((p) => {
            const u = URG[p.urgency] || URG.normal;
            const isHL = p.daysLeft <= 45 && qKey(p) === "topRight";
            const isS = sel?.id === p.id;
            return (
              <div key={p.id} onClick={() => { setSel(p); setProposed(false); }} style={{ position: "absolute", left: `${p.progress * 100}%`, bottom: `${p.engagement * 100}%`, transform: "translate(-50%,50%)", zIndex: isS ? 20 : 10, cursor: "pointer" }}>
                {isHL && <div style={{ position: "absolute", inset: -7, borderRadius: "50%", border: `1px solid ${u.color}`, animation: "bPulse 2.4s infinite", opacity: 0.6, pointerEvents: "none" }} />}
                <div style={{
                  width: isS ? 48 : 40, height: isS ? 48 : 40, borderRadius: "50%",
                  background: `radial-gradient(circle at 35% 35%,${u.color}50,${u.color}18)`,
                  border: `2px solid ${u.color}`, boxShadow: isS ? u.glow : `0 0 0 1px ${u.color}44`,
                  display: "flex", alignItems: "center", justifyContent: "center", transition: "all .18s", position: "relative"
                }}>
                  <span style={{ fontSize: isS ? 11 : 9, fontWeight: 700, color: "#f1f5f9", fontFamily: "'DM Mono',monospace" }}>{p.initials}</span>
                  {p.daysLeft <= 45 && <div style={{ position: "absolute", top: -7, right: -7, background: p.daysLeft <= 20 ? "#ef4444" : "#f59e0b", color: "#fff", fontSize: 7, fontWeight: 800, borderRadius: 7, padding: "2px 4px", fontFamily: "'DM Mono',monospace" }}>D-{p.daysLeft}</div>}
                </div>
              </div>
            );
          })}
          <div style={{ position: "absolute", bottom: 6, left: "50%", transform: "translateX(-50%)", fontSize: 7, color: "#334155", letterSpacing: 3 }}>PROGRESSO -></div>
          <div style={{ position: "absolute", left: 6, top: "50%", transform: "translateY(-50%) rotate(-90deg)", fontSize: 7, color: "#334155", letterSpacing: 3 }}>ENGAJAMENTO</div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8, overflowY: "auto" }}>
          {!matrixLoading && students.length === 0 && (
            <div style={{ color: "#64748b", fontSize: 10, textAlign: "center", marginTop: 30, fontFamily: "'DM Mono',monospace", letterSpacing: 1 }}>
              Sem alunos para o filtro atual.
            </div>
          )}

          {sel ? (
            <div style={{ animation: "fadeIn .2s", display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
                  background: `radial-gradient(circle at 35% 35%,${(URG[sel.urgency] || URG.normal).color}40,${(URG[sel.urgency] || URG.normal).color}10)`,
                  border: `1.5px solid ${(URG[sel.urgency] || URG.normal).color}`,
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 800, color: "#f1f5f9", fontFamily: "'DM Mono',monospace"
                }}>
                  {sel.initials}
                </div>
                <div>
                  <div style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 700 }}>{sel.name}</div>
                  <div style={{ color: "#334155", fontSize: 9, marginTop: 1 }}>{sel.programName || sel.plan}</div>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 6 }}>
                {[[`D-${sel.daysLeft}`, sel.daysLeft <= 20 ? "#ef4444" : "#f59e0b", "DIAS"], [`${Math.round(sel.engagement * 100)}%`, "#10b981", "ENGAJ."], [formatCurrencyBRL(sel.ltv), "#a78bfa", "LTV"]].map(([v, c, l]) => (
                  <div key={l} style={{ background: "#0f172a", borderRadius: 6, padding: "7px", textAlign: "center" }}>
                    <div style={{ color: "#334155", fontSize: 6, letterSpacing: 2, marginBottom: 2, textTransform: "uppercase" }}>{l}</div>
                    <div style={{ color: c, fontSize: 13, fontWeight: 800, fontFamily: "'DM Mono',monospace" }}>{v}</div>
                  </div>
                ))}
              </div>
              <HormoziMeter p={sel} />
              <div style={{ background: "rgba(16,185,129,.06)", border: "1px solid rgba(16,185,129,.2)", borderLeft: "3px solid #10b981", borderRadius: "0 7px 7px 0", padding: "10px 12px" }}>
                <div style={{ color: "#64748b", fontSize: 7, letterSpacing: 2, textTransform: "uppercase", marginBottom: 4 }}>MOTIVO DE RENOVACAO</div>
                <p style={{ color: "#94a3b8", fontSize: 11, lineHeight: 1.65, margin: 0 }}>{sel.renewalReason}</p>
              </div>
              <div style={{ background: "rgba(99,102,241,.08)", border: "1px solid rgba(99,102,241,.2)", borderRadius: 7, padding: "10px 12px" }}>
                <div style={{ color: "#6366f1", fontSize: 7, letterSpacing: 2, textTransform: "uppercase", marginBottom: 3 }}>SUGESTAO DE PLANO</div>
                <div style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 600 }}>{sel.suggestion}</div>
              </div>
              {!proposed ? (
                <button onClick={() => setProposed(true)} style={{ width: "100%", padding: "11px 0", background: "linear-gradient(135deg,#6366f1,#4f46e5)", border: "none", borderRadius: 8, color: "#fff", fontSize: 10, fontWeight: 700, letterSpacing: 1, cursor: "pointer", boxShadow: "0 4px 18px rgba(99,102,241,.4)", fontFamily: "'Sora',sans-serif" }}>
                  Gerar Proposta Baseada em Dados
                </button>
              ) : (
                <div style={{ padding: "11px", background: "rgba(16,185,129,.1)", border: "1px solid rgba(16,185,129,.3)", borderRadius: 8, textAlign: "center", animation: "fadeIn .3s" }}>
                  <div style={{ color: "#10b981", fontSize: 12, fontWeight: 700, marginBottom: 2 }}>Proposta gerada</div>
                  <div style={{ color: "#64748b", fontSize: 10 }}>Enviada ao painel de mentoria</div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: "#1e293b", fontSize: 10, textAlign: "center", marginTop: 30, fontFamily: "'DM Mono',monospace", letterSpacing: 1 }}>
              Clique em um aluno
            </div>
          )}
          <div style={{ marginTop: "auto", paddingTop: 8, borderTop: "1px solid rgba(255,255,255,.04)" }}>
            {[...students].sort((a, b) => a.daysLeft - b.daysLeft).slice(0, 3).map((p) => {
              const u = URG[p.urgency] || URG.normal;
              return (
                <div key={p.id} onClick={() => { setSel(p); setProposed(false); }} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 9px", marginBottom: 5, background: sel?.id === p.id ? "rgba(99,102,241,.1)" : "rgba(255,255,255,.02)", border: `1px solid ${sel?.id === p.id ? "rgba(99,102,241,.3)" : "rgba(255,255,255,.05)"}`, borderRadius: 7, cursor: "pointer" }}>
                  <div style={{ width: 26, height: 26, borderRadius: "50%", background: `${u.color}22`, border: `1.5px solid ${u.color}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 8, fontWeight: 800, color: "#f1f5f9", fontFamily: "'DM Mono',monospace", flexShrink: 0 }}>{p.initials}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ color: "#e2e8f0", fontSize: 10, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name}</div>
                    <div style={{ color: "#334155", fontSize: 8, marginTop: 1 }}>{p.programName || p.plan}</div>
                  </div>
                  <div style={{ color: p.daysLeft <= 20 ? "#ef4444" : "#f59e0b", fontSize: 9, fontFamily: "'DM Mono',monospace", fontWeight: 800, flexShrink: 0 }}>D-{p.daysLeft}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function Particles() {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d");
    const setSize = () => { c.width = c.offsetWidth; c.height = c.offsetHeight; };
    setSize();
    const pts = Array.from({ length: 55 }, () => ({
      x: Math.random() * c.width, y: Math.random() * c.height,
      vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25, r: Math.random() * 1.4 + .4,
      col: [`rgba(0,238,255,`, `rgba(212,175,55,`, `rgba(167,139,250,`][Math.floor(Math.random() * 3)],
    }));
    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, c.width, c.height);
      pts.forEach(p => { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > c.width) p.vx *= -1; if (p.y < 0 || p.y > c.height) p.vy *= -1; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = p.col + ".5)"; ctx.fill(); });
      pts.forEach((a, i) => pts.slice(i + 1).forEach(b => { const d = Math.hypot(a.x - b.x, a.y - b.y); if (d < 90) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.strokeStyle = `rgba(255,255,255,${.03 * (1 - d / 90)})`; ctx.lineWidth = .5; ctx.stroke(); } }));
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, []);
  return <canvas ref={ref} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }} />;
}

// â”€â”€ MODULE ICONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const ModIcon = ({ id }) => {
  if (id === "comando") return (
    <svg width={44} height={44} viewBox="0 0 44 44" fill="none">
      <rect x={3} y={18} width={4} height={20} rx={1} fill="#00eeff" opacity={.8} />
      <rect x={11} y={12} width={4} height={26} rx={1} fill="#00eeff" />
      <rect x={19} y={22} width={4} height={16} rx={1} fill="#00ff87" opacity={.9} />
      <rect x={27} y={8} width={4} height={30} rx={1} fill="#00eeff" opacity={.7} />
      <rect x={35} y={16} width={4} height={22} rx={1} fill="#ffd60a" opacity={.9} />
      <circle cx={37} cy={10} r={4} fill="#ff3a3a" opacity={.9} />
    </svg>
  );
  if (id === "radar") return (
    <svg width={44} height={44} viewBox="0 0 44 44" fill="none">
      <polygon points="22,3 41,15 41,31 22,43 3,31 3,15" fill="none" stroke="#d4af37" strokeWidth={1} opacity={.25} />
      <polygon points="22,9 36,17 36,29 22,37 8,29 8,17" fill="none" stroke="#d4af37" strokeWidth={1} opacity={.5} />
      <polygon points="22,5 39,16 39,30 22,41 5,30 5,16" fill="rgba(212,175,55,.12)" stroke="#d4af37" strokeWidth={2} />
      {[0, 1, 2, 3, 4, 5].map(i => { const a = (60 * i - 90) * Math.PI / 180; return <line key={i} x1={22} y1={22} x2={22 + 18 * Math.cos(a)} y2={22 + 18 * Math.sin(a)} stroke="#d4af3744" strokeWidth={1} />; })}
      <circle cx={22} cy={22} r={2.5} fill="#d4af37" />
    </svg>
  );
  return (
    <svg width={44} height={44} viewBox="0 0 44 44" fill="none">
      <line x1={22} y1={2} x2={22} y2={42} stroke="rgba(255,255,255,.08)" strokeWidth={1} strokeDasharray="3 3" />
      <line x1={2} y1={22} x2={42} y2={22} stroke="rgba(255,255,255,.08)" strokeWidth={1} strokeDasharray="3 3" />
      <circle cx={32} cy={12} r={7} fill="rgba(16,185,129,.25)" stroke="#10b981" strokeWidth={1.5} />
      <circle cx={32} cy={12} r={3} fill="#10b981" />
      <circle cx={12} cy={12} r={5} fill="rgba(245,158,11,.18)" stroke="#f59e0b" strokeWidth={1.5} />
      <circle cx={32} cy={32} r={4} fill="rgba(167,139,250,.18)" stroke="#a78bfa" strokeWidth={1.5} />
      <circle cx={12} cy={32} r={6} fill="rgba(239,68,68,.18)" stroke="#ef4444" strokeWidth={1.5} />
    </svg>
  );
};

// â”€â”€ HUB HOME â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function HubHome({ onSelect, students = [], onNewPatient }) {
  const [hov, setHov] = useState(null);
  const [time, setTime] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t); }, []);
  const totalLTV = students.reduce((s, p) => s + (parseFloat(String(p.ltv)) || 0), 0);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", background: "#02060f", color: "#e2e8f0", fontFamily: "'Sora',sans-serif", overflow: "hidden", position: "relative" }}>
      <Particles />

      {/* Top nav */}
      <div style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 32px", height: 58, borderBottom: "1px solid rgba(255,255,255,.04)", background: "rgba(2,6,15,.85)", backdropFilter: "blur(12px)", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ position: "relative", width: 30, height: 30 }}>
            <div style={{ position: "absolute", inset: 0, borderRadius: "50%", border: "1px solid rgba(0,238,255,.4)", animation: "rotateSlow 8s linear infinite" }} />
            <div style={{ position: "absolute", inset: 4, borderRadius: "50%", background: "radial-gradient(circle,rgba(0,238,255,.25),rgba(0,238,255,.04))" }} />
            <div style={{ position: "absolute", inset: "50%", width: 5, height: 5, marginLeft: -2.5, marginTop: -2.5, borderRadius: "50%", background: "#00eeff", boxShadow: "0 0 8px #00eeff" }} />
          </div>
          <div>
            <div style={{ color: "#00eeff", fontSize: 12, fontWeight: 700, letterSpacing: 2, fontFamily: "'DM Mono',monospace" }}>CÃ‰REBRO JPE</div>
            <div style={{ color: "#1e293b", fontSize: 8, letterSpacing: 3 }}>JORNADA DO ALUNO ESTRUTURADA</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          {[["ALUNOS", String(students.length), "#00ff87"], ["LTV TOTAL", "R$" + (totalLTV / 1000).toFixed(0) + "k", "#d4af37"], ["ALERTAS D-45", String(students.filter(p => p.daysLeft <= 45).length), "#f59e0b"]].map(([l, v, c]) => (
            <div key={l} style={{ textAlign: "center" }}>
              <div style={{ color: c, fontSize: 15, fontWeight: 800, fontFamily: "'DM Mono',monospace", lineHeight: 1 }}>{v}</div>
              <div style={{ color: "#1e293b", fontSize: 7, letterSpacing: 2, marginTop: 2 }}>{l}</div>
            </div>
          ))}
          <button onClick={onNewPatient} style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "7px 14px", borderRadius: 8, cursor: "pointer",
            background: "linear-gradient(135deg,#0a3050,#062040)",
            border: "1px solid rgba(0,238,255,.3)",
            color: "#00eeff", fontFamily: "'DM Mono',monospace", fontSize: 9,
            fontWeight: 700, letterSpacing: 1.5,
            boxShadow: "0 4px 16px rgba(0,238,255,.1)", transition: "all .2s"
          }}>
            <span style={{ fontSize: 14, lineHeight: 1 }}>+</span> ALUNO
          </button>
          <div style={{ color: "#1e293b", fontSize: 9, fontFamily: "'DM Mono',monospace", paddingLeft: 14, borderLeft: "1px solid rgba(255,255,255,.05)" }}>
            {time.toLocaleTimeString("pt-BR")}
          </div>
        </div>
      </div>

      {/* Hero */}
      <div style={{ position: "relative", zIndex: 10, flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "0 32px 24px", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18, animation: "fadeUp .5s ease both" }}>
          <div style={{ height: 1, width: 36, background: "linear-gradient(90deg,transparent,rgba(0,238,255,.5))" }} />
          <span style={{ color: "#00eeff", fontSize: 8, letterSpacing: 5, fontFamily: "'DM Mono',monospace", textTransform: "uppercase", whiteSpace: "nowrap" }}>Sistema Integrado de Inteligencia de Mentoria</span>
          <div style={{ height: 1, width: 36, background: "linear-gradient(90deg,rgba(0,238,255,.5),transparent)" }} />
        </div>

        <h1 style={{
          fontFamily: "'Cinzel',serif", fontSize: "clamp(24px,3.5vw,46px)", fontWeight: 600, textAlign: "center", letterSpacing: 1.5,
          background: "linear-gradient(135deg,#e2e8f0 0%,#d4af37 45%,#00eeff 100%)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
          backgroundSize: "200% auto", animation: "shimmer 5s linear infinite,fadeUp .7s .08s ease both",
          marginBottom: 10, lineHeight: 1.15
        }}>
          Plataforma High Ticket<br />de Mentorias
        </h1>

        <p style={{
          color: "#475569", fontSize: 13, textAlign: "center", maxWidth: 520, lineHeight: 1.75, marginBottom: 40,
          animation: "fadeUp .7s .15s ease both", fontWeight: 300
        }}>
          TrÃªs mÃ³dulos de decisÃ£o baseados na{" "}
          <em style={{ color: "#d4af37", fontStyle: "normal" }}>metodologia LTV</em> do seu programa de mentoria.{" "}
          Selecione um mÃ³dulo para iniciar.
        </p>

        {/* Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 18, width: "100%", maxWidth: 960, animation: "fadeUp .8s .22s ease both" }}>
          {MODULES_META.map(mod => (
            <div key={mod.id}
              onMouseEnter={() => setHov(mod.id)}
              onMouseLeave={() => setHov(null)}
              onClick={() => onSelect(mod.id)}
              style={{
                position: "relative", overflow: "hidden",
                background: hov === mod.id ? "linear-gradient(135deg,#0c1424,#0f1a30)" : "linear-gradient(135deg,#070d1a,#0a1120)",
                border: `1px solid ${hov === mod.id ? mod.accent + "55" : "rgba(255,255,255,.07)"}`,
                borderRadius: 14, padding: "24px 22px", cursor: "pointer",
                transition: "all .25s cubic-bezier(.4,0,.2,1)",
                transform: hov === mod.id ? "translateY(-5px) scale(1.01)" : "none",
                boxShadow: hov === mod.id ? `0 20px 50px rgba(0,0,0,.5),0 0 30px ${mod.accent}10` : "0 4px 18px rgba(0,0,0,.3)"
              }}>
              {/* Top edge glow */}
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 1, background: `linear-gradient(90deg,transparent,${mod.accent}88,transparent)`, opacity: hov === mod.id ? 1 : 0, transition: "opacity .3s" }} />
              <div style={{ position: "absolute", top: 14, right: 18, fontFamily: "'DM Mono',monospace", fontSize: 10, color: "rgba(255,255,255,.05)", fontWeight: 700, letterSpacing: 2 }}>{mod.num}</div>
              <div style={{ marginBottom: 16, transition: "transform .25s", transform: hov === mod.id ? "scale(1.08)" : "scale(1)" }}><ModIcon id={mod.id} /></div>
              <div style={{ fontFamily: "'DM Mono',monospace", fontSize: 7, letterSpacing: 3, color: mod.accent, textTransform: "uppercase", marginBottom: 5 }}>{mod.sub}</div>
              <h3 style={{ color: "#f1f5f9", fontSize: 16, fontWeight: 700, letterSpacing: -0.3, marginBottom: 8, lineHeight: 1.2 }}>{mod.label}</h3>
              <p style={{ color: "#475569", fontSize: 11, lineHeight: 1.7, marginBottom: 16, minHeight: 52 }}>{mod.desc}</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 18 }}>
                {mod.tags.map(tg => (
                  <span key={tg} style={{ fontSize: 7, color: mod.accent, border: `1px solid ${mod.accent}33`, borderRadius: 3, padding: "2px 6px", background: `${mod.accent}0a`, letterSpacing: .5 }}>{tg}</span>
                ))}
              </div>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "9px 12px", background: hov === mod.id ? `${mod.accent}18` : "rgba(255,255,255,.03)",
                border: `1px solid ${hov === mod.id ? mod.accent + "44" : "rgba(255,255,255,.05)"}`,
                borderRadius: 7, transition: "all .25s"
              }}>
                <span style={{ color: hov === mod.id ? mod.accent : "#334155", fontSize: 10, fontWeight: 700, letterSpacing: 1, fontFamily: "'DM Mono',monospace", transition: "color .25s" }}>ABRIR MÃ“DULO</span>
                <span style={{ color: mod.accent, fontSize: 14, opacity: hov === mod.id ? 1 : .25, transition: "all .25s", transform: hov === mod.id ? "translateX(2px)" : "none" }}>â†’</span>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 28, color: "#1e293b", fontSize: 8, letterSpacing: 3, fontFamily: "'DM Mono',monospace", textAlign: "center", animation: "fadeUp .9s .35s ease both" }}>
          SWAIF LTV MENTOR Â· GESTÃƒO DE MENTORIAS HIGH TICKET Â· JPE Â© 2025
        </div>
      </div>
    </div>
  );
}

// â”€â”€ TOP MODULE BAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function ModuleBar({ active, onNav }) {
  const mod = MODULES_META.find(m => m.id === active);
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 18px", height: 46,
      borderBottom: "1px solid rgba(255,255,255,.05)", background: "rgba(2,6,15,.96)", backdropFilter: "blur(12px)", flexShrink: 0, zIndex: 50
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button onClick={() => onNav("home")} style={{
          display: "flex", alignItems: "center", gap: 7,
          background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.08)",
          borderRadius: 7, padding: "5px 11px", cursor: "pointer", color: "#64748b",
          fontFamily: "'DM Mono',monospace", fontSize: 9, letterSpacing: 1, transition: "all .15s"
        }}
          onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,.09)"; e.currentTarget.style.color = "#e2e8f0"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,.04)"; e.currentTarget.style.color = "#64748b"; }}>
          â† HUB
        </button>
        <div style={{ width: 1, height: 18, background: "rgba(255,255,255,.07)" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <div style={{ width: 5, height: 5, borderRadius: "50%", background: mod?.accent, boxShadow: `0 0 7px ${mod?.accent}` }} />
          <span style={{ color: "#e2e8f0", fontSize: 11, fontWeight: 600 }}>{mod?.label}</span>
          <span style={{ color: "#334155", fontSize: 9, letterSpacing: .5 }}>{mod?.sub}</span>
        </div>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {MODULES_META.map(m => (
          <button key={m.id} onClick={() => onNav(m.id)} style={{
            padding: "4px 11px", fontSize: 8, letterSpacing: 1, cursor: "pointer",
            background: active === m.id ? `${m.accent}1a` : "rgba(255,255,255,.03)",
            border: `1px solid ${active === m.id ? m.accent + "44" : "rgba(255,255,255,.05)"}`,
            borderRadius: 6, color: active === m.id ? m.accent : "#475569", transition: "all .15s",
            fontFamily: "'DM Mono',monospace", textTransform: "uppercase"
          }}>
            {m.num}
          </button>
        ))}
      </div>
    </div>
  );
}

// â”€â”€ MAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function App() {
  const { data: studentList, loading: studentsLoading, error: studentsError, refresh: refreshClients } = useClients();
  const { logout, accessToken } = useAuth();
  const [view, setView] = useState("home");
  const [fading, setFading] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [showCadastro, setShowCadastro] = useState(false);

  useEffect(() => {
    if (studentList?.length && !selectedStudentId) setSelectedStudentId(studentList[0].id);
  }, [studentList]);

  const go = (target) => {
    setFading(true);
    setTimeout(() => { setView(target); setFading(false); }, 180);
  };

  const selectedStudentName = studentList?.find(s => s.id === selectedStudentId)?.name ?? null;
  const students = studentList ?? [];

  return (
    <>
      <GS />
      <div style={{
        height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden",
        opacity: fading ? 0 : 1, transition: "opacity .18s"
      }}>
        {view !== "home" && <ModuleBar active={view} onNav={go} />}
        <div style={{ flex: 1, overflow: "hidden", minHeight: 0 }}>
          {studentsError && (
            <div style={{ padding: 20, color: "#ff3a3a", fontFamily: "monospace" }}>
              Erro ao carregar alunos: {studentsError}
            </div>
          )}
          {view === "home" && <HubHome onSelect={go} students={students} onNewPatient={() => setShowCadastro(true)} />}
          {view === "comando" && <CommandoModule students={students} />}
          {view === "radar" && <RadarModule studentId={selectedStudentId} studentName={selectedStudentName} />}
          {view === "matriz" && <MatrizModule />}
        </div>
      </div>
      {showCadastro && (
        <CadastroModal
          onClose={() => setShowCadastro(false)}
          programName={students[0]?.programName ?? 'â€”'}
          programId={students[0]?.programId}
          onCreated={() => { setShowCadastro(false); refreshClients(); }}
        />
      )}
    </>
  );
}



