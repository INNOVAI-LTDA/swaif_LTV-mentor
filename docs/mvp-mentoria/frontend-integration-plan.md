# Frontend Integration Plan (MVP Mentoria)

Data: 2026-03-09

## 1) Objetivo e escopo

Preparar a integracao do frontend com o backend MVP ja implementado, preservando a estrutura e assinatura visual das 3 visoes:
- Centro de Comando
- Radar de Transformacao
- Matriz de Renovacao Antecipada

Escopo desta fase:
- planejamento de execucao em marcos pequenos
- definicao de ajustes frontend vs ajustes residuais backend
- mitigacao de riscos de integracao
- sem redesign de interface

## 2) Fonte de verdade usada

- `docs/mvp-mentoria/backend-first-report.md`
- `docs/mvp-mentoria/backend-implementation-plan.md`
- `docs/mvp-mentoria/backend-readiness-for-frontend.md`
- `docs/mvp-mentoria/backend-task-checklist.md`
- `docs/mvp-mentoria/backend-test-strategy.md`
- `docs/mvp-mentoria/contracts-command-center.md`
- `docs/mvp-mentoria/contracts-freeze-v1.md`
- `docs/mvp-mentoria/contracts-radar.md`
- `docs/mvp-mentoria/contracts-renewal-matrix.md`
- `docs/mvp-mentoria/data-model.md`
- `docs/mvp-mentoria/frontend-backend-gap-analysis.md`
- `docs/mvp-mentoria/naming-and-domain-notes.md`

## 3) Estado atual do frontend (diagnostico objetivo)

Base observada:
- `origin/jpe-hub.jsx`
- `origin/jpe-command-center.jsx`
- `origin/radar-longevidade.jsx`
- `origin/matriz-renovacao.jsx`

Achados principais:
- Estrutura visual das 3 visoes ja existe e deve ser preservada.
- O codigo ja pressupoe hooks de API (`useStudents`, `useStudentDetail`, `useStudentRadar`, `useClients`, `useClientRadar`), mas esses arquivos nao estao versionados neste repositorio.
- Naming misto ainda presente em labels e estado (`patient/client/student`).
- Regras de calculo de exibicao estao no frontend (slider do radar, formatações, agregados de topo em algumas telas).
- Backend ja entrega contratos core das 3 visoes, com lacunas pontuais conhecidas (anomalia/timeline do Centro e `insight` opcional no Radar).

## 4) Principios de integracao

- Nao alterar layout, hierarquia visual ou linguagem de interacao das telas.
- Manter contratos backend v1 congelados como referencia tecnica.
- Resolver divergencias de naming via camada de adaptacao no frontend.
- Tratar campos opcionais com null-safety.
- Concentrar transformacoes de formato (percentual, moeda, labels) em utilitarios unicos.

## 5) Plano por marcos pequenos

## Marco F0 - Preparacao tecnica do frontend
Objetivo:
- criar base de integracao sem alterar UI

Entregas:
- inventario dos pontos de consumo de dados por visao
- definicao de `API_BASE_URL` por ambiente
- definicao unica de cliente HTTP e interceptors de auth/erro

Criterio de pronto:
- frontend consegue autenticar e fazer chamadas protegidas em ambiente local
- erro 401/403/404/409/422 tratado de forma consistente em toasts/banners

Dependencias backend:
- habilitacao de CORS para origem do frontend (bloqueador browser)

## Marco F1 - Camada de dominio e adaptadores
Objetivo:
- normalizar naming e tipos sem tocar no layout

Entregas:
- adapter unico: `student/client/patient -> student`
- normalizacao de `programName` com alias de leitura para `plan`
- utilitarios de formatacao:
  - percentual para `progress/engagement`
  - moeda para `ltv`

Criterio de pronto:
- componentes passam a receber shape interno estavel, independente da origem do payload

Dependencias backend:
- nenhuma (com contrato atual e possivel adaptar 100% no front)

## Marco F2 - Integracao Centro de Comando
Objetivo:
- ligar lista e detalhe ao backend real

