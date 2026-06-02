# Plano de implementação — Supabase-only para Provider Workspace e Admin Database View

## 1. Contexto

O projeto saiu do modelo antigo baseado em JSONs locais e passou a usar Supabase como fonte de verdade. O objetivo deste plano é orientar uma implementação incremental, atômica e validável para garantir que as telas de runtime consumam exclusivamente o Supabase.

Escopo prioritário:

```text
A) Centro de Comando do provider
B) Radar do provider
C) Matriz de renovação
D) Admin Database View
```

A implementação deve ser contínua, em ciclos pequenos, com uma tarefa por execução do agente. Cada tarefa abaixo foi desenhada para ser simples, testável e validável por humano.

---

## 2. Decisões de domínio já fechadas

```text
provider = deva_accmed_users.role = 'provider'
client/aluno = deva_accmed_users.role = 'client'
admin = deva_accmed_users.role = 'admin'

organization = empresa/conta contratante, ex: ACCMed
product = produto/programa pertencente à organization
mentoria = apenas texto/nome/categoria de produto, não é entidade técnica própria

enrollment = vínculo oficial provider -> client -> product
runtime = Supabase obrigatório
JSON = proibido nos fluxos A/B/C/D
auth = deva_accmed_users.password_hash
```

Não criar novas entidades técnicas chamadas `mentor`, `student` ou `aluno`. Essas palavras podem continuar aparecendo na UI quando fizer sentido, mas o backend deve trabalhar com `provider`, `client`, `product` e `enrollment`.

---

## 3. Schema Supabase relevante

### 3.1 Usuários

Tabela:

```sql
deva_accmed_users
```

Campos relevantes:

```text
id BIGINT
email TEXT
role TEXT
full_name TEXT
is_active BOOLEAN
organization_id BIGINT
password_hash TEXT
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Roles válidas para runtime:

```text
admin
provider
client
```

### 3.2 Organizações

Tabela:

```sql
deva_accmed_organizations
```

Campos relevantes:

```text
id
name
brand_name
slug
cnpj
timezone
currency
status
is_active
notes
created_at
updated_at
```

### 3.3 Produtos

Tabela:

```sql
deva_accmed_products
```

Campos relevantes:

```text
id
organization_id
name
slug
category
status
description
created_at
updated_at
```

Relacionamento:

```text
deva_accmed_products.organization_id -> deva_accmed_organizations.id
```

### 3.4 Enrollments

Tabela:

```sql
deva_accmed_enrollments
```

Campos relevantes:

```text
id
provider_user_id
client_user_id
product_id
start_day
days_left
investment
decision_matrix_status
status
created_at
updated_at
```

Relacionamentos:

```text
provider_user_id -> deva_accmed_users.id
client_user_id   -> deva_accmed_users.id
product_id       -> deva_accmed_products.id
```

### 3.5 Pilares

Tabela:

```sql
deva_accmed_product_pillars
```

Campos relevantes:

```text
id
product_id
name
slug
order_index
metadata
is_active
```

Relacionamento:

```text
product_id -> deva_accmed_products.id
```

### 3.6 Métricas

Tabela:

```sql
deva_accmed_product_metrics
```

Campos relevantes:

```text
id
pillar_id
name
slug
direction
unit
scoring_rules
score_type
min_score
max_score
max_score_basis
mcv
is_active
created_at
updated_at
```

Relacionamento:

```text
pillar_id -> deva_accmed_product_pillars.id
```

### 3.7 Medições runtime

Tabela:

```sql
deva_accmed_runtime_measurements
```

Campos relevantes:

```text
id TEXT
enrollment_id TEXT
metric_id TEXT
value_baseline DOUBLE PRECISION
value_current DOUBLE PRECISION
value_projected DOUBLE PRECISION
improving_trend BOOLEAN
created_at
updated_at
```

Observação: `enrollment_id` e `metric_id` são `TEXT`; no código, normalize IDs como `str(...)`.

### 3.8 Checkpoints runtime

Tabela:

```sql
deva_accmed_runtime_checkpoints
```

Campos relevantes:

```text
id TEXT
enrollment_id TEXT
week INTEGER
status TEXT
label TEXT
created_at
updated_at
```

---

## 4. Regra de ouro da implementação

Quando `SUPABASE_DB_URL` estiver configurado, os fluxos abaixo não podem consultar JSON, memória local ou stores derivados de JSON:

```text
/auth/login
/me
/provider/me
/provider/me/hierarchy
/mentor/centro-comando/alunos
/mentor/radar/clientes
/mentor/radar/alunos/{client_id}
/mentor/matriz-renovacao
/admin/database-view
```

Repositories proibidos nesses fluxos:

```text
MentorRepository
EnrollmentRepository local/memória
ProductAssignmentRepository JSON
JsonRepository para dados runtime A/B/C/D
```

O código pode manter arquivos antigos por compatibilidade temporária, mas eles não podem ser usados nos fluxos acima.

---

## 5. Instruções para agente bmad/BMAD

### 5.1 Modo de execução

Execute **uma tarefa por ciclo**. Não agrupe tarefas. Não antecipe tarefas futuras.

Formato recomendado de execução:

```text
1. Ler esta especificação.
2. Executar somente a tarefa indicada.
3. Fazer a menor alteração possível.
4. Adicionar ou ajustar testes na mesma tarefa.
5. Rodar validação mínima da tarefa.
6. Reportar:
   - arquivos alterados;
   - decisão tomada;
   - testes executados;
   - evidência manual para validação humana;
   - próximos bloqueios, se houver.
