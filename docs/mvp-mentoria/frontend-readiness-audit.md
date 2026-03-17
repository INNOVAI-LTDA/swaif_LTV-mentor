# Frontend Readiness Audit (Integracao com Backend MVP)

Data: 2026-03-09

## 0) Escopo e fontes obrigatorias

Esta auditoria cruza o frontend atual disponivel em `origin/*.jsx` com:
- `docs/mvp-mentoria/backend-readiness-for-frontend.md`
- `docs/mvp-mentoria/contracts-command-center.md`
- `docs/mvp-mentoria/contracts-radar.md`
- `docs/mvp-mentoria/contracts-renewal-matrix.md`
- `docs/mvp-mentoria/contracts-freeze-v1.md`
- `docs/mvp-mentoria/frontend-backend-gap-analysis.md`
- `docs/mvp-mentoria/naming-and-domain-notes.md`

Observacao importante:
- No repositorio auditado nao existem os arquivos fisicos de `./hooks/*`, `./services/*`, `./contexts/*` e `CadastroModal` importados pelos JSX. O mapeamento de hooks/services abaixo e baseado em imports e uso nos componentes.

---

## 1) Mapeamento do frontend atual

## 1.1 Pontos de entrada (entry points)

1. `origin/jpe-hub.jsx`:
- `export default function App()` (hub com navegacao entre Centro/Radar/Matriz).
- Importa `useClients`, `useClientRadar`, `useAuth`, `CadastroModal`.

2. `origin/jpe-command-center.jsx`:
- `export default function App()` (tela standalone do Centro).
- Importa `useStudents`, `useStudentDetail`.

3. `origin/radar-longevidade.jsx`:
- `export default function App()` (tela standalone do Radar).
- Importa `useStudents`, `useStudentRadar`.

4. `origin/matriz-renovacao.jsx`:
- `export default function App()` (tela standalone da Matriz).
- Importa `useStudents`.

## 1.2 Hooks mapeados (por import/uso)

- `useStudents`:
  - usado em `jpe-command-center.jsx`, `radar-longevidade.jsx`, `matriz-renovacao.jsx`.
- `useStudentDetail`:
  - usado em `jpe-command-center.jsx` (detalhe lateral por `selectedId`).
- `useStudentRadar`:
  - usado em `radar-longevidade.jsx`.
- `useClients`:
  - usado em `jpe-hub.jsx`.
- `useClientRadar`:
  - usado em `jpe-hub.jsx`.
- `useAuth`:
  - usado em `jpe-hub.jsx` (token/logout importados, sem uso efetivo no arquivo).

## 1.3 Services mapeados

- Nao ha import direto de `./services` nem chamada `fetch`/`axios` nos JSX auditados.
- A camada de acesso a API esta implicitamente delegada aos hooks.
- Implicacao: sem os hooks no repo, a prontidao real de rede/auth nao e verificavel nesta auditoria.

## 1.4 Componentes principais por visao

Centro:
- `CommandoModule` (hub), `TopBar`, `PatientRow`, `PatientDetail`, `HormoziMeter`, `InsightCard/InsightModal`.

Radar:
- `RadarModule` (hub), `LongevityRadar`, `PillarRow`, `BioAgeCounter`.

Matriz:
- `MatrizModule` (hub), `Matrix`, `PatientBubble`, `PatientDrawer`, `MarkerBar`.

Shell/hub:
- `HubHome`, `ModuleBar`, `Particles`, `ModIcon`.

---

## 2) Mocks, hardcodes e contratos implicitos

## 2.1 Mocks/hardcodes detectados

1. `origin/matriz-renovacao.jsx`:
- bloco `const _REMOVED = [...]` com dataset hardcoded legado de pacientes.

2. Textos e narrativa hardcoded clinica:
- multiplos labels e CTAs com linguagem clinica em todos os arquivos (detalhado na secao 3).

3. Selecao fixa de aluno no Radar standalone:
- `studentList?.[0]?.id` e `studentList?.[0]?.name`.

4. KPIs e formatacoes calculados localmente:
- `ltv`, `avgEngagement`, `criticalRenewals`, `rescueCount`, percentuais.

## 2.2 Contratos ainda implicitos (nao tipados localmente)

1. Centro (hub) usa campos nao garantidos no contrato de lista do Centro:
- `sel.renewalReason` no painel direito de `CommandoModule` do hub.
- lista do endpoint `/admin/centro-comando/alunos` nao congela `renewalReason`.

2. Campo legado nao alinhado ao contrato v1:
- `programId={students[0]?.programId}` para `CadastroModal` no hub.
- `programId` nao faz parte do contrato congelado das 3 visoes.

3. Logica de risco legada:
- `getRisk = p.segments...` em `jpe-hub.jsx`; `segments` nao faz parte dos contratos v1 atuais.

