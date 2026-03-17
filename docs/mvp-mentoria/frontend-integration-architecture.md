# Frontend Integration Architecture (MVP Mentoria)

Data: 2026-03-09

## 0) Objetivo

Definir a arquitetura de integracao do frontend com o backend MVP de mentoria, mantendo:
- contrato v1 congelado (`contracts-freeze-v1.md`)
- estrutura das 3 visoes (Centro, Radar, Matriz)
- migracao de linguagem clinica para mentoria
- baixo risco de regressao visual

## 1) Principios arquiteturais

1. Contrato v1 como fonte tecnica:
- nao assumir campos fora dos contratos congelados sem fallback.

2. Separacao de responsabilidades:
- `HTTP client` (rede/auth/erros)
- `services` (chamadas por caso de uso)
- `adapters` (raw API -> modelo de dominio frontend)
- `formatters` (apresentacao de percentual/moeda)

3. Dominio interno estavel:
- frontend trabalha com naming canonico unico, independente de alias legado.

4. Tolerancia a evolucao:
- campos opcionais e aliases tratados em camada de adaptacao, nao no componente.

5. UI resiliente:
- loading, erro e vazio padronizados por estado de recurso.

---

## 2) Desenho em camadas

Fluxo recomendado:
1. `Component/Hook de tela`
2. `View Service` (por visualizacao)
3. `Api Client` (HTTP)
4. `Contract Adapter` (raw -> dominio)
5. `Domain Model` consumido pela UI
6. `Formatters` aplicados no render (nao no adapter)

Representacao logica:

```txt
UI (Centro/Radar/Matriz)
  -> view-services/*
    -> api-client/http.ts
      -> endpoints v1 backend
    -> adapters/*
      -> domain-models/*
  -> formatters/*
```

---

## 3) Camada de API / client HTTP

## 3.1 Responsabilidade

- centralizar `baseURL`, headers e token Bearer
- padronizar parsing de sucesso/erro
- mapear payload de erro v1:
  - `{ error: { status, code, message, details } }`

## 3.2 Contrato minimo do client

Operacoes:
- `get<T>(path, options?)`
- `post<T>(path, body, options?)`
- `put<T>(path, body, options?)` (para expansao futura)
- `delete<T>(path, options?)` (para expansao futura)

Comportamentos obrigatorios:
- incluir `Authorization: Bearer <token>` quando existir sessao
- timeout unico por request
- normalizar erro para `AppError`:
  - `httpStatus`
  - `code`
  - `message`
  - `details`
  - `isNetworkError`

## 3.3 Regras de erro

- `401`: sessao invalida/expirada (acionar fluxo de logout controlado)
- `403`: permissao insuficiente (mensagem de acesso)
- `404`: recurso nao encontrado (vazio orientado ao contexto)
- `409`: conflito de regra de negocio
- `422`: validacao de payload

## 3.4 Dependencia externa

- backend precisa CORS habilitado para origem do frontend (bloqueador browser registrado em `backend-readiness-for-frontend.md`).

---

## 4) Services por visualizacao

## 4.1 AuthService (cross-cutting)

Metodos:
- `login(email, password)` -> token
- `getMe()` -> usuario autenticado

Saida:
- `AuthSession` (token, user, role)

## 4.2 CommandCenterService

Endpoints:
- `GET /admin/centro-comando/alunos`
- `GET /admin/centro-comando/alunos/{student_id}`

Metodos:
- `listStudents()`
- `getStudentDetail(studentId)`
- `deriveTopKpis(items)` (local: ativos, alertas, D-45)

## 4.3 RadarService

Endpoint:
- `GET /admin/radar/alunos/{student_id}`

Metodos:
- `getStudentRadar(studentId)`
- `simulateRadarProjection(axisScores, slider)` (calculo local de UI)

## 4.4 RenewalMatrixService

Endpoint:
- `GET /admin/matriz-renovacao?filter=all|topRight|critical|rescue`

Metodos:
- `getMatrix(filter)`
- `deriveMatrixKpis(items)` apenas como fallback, se necessario

---

## 5) Adapters de contrato

## 5.1 Objetivo

Converter payload bruto da API (raw DTO) para modelo de dominio frontend canonico.

## 5.2 Modelos canonicos sugeridos

- `StudentListItemDomain`
- `StudentDetailDomain`
- `RadarAxisDomain`
- `RadarDomain`
- `MatrixItemDomain`
- `MatrixDomain`

## 5.3 Regras de adaptacao obrigatorias

1. Normalizar entidade:
- qualquer alias de pessoa vira `student`.

