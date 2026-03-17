import type { CSSProperties } from "react";
import type { MatrixItem, Urgency } from "../../../domain/models";

type MatrixBoardProps = {
  items: MatrixItem[];
  selectedId: string | null;
  onSelect: (item: MatrixItem) => void;
};

const QUADRANT_META = {
  topRight: {
    title: "Renovar",
    subtitle: "Alto progresso · Alto engajamento",
    className: "mx-quadrant--top-right"
  },
  topLeft: {
    title: "Resgatar valor",
    subtitle: "Baixo progresso · Alto engajamento",
    className: "mx-quadrant--top-left"
  },
  bottomRight: {
    title: "Ajustar plano",
    subtitle: "Alto progresso · Baixo engajamento",
    className: "mx-quadrant--bottom-right"
  },
  bottomLeft: {
    title: "Recuperação urgente",
    subtitle: "Baixo progresso · Baixo engajamento",
    className: "mx-quadrant--bottom-left"
  }
} as const;

const URGENCY_META: Record<Urgency, { className: string }> = {
  normal: { className: "mx-bubble--normal" },
  watch: { className: "mx-bubble--watch" },
  critical: { className: "mx-bubble--critical" },
  rescue: { className: "mx-bubble--rescue" }
};

function clampPercent(value01: number) {
  const safe = Number.isFinite(value01) ? value01 : 0;
  return Math.max(0, Math.min(100, safe * 100));
}

function bubbleSize(ltv: number, minLtv: number, maxLtv: number) {
  if (!Number.isFinite(ltv) || maxLtv <= minLtv) {
    return 48;
  }
  const ratio = (ltv - minLtv) / (maxLtv - minLtv);
  return Math.round(42 + Math.max(0, Math.min(1, ratio)) * 18);
}

function resolveInitials(item: MatrixItem) {
  const normalized = (item.initials || "").trim();
  if (normalized.length > 0) {
    return normalized.toUpperCase().slice(0, 3);
  }
  return item.name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((chunk) => chunk[0]?.toUpperCase() ?? "")
    .join("");
}

export function MatrixBoard({ items, selectedId, onSelect }: MatrixBoardProps) {
  const ltvs = items.map((item) => item.ltv);
  const minLtv = ltvs.length > 0 ? Math.min(...ltvs) : 0;
  const maxLtv = ltvs.length > 0 ? Math.max(...ltvs) : 0;

  return (
    <article className="mx-board">
      <div className="mx-board-surface">
        {Object.entries(QUADRANT_META).map(([quadrant, meta]) => (
          <section key={quadrant} className={`mx-quadrant ${meta.className}`}>
            <h3>{meta.title}</h3>
            <p>{meta.subtitle}</p>
          </section>
        ))}

        <div className="mx-board-axis mx-board-axis--vertical" aria-hidden="true" />
        <div className="mx-board-axis mx-board-axis--horizontal" aria-hidden="true" />

        <div className="mx-axis-label mx-axis-label--x">progresso da jornada</div>
        <div className="mx-axis-label mx-axis-label--y">engajamento do aluno</div>

        {items.map((item) => {
          const urgency = URGENCY_META[item.urgency];
          const active = selectedId === item.id;
          const style: CSSProperties = {
            left: `${clampPercent(item.progress)}%`,
            bottom: `${clampPercent(item.engagement)}%`,
            width: bubbleSize(item.ltv, minLtv, maxLtv),
            height: bubbleSize(item.ltv, minLtv, maxLtv)
          };

          return (
            <button
              key={item.id}
              type="button"
              className={`mx-bubble ${urgency.className} ${active ? "is-selected" : ""}`}
              style={style}
              onClick={() => onSelect(item)}
              title={`${item.name} - ${item.programName}`}
            >
              <span>{resolveInitials(item)}</span>
              {item.daysLeft <= 45 && <small>D-{item.daysLeft}</small>}
            </button>
          );
        })}
      </div>
    </article>
  );
}
