# Centro de Comando - contratos aparentes (engenharia reversa inicial)

## 1) Visualizacao e papel
- Visualizacao: `Centro de Comando`.
- Papel: monitorar a jornada ativa dos alunos por excecao, destacando risco (`urgency`), janela de renovacao (`daysLeft <= 45`) e progresso do ciclo.
- Evidencias: `origin/jpe-command-center.jsx` e modulo `CommandoModule` em `origin/jpe-hub.jsx`.

## 2) Fontes de dados aparentes
- Lista resumida: `useStudents()` (arquivo dedicado) ou `useClients()` (hub).
- Detalhe do aluno: `useStudentDetail(selectedId)` (arquivo dedicado).
- Estado local de UI: selecao do aluno, popup de anomalia, hora atual.

## 3) Contratos de dados aparentes

### 3.1 Item da lista (resumo)
Campos usados no grid principal:
- `id`
- `name`
- `programName`
- `urgency` (`rescue`, `watch`, `critical`, `normal` ou equivalente)
- `daysLeft`
- `day`
- `totalDays`
- `engagement` (0..1)
- `progress` (0..1, usado no hub)
- `hormoziScore` (mostrado no painel lateral em algumas variacoes)

Contrato inferido:
```json
{
  "id": "string|number",
  "name": "string",
  "programName": "string",
  "urgency": "rescue|watch|critical|normal",
  "daysLeft": 45,
  "day": 30,
  "totalDays": 180,
  "engagement": 0.72,
  "progress": 0.55,
  "hormoziScore": 63
}
```

### 3.2 Detalhe do aluno (painel direito)
Campos adicionais usados:
- `metricValues[]` com:
  - `id`
  - `metricLabel`
  - `valueCurrent`
  - `valueBaseline`
  - `improvingTrend` (opcional)
  - `unit` (opcional)
  - `optimal` (opcional)
- `checkpoints[]` com:
  - `id`
  - `week`
  - `status` (`green|yellow|red`)
  - `label` (opcional)

Contrato inferido:
```json
{
  "id": "string|number",
  "name": "string",
  "programName": "string",
  "day": 30,
  "totalDays": 180,
  "daysLeft": 150,
  "urgency": "watch",
  "engagement": 0.72,
  "hormoziScore": 63,
  "metricValues": [
    {
      "id": "string|number",
      "metricLabel": "string",
      "valueCurrent": "number|string",
      "valueBaseline": "number|string",
      "improvingTrend": true,
      "unit": "string",
      "optimal": "string"
    }
  ],
  "checkpoints": [
    {
      "id": "string|number",
      "week": 4,
      "status": "green|yellow|red",
      "label": "string"
    }
  ]
}
```

### 3.3 Objeto de anomalia (modal)
Contrato exposto por backend (`anomalies[]` e `timeline[].anomaly`):
```json
{
  "marker": "string",
  "value": "string|number",
  "ref": "string",
  "cause": "string",
  "action": "string"
}
```

### 3.4 Endpoint dedicado de timeline/anomalias
Contrato atual:
```json
{
  "studentId": "string|number",
  "timeline": [
    {
      "week": 4,
      "label": "string",
      "status": "green|yellow|red",
      "anomaly": {
        "marker": "string",
        "value": "string|number",
        "ref": "string",
        "cause": "string",
        "action": "string"
      }
    }
  ],
  "anomalies": [
    {
      "marker": "string",
      "value": "string|number",
      "ref": "string",
      "cause": "string",
      "action": "string"
    }
  ],
  "summary": {
    "anomalyCount": 1,
    "hasAnomalies": true,
    "currentWeek": 5,
    "lastWeek": 8
  }
}
```

## 4) Dados resumidos vs detalhados (nesta visao)
- Resumidos:
  - contagem de ativos, alertas, D-45
  - status por cor e tags
  - progresso do ciclo na linha
- Detalhados:
  - evolucao por metrica (`metricValues`)
  - checkpoints semanais
  - score de valor (Hormozi) e textos de acao para renovacao

## 5) Ambiguidades/inconsistencias observadas
- `getBioAgeDelta` retorna percentual de `engagement`, nao delta de idade biologica.
- Componente `Timeline` (com `segments` e anomalias) existe, mas nao aparece conectado ao fluxo principal da lista.
- `MARKER_CONFIG` esta definido, mas nao participa do render atual.
- Terminologia varia entre `patients` (UI) e `students` (hook), o que pode gerar contrato semantico confuso.