```

### 5.2 Prompt recomendado para cada ciclo

Use este padrão no bmad/BMAD:

```text
Execute somente a tarefa <ID_DA_TAREFA> do arquivo docs/provider-supabase-runtime-plan.md.

Regras:
- Não execute tarefas futuras.
- Não faça refatoração ampla.
- Não use JSON como fallback.
- Não altere schema além do explicitamente pedido.
- Não introduza secrets.
- Adicione/ajuste testes mínimos da tarefa.
- Ao final, reporte arquivos alterados, testes executados e validação manual.
```

Se usar o Makefile BMAD do repo, adapte o comando conforme seu ambiente. Exemplo:

```bash
make bmad-quick-dev EXECUTE=1 INSTRUCTION="Execute somente a tarefa T01 do arquivo docs/provider-supabase-runtime-plan.md. Não avance para outras tarefas."
```

### 5.3 Critério de parada

O agente deve parar ao final de cada tarefa, mesmo que veja oportunidades de melhoria. A próxima tarefa deve ser disparada manualmente pelo operador.

---

## 6. Plano de implementação

### Fase 0 — Preflight e proteção contra regressão

Objetivo: entender estado atual, criar testes/guardrails mínimos e evitar que o agente mexa em várias frentes ao mesmo tempo.

### Fase 1 — Autenticação e identidade provider

Objetivo: garantir login via `deva_accmed_users.password_hash`, remover provisionamento automático e resolver o provider sem `MentorRepository`.

### Fase 2 — Repositories Supabase-only

Objetivo: criar a camada de leitura Supabase para users, enrollments, products, pillars, metrics, measurements e checkpoints.

### Fase 3 — Endpoints de diagnóstico

Objetivo: criar `/provider/me` e `/provider/me/hierarchy` para validar a árvore antes de plugar as telas principais.

### Fase 4 — Plugar telas A/B/C

Objetivo: fazer Centro de Comando, Radar e Matriz consumirem a hierarquia Supabase-only.

### Fase 5 — Admin Database View

Objetivo: expor uma visão administrativa completa do estado do banco e checagens de integridade.

### Fase 6 — Remoção de fallback JSON no runtime

Objetivo: impedir regressão para JSON nos fluxos A/B/C/D.

### Fase 7 — Frontend e validação visual

Objetivo: garantir que o frontend exiba os dados vindos do Supabase e que as mensagens/estados sejam claros.

---

# 7. Backlog de tarefas atômicas

## T00 — Criar arquivo de referência no repositório

**Objetivo:** versionar este plano dentro do repositório.

**Arquivos alvo:**

```text
docs/provider-supabase-runtime-plan.md
```

**Instruções:**

1. Criar o arquivo acima.
2. Copiar este plano inteiro para ele.
3. Não alterar código.
4. Não alterar testes.

**Validação:**

```bash
git diff -- docs/provider-supabase-runtime-plan.md
```

**Critério humano de aceite:**

```text
O arquivo existe, está legível e contém tarefas atômicas.
```

---

## T01 — Fazer preflight do estado atual

**Objetivo:** registrar quais testes passam antes das mudanças.

**Arquivos alvo:**

```text
Nenhum arquivo de produção.
Opcional: docs/execution/provider-supabase-preflight.md
```

**Instruções:**

1. Rodar testes backend, se o ambiente permitir.
2. Rodar build/test frontend, se o ambiente permitir.
3. Registrar comandos executados e resultado.
4. Não corrigir falhas nesta tarefa.

**Comandos sugeridos:**

```bash
cd backend && pytest
cd frontend && npm test
cd frontend && npm run build
```

**Validação:**

```text
Relatório com:
- comandos executados;
- sucesso/falha;
- falhas conhecidas;
- dependências ausentes.
```

**Critério humano de aceite:**

```text
Existe um baseline claro antes das mudanças.
```

---

## T02 — Confirmar coluna `password_hash` no repository de users

**Objetivo:** garantir que o backend lê `password_hash` de `deva_accmed_users`.

**Arquivos prováveis:**

```text
backend/app/storage/contact_user_repository.py
backend/app/storage/user_repository.py
backend/tests/unit ou backend/tests/api
```

**Instruções:**

1. Verificar se o repository seleciona `password_hash` quando a coluna existe.
2. Se já estiver implementado, adicionar teste de proteção.
3. Se faltar em algum fluxo, ajustar somente esse fluxo.
4. Não mudar regra de login nesta tarefa.

**Validação mínima:**

```text
Teste prova que user carregado do Supabase contém password_hash quando a coluna existe.
```

**Critério humano de aceite:**

```text
O backend consegue ler password_hash sem depender de JSON.
```

---

## T03 — Remover provisionamento automático por senha default

**Objetivo:** impedir criação automática de `client` por senha padrão.

**Arquivos prováveis:**

```text
backend/app/services/auth_service.py
backend/app/api/routes/auth.py
backend/tests/unit/test_auth_service*.py
backend/tests/api/test_auth*.py
```

**Instruções:**

1. Remover ou desabilitar `_provision_client_user` no fluxo Supabase.
2. Login deve depender de usuário existente com `password_hash`.
3. Não criar usuário durante login.
4. Não usar `APP_DEFAULT_STUDENT_PASSWORD`.
5. Preservar envelope de erro padronizado.

**Resultado esperado:**

```text
Usuário inexistente -> AUTH_INVALID_CREDENTIALS
Usuário sem password_hash -> AUTH_PASSWORD_NOT_CONFIGURED
Senha errada -> AUTH_INVALID_CREDENTIALS
```

**Validação mínima:**

```bash
cd backend && pytest backend/tests -k "auth"
```

**Critério humano de aceite:**

```text
Login nunca cria client automaticamente.
```

---

## T04 — Tornar `APP_AUTH_SECRET` obrigatório fora de local/test

**Objetivo:** remover fallback inseguro `dev-auth-secret` em ambiente production-like.

**Arquivos prováveis:**

```text
backend/app/api/routes/auth.py
backend/app/config/runtime.py
backend/tests/unit/test_runtime_config*.py
backend/tests/api/test_auth*.py
```

**Instruções:**

1. Criar helper para obter `APP_AUTH_SECRET`.
2. Em `local`, `development`, `dev` e `test`, fallback pode existir.
3. Fora disso, ausência de `APP_AUTH_SECRET` deve falhar com erro claro.
4. Não alterar token format nesta tarefa.

**Validação mínima:**

```text
APP_ENV=production sem APP_AUTH_SECRET falha.
APP_ENV=local sem APP_AUTH_SECRET continua funcionando para dev.
```

**Critério humano de aceite:**

```text
Não há fallback silencioso em produção.
```

---

## T05 — Criar `require_provider_user`

**Objetivo:** validar token e role `provider` sem acessar `MentorRepository`.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/app/api/routes/provider.py ou backend/app/api/routes/provider_workspace.py
backend/tests/api/test_provider_auth*.py
```