4. Contrato de erro v1 nao evidenciado na UI:
- nao ha prova no JSX de tratamento padrao do payload `{ error: { status, code, message, details } }`.

---

## 3) Naming clinico ainda presente (migrar para mentoria)

Termos recorrentes detectados:
- `paciente/pacientes`
- `clinico/clinica`
- `biologico/jornada biologica/idade bio`
- `biomarcadores`
- `painel medico`

Arquivos com maior incidencia:
- `origin/jpe-command-center.jsx`
- `origin/jpe-hub.jsx`
- `origin/matriz-renovacao.jsx`
- `origin/radar-longevidade.jsx`

Impacto:
- conflita com `contracts-freeze-v1.md` e `naming-and-domain-notes.md` (dominio alvo: mentor, aluno, mentoria, metodo).

---

## 4) Componentes integraveis sem refatoracao estrutural

Podem integrar com backend atual mantendo layout:

1. Centro standalone (`jpe-command-center.jsx`):
- fluxo lista + detalhe ja separado por hook (`useStudents` + `useStudentDetail`);
- estrutura visual compativel com contratos de `/admin/centro-comando/*`.

2. Radar standalone (`radar-longevidade.jsx`):
- consumo de `axisScores` com fallback de `projected`;
- slider e calculos locais coerentes com contrato do Radar.

3. Matriz standalone (`matriz-renovacao.jsx`):
- bolhas, drawer e KPIs alinhados ao shape de `items` e `kpis` da Matriz.

4. Hub (`jpe-hub.jsx`) como shell:
- navegacao e composicao de modulos podem ser mantidas;
- requer alinhamento de hooks/naming, sem redesenho.

---

## 5) Classificacao de prontidao

## 5.1 Pronto para integrar

1. `origin/jpe-command-center.jsx` (estrutura de tela do Centro):
- pronto no desenho de composicao (lista + detalhe + painel).

2. `origin/radar-longevidade.jsx` (estrutura de tela do Radar):
- pronto no desenho de eixo/simulacao.

3. `origin/matriz-renovacao.jsx` (estrutura de tela da Matriz):
- pronto no desenho de quadrantes/bolhas/drawer.

4. `origin/jpe-hub.jsx` (orquestracao visual):
- pronto como shell de navegacao entre as 3 visoes.

## 5.2 Precisa de adapter

1. Hooks e dominio de entidade:
- unificar `useStudents/useClients`, `useStudentRadar/useClientRadar`;
- normalizar `patient/client/student` para um unico dominio interno (`student`).

2. Campos com alias:
- `programName` x `plan`.

3. Tipos e formato:
- parse/normalizacao de numeros (`ltv`, `baseline/current/projected`);
- formatacao de percentual para `progress/engagement`.

4. Erro v1:
- adapter de erro para payload padrao `{ error: ... }` (401/404/409/422).

## 5.3 Precisa de refatoracao leve

1. `origin/jpe-hub.jsx`:
- remover dependencia implicita de `segments` em `getRisk`;
- corrigir uso de campos nao congelados (`programId` no modal, `renewalReason` no Centro sem garantia de origem);
- aplicar tratamento de loading/autenticacao hoje incompleto (vars declaradas e nao usadas).

2. `origin/jpe-command-center.jsx`:
- proteger divisao por zero em calculos com `totalDays` (`getProgress`, `HormoziMeter`, checkpoints);
- revisar fluxo de anomalia para fallback explicito (ja que endpoint dedicado nao existe no backend atual).

3. `origin/radar-longevidade.jsx`:
- limpar estado/import nao usado (`activePillar`, import de `recharts` sem uso no render atual).

4. `origin/matriz-renovacao.jsx`:
- remover bloco legado `_REMOVED` do runtime ativo;
- consolidar terminologia de drawer e CTA para mentoria.

## 5.4 Nao usar / legado

1. Bloco `_REMOVED` em `origin/matriz-renovacao.jsx`.
2. Fluxo `Timeline`/`AnomalyDot` em `origin/jpe-command-center.jsx` (declarado e nao conectado ao fluxo principal).
3. Logica `getRisk` baseada em `segments` em `origin/jpe-hub.jsx` (contrato antigo, fora do v1 atual).
4. Imports/estados sem uso que indicam sobra de iteracoes anteriores:
- `studentsLoading`, `accessToken`, `logout` no hub;
- `listLoading` no Centro standalone;
- `activePillar` no Radar standalone.

---

## 6) Diagnostico final objetivo

Nivel geral de prontidao frontend para integracao com backend v1: **medio-alto**.

Resumo:
- A arquitetura visual das 3 visoes esta pronta e nao exige redesign.
- O principal bloqueio tecnico nao estrutural esta na camada de dados (hooks nao versionados no repo, adapters de naming/tipos, e limpeza de legado).
- Com adapter de dominio + refatoracoes leves, o frontend fica apto para integrar com os endpoints v1 ja implementados.
