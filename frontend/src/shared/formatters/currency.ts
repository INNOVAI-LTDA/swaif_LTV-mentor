export function formatCurrencyBRL(value: number): string {
  const safe = Number.isFinite(value) ? value : 0;
  return safe.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });
}