**Instruções:**

1. Criar função `require_provider_user`.
2. Ela deve usar token atual e `AuthService.get_current_user`.
3. Validar:
   - usuário existe;
   - `is_active = true`;
   - `role = provider`.
4. Não buscar em `MentorRepository`.
5. Não alterar endpoints `/mentor/*` ainda.

**Validação mínima:**

```text
Sem token -> 401.
Token admin -> 403.
Token client -> 403.
Token provider -> 200 em teste simples.
```

**Critério humano de aceite:**

```text
Existe um dependency guard para provider sem JSON.
```

---

## T06 — Criar endpoint `GET /provider/me`

**Objetivo:** expor o provider autenticado diretamente do Supabase.

**Arquivos prováveis:**

```text
backend/app/api/routes/provider.py
backend/app/main.py
backend/tests/api/test_provider_me.py
```

**Instruções:**

1. Criar router novo com prefixo `/provider`.
2. Registrar no `main.py`.
3. Endpoint `GET /provider/me` deve depender de `require_provider_user`.
4. Retornar:
   - id;
   - email;
   - fullName;
   - role;
   - organizationId.
5. Não mexer nas telas A/B/C ainda.

**Resposta esperada:**

```json
{
  "id": "1",
  "email": "provider@accmed.com.br",
  "fullName": "Nome Provider",
  "role": "provider",
  "organizationId": "1"
}
```

**Validação mínima:**

```bash
cd backend && pytest backend/tests/api/test_provider_me.py
```

**Critério humano de aceite:**

```text
Provider logado consegue chamar /provider/me.
```

---

## T07 — Criar `SupabaseEnrollmentRepository.list_active_by_provider`

**Objetivo:** ler enrollments ativos diretamente de `deva_accmed_enrollments`.

**Arquivos prováveis:**

```text
backend/app/storage/supabase_enrollment_repository.py
backend/tests/unit/test_supabase_enrollment_repository.py
```

**Instruções:**

1. Criar repository novo.
2. Receber `database_url` ou usar config existente.
3. Implementar `list_active_by_provider(provider_user_id: str)`.
4. Normalizar IDs como string.
5. Não usar `EnrollmentRepository` antigo.
6. Não usar JSON.

**Query base:**

```sql
SELECT
  id,
  provider_user_id,
  client_user_id,
  product_id,
  start_day,
  days_left,
  investment,
  decision_matrix_status,
  status,
  created_at,
  updated_at
FROM deva_accmed_enrollments
WHERE provider_user_id = %s
  AND status = 'active'
ORDER BY updated_at DESC, id DESC;
```

**Mapeamento mínimo:**

```python
{
  "id": str(row["id"]),
  "enrollment_id": str(row["id"]),
  "provider_user_id": str(row["provider_user_id"]),
  "client_user_id": str(row["client_user_id"]),
  "product_id": str(row["product_id"]),
  "status": row["status"],
}
```

**Validação mínima:**

```text
Teste cobre:
- provider com 2 enrollments ativos;
- enrollment inactive não aparece;
- IDs retornam como string.
```

**Critério humano de aceite:**

```text
Repository retorna somente enrollments ativos do provider.
```

---

## T08 — Criar `SupabaseProviderHierarchyRepository`

**Objetivo:** montar linhas base provider -> client -> product -> organization.

**Arquivos prováveis:**

