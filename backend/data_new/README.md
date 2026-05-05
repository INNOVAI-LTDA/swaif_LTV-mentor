# data_new

Conjunto de tabelas fundamentais já ajustado para o novo modelo:

- `organizations.json` (empresa/tenant raiz)
- `products.json` (produto/programa da organização)
- `students.json`
- `mentors.json`
- `users.json`
- `enrollments.json`
- `measurements.json`
- `pillars.json`
- `metrics.json`
- `calculation_methods.json`

## Ajustes aplicados neste diretório

1. `clients` foi absorvido semanticamente em `organizations`.
2. `organizations` antigo foi migrado para `products`.
3. `protocols` foi removido deste recorte.

## Regras de cálculo esperadas

1. **Métrica**: medida normalizada em `0..1`.
2. **Pilar**: média geométrica das métricas normalizadas do pilar.
3. **Produto**: média geométrica dos pilares normalizados.
4. **Matriz de decisão**: etapa complementar de posicionamento (threshold/quadrante) derivada das medidas.

> Na UI, os valores normalizados `0..1` podem ser exibidos em percentual (`0%..100%`).
