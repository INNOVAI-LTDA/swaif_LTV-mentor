import { coerceNumber } from "../adapters/domainAdapter.js";

export function formatPercent01(value01, options = {}) {
  const { minimumFractionDigits = 0, maximumFractionDigits = 0 } = options;
  const safe = coerceNumber(value01, 0);
  const percent = safe * 100;
  return `${percent.toLocaleString("pt-BR", {
    minimumFractionDigits,
    maximumFractionDigits,
  })}%`;
}

export function formatCurrencyBRL(value) {
  const safe = coerceNumber(value, 0);
  return safe.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

