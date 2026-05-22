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
    className: "mx-quadrant--top-right"
  },
  topLeft: {
    title: "Ajustar plano",
    className: "mx-quadrant--top-left"
  },
  bottomRight: {
    title: "Resgatar valor",
    className: "mx-quadrant--bottom-right"
  },
  bottomLeft: {
    title: "Recuperação urgente",
    className: "mx-quadrant--bottom-left"
  }
} as const;

const URGENCY_META: Record<Urgency, { className: string }> = {
  normal: { className: "mx-bubble--normal" },
  watch: { className: "mx-bubble--watch" },
  critical: { className: "mx-bubble--critical" },
  rescue: { className: "mx-bubble--rescue" }
};

function normalizeScore(value: number) {
  const safe = Number.isFinite(value) ? value : 0;
  if (safe > 1) {
    return Math.max(0, Math.min(1, safe / 100));
  }
  return Math.max(0, Math.min(1, safe));
}

function clampPercent(value01: number) {
  const safe = normalizeScore(value01);
  const padding = 0.08;
  return (padding + safe * (1 - padding * 2)) * 100;
}

function clampBubblePositionPercent(value: number) {
  return Math.max(4, Math.min(96, value));
}

function hashString(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function spreadForCollision({ index, total, seed }: { index: number; total: number; seed: number }) {
  if (total <= 1) {
    return { x: 0, y: 0 };
  }

  const goldenAngle = 2.399963229728653;
  const baseAngle = ((seed % 360) * Math.PI) / 180;
  const angle = baseAngle + index * goldenAngle;
  const radius = (Math.sqrt(index + 1) / Math.sqrt(total)) * 12;

  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  };
}

function resolveVisualQuadrant(item: Pick<MatrixItem, "progress" | "engagement">) {
  const progress = normalizeScore(item.progress);
  const engagement = normalizeScore(item.engagement);
  const isRight = progress >= 0.5;
  const isTop = engagement >= 0.5;

  if (isTop && isRight) {
    return "topRight";
  }
  if (isTop) {
    return "topLeft";
  }
  if (isRight) {
    return "bottomRight";
  }
  return "bottomLeft";
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

  const collisionGroups = new Map<string, MatrixItem[]>();
  for (const item of items) {
    const key = `${normalizeScore(item.progress).toFixed(4)}|${normalizeScore(item.engagement).toFixed(4)}`;
    const group = collisionGroups.get(key);
    if (group) {
      group.push(item);
    } else {
      collisionGroups.set(key, [item]);
    }
  }

  const collisionMetaById = new Map<string, { index: number; total: number; seed: number }>();
  for (const group of collisionGroups.values()) {
    const total = group.length;
    for (let index = 0; index < total; index += 1) {
      const item = group[index];
      collisionMetaById.set(item.id, {
        index,
        total,
        seed: hashString(item.id),
      });
    }
  }

  return (
    <article className="mx-board">
      <div className="mx-board-surface">
        {Object.entries(QUADRANT_META).map(([quadrant, meta]) => (
          <section key={quadrant} className={`mx-quadrant ${meta.className}`}>
            <h3>{meta.title}</h3>
          </section>
        ))}

        <div className="mx-board-axis mx-board-axis--vertical" aria-hidden="true" />
        <div className="mx-board-axis mx-board-axis--horizontal" aria-hidden="true" />

        <div className="mx-axis-label mx-axis-label--x">progresso da jornada</div>
        <div className="mx-axis-label mx-axis-label--y">engajamento do aluno</div>

        {items.map((item) => {
          const urgency = URGENCY_META[item.urgency];
          const active = selectedId === item.id;
          const visualQuadrant = resolveVisualQuadrant(item);
          const collisionMeta = collisionMetaById.get(item.id) || { index: 0, total: 1, seed: hashString(item.id) };
          const spread = spreadForCollision({
            index: collisionMeta.index,
            total: collisionMeta.total,
            seed: collisionMeta.seed,
          });
          const left = clampBubblePositionPercent(clampPercent(item.progress) + spread.x);
          const bottom = clampBubblePositionPercent(clampPercent(item.engagement) + spread.y);
          const style: CSSProperties = {
            left: `${left}%`,
            bottom: `${bottom}%`,
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
              data-visual-quadrant={visualQuadrant}
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