```text
backend/app/storage/supabase_provider_hierarchy_repository.py
backend/tests/unit/test_supabase_provider_hierarchy_repository.py
```

**Instruções:**

1. Criar método `list_active_provider_hierarchy(provider_user_id: str)`.
2. Usar joins entre users, enrollments, products e organizations.
3. Validar `provider.role = 'provider'`.
4. Validar `client.role = 'client'`.
5. Validar `provider.is_active = true`.
6. Validar `client.is_active = true`.
7. Não consultar JSON.

**Query base:**

```sql
SELECT
  e.id AS enrollment_id,
  e.status AS enrollment_status,
  e.start_day,
  e.days_left,
  e.investment,
  e.decision_matrix_status,

  provider.id AS provider_id,
  provider.full_name AS provider_name,
  provider.email AS provider_email,
  provider.organization_id AS provider_organization_id,

  client.id AS client_id,
  client.full_name AS client_name,
  client.email AS client_email,

  p.id AS product_id,
  p.name AS product_name,
  p.slug AS product_slug,
  p.category AS product_category,

  o.id AS organization_id,
  o.name AS organization_name,
  o.slug AS organization_slug

FROM deva_accmed_enrollments e
JOIN deva_accmed_users provider
  ON provider.id = e.provider_user_id
 AND provider.role = 'provider'
 AND provider.is_active = true
JOIN deva_accmed_users client
  ON client.id = e.client_user_id
 AND client.role = 'client'
 AND client.is_active = true
JOIN deva_accmed_products p
  ON p.id = e.product_id
JOIN deva_accmed_organizations o
  ON o.id = p.organization_id
WHERE e.provider_user_id = %s
  AND e.status = 'active'
ORDER BY client.full_name ASC, e.updated_at DESC;
```

**Validação mínima:**

```text
Teste prova que Provider A não recebe clients do Provider B.
```

**Critério humano de aceite:**

```text
A hierarquia base está disponível em uma única consulta ou repository.
```

---

## T09 — Criar `ProviderHierarchyService`

**Objetivo:** transformar linhas SQL em payload de hierarquia.

**Arquivos prováveis:**

```text
backend/app/services/provider_hierarchy_service.py
backend/tests/unit/test_provider_hierarchy_service.py
```

**Instruções:**

1. Receber repository de hierarquia.
2. Criar método `get_provider_hierarchy(provider_user_id: str)`.
3. Agrupar:
   - provider;
   - organization;
   - products;
   - enrollments;
   - clients.
4. Deduplicar products por `product_id`.
5. Deduplicar clients por `client_id`.
6. Não buscar métricas ainda.

**Payload mínimo:**

```json
{
  "provider": {},
  "organization": {},
  "products": [],
  "enrollments": [],
  "clients": []
}
```

**Validação mínima:**

```text
Teste com duas linhas do mesmo produto não duplica product.
Teste com dois clients retorna dois clients.
```

**Critério humano de aceite:**

```text
Service retorna árvore estável e legível.
```

---

## T10 — Criar endpoint `GET /provider/me/hierarchy`

**Objetivo:** validar a árvore provider -> clients -> products -> enrollments via API.

**Arquivos prováveis:**

```text
backend/app/api/routes/provider.py
backend/tests/api/test_provider_hierarchy.py
```

**Instruções:**

1. Adicionar endpoint no router `/provider`.
2. Depender de `require_provider_user`.
3. Chamar `ProviderHierarchyService`.
4. Retornar payload da T09.
5. Não alterar endpoints `/mentor/*` ainda.

**Validação mínima:**

```text
Provider A recebe só a própria hierarquia.
Admin recebe 403.
Client recebe 403.
Sem token recebe 401.
```

**Critério humano de aceite:**

```text
É possível validar a hierarquia pelo browser/Postman/curl antes de alterar telas.
```

---

## T11 — Criar repository para pillars/metrics por product

**Objetivo:** ler pilares e métricas do produto no Supabase.

**Arquivos prováveis:**

```text
backend/app/storage/supabase_product_metric_repository.py
backend/tests/unit/test_supabase_product_metric_repository.py
```

**Instruções:**

1. Criar método `list_metric_tree_by_product(product_id: str)`.
2. Buscar pillars ativos e metrics ativas.
3. Ordenar pillars por `order_index`.
4. Normalizar IDs como string.
5. Não buscar measurements nesta tarefa.

**Query base:**

```sql
SELECT
  pp.id AS pillar_id,
  pp.name AS pillar_name,
  pp.slug AS pillar_slug,
  pp.order_index,

  pm.id AS metric_id,
  pm.name AS metric_name,
  pm.slug AS metric_slug,
  pm.direction,
  pm.unit,
  pm.scoring_rules,
  pm.score_type,
  pm.min_score,
  pm.max_score,
  pm.max_score_basis,
  pm.mcv

FROM deva_accmed_product_pillars pp
JOIN deva_accmed_product_metrics pm
  ON pm.pillar_id = pp.id
 AND pm.is_active = true
WHERE pp.product_id = %s
  AND pp.is_active = true
ORDER BY pp.order_index ASC, pm.id ASC;
```

**Validação mínima:**

```text
Teste cobre produto com 2 pillars e múltiplas metrics.
```

**Critério humano de aceite:**

