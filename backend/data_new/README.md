# data_new

Conjunto de tabelas fundamentais para o redesenho:

- `students.json`
- `clients.json`
- `organizations.json`
- `mentors.json`
- `users.json`
- `protocols.json`
- `pillars.json`
- `metrics.json`
- `calculation_methods.json`

## Regras de cálculo esperadas

1. **Métrica**: medida normalizada em `0..1`.
2. **Pilar**: média geométrica das métricas normalizadas do pilar.
3. **Protocolo**: média geométrica dos pilares normalizados.
4. **Matriz de decisão**: etapa complementar de posicionamento (com possíveis thresholds e regras de quadrante), derivada das medidas já calculadas.

> Observação: na UI, os valores normalizados `0..1` podem ser exibidos em percentual (`0%..100%`).


## Auditoria de nomenclatura

- Veja `clients-organizations-protocols-audit.md` para inconsistências e proposta de ajuste.
