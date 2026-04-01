type RadarPoint = {
  axisLabel: string;
  baseline: number;
  current: number;
  projected: number;
};

type RadarChartProps = {
  points: RadarPoint[];
  title: string;
};

function polarToXY(angleDeg: number, radius: number, cx: number, cy: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return {
    x: cx + radius * Math.cos(rad),
    y: cy + radius * Math.sin(rad)
  };
}

function polygonPath(values: number[], max: number, radius: number, cx: number, cy: number) {
  if (values.length === 0) {
    return "";
  }

  const parts: string[] = [];
  const count = values.length;

  values.forEach((value, index) => {
    const pct = Math.max(0, Math.min(1, value / max));
    const point = polarToXY((360 / count) * index, radius * pct, cx, cy);
    parts.push(`${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`);
  });

  return `${parts.join(" ")} Z`;
}

export function RadarChart({ points, title }: RadarChartProps) {
  const size = 460;
  const center = size / 2;
  const radius = 160;
  const rings = [20, 40, 60, 80, 100];
  const count = points.length;

  if (count === 0) {
    return (
      <div className="radar-chart-empty">
        <p>Sem eixos para renderizar o radar.</p>
      </div>
    );
  }

  const baseline = points.map((axis) => axis.baseline);
  const current = points.map((axis) => axis.current);
  const projected = points.map((axis) => axis.projected);
  const baselinePath = polygonPath(baseline, 1, radius, center, center);
  const currentPath = polygonPath(current, 1, radius, center, center);
  const projectedPath = polygonPath(projected, 1, radius, center, center);

  return (
    <figure className="radar-chart">
      <figcaption>{title}</figcaption>
      <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label={title}>
        <defs>
          <linearGradient id="radarBaseline" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7f8ea2" stopOpacity="0.24" />
            <stop offset="100%" stopColor="#7f8ea2" stopOpacity="0.04" />
          </linearGradient>
          <linearGradient id="radarCurrent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f7b955" stopOpacity="0.50" />
            <stop offset="100%" stopColor="#f78f47" stopOpacity="0.14" />
          </linearGradient>
        </defs>

        {rings.map((ring) => (
          <circle
            key={ring}
            cx={center}
            cy={center}
            r={(radius * ring) / 100}
            fill="none"
            stroke="rgba(169, 186, 212, 0.24)"
            strokeWidth={1}
          />
        ))}

        {points.map((axis, index) => {
          const angle = (360 / count) * index;
          const edge = polarToXY(angle, radius, center, center);
          const labelPos = polarToXY(angle, radius + 26, center, center);

          return (
            <g key={axis.axisLabel}>
              <line
                x1={center}
                y1={center}
                x2={edge.x}
                y2={edge.y}
                stroke="rgba(169, 186, 212, 0.22)"
                strokeWidth={1}
              />
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#b7c9e4"
                fontSize="11"
              >
                {axis.axisLabel}
              </text>
            </g>
          );
        })}

        <path d={baselinePath} fill="url(#radarBaseline)" stroke="#9da9ba" strokeWidth={1.6} />
        <path d={projectedPath} fill="none" stroke="#8df2c6" strokeWidth={1.8} strokeDasharray="8 6" />
        <path d={currentPath} fill="url(#radarCurrent)" stroke="#ffcb6b" strokeWidth={2.4} />
      </svg>
    </figure>
  );
}
