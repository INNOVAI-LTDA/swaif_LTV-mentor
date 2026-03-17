export function formatPercent01(value: number, fractionDigits = 0): string {
  const safe = Number.isFinite(value) ? value : 0;
  return `${(safe * 100).toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  })}%`;
}