```text
Repository retorna árvore de métricas por produto.
```

---

## T12 — Criar repository de runtime measurements

**Objetivo:** ler medições por enrollment no Supabase.

**Arquivos prováveis:**

```text
backend/app/storage/supabase_runtime_measurement_repository.py
backend/tests/unit/test_supabase_runtime_measurement_repository.py
```

**Instruções:**

1. Criar método `list_by_enrollment(enrollment_id: str)`.
2. Criar método `list_by_enrollments(enrollment_ids: list[str])`, se simples.
3. Normalizar `enrollment_id` e `metric_id` como string.
4. Não calcular score nesta tarefa.

**Query base:**

```sql
SELECT
  id,
  enrollment_id,
  metric_id,
  value_baseline,
  value_current,
  value_projected,
  improving_trend,
  created_at,
  updated_at
FROM deva_accmed_runtime_measurements
WHERE enrollment_id = %s;
```

**Validação mínima:**

```text
Teste cobre measurement com projected null.
```

**Critério humano de aceite:**

```text
Medições runtime são lidas sem JSON.
```

---

## T13 — Criar repository de runtime checkpoints

**Objetivo:** ler checkpoints por enrollment no Supabase.

**Arquivos prováveis:**

```text
backend/app/storage/supabase_runtime_checkpoint_repository.py
backend/tests/unit/test_supabase_runtime_checkpoint_repository.py
```

**Instruções:**

1. Criar método `list_by_enrollment(enrollment_id: str)`.
2. Ordenar por `week ASC`.
3. Normalizar `enrollment_id` como string.
4. Não alterar endpoint ainda.

**Query base:**

```sql
SELECT
  id,
  enrollment_id,
  week,
  status,
  label,
  created_at,
  updated_at
FROM deva_accmed_runtime_checkpoints
WHERE enrollment_id = %s
ORDER BY week ASC;
```

**Validação mínima:**

```text
Teste garante ordenação por week.
```

**Critério humano de aceite:**

```text
Checkpoints runtime são lidos sem JSON.
```

---

## T14 — Adicionar endpoint diagnóstico de radar por enrollment

**Objetivo:** validar métricas + medições antes de alterar `/mentor/radar`.

**Arquivos prováveis:**

```text
backend/app/api/routes/provider.py
backend/app/services/provider_hierarchy_service.py
backend/tests/api/test_provider_enrollment_radar_debug.py
```

**Endpoint sugerido:**

```http
GET /provider/me/enrollments/{enrollment_id}/metric-tree
```

**Instruções:**

1. Validar que o enrollment pertence ao provider autenticado.
2. Buscar product do enrollment.
3. Buscar pillars/metrics do product.
4. Buscar runtime measurements do enrollment.
5. Combinar por `metric_id`.
6. Retornar payload diagnóstico.

**Validação mínima:**

```text
Provider não acessa enrollment de outro provider.
Provider acessa próprio enrollment.
```

**Critério humano de aceite:**

```text
É possível ver pillars, metrics e measurements de um enrollment no endpoint diagnóstico.
```

---

## T15 — Substituir `require_mentor_profile` em `/mentor/*`

