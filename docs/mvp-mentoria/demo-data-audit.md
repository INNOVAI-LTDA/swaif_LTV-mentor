# Demo Data Audit (MVP Mentoria)

Data: 2026-03-09

## Escopo e metodo

Auditoria feita sobre:
- arquivos `backend/data/*.json`
- logica real de derivacao em `backend/app/services/indicator_carga_service.py`
- consumo de KPI no frontend (Hub, Centro e Matriz)
- narrativa alvo em `docs/mvp-mentoria/demo-narrative.md`

Objetivo: validar a base simulada apos carga, sem alterar contrato nem implementar features.

## Resumo executivo

- Coerencia geral entre backend e visualizacoes: **boa**
- Distribuicao para Matriz: **suficiente e balanceada**
- Narrativa por perfil: **boa, com pontos de repeticao**
- Radar: **coerente no macro**, com **1 inconsistencia estrutural de unidade**
- KPIs de Hub/Centro: **consistentes**, com **1 ambiguidade de escala**
- Risco geral da base demo: **medio**

## 1) Coerencia entre dados do backend e as 3 visualizacoes

Evidencias principais:
- 10 alunos ativos no Centro.
- 10 itens na Matriz (`filter=all`).
- 3 eixos no Radar para todos os alunos.
- Todos os alunos com:
  - enrollment ativo
  - 6 medições (2 por pilar)
  - 5 checkpoints

Consistencia operacional observada:
- `programName` uniforme na base inteira.
- `day <= total_days` em todos os enrollments.
- `daysLeft` coerente com janela de renovacao.
- `urgency` derivada pelo backend bate com a intencao geral dos perfis.

Diagnostico: **coerente** para demonstracao end-to-end.

## 2) Distribuicao para a Matriz

Distribuicao atual:
- `topRight`: 4
- `topLeft`: 2
- `bottomLeft`: 2
- `bottomRight`: 2

Filtros de negocio:
- `all`: 10
- `topRight`: 4
- `critical` (D-45 + topRight): 2
- `rescue`: 2

Leitura:
- Ha massa suficiente para todos os filtros da Matriz.
- A distribuicao evita concentracao em um unico quadrante.

Diagnostico: **suficiente e bem distribuida**.

## 3) Historias dos alunos (diferentes e plausiveis)

Pontos fortes:
- Campeoes e estrategicos de LTV aparecem com alto progresso/engajamento.
- Casos de resgate aparecem com engajamento muito baixo e sinais fortes de risco.
- Risco silencioso e promissores mal aproveitados aparecem em quadrantes distintos (`bottomLeft` vs `topLeft`).

Pontos de atencao:
- Os quatro perfis nao positivos (risco silencioso + promissores + resgate) ficaram com `anomaly_count = 6` em bloco, o que reduz nuance narrativa.
- Campeoes e estrategicos de LTV estao muito proximos em padrao numerico (diferenca pequena de historia operacional).

Diagnostico: **plausivel**, mas com margem para maior diferenciacao narrativa.

## 4) Coerencia de evolucao no Radar

Pontos fortes:
- Todos os alunos possuem 3 eixos.
- Tendencias esperadas:
  - campeoes/ltv: `avgCurrent > avgBaseline`
  - risco/resgate: `avgCurrent < avgBaseline`
  - `avgProjected >= avgCurrent` em todos os casos (coerente com simulacao de proximo ciclo)

Ponto critico:
- O eixo de disciplina mistura metricas de unidade diferente:
  - `%` (ritmo de entregas)
  - `dias` (atraso medio)
- Como o Radar faz media numerica simples por pilar, ha mistura semantica de unidades no mesmo score.

Diagnostico: **coerente no macro**, com **inconsistencia estrutural de unidade**.

## 5) KPIs do Hub e do Centro

Valores auditados:
- Centro:
  - ativos: 10
  - alertas de resgate: 2
  - D-45: 4
  - LTV monitorado (soma): 243500
- Matriz/KPIs:
  - totalLTV: 243500
  - criticalRenewals: 2
  - rescueCount: 2
  - avgEngagement: 59.5

Coerencia:
- Os numeros fazem sentido entre Centro, Matriz e Hub.
- O Hub recalcula KPIs da matriz a partir dos itens (escala 0..1), enquanto a API da Matriz retorna `avgEngagement` em 0..100.
- A UI atual trata essa diferenca, mas a coexistencia de duas escalas aumenta risco de regressao futura.

Diagnostico: **coerente para demo atual**, com **ambiguidade de escala**.

## 6) Valores estranhos, inconsistencias e narrativas fracas

| ID | Achado | Impacto | Risco |
|---|---|---|---|
| DDA-01 | Mistura de unidade no Radar (`%` e `dias` no mesmo eixo). | Pode distorcer leitura de score por pilar. | Alto |
| DDA-02 | `avgEngagement` usa escalas diferentes entre backend (0..100) e derivacao do Hub (0..1). | Risco de exibicao incorreta em evolucoes futuras. | Medio |
| DDA-03 | Alunos nao positivos concentram `anomaly_count=6` (padrao muito uniforme). | Narrativa perde nuance e realismo. | Medio |
| DDA-04 | `currentWeek` pode ficar maior que `lastWeek` no resumo da timeline (ex.: std_9). | Pequena incoerencia visual/semantica em leitura de progresso. | Baixo |
| DDA-05 | `critical` de urgencia nao aparece na coorte (somente `normal/watch/rescue`). | Menor variedade para demonstrar a faixa intermediaria de risco alto. | Baixo |
| DDA-06 | Nome tecnico `ltv_cents` segue semantica de inteiro BRL (nao centavos reais). | Pode gerar interpretacao errada em integracoes futuras. | Medio |

## Recomendacoes (somente dados, sem novas features)

1. Ajustar a base de metricas para evitar mistura de unidade dentro do mesmo pilar exibido no Radar.
2. Tornar explicita uma unica escala de engajamento para KPI agregado na base de demo (ou documentar claramente a conversao).
3. Diversificar anomalias dos perfis intermediarios:
   - nem todos com 6 anomalias
   - usar combinacoes de checkpoint amarelo/vermelho mais graduais
4. Ajustar alguns `day`/checkpoints para evitar `currentWeek > lastWeek` em casos de demonstracao.
5. Incluir 1-2 alunos em estado `critical` (sem virar `rescue`) para ampliar cobertura narrativa.
6. Documentar no roteiro da demo que `ltv_cents` esta sendo usado como valor nominal na visualizacao atual.

## Conclusao

A base simulada esta **apta para demonstracao** e cobre bem as 3 visualizacoes com distribuicao util de casos.  
Os principais riscos nao estao em falta de dados, e sim em **consistencia semantica** (unidades/escala) e em **refino narrativo** (granularidade de anomalias entre perfis).
