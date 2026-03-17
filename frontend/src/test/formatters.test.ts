import { formatCurrencyBRL } from "../shared/formatters/currency";
import { formatPercent01 } from "../shared/formatters/percent";

describe("formatters", () => {
  it("formata percentual 0..1", () => {
    expect(formatPercent01(0.42)).toBe("42%");
  });

  it("formata moeda BRL", () => {
    expect(formatCurrencyBRL(1234)).toContain("1.234");
  });
});
