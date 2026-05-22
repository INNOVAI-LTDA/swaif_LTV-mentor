# Radar de Transformacao - contratos aparentes (engenharia reversa inicial)

## 1) Visualizacao e papel
- Visualizacao: `Radar de Transformacao`.
- Papel: comparar baseline vs estado atual e projecao de ciclo seguinte nos eixos/pilares do metodo, com slider de simulacao.
- Evidencias: `origin/radar-longevidade.jsx` e modulo `RadarModule` em `origin/jpe-hub.jsx`.

## 2) Fontes de dados aparentes
- Contexto do aluno:
  - standalone: `useStudents()` e selecao do primeiro item.
  - hub: `studentId` vem da selecao global.
- Dados do radar:
  - standalone: `useStudentRadar(studentId)`
  - hub: `useClientRadar(studentId)`

## 3) Contratos de dados aparentes

### 3.1 Estrutura principal do radar
Contrato inferido:
```json
{
  "axisScores": [
    {
      "axisKey": "string",
      "axisLabel": "string",
      "axisSub": "string",
      "baseline": "number|string",
      "current": "number|string",
      "projected": "number|string",
      "insight": "string"
    }
  ]
}
```

Notas:
- `baseline`, `current`, `projected` chegam como string em varios trechos e sao convertidos com `parseFloat`.
- `projected` tem fallback para `current` no backend quando ausente na origem.
- `axisSub` pode vir vazio.
- `insight` e obrigatorio no contrato v1 atual (`axisScores[].insight`).

### 3.2 Derivacoes usadas pela UI
- `active[i] = current[i] + (projected[i] - current[i]) * (slider/100)`
- `avgBaseline`, `avgCurrent`, `avgProjected`
- `activeScore = avgCurrent + (avgProjected - avgCurrent) * (slider/100)`
- `delta eixo = active[i] - baseline[i]`

## 4) Dados resumidos vs detalhados (nesta visao)
- Resumidos:
  - quantidade de eixos
  - score medio agregado
  - delta total contra baseline
- Detalhados:
  - valor por eixo (baseline, atual, projetado)
  - subtitulo por eixo (`axisSub`)
  - variação por eixo (`+N pts`)
  - narrativas de projecao para ciclo seguinte

## 5) Ambiguidades/inconsistencias observadas
- Nomenclatura de hooks inconsistente: `useStudentRadar` vs `useClientRadar`.
- Entidade base varia (`student`, `client`, `patient`) entre arquivos.
- No standalone, o radar fixa no primeiro aluno (`studentList[0]`), sem seletor explicito.
- Imports/estado potencialmente legados no standalone (`recharts`, `activePillar`, `radarLoading`) nao dirigem o fluxo final.
- O texto visual fala em "7 pilares", mas o contrato real e dinamico por `axisScores.length`.
