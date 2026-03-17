# Backend Readiness for Frontend (Marco 9)

Data da revisao: 2026-03-09 (atualizado)

## 0) Resumo objetivo
- Estado atual: backend funcional para o fluxo MVP principal (auth + onboarding administrativo + 3 visoes).
- Evidencia de estabilidade: `python -m pytest tests -q --basetemp .tmp_pytest_full` com `53 passed`.
- Nivel geral para integracao: **alto para fluxo core**, com alguns pontos ainda **parciais** para uma integracao frontend "completa" (multi-origem, UX admin extensa e contratos auxiliares).

## 1) Endpoints ja implementados

| Metodo | Endpoint | Auth | Status principal |
|---|---|---|---|
| GET | `/health` | Nao | 200 |
| POST | `/auth/login` | Nao | 200, 401, 422 |
| GET | `/me` | Bearer | 200, 401 |
| POST | `/admin/mentorias` | Bearer admin | 201, 401, 403, 409, 422 |
| POST | `/admin/mentores` | Bearer admin | 201, 401, 403, 409, 422 |
| POST | `/admin/mentorias/{organization_id}/vincular-mentor` | Bearer admin | 200, 401, 403, 404, 422 |
| GET | `/admin/mentorias/{organization_id}` | Bearer admin | 200, 401, 403, 404 |
| POST | `/admin/protocolos` | Bearer admin | 201, 401, 403, 409, 422 |
| POST | `/admin/pilares` | Bearer admin | 201, 401, 403, 404, 409, 422 |
| POST | `/admin/metricas` | Bearer admin | 201, 401, 403, 404, 409, 422 |
| GET | `/admin/protocolos/{protocol_id}/estrutura` | Bearer admin | 200, 401, 403, 404 |
| POST | `/admin/alunos` | Bearer admin | 201, 401, 403, 409, 422 |
| POST | `/admin/alunos/{student_id}/vincular-mentoria` | Bearer admin | 200, 401, 403, 404, 409, 422 |
| GET | `/admin/mentorias/{organization_id}/alunos` | Bearer admin | 200, 401, 403, 404 |
| POST | `/admin/alunos/{student_id}/indicadores/carga-inicial` | Bearer admin | 200, 401, 403, 404, 422 |
| GET | `/admin/alunos/{student_id}/detalhe` | Bearer admin | 200, 401, 403, 404 |
| GET | `/admin/centro-comando/alunos` | Bearer admin | 200, 401, 403 |
| GET | `/admin/centro-comando/alunos/{student_id}` | Bearer admin | 200, 401, 403, 404 |
| GET | `/admin/centro-comando/alunos/{student_id}/timeline-anomalias` | Bearer admin | 200, 401, 403, 404 |
| GET | `/admin/radar/alunos/{student_id}` | Bearer admin | 200, 401, 403, 404 |
| GET | `/admin/matriz-renovacao?filter=all|topRight|critical|rescue` | Bearer admin | 200, 401, 403 |

## 2) Contratos atuais de request/response

## 2.1 Contrato de erro padrao (global)

```json
{
  "error": {
    "status": 409,
    "code": "MENTORIA_CONFLICT",
    "message": "Ja existe mentoria com este slug.",
    "details": null
  }
}
```

Codigos de status padronizados no hardening: `401`, `404`, `409`, `422`.

## 2.2 Auth

- `POST /auth/login`
  - Request:
  ```json
  { "email": "admin@swaif.local", "password": "admin123" }
  ```
  - Response 200:
  ```json
  { "access_token": "string", "token_type": "bearer" }
  ```

- `GET /me`
  - Header: `Authorization: Bearer <token>`
  - Response 200:
  ```json
  { "id": "usr_admin", "email": "admin@swaif.local", "role": "admin" }
  ```

## 2.3 Admin de mentoria/mentor

- `POST /admin/mentorias`
  - Request: `{ "name": "Mentoria X", "slug": "mentoria-x" }`
  - Response: `{ "id", "name", "slug", "mentor_id", "is_active" }`

