# Matriz de Renovacao Antecipada - contratos aparentes (engenharia reversa inicial)

## 1) Visualizacao e papel
- Visualizacao: `Matriz de Renovacao Antecipada`.
- Papel: posicionar alunos por `progresso x engajamento`, priorizando renovacao, resgate e oportunidade de receita.
- Evidencias: `origin/matriz-renovacao.jsx` e modulo `MatrizModule` em `origin/jpe-hub.jsx`.

## 2) Fontes de dados aparentes
- Lista de alunos:
  - standalone: `useStudents()`
  - hub: `useClients()`
- Sem endpoint de detalhe dedicado nesta tela; o drawer usa dados do proprio item selecionado.

## 3) Contratos de dados aparentes

### 3.1 Item para plotagem na matriz
Campos usados para bolha, filtros e KPI:
- `id`
- `name`
- `initials`
- `programName` (em alguns pontos aparece `plan`)
- `progress` (0..1)
- `engagement` (0..1)
- `daysLeft`
- `urgency` (`critical|watch|rescue|normal`)
- `ltv`
- `renewalReason`
- `suggestion`
- `markers[]` (detalhe lateral/drawer)

Contrato inferido:
```json
{
  "id": "string|number",
  "name": "string",
  "initials": "string",
  "programName": "string",
  "plan": "string",
  "progress": 0.73,
  "engagement": 0.52,
  "daysLeft": 38,
  "urgency": "watch",
  "ltv": 15600,
  "renewalReason": "string",
  "suggestion": "string",
  "markers": [
    {
      "label": "string",
      "value": "string",
      "target": "string",
      "pct": 74,
      "improving": true
    }
  ]
}
```

### 3.2 Regras de classificacao (quadrantes)
- `topRight`: `progress >= 0.6` e `engagement >= 0.6`
- `topLeft`: `progress < 0.6` e `engagement >= 0.6`
- `bottomRight`: `progress >= 0.6` e `engagement < 0.6`
- `bottomLeft`: caso restante

### 3.3 Agregacoes/KPIs
- `totalLTV = soma(ltv)`
- `criticalRenewals = count(daysLeft <= 45 && quadrante == topRight)`
- `rescueCount = count(urgency == rescue)`
- `avgEngagement = media(engagement) * 100`

## 4) Dados resumidos vs detalhados (nesta visao)
- Resumidos:
  - bolha por aluno (posicao e estado)
  - KPIs de topo (LTV, D-45, resgate, media de engajamento)
  - filtros rapidos (`all`, `topRight`, `critical`, `rescue`)
- Detalhados:
  - drawer/painel com motivo de renovacao (`renewalReason`)
  - sugestao de plano (`suggestion`)
  - barras de indicadores (`markers[]`)
  - composicao da posicao na matriz (progresso e engajamento)

## 5) Ambiguidades/inconsistencias observadas
- Campo de programa alterna entre `programName` e `plan`.
- A legenda usa linguagem clinica, mas o topo tambem fala em "alunos" (mistura de dominios).
- Status `critical` e desenhado com cor de alta performance (verde), podendo conflitar com semantica de "critico".
- O arquivo contem bloco `_REMOVED` com contrato legado (idade, risco, bioAgeDelta, pilares) que nao esta totalmente refletido no fluxo ativo.