Entregas:
- lista: `GET /admin/centro-comando/alunos`
- detalhe lateral: `GET /admin/centro-comando/alunos/{student_id}`
- fallback visual para ausencia de dados de anomalia/timeline

Criterio de pronto:
- render estavel com loading/empty/error states
- KPI de topo derivado localmente da lista (ativos, alertas, D-45)

Dependencias backend:
- opcional: endpoint de anomalia/timeline se esse bloco for obrigatorio

## Marco F3 - Integracao Radar de Transformacao
Objetivo:
- ligar eixos e simulacao ao contrato real

Entregas:
- leitura de `GET /admin/radar/alunos/{student_id}`
- parser robusto para numeros (`baseline/current/projected`)
- `insight` tratado como opcional

Criterio de pronto:
- simulacao do slider operando com dados reais
- medias e deltas batendo com contrato de tela

Dependencias backend:
- opcional: preencher `insight` por eixo caso copy dinamica seja requisito

## Marco F4 - Integracao Matriz de Renovacao
Objetivo:
- consumir endpoint agregado e manter drawer atual

Entregas:
- leitura de `GET /admin/matriz-renovacao?filter=...`
- uso de filtros `all|topRight|critical|rescue`
- compatibilidade com `programName/plan`

Criterio de pronto:
- bolhas, KPIs e drawer renderizando com payload real
- sem mudanca estrutural de layout

Dependencias backend:
- nenhuma obrigatoria (contrato core ja cobre a visao)

## Marco F5 - Migracao de linguagem (clinica -> mentoria)
Objetivo:
- padronizar copy sem impacto visual

Entregas:
- dicionario de termos de mentoria aplicado em labels, CTAs e mensagens
- revisao de strings legadas clinicas nas 3 visoes e hub

Criterio de pronto:
- nenhum texto funcional principal com termos clinicos remanescentes

Dependencias backend:
- manter mensagens de erro alinhadas ao dominio mentoria (ja indicado como concluido no backend)

## Marco F6 - Hardening frontend de integracao
Objetivo:
- estabilizar comportamento e reduzir regressao

Entregas:
- tratamento padrao de erro e fallback por visao
- instrumentacao minima de logs de erro de rede/contrato
- validacao final de compatibilidade com contrato v1 congelado

Criterio de pronto:
- suite de testes frontend verde (unit + integracao + e2e)
- checklist frontend 100% concluido

Dependencias backend:
- confirmar CORS ativo no ambiente de execucao do frontend

## 6) Riscos de integracao e mitigacao

1. CORS ausente bloquear chamadas no browser.
- Mitigacao: habilitar CORS antes de iniciar teste E2E frontend.

2. Divergencia de naming (`patient/client/student`, `programName/plan`).
- Mitigacao: camada de adaptacao unica no frontend com testes unitarios.

3. Campos opcionais faltantes quebrarem render (`insight`, `valueProjected`, `optimal`).
- Mitigacao: null-safety e defaults de exibicao.

4. Drift de contrato durante ajustes finais.
- Mitigacao: testes de contrato frontend contra payloads v1 congelados.

5. Frontend atual referenciar hooks/estrutura nao versionados neste repo.
- Mitigacao: primeiro marco dedicado a consolidar localizacao real de hooks e cliente API.

## 7) Ajustes frontend vs backend (residual)

## Fazer no frontend (obrigatorio)
- criar/ajustar cliente API com token Bearer
- padronizar adapters de dominio
- normalizar formatacao percentual/moeda
- tratar campos opcionais e estados de erro/loading
- migrar copy clinica para mentoria mantendo layout

## Fazer no backend (residual)
- habilitar CORS para ambiente frontend
- opcional: endpoint de anomalia/timeline do Centro
- opcional: `insight` no Radar por eixo

## 8) Sequenciamento sugerido

Ordem recomendada:
1. F0
2. F1
3. F2
4. F3
5. F4
6. F5
7. F6

Racional:
- reduz risco tecnico cedo (CORS, auth, adapters)
- integra primeiro o que mais acopla estado global (Centro)
- posterga ajustes opcionais de backend para depois de validar fluxo core