- `POST /admin/mentores`
  - Request: `{ "full_name": "Nome", "email": "mentor@swaif.local" }`
  - Response: `{ "id", "full_name", "email", "is_active", "organization_id" }`

- `POST /admin/mentorias/{organization_id}/vincular-mentor`
  - Request: `{ "mentor_id": "mtr_1" }`
  - Response: `OrganizationOut`

- `GET /admin/mentorias/{organization_id}`
  - Response: organization + campo `mentor` embutido (ou `null`).

## 2.4 Admin de metodo (protocolo/pilar/metrica)

- `POST /admin/protocolos`
  - Request: `{ "organization_id", "name", "code?", "metadata?" }`
  - Response: `{ "id", "organization_id", "name", "code", "metadata", "is_active" }`

- `POST /admin/pilares`
  - Request: `{ "protocol_id", "name", "code?", "order_index?", "metadata?" }`
  - Response: `{ "id", "protocol_id", "name", "code", "order_index", "metadata", "is_active" }`

- `POST /admin/metricas`
  - Request: `{ "protocol_id", "pillar_id", "name", "code?", "direction?", "unit?", "metadata?" }`
  - Response: `{ "id", "protocol_id", "pillar_id", "name", "code", "direction", "unit", "metadata", "is_active" }`

- `GET /admin/protocolos/{protocol_id}/estrutura`
  - Response:
  ```json
  {
    "protocol": { "...": "ProtocolOut" },
    "pillars": [
      { "...": "PillarOut", "metrics": [{ "...": "MetricOut" }] }
    ]
  }
  ```

## 2.5 Admin de alunos e carga de indicadores

- `POST /admin/alunos`
  - Request: `{ "full_name", "initials?", "email?" }`
  - Response: `{ "id", "full_name", "initials", "email", "status", "is_active" }`

- `POST /admin/alunos/{student_id}/vincular-mentoria`
  - Request: `{ "organization_id", "progress_score", "engagement_score", "urgency_status?", "day?", "total_days?", "days_left?", "ltv_cents?" }`
  - Response: `{ "id", "student_id", "organization_id", "progress_score", "engagement_score", "urgency_status", "day", "total_days", "days_left", "ltv_cents", "is_active" }`

- `GET /admin/mentorias/{organization_id}/alunos`
  - Response: lista de enrollment + objeto `student`.

- `POST /admin/alunos/{student_id}/indicadores/carga-inicial`
  - Request:
  ```json
  {
    "metric_values": [
      {
        "metric_id": "met_1",
        "value_baseline": 50,
        "value_current": 60,
        "value_projected": 70,
        "improving_trend": true
      }
    ],
    "checkpoints": [
      { "week": 1, "status": "green", "label": "Inicio" }
    ]
  }
  ```
  - Response: `{ "student_id", "enrollment_id", "measurement_count", "checkpoint_count" }`

## 2.6 Contratos das 3 visoes

- `GET /admin/centro-comando/alunos`
  - Item: `{ id, name, programName, urgency, risk, daysLeft, day, totalDays, engagement, progress, d45, hormoziScore, ltv }`

- `GET /admin/centro-comando/alunos/{student_id}`
  - Campos do resumo +:
  - `metricValues[]`: `{ id, metricLabel, valueCurrent, valueBaseline, valueProjected, improvingTrend, unit, optimal }`
  - `checkpoints[]`: `{ id, week, status, label }`

- `GET /admin/radar/alunos/{student_id}`
  - `{ studentId, axisScores[], avgBaseline, avgCurrent, avgProjected }`
  - `axisScores[]`: `{ axisKey, axisLabel, axisSub, baseline, current, projected, insight }`

- `GET /admin/centro-comando/alunos/{student_id}/timeline-anomalias`
  - `{ studentId, timeline[], anomalies[], summary }`
  - `timeline[]`: `{ week, label, status, anomaly }`
  - `anomalies[]`: `{ marker, value, ref, cause, action }`
  - `summary`: `{ anomalyCount, hasAnomalies, currentWeek, lastWeek }`

