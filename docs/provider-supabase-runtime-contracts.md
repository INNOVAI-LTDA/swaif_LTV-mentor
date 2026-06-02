# Provider Runtime Contracts (Supabase-Only)

Data: 2026-05-29

## 1. Objetivo

Este documento consolida o contrato operacional final do runtime provider/admin com Supabase como fonte exclusiva para os fluxos:

- Centro de Comando do provider
- Radar do provider
- Matriz de renovacao
- Admin Database View

## 2. Roles Oficiais

- `admin`: gestao e auditoria global.
- `provider`: dono da carteira operacional.
- `client`: aluno/cliente vinculado ao provider.

Roles legadas como `mentor`/`student` nao sao roles persistidas do runtime Supabase.

## 3. Tabelas Runtime Relevantes

- `deva_accmed_users`
- `deva_accmed_organizations`
- `deva_accmed_products`
- `deva_accmed_enrollments`
- `deva_accmed_product_pillars`
- `deva_accmed_product_metrics`
- `deva_accmed_runtime_measurements`
- `deva_accmed_runtime_checkpoints`

## 4. Endpoints e Autorizacao

### 4.1 Identidade provider

- `GET /provider/me`
  - auth: token valido com `role=provider`.
  - resposta:
    - `id`
    - `email`
    - `fullName`
    - `role`
    - `organizationId`

- `GET /provider/me/hierarchy`
  - auth: token provider.
  - runtime: `SUPABASE_DB_URL` obrigatorio.
  - resposta: arvore provider -> organization -> products -> enrollments -> clients.

- `GET /provider/me/enrollments/{enrollment_id}/metric-tree`
  - auth: token provider.
  - ownership: enrollment precisa pertencer ao provider autenticado.
  - resposta: pilares, metricas e measurements do enrollment.

### 4.2 Workspace mentor/provider (rotas mantidas com prefixo `/mentor`)

- `GET /mentor/centro-comando/alunos`
- `GET /mentor/radar/clientes`
- `GET /mentor/radar/alunos/{client_id}`
- `GET /mentor/matriz-renovacao`

Regras:

- auth: token provider.
- ownership: provider so enxerga clients vinculados por enrollment ativo.
- runtime: `SUPABASE_DB_URL` obrigatorio para fluxo Supabase-only.

### 4.3 Admin Database View

- `GET /admin/database-view`
- `GET /admin/database-view/tables`
- `GET /admin/database-view/tables/{table}/records`

Regras:

- auth: token admin.
- runtime: `SUPABASE_DB_URL` obrigatorio.
- seguranca: `password_hash` nao pode aparecer em payload publico.

## 5. Ownership e Isolamento de Dados

Regras obrigatorias:

- provider nao acessa enrollment/client de outro provider.
- admin pode auditar dataset completo via Database View.
- `client_user_id` e `provider_user_id` sao sempre validados a partir de enrollments ativos.

## 6. Shape de Payloads (resumo)

### 6.1 Command Center item

- `id` (client id)
- `name`
- `programName`
- `daysLeft`
- `ltv`
- `urgency`
- `risk`

### 6.2 Radar agregado

- `clients[]`
- `axisScores[]`
- `avgBaseline`
- `avgCurrent`
- `avgProjected`

### 6.3 Radar individual

- `studentId`
- `axisScores[]`
- `avgBaseline`
- `avgCurrent`
- `avgProjected`

### 6.4 Matriz

- `filter`
- `items[]`
- `kpis`
- `context`

Observacao de compatibilidade:

- `quadrant` segue valores canonicos da UI (`topRight`, `topLeft`, `bottomRight`, `bottomLeft`).
- `decisionMatrixStatus` preserva semantica de filtro (`critical`, `rescue`, `topRight` etc.).

### 6.5 Erro padronizado

Todos os erros HTTP devem manter envelope:

```json
{
  "error": {
    "status": 503,
    "code": "SUPABASE_DB_URL_REQUIRED",
    "message": "SUPABASE_DB_URL obrigatorio para runtime sem fallback JSON.",
    "details": null
  }
}
```

## 7. Guardrails de Runtime

- Quando `SUPABASE_RUNTIME_REQUIRED=true`, fallback para JSON nos fluxos runtime deve falhar explicitamente.
- `SUPABASE_DB_URL` ausente em modo runtime required deve retornar erro claro (`503` + `SUPABASE_DB_URL_REQUIRED`) nas rotas aplicaveis.

## 8. Proibicao de JSON nos Fluxos A/B/C/D

Nos fluxos abaixo, a fonte de verdade e exclusivamente Supabase:

- `/provider/me`
- `/provider/me/hierarchy`
- `/mentor/centro-comando/alunos`
- `/mentor/radar/clientes`
- `/mentor/radar/alunos/{client_id}`
- `/mentor/matriz-renovacao`
- `/admin/database-view`

Nao usar fallback para repositories JSON nesses fluxos.
