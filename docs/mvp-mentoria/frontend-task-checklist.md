# Frontend Task Checklist (MVP Mentoria)

Data: 2026-03-09

## Regras de execucao
- [x] Executar em marcos pequenos (F0..F6), sem redesign
- [x] Preservar estrutura visual das 3 visoes
- [x] Tratar contratos v1 congelados como fonte tecnica
- [x] Nao fechar marco sem testes do marco + regressao frontend

## F0 - Preparacao tecnica
- [x] Mapear local real dos hooks e cliente HTTP usados pelo frontend
- [x] Definir variavel de ambiente `API_BASE_URL`
- [x] Configurar cliente HTTP unico com header `Authorization: Bearer <token>`
- [x] Configurar tratamento padrao do payload de erro `{ error: { status, code, message, details } }`
- [x] Validar login + chamada autenticada de smoke no ambiente local
- [x] Confirmar pre-condicao de CORS no ambiente backend usado pelo frontend

## F1 - Camada de adaptacao de dominio
- [x] Criar adapter unico de entidade para normalizar `patient/client/student` -> `student`
- [x] Padronizar campo de programa para consumo interno (`programName`), com fallback `plan`
- [x] Normalizar coercoes numericas (`parseFloat`) em camada de adapter (evitar parsing espalhado)
- [x] Criar utilitario de percentual para `progress` e `engagement`
- [x] Criar utilitario de moeda para `ltv`
- [x] Cobrir adapters/utilitarios com testes unitarios

## F2 - Integracao Centro de Comando
- [x] Integrar lista com `GET /admin/centro-comando/alunos`
- [x] Integrar detalhe com `GET /admin/centro-comando/alunos/{student_id}`
- [x] Garantir selecao inicial de aluno sem dependencias de mock
- [x] Implementar estados de loading/empty/error para lista e detalhe
- [x] Derivar KPIs de topo no frontend (ativos, alertas, D-45) a partir da lista
- [x] Tratar ausencia de anomalia/timeline sem quebrar UX
- [x] Revisar labels de dominio (aluno/mentoria/mentor) sem alterar layout

## F3 - Integracao Radar de Transformacao
- [x] Integrar com `GET /admin/radar/alunos/{student_id}`
- [x] Mapear `axisScores` para modelo interno estavel (`axisKey`, `axisLabel`, `axisSub`, `baseline`, `current`, `projected`)
- [x] Aplicar fallback `projected <- current` quando ausente
- [x] Tratar `insight` como opcional
- [x] Validar calculos de simulacao do slider (`active`, medias, deltas)
- [x] Revisar copy para mentoria mantendo hierarquia visual

## F4 - Integracao Matriz de Renovacao Antecipada
- [x] Integrar com `GET /admin/matriz-renovacao` e query `filter`
- [x] Garantir filtros `all|topRight|critical|rescue` conectados ao backend
- [x] Validar KPIs de topo com dados reais (`totalLTV`, `criticalRenewals`, `rescueCount`, `avgEngagement`)
- [x] Garantir drawer com campos `renewalReason`, `suggestion`, `markers`
- [x] Compatibilizar `programName` e `plan` sem duplicar render
- [x] Revisar semantica visual de `urgency` (critical/watch/rescue/normal) sem redesign

## F5 - Migracao de linguagem (clinica -> mentoria)
- [x] Criar lista de termos proibidos/permitidos baseada em `naming-and-domain-notes.md`
- [x] Revisar strings de Centro de Comando
- [x] Revisar strings de Radar
- [x] Revisar strings de Matriz
- [x] Revisar strings do Hub e CTAs auxiliares
- [x] Revisar mensagens de erro e vazios com linguagem de mentoria

## F6 - Hardening de integracao frontend
- [x] Garantir tratamento consistente de `401/403/404/409/422`
- [x] Garantir fluxo de logout ao detectar token invalido/expirado
- [x] Instrumentar logs minimos de falha de rede/contrato
- [x] Validar regressao das 3 visoes em ambiente integrado
- [x] Executar suite de testes frontend (unit + integracao + e2e)
- [x] Registrar evidencias finais de integracao (comandos e resultados)

