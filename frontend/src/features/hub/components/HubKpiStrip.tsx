type KpiItem = {
  label: string;
  value: string;
  tone?: "neutral" | "success" | "warning" | "danger";
};

type HubKpiStripProps = {
  items: KpiItem[];
};

export function HubKpiStrip({ items }: HubKpiStripProps) {
  return (
    <div className="hub-kpi-strip">
      {items.map((item) => (
        <article key={item.label} className={`hub-kpi-item hub-kpi-item--${item.tone ?? "neutral"}`}>
          <p className="hub-kpi-label">{item.label}</p>
          <p className="hub-kpi-value">{item.value}</p>
        </article>
      ))}
    </div>
  );
}