**Objetivo:** remover dependência de `MentorRepository` das rotas existentes.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/tests/api/test_mentor_routes_auth.py
```

**Instruções:**

1. Trocar `require_mentor_profile` por dependency baseada em `require_provider_user`.
2. Manter nome externo das rotas `/mentor/*`.
3. O objeto retornado deve conter pelo menos:
   - id;
   - email;
   - full_name;
   - organization_id;
   - role.
4. Não alterar lógica de dados das rotas ainda.
5. Remover import de `MentorRepository` se ficar sem uso.

**Validação mínima:**

```text
Rotas /mentor/* autenticam provider sem procurar mentors.json.
```

**Critério humano de aceite:**

```text
Provider real do Supabase passa pela autorização de /mentor/*.
```

---

## T16 — Plugar Centro de Comando no Supabase

**Objetivo:** fazer `/mentor/centro-comando/alunos` listar apenas clients do provider autenticado.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/app/services/provider_workspace_service.py ou backend/app/services/indicator_carga_service.py
backend/tests/api/test_mentor_command_center_supabase.py
```

**Instruções:**

1. Usar provider autenticado.
2. Buscar enrollments ativos por `provider_user_id`.
3. Buscar clients via `client_user_id`.
4. Buscar product via `product_id`.
5. Montar payload compatível com frontend atual.
6. Não consultar `EnrollmentRepository` local.
7. Não consultar `ProductAssignmentRepository` JSON.

**Campos mínimos por item:**

```text
id = client_id
name = client.full_name
programName = product.name
daysLeft = enrollment.days_left
ltv = investment convertido se necessário
urgency/risk = derivado simples quando não houver score completo
```

**Validação mínima:**

```text
Provider A vê Client A.
Provider A não vê Client B de outro provider.
```

**Critério humano de aceite:**

```text
Centro de Comando carrega dados reais do Supabase.
```

---

## T17 — Plugar Radar agregado `/mentor/radar/clientes`

**Objetivo:** fazer radar agregado usar clients/enrollments do provider.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/app/services/provider_workspace_service.py
backend/tests/api/test_mentor_radar_clients_supabase.py
```

**Instruções:**

1. Usar os enrollments ativos do provider.
2. Para cada enrollment, buscar metric tree + measurements.
3. Calcular médias por pilar/eixo.
4. Retornar payload compatível com frontend atual.
5. Não consultar JSON.

**Validação mínima:**

```text
Provider com 2 clients recebe radar agregado dos 2.
Provider sem measurements recebe payload vazio/controlado, não erro 500.
```

**Critério humano de aceite:**

```text
Tela Radar carrega com dados do Supabase.
```

---

## T18 — Plugar Radar individual `/mentor/radar/alunos/{client_id}`

**Objetivo:** exibir radar de um client específico apenas se ele pertence ao provider.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/app/services/provider_workspace_service.py
backend/tests/api/test_mentor_radar_student_supabase.py
```

**Instruções:**

1. Receber `client_id`.
2. Buscar enrollment ativo por `provider_user_id + client_user_id`.
3. Se não existir, retornar 404 ou 403 padronizado.
4. Buscar pillars/metrics por product.
5. Buscar measurements por enrollment.
6. Montar radar individual.
7. Não consultar JSON.

**Validação mínima:**

```text
Client próprio -> 200.
Client de outro provider -> 404/403.
Client inexistente -> 404.
```

**Critério humano de aceite:**

```text
Provider não consegue vazar dados de outro provider.
```

---

## T19 — Plugar Matriz de Renovação

**Objetivo:** fazer `/mentor/matriz-renovacao` usar enrollments do provider no Supabase.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/app/services/provider_workspace_service.py
backend/tests/api/test_mentor_renewal_matrix_supabase.py
```

**Instruções:**

1. Buscar enrollments ativos do provider.
2. Para cada enrollment, buscar client e product.
3. Calcular ou mapear:
   - progress;
   - engagement;
   - quadrant;
   - daysLeft;
   - ltv;
   - decision_matrix_status.
4. Usar `decision_matrix_status` quando houver valor confiável.
5. Não consultar JSON.

**Validação mínima:**

```text
Matriz retorna apenas clients do provider.
Filtro topRight/critical/rescue continua funcionando, se já existir.
```

**Critério humano de aceite:**

```text
Matriz mostra dados reais e filtrados do provider.
```

---

## T20 — Criar endpoint Admin Database View

**Objetivo:** expor estado completo do Supabase para validação operacional.

**Arquivos prováveis:**

```text
backend/app/api/routes/admin_database_view.py
backend/app/services/admin_database_view_service.py
backend/tests/api/test_admin_database_view_supabase.py
```

**Instruções:**

1. Endpoint deve exigir admin.
2. Buscar:
   - organizations;
   - users agrupados por role;
   - products;
   - enrollments;
   - pillars;
   - metrics;
   - measurements;
   - checkpoints.
3. Não retornar `password_hash`.
4. Não consultar JSON.
5. Incluir `integrity`.

**Payload mínimo:**

```json
{
  "organizations": [],
  "users": {
    "admins": [],
    "providers": [],
    "clients": []
  },
  "products": [],
  "enrollments": [],
  "pillars": [],
  "metrics": [],
  "measurements": [],
  "checkpoints": [],
  "integrity": {}
}
```

**Validação mínima:**

```text
Admin -> 200.
Provider -> 403.
Sem token -> 401.
password_hash não aparece.
```

**Critério humano de aceite:**

```text
Admin consegue auditar dados do Supabase em uma única resposta.
```

---

## T21 — Implementar integrity checks da Admin Database View

**Objetivo:** detectar vínculos quebrados no banco.

**Arquivos prováveis:**

```text
backend/app/services/admin_database_view_service.py
backend/tests/unit/test_admin_database_view_integrity.py
```

**Checks mínimos:**

```text
providersWithoutEnrollments
clientsWithoutEnrollments
enrollmentsWithoutProvider
enrollmentsWithoutClient
enrollmentsWithoutProduct
measurementsWithoutEnrollment
measurementsWithoutMetric
checkpointsWithoutEnrollment
productsWithoutOrganization
metricsWithoutPillar
pillarsWithoutProduct
```

**Instruções:**

1. Implementar checks em memória após consulta.
2. Retornar IDs e contexto mínimo.
3. Não falhar a API por inconsistência; reportar em `integrity`.

**Validação mínima:**

```text
Teste cria dados inconsistentes e espera entradas no integrity.
```

**Critério humano de aceite:**

```text
A tela admin ajuda a descobrir por que um provider não enxerga dados.
```

---

## T22 — Atualizar frontend para consumir `/provider/me`

**Objetivo:** permitir diagnóstico visual do provider autenticado.

**Arquivos prováveis:**

```text
frontend/src/domain/services/*
frontend/src/shared/api/*
frontend/src/features/*
frontend/src/test/*
```

**Instruções:**

1. Criar client/service para `GET /provider/me`.
2. Não duplicar lógica de auth.
3. Usar `httpClient` existente.
4. Criar teste simples do service ou hook.
5. Não alterar telas A/B/C ainda, se não for necessário.

**Validação mínima:**

```bash
cd frontend && npm test
```

**Critério humano de aceite:**

```text
Frontend consegue consultar provider atual.
```

---

## T23 — Atualizar frontend para Admin Database View

**Objetivo:** exibir dados e integrity checks do Supabase.

**Arquivos prováveis:**

```text
frontend/src/features/admin/*
frontend/src/domain/services/*
frontend/src/test/*
```

**Instruções:**

1. Consumir `GET /admin/database-view`.
2. Mostrar seções:
   - users;
   - organizations;
   - products;
   - enrollments;
   - metrics;
   - measurements;
   - checkpoints;
   - integrity.
3. Não exibir `password_hash`.
4. Mostrar estado vazio quando listas vierem vazias.
5. Mostrar erro padronizado do `httpClient`.

**Validação mínima:**

```bash
cd frontend && npm test
cd frontend && npm run build
```

**Critério humano de aceite:**

```text
Admin consegue ver no frontend o que existe no Supabase e as inconsistências.
```

---

## T24 — Atualizar frontend Centro de Comando, se necessário

**Objetivo:** garantir compatibilidade da tela com o payload Supabase.

**Arquivos prováveis:**

```text
frontend/src/features/command-center/*
frontend/src/domain/services/*
frontend/src/contracts/*
frontend/src/test/*
```

**Instruções:**

1. Verificar contrato atual da tela.
2. Ajustar adapters, não componentes, se houver diferença de payload.
3. Não colocar normalização de API dentro de JSX.
4. Manter linguagem visual “aluno” se for copy de produto.
5. Não alterar regras de backend.

**Validação mínima:**

```bash
cd frontend && npm test
cd frontend && npm run build
```

**Critério humano de aceite:**

```text
Centro de Comando renderiza clients do provider vindos do Supabase.
```

---

## T25 — Atualizar frontend Radar, se necessário

**Objetivo:** garantir compatibilidade da tela Radar com o payload Supabase.

**Arquivos prováveis:**

```text
frontend/src/features/radar/*
frontend/src/domain/services/*
frontend/src/contracts/*
frontend/src/test/*
```

**Instruções:**

1. Ajustar adapter/contract.
2. Garantir estados loading/error/empty.
3. Garantir que client sem measurements não quebra tela.
4. Não inserir regra de ownership no frontend; isso é backend.

**Validação mínima:**

```bash
cd frontend && npm test
cd frontend && npm run build
```

**Critério humano de aceite:**

```text
Radar agregado e individual carregam com dados Supabase.
```

---

## T26 — Atualizar frontend Matriz, se necessário

**Objetivo:** garantir compatibilidade da Matriz com o payload Supabase.

**Arquivos prováveis:**

```text
frontend/src/features/matrix/*
frontend/src/domain/services/*
frontend/src/contracts/*
frontend/src/test/*
```

**Instruções:**

1. Ajustar adapter/contract.
2. Validar quadrantes.
3. Validar filtros.
4. Garantir estado vazio para provider sem enrollments.

**Validação mínima:**

```bash
cd frontend && npm test
cd frontend && npm run build
```

**Critério humano de aceite:**

```text
Matriz renderiza somente clients do provider autenticado.
```

---

## T27 — Criar guardrail contra uso de JSON em runtime Supabase

**Objetivo:** impedir regressão para JSON nos fluxos A/B/C/D.

**Arquivos prováveis:**

```text
backend/app/config/runtime.py
backend/app/storage/*
backend/tests/unit/test_supabase_runtime_guardrails.py
```

**Instruções:**

1. Quando `SUPABASE_RUNTIME_REQUIRED=true`, qualquer tentativa de instanciar repository JSON para fluxo runtime deve falhar.
2. Não bloquear arquivos BMAD/docs/test fixtures.
3. Garantir erro claro.
4. Não apagar repositories antigos nesta tarefa.

**Validação mínima:**

```text
Teste garante que runtime required bloqueia fallback JSON.
```

**Critério humano de aceite:**

```text
Configuração de produção não volta para JSON silenciosamente.
```

---

## T28 — Remover imports não usados e rotas antigas não runtime

**Objetivo:** limpar dependências após os fluxos já estarem Supabase-only.

**Arquivos prováveis:**

```text
backend/app/api/routes/mentor.py
backend/app/main.py
backend/app/services/*
backend/app/storage/*
```

**Instruções:**

1. Remover import de `MentorRepository` se não usado.
2. Remover dependency antiga `require_mentor_profile` se substituída.
3. Não deletar arquivos inteiros sem validação.
4. Rodar testes relevantes.

**Validação mínima:**

```bash
cd backend && pytest backend/tests
```

**Critério humano de aceite:**

```text
O código runtime não referencia MentorRepository no fluxo provider.
```

---

## T29 — Documentar contratos finais

**Objetivo:** registrar o novo modelo oficial.

**Arquivos alvo:**

```text
docs/provider-supabase-runtime-contracts.md
README.md, se fizer sentido
```

**Instruções:**

1. Documentar:
   - roles;
   - tabelas;
   - endpoints;
   - regras de ownership;
   - payloads principais;
   - proibição de JSON runtime.
2. Não alterar código.

**Validação:**

```text
Revisão humana do documento.
```

**Critério humano de aceite:**

```text
Novo implementador entende o modelo sem perguntar.
```

---

## T30 — Validação end-to-end manual

**Objetivo:** validar o fluxo real no ambiente conectado ao Supabase.

**Arquivos alvo:**

```text
docs/execution/provider-supabase-e2e-validation.md
```

**Roteiro manual:**

1. Logar como admin.
2. Abrir Admin Database View.
3. Confirmar:
   - users por role;
   - products;
   - enrollments;
   - measurements;
   - checkpoints;
   - integrity sem erros críticos.
4. Logar como provider.
5. Abrir Centro de Comando.
6. Abrir Radar.
7. Abrir Matriz.
8. Tentar acessar client de outro provider via URL/API.
9. Confirmar bloqueio.

**Critério humano de aceite:**

```text
Admin vê tudo.
Provider vê somente sua carteira.
Nenhuma tela A/B/C/D depende de JSON.
```

---

# 8. Ordem recomendada de execução

A ordem abaixo deve ser seguida:

```text
T00
T01
T02
T03
T04
T05
T06
T07
T08
T09
T10
T11
T12
T13
T14
T15
T16
T17
T18
T19
T20
T21
T22
T23
T24
T25
T26
T27
T28
T29
T30
```

Não pular para frontend antes de validar `/provider/me/hierarchy`.

---

# 9. Definition of Done geral

A implementação só deve ser considerada concluída quando:

```text
[ ] Provider loga usando deva_accmed_users.password_hash.
[ ] /me retorna role provider.
[ ] /provider/me retorna dados do provider autenticado.
[ ] /provider/me/hierarchy retorna provider -> organization -> products -> enrollments -> clients.
[ ] /mentor/centro-comando/alunos usa Supabase.
[ ] /mentor/radar/clientes usa Supabase.
[ ] /mentor/radar/alunos/{client_id} usa Supabase e valida ownership.
[ ] /mentor/matriz-renovacao usa Supabase.
[ ] /admin/database-view usa Supabase.
[ ] password_hash nunca aparece em payload público.
[ ] Provider não vê client de outro provider.
[ ] Admin Database View mostra integrity checks.
[ ] JSON não é usado nos fluxos A/B/C/D.
[ ] Testes backend relevantes passam.
[ ] Testes/build frontend relevantes passam.
[ ] Validação manual T30 foi registrada.
```

---

# 10. Observações importantes para o agente

1. Não confundir `organization_id` com `product_id`.
2. Não transformar produto em organização.
3. Não recriar `mentors.json`.
4. Não recriar `students.json`.
5. Não usar `student` ou `aluno` como role persistida.
6. Não criar senha default para todos os clients.
7. Não exibir `password_hash`.
8. Não usar e-mail fixo para autorização admin/provider.
9. Não resolver autorização no frontend.
10. Não fazer refactor amplo do `IndicatorCargaService` antes de provar a hierarquia no endpoint diagnóstico.

---

# 11. Queries úteis para debugging

## Provider workspace

```sql
SELECT
  e.id AS enrollment_id,
  e.status AS enrollment_status,
  e.start_day,
  e.days_left,
  e.investment,
  e.decision_matrix_status,

  provider.id AS provider_id,
  provider.full_name AS provider_name,
  provider.email AS provider_email,

  client.id AS client_id,
  client.full_name AS client_name,
  client.email AS client_email,

  p.id AS product_id,
  p.name AS product_name,
  p.slug AS product_slug,
  p.category AS product_category,

  o.id AS organization_id,
  o.name AS organization_name,
  o.slug AS organization_slug

FROM deva_accmed_enrollments e
JOIN deva_accmed_users provider
  ON provider.id = e.provider_user_id
 AND provider.role = 'provider'
 AND provider.is_active = true
JOIN deva_accmed_users client
  ON client.id = e.client_user_id
 AND client.role = 'client'
 AND client.is_active = true
JOIN deva_accmed_products p
  ON p.id = e.product_id
JOIN deva_accmed_organizations o
  ON o.id = p.organization_id
WHERE e.provider_user_id = :provider_user_id
  AND e.status = 'active';
```

## Radar por enrollment

```sql
SELECT
  e.id AS enrollment_id,

  pp.id AS pillar_id,
  pp.name AS pillar_name,
  pp.slug AS pillar_slug,
  pp.order_index,

  pm.id AS metric_id,
  pm.name AS metric_name,
  pm.slug AS metric_slug,
  pm.direction,
  pm.unit,
  pm.scoring_rules,
  pm.score_type,
  pm.min_score,
  pm.max_score,
  pm.max_score_basis,
  pm.mcv,

  rm.id AS measurement_id,
  rm.value_baseline,
  rm.value_current,
  rm.value_projected,
  rm.improving_trend

FROM deva_accmed_enrollments e
JOIN deva_accmed_products p
  ON p.id = e.product_id
JOIN deva_accmed_product_pillars pp
  ON pp.product_id = p.id
 AND pp.is_active = true
JOIN deva_accmed_product_metrics pm
  ON pm.pillar_id = pp.id
 AND pm.is_active = true
LEFT JOIN deva_accmed_runtime_measurements rm
  ON rm.enrollment_id = e.id::text
 AND rm.metric_id = pm.id::text
WHERE e.id = :enrollment_id;
```

## Checkpoints por enrollment

```sql
SELECT
  id,
  enrollment_id,
  week,
  status,
  label,
  created_at,
  updated_at
FROM deva_accmed_runtime_checkpoints
WHERE enrollment_id = :enrollment_id
ORDER BY week ASC;
```