## Dependencias residuais de backend (acompanhamento)
- [x] CORS habilitado para origem do frontend em ambiente alvo
- [x] Decisao sobre endpoint de anomalia/timeline do Centro (se obrigatorio)
- [x] Decisao sobre campo `insight` no Radar (se obrigatorio)

## Gate final de pronto
- [x] Centro de Comando operando com dados reais sem erro de contrato
- [x] Radar operando com slider e agregados corretos
- [x] Matriz operando com bolhas, filtros, KPIs e drawer corretos
- [x] Linguagem de mentoria aplicada nas 3 visoes
- [x] Nenhuma mudanca estrutural de interface introduzida

## Evidencias F0 (2026-03-09)
- [x] Smoke auth backend local: `node origin/scripts/f0-smoke-auth.mjs` (com backend local em `http://127.0.0.1:8000`) -> `PASS` com `/me` retornando `usr_admin`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.
- [x] Pre-condicao CORS confirmada como pendente no backend atual: `backend/app/main.py` sem `CORSMiddleware`.

## Evidencias F1 (2026-03-09)
- [x] Runner unitario de adapters + formatters: `node origin/tests/unit/f1-unit-runner.mjs` -> `F1 unit runner: PASS`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.

## Evidencias F2 (2026-03-09)
- [x] Integracao Centro com estados resilientes (lista + detalhe), selecao estavel e KPIs derivados em `origin/jpe-command-center.jsx` usando `origin/lib/commandCenterUtils.js`.
- [x] Runner unitario F2: `node origin/tests/unit/f2-command-center-runner.mjs` -> `F2 command center runner: PASS`.
- [x] Regressao F1 apos mudancas de F2: `node origin/tests/unit/f1-unit-runner.mjs` -> `F1 unit runner: PASS`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.

## Evidencias F3 (2026-03-09)
- [x] Hardening do Radar em `origin/radar-longevidade.jsx` e `origin/jpe-hub.jsx` com estados de loading/error/empty, simulacao centralizada e fallback de `insight`.
- [x] Utilitarios do Radar adicionados em `origin/lib/radarUtils.js` (`normalizeRadarAxisScores`, `simulateRadar`, `getRadarInsight`).
- [x] Runner unitario F3: `node origin/tests/unit/f3-radar-runner.mjs` -> `F3 radar runner: PASS`.
- [x] Regressao F2 apos mudancas de F3: `node origin/tests/unit/f2-command-center-runner.mjs` -> `F2 command center runner: PASS`.
- [x] Regressao F1 apos mudancas de F3: `node origin/tests/unit/f1-unit-runner.mjs` -> `F1 unit runner: PASS`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.

## Evidencias F4 (2026-03-09)
- [x] Integracao da Matriz com filtro remoto em `origin/matriz-renovacao.jsx` e `origin/jpe-hub.jsx` usando `origin/hooks/useRenewalMatrix.js` + `origin/services/matrixService.js`.
- [x] Utilitarios da Matriz adicionados em `origin/lib/matrixUtils.js` (`normalizeMatrixFilter`, `matrixQuadrant`, `deriveMatrixKpis`, `resolveMatrixKpis`).
- [x] Runner unitario F4: `node origin/tests/unit/f4-matrix-runner.mjs` -> `F4 matrix runner: PASS`.
- [x] Regressao F3 apos mudancas de F4: `node origin/tests/unit/f3-radar-runner.mjs` -> `F3 radar runner: PASS`.
- [x] Regressao F2 apos mudancas de F4: `node origin/tests/unit/f2-command-center-runner.mjs` -> `F2 command center runner: PASS`.
- [x] Regressao F1 apos mudancas de F4: `node origin/tests/unit/f1-unit-runner.mjs` -> `F1 unit runner: PASS`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.

