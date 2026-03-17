# Frontend x Backend Gap Analysis (Marco 9)

Data: 2026-03-09 (atualizado)

Base de comparacao:
- `docs/mvp-mentoria/backend-readiness-for-frontend.md`
- `docs/mvp-mentoria/contracts-command-center.md`
- `docs/mvp-mentoria/contracts-radar.md`
- `docs/mvp-mentoria/contracts-renewal-matrix.md`

## 1) Centro de Comando

## 1.1 Campos ja atendidos
- Lista (`GET /admin/centro-comando/alunos`):
  - `id`, `name`, `programName`, `urgency`, `daysLeft`, `day`, `totalDays`, `engagement`, `progress`, `hormoziScore`
  - Extras disponiveis: `risk`, `d45`, `ltv`
- Detalhe (`GET /admin/centro-comando/alunos/{student_id}`):
  - `metricValues[]`: `id`, `metricLabel`, `valueCurrent`, `valueBaseline`, `valueProjected`, `improvingTrend`, `unit`, `optimal`
  - `checkpoints[]`: `id`, `week`, `status`, `label`

## 1.2 Campos faltantes
- Sem lacuna de contrato para o fluxo principal:
  - Endpoint dedicado disponivel em `GET /admin/centro-comando/alunos/{student_id}/timeline-anomalias`.
  - Payload com `timeline[]`, `anomalies[]` e `summary` cobre o modal de anomalia.

## 1.3 Nomes inconsistentes
- Front usa variacoes `students/clients/patients`; backend usa `alunos/students`.
- Backend usa rota em portugues (`/admin/centro-comando/alunos`) e IDs internos `student_id`; hooks do front podem usar nomenclatura `client`.

## 1.4 Dados que dependem de calculo/transformacao
- `progress` e `engagement` chegam em escala `0..1` e precisam formatacao percentual no front.
- `ltv` chega numerico (derivado de `ltv_cents`) e precisa formatacao monetaria no front.
- Contadores de topo (ativos, alertas, D-45) nao tem endpoint dedicado; podem ser derivados da lista.

## 1.5 Adaptacoes recomendadas
- Frontend:
  - Criar adapter unico para normalizar `student/client/patient` -> `student`.
  - Centralizar formatacao de percentual e moeda.
  - Derivar KPIs de topo localmente enquanto nao houver endpoint agregado.

---

## 2) Radar de Transformacao

## 2.1 Campos ja atendidos
- Endpoint (`GET /admin/radar/alunos/{student_id}`):
  - `studentId`
  - `axisScores[]`: `axisKey`, `axisLabel`, `axisSub`, `baseline`, `current`, `projected`, `insight`
  - `avgBaseline`, `avgCurrent`, `avgProjected`
- Regra de fallback de `projected` ausente para `current` ja esta no backend.

## 2.2 Campos faltantes
- Sem lacuna de contrato para o fluxo principal.

## 2.3 Nomes inconsistentes
- Hooks de front citados no contrato: `useStudentRadar` e `useClientRadar`; backend padroniza em `studentId`.
- Rota usa `alunos`, enquanto parte do front pode usar semantica `client`.

## 2.4 Dados que dependem de calculo/transformacao
- Slider/simulacao continua sendo responsabilidade do front:
  - `active = current + (projected-current)*slider`
  - `activeScore`, deltas por eixo.
- Se front espera strings numericas, deve aceitar numero puro (backend retorna numero).

## 2.5 Adaptacoes recomendadas
- Frontend:
  - Unificar leitura de `studentId` mesmo para componentes legados `client`.
  - Manter fallback defensivo para `insight` em componentes legados.

---

## 3) Matriz de Renovacao Antecipada

## 3.1 Campos ja atendidos
- Endpoint (`GET /admin/matriz-renovacao`):
  - Topo: `kpis.totalLTV`, `kpis.criticalRenewals`, `kpis.rescueCount`, `kpis.avgEngagement`
  - Item: `id`, `name`, `initials`, `programName`, `plan`, `progress`, `engagement`, `daysLeft`, `urgency`, `ltv`, `renewalReason`, `suggestion`, `markers`, `quadrant`
  - Filtros suportados: `all`, `topRight`, `critical`, `rescue`

## 3.2 Campos faltantes
- Nao ha endpoint de detalhe dedicado (o contrato exploratorio tambem considera que o drawer usa o proprio item). Sem gap funcional direto aqui.

## 3.3 Nomes inconsistentes
- Campo de programa aparece em duplicidade (`programName` e `plan`), o que resolve compatibilidade, mas pede padrao unico no front.
- Semantica de `urgency=critical` pode conflitar com paleta visual legada (observacao do contrato exploratorio).

## 3.4 Dados que dependem de calculo/transformacao
- `ltv` precisa formatacao monetaria no front.
- `progress`/`engagement` em `0..1` precisam formatacao percentual.
- `markers.value/target` podem vir numericos; front legado pode tratar como string.

## 3.5 Adaptacoes recomendadas
- Frontend:
  - Escolher campo canonico para programa (`programName` recomendado) e tratar `plan` como alias.
  - Padronizar paleta/semantica visual de `urgency`.
- Backend:
  - Opcional: documentar explicitamente unidade de `ltv` (cents) no contrato publico.

---

## 4) Consolidado (o que falta para integracao completa)

## 4.1 Campos atendidos vs faltantes
- **Centro**: atendido no core, incluindo timeline/anomalias.
- **Radar**: atendido no core, incluindo `insight` por eixo.
- **Matriz**: atendido no core para bolha + KPI + filtros.

## 4.2 Inconsistencias de naming (prioridade alta)
- Entidade pessoa: `student/aluno/client/patient` (padronizar no adapter de front).
- Campo de programa: `programName` vs `plan` (definir canonico no front).

## 4.3 Dados que ainda exigem transformacao no front
- Percentuais: `progress`, `engagement`.
- Valor monetario: `ltv`.
- Agregados de topo no Centro: derivacao local a partir da lista (ate existir endpoint dedicado, se necessario).

---

## 5) Divisao objetiva de adaptacoes (Front vs Backend)

## 5.1 Fazer no Frontend
- Implementar camada de adaptacao de nomes (`client/patient` -> `student`).
- Padronizar campo de programa consumido (`programName`) e manter alias `plan`.
- Formatar percentuais e moeda.
- Tratar campos opcionais (`valueProjected`, `optimal`) com null-safety.
- Derivar contadores do Centro a partir da lista (curto prazo).

## 5.2 Fazer no Backend
- Sem bloqueador residual para as 3 visoes no contrato v1.
