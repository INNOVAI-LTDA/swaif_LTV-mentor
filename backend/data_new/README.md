# data_new

Conjunto de tabelas fundamentais já ajustado para o novo modelo:

- `organizations.json` (empresa/tenant raiz)
- `products.json` (produto/programa da organização)
- `protocols.json` (ligado ao produto e à organização)
- `students.json`
- `mentors.json`
- `users.json`
- `pillars.json`
- `metrics.json`
- `calculation_methods.json`

## Ajustes aplicados neste diretório

1. `clients` foi absorvido semanticamente em `organizations`.
2. `organizations` antigo foi migrado para `products`.
3. `protocols` passou a expor:
   - `organization_id` (empresa)
   - `product_id` (produto/programa)

## Regras de cálculo esperadas

1. **Métrica**: medida normalizada em `0..1`.
2. **Pilar**: média geométrica das métricas normalizadas do pilar.
3. **Protocolo**: média geométrica dos pilares normalizados.
4. **Matriz de decisão**: etapa complementar de posicionamento (threshold/quadrante) derivada das medidas.

> Na UI, os valores normalizados `0..1` podem ser exibidos em percentual (`0%..100%`).