- `GET /admin/matriz-renovacao`
  - `{ filter, items[], kpis }`
  - `items[]`: `{ id, name, initials, programName, plan, progress, engagement, daysLeft, urgency, ltv, renewalReason, suggestion, markers, quadrant }`
  - `kpis`: `{ totalLTV, criticalRenewals, rescueCount, avgEngagement }`

## 3) Modelos e calculos ja disponiveis

## 3.1 Modelos persistidos (JSON)
- `users`: `id, email, password_hash, role, is_active`
- `organizations`: `id, name, slug, mentor_id, is_active`
- `mentors`: `id, full_name, email, organization_id, is_active`
- `protocols`: `id, organization_id, name, code, metadata, is_active`
- `pillars`: `id, protocol_id, name, code, order_index, metadata, is_active`
- `metrics`: `id, protocol_id, pillar_id, name, code, direction, unit, metadata, is_active`
- `students`: `id, full_name, initials, email, status, is_active`
- `enrollments`: `id, student_id, organization_id, progress_score, engagement_score, urgency_status, day, total_days, days_left, ltv_cents, is_active`
- `measurements`: `id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend`
- `checkpoints`: `id, enrollment_id, week, status, label`

## 3.2 Calculos de negocio implementados
- `progress`: `day/total_days` (fallback para `progress_score` se `total_days == 0`).
- `urgency`: regra por `engagement` e `days_left` (`normal|watch|critical|rescue`).
- `risk`: derivado de `urgency` (`low|medium|high`).
- `d45`: `days_left <= 45`.
- `hormoziScore`: `(progress * 0.4 + engagement * 0.6) * 100`, clamp `0..100`.
- `quadrant` matriz: `topRight|topLeft|bottomRight|bottomLeft`.
- KPIs matriz: `totalLTV`, `criticalRenewals`, `rescueCount`, `avgEngagement`.
- Radar: agregacao por pilar com medias `baseline/current/projected`.
- Fallback radar: `projected = current` quando ausente.
- Persistencia JSON: escrita atomica + lock por arquivo (concorrencia basica).

## 4) Lacunas que ainda impedem integracao completa com o front

1. **Superficie de API admin ainda minimalista**:
- Ha criacao e alguns detalhes, mas faltam listagens/edicao/exclusao para varios agregados (mentorias, mentores, protocolos, pilares, metricas, alunos) se o frontend administrativo exigir CRUD completo.

2. **Contrato de estrutura do metodo sem schema dedicado**:
- `GET /admin/protocolos/{protocol_id}/estrutura` retorna `dict` (sem `response_model` Pydantic), reduzindo garantias de tipagem/documentacao OpenAPI para o front.

3. **Token/auth para producao ainda basico**:
- Sem refresh token, sem revogacao/logout e sem fluxo de usuario externo. Para ambiente produtivo com frontend publico, isso tende a ser insuficiente.

## 5) Classificacao (pronto, parcial, pendente)

## 5.1 Pronto para uso
- Auth basica (`/auth/login`, `/me`) com protecao Bearer.
- Fluxo admin core: criar mentoria/mentor/metodo/aluno, vinculos e carga inicial.
- Endpoints de visao consumiveis por frontend:
  - Centro (`/admin/centro-comando/*`)
  - Radar (`/admin/radar/alunos/{student_id}`)
  - Matriz (`/admin/matriz-renovacao`)
- Padrao de erro unificado (`401/404/409/422`).
- Estabilidade de regressao atual (`53 passed`).

## 5.2 Parcial
- API administrativa para operacao completa de backoffice (faltam rotas de manutencao ampla).
- Contrato de estrutura de metodo (funcional, mas sem schema tipado dedicado).
- Seguranca de sessao para escala/producao (somente fluxo basico).

## 5.3 Pendente
- Plano formal de versionamento de API e governance de contratos OpenAPI para evolucao com frontend.