2. Normalizar programa:
- `programName` como canonico
- `plan` como alias de leitura.

3. Tipos numericos:
- garantir `number` para `progress`, `engagement`, `ltv`, `baseline`, `current`, `projected`.

4. Campos opcionais:
- Radar: `insight` opcional.
- Centro: `valueProjected`, `optimal` opcionais.
- Matriz: `markers` opcional com default `[]`.

5. Fallbacks:
- Radar: `projected = current` se ausente.
- Strings vazias para textos opcionais quando necessario no render.

---

## 6) Normalizacao de naming

## 6.1 Canonico tecnico no frontend

- Pessoa: `student`
- Profissional: `mentor`
- Programa: `mentoria` no texto; `programName` no dado tecnico
- Metodo: `method`/`protocol` conforme contrato admin

## 6.2 Mapeamento de aliases legados

- `patient` -> `student`
- `client` -> `student`
- `plan` -> `programName`
- termos clinicos de UI migrar para mentoria:
  - paciente -> aluno
  - medico -> mentor
  - biomarcador -> indicador
  - jornada biologica -> jornada de transformacao

## 6.3 Regra de ouro

- componente de UI nao deve conter logica de alias; isso fica no adapter.

---

## 7) Formatacao centralizada (percentual e moeda)

## 7.1 Politica

- modelos de dominio armazenam valores numericos crus
- formatacao ocorre somente na camada de exibicao via utilitarios centrais

## 7.2 Utilitarios minimos

- `formatPercent01(value01)`:
  - entrada esperada `0..1`
  - saida `xx%`

- `formatCurrencyBRL(value)`:
  - entrada numerica de `ltv`
  - saida monetaria padrao BRL

- `coerceNumber(value, fallback=0)`:
  - parser defensivo para legado string/number

## 7.3 Beneficio

- evita parsing/formatting duplicado em cada componente
- reduz bugs de inconsistencias entre Centro/Radar/Matriz

---

## 8) Loading, erro e estado vazio

## 8.1 Estado padrao de recurso

Cada consumo de service segue:
- `idle`
- `loading`
- `success`
- `empty`
- `error`

## 8.2 Regras por estado

- `loading`: skeleton/spinner contextual da visao
- `empty`: mensagem orientada ao negocio (sem dado para exibir)
- `error`: componente padrao com `message` + acao `tentar novamente`
- `success`: render normal

## 8.3 Padrao de UX de erro

- mensagens de erro usam semantica de mentoria
- erro tecnico detalhado fica em log, nao no texto principal

---

## 9) Campos opcionais e aliases legados

## 9.1 Estrategia

1. Adapter com fallback deterministico:
- sempre definir valores default para opcionais.

2. Leitura por ordem de precedencia:
- exemplo programa: `programName ?? plan ?? ""`.

3. Nao quebrar render por ausencia de campo:
- exibir placeholder semanticamente neutro.

4. Telemetria de degradacao:
- registrar quando fallback/alias foi usado para monitorar legado.

## 9.2 Casos mapeados (v1)

- Centro:
  - anomalia/timeline nao garantida por endpoint dedicado (tratar como opcional).
- Radar:
  - `insight` opcional.
- Matriz:
  - `programName` e `plan` coexistem.
  - `markers.value/target` pode variar string/numero.

---

## 10) Contratos por visao (resumo tecnico)

## Centro de Comando

Service:
- `listStudents()`
- `getStudentDetail(studentId)`

Adapter:
- normaliza lista/detalhe para `Student*Domain`
- formata apenas no componente (percentual/moeda)

## Radar de Transformacao

Service:
- `getStudentRadar(studentId)`

Adapter:
- parse numerico dos eixos
- fallback `projected`
- `insight` opcional

## Matriz de Renovacao Antecipada

Service:
- `getMatrix(filter)`

Adapter:
- normaliza `programName/plan`
- parse numerico de bolha/KPI
- `markers` seguro

---

## 11) Decisoes de compatibilidade

1. Compatibilidade backward no frontend:
- aceitar aliases legados por 1 ciclo de integracao.

2. Compatibilidade forward com backend:
- nao depender de campos fora do contrato v1.

3. Politica de evolucao:
- qualquer breaking change de contrato deve gerar versao nova de adapter.

---

## 12) Dependencias residuais de backend

1. Obrigatorio para browser:
- CORS habilitado.

2. Opcionais de produto:
- endpoint de anomalia/timeline no Centro.
- `insight` por eixo no Radar.

Esses itens nao bloqueiam integracao core das 3 visoes.