## Evidencias F5 (2026-03-09)
- [x] Lexico de mentoria criado em `docs/mvp-mentoria/frontend-mentoria-lexicon.md` com termos proibidos/permitidos e regras de uso.
- [x] Migracao de copy aplicada sem alterar layout em `origin/jpe-command-center.jsx`, `origin/radar-longevidade.jsx`, `origin/matriz-renovacao.jsx` e `origin/jpe-hub.jsx`.
- [x] Runner unitario F5 (linguagem): `node origin/tests/unit/f5-copy-runner.mjs` -> `F5 copy runner: PASS`.
- [x] Regressao F4 apos mudancas de F5: `node origin/tests/unit/f4-matrix-runner.mjs` -> `F4 matrix runner: PASS`.
- [x] Regressao F3 apos mudancas de F5: `node origin/tests/unit/f3-radar-runner.mjs` -> `F3 radar runner: PASS`.
- [x] Regressao F2 apos mudancas de F5: `node origin/tests/unit/f2-command-center-runner.mjs` -> `F2 command center runner: PASS`.
- [x] Regressao F1 apos mudancas de F5: `node origin/tests/unit/f1-unit-runner.mjs` -> `F1 unit runner: PASS`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.

## Evidencias F6 (2026-03-09)
- [x] Hardening de erro HTTP em `origin/lib/errors.js` com mapeamento consistente para `401/403/404/409/422`.
- [x] Logout automatico em `401` com evento global em `origin/lib/httpClient.js` + `origin/lib/httpEvents.js` + assinatura no `origin/contexts/AuthContext.jsx`.
- [x] Instrumentacao minima de falha HTTP/contrato/recurso em `origin/lib/integrationLogger.js`, `origin/hooks/useAsyncResource.js` e services de Centro/Radar/Matriz.
- [x] Runner unitario F6: `node origin/tests/unit/f6-hardening-runner.mjs` -> `F6 hardening runner: PASS`.
- [x] Runner de integracao F6: `node origin/tests/integration/f6-integration-runner.mjs` -> `F6 integration runner: PASS`.
- [x] Runner de smoke e2e F6: `node origin/tests/e2e/f6-smoke-flow-runner.mjs` -> `F6 e2e smoke runner: PASS`.
- [x] Regressao F5 apos mudancas de F6: `node origin/tests/unit/f5-copy-runner.mjs` -> `F5 copy runner: PASS`.
- [x] Regressao F4 apos mudancas de F6: `node origin/tests/unit/f4-matrix-runner.mjs` -> `F4 matrix runner: PASS`.
- [x] Regressao F3 apos mudancas de F6: `node origin/tests/unit/f3-radar-runner.mjs` -> `F3 radar runner: PASS`.
- [x] Regressao F2 apos mudancas de F6: `node origin/tests/unit/f2-command-center-runner.mjs` -> `F2 command center runner: PASS`.
- [x] Regressao F1 apos mudancas de F6: `node origin/tests/unit/f1-unit-runner.mjs` -> `F1 unit runner: PASS`.
- [x] Regressao minima de imports dos entry points: checagem automatica dos imports relativos em `origin/*.jsx` -> `Import regression check: PASS`.

## Evidencias - Dependencias residuais backend (2026-03-09)
- [x] CORS aplicado em `backend/app/main.py` via `CORSMiddleware`, com suporte a `CORS_ALLOW_ORIGINS` e defaults para ambientes locais de frontend (`:5173` e `:3000`).
- [x] Endpoint de timeline/anomalias disponibilizado: `GET /admin/centro-comando/alunos/{student_id}/timeline-anomalias` (rota em `backend/app/api/routes/admin_students.py` e service em `backend/app/services/indicator_carga_service.py`).
- [x] Campo `insight` decidido como obrigatorio no Radar e retornado em `axisScores[]` por `GET /admin/radar/alunos/{student_id}`.
- [x] Testes-alvo de validacao: `Set-Location backend; $env:PYTHONPATH='.vendor'; python -m pytest tests/test_health.py tests/api/test_command_center_api.py tests/api/test_radar_api.py tests/unit/test_radar_service.py tests/e2e/test_smoke_mvp_flow.py -q` -> `10 passed`.
- [x] Regressao backend completa: `Set-Location backend; $env:PYTHONPATH='.vendor'; python -m pytest tests -q --basetemp .tmp_pytest_full` -> `53 passed`.
