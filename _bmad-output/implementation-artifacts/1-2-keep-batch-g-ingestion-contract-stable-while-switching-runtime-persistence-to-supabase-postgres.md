# Story 1.2: Keep Batch G Ingestion Contract-Stable While Switching Runtime Persistence to Supabase/Postgres

Status: done

## Story

Como mantenedor da plataforma,
quero manter o contrato v1 do Batch G estavel enquanto movemos a persistencia de runtime para Supabase/Postgres,
para que a evolucao interna de storage nao quebre frontend, operacao e testes de regressao.

## Fontes Autoritativas (Normativas para esta Story)

- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-11.md`
- `docs/architecture/new_database_architecture.md`
- `docs/mvp-mentoria/contracts-freeze-v1.md`
- `docs/mvp-mentoria/frontend-integration-architecture.md`
- `_bmad-output/project-context.md`

## Escopo (In)

1. Reforcar o caminho de escrita/leitura de runtime para entidades de ingestao aprovadas usando repositorios Supabase/Postgres.
2. Preservar endpoints v1, tipos e envelope padrao de erro.
3. Remover dependencia de fallback JSON em caminhos de runtime de producao para a ingestao Batch G.
4. Explicitar comportamento para dominios ainda nao resolvidos sem fallback silencioso.

## Fora de Escopo (Out)

1. Redesenho amplo de contratos v1 ou de nomenclatura de payload.
2. Refatoracao geral de toda a camada de storage fora das entidades desta story.
3. Migracao historica completa de todos os dominios nao relacionados ao fluxo Batch G desta etapa.

## Restricoes de Arquitetura e Contrato (Obrigatorias)

1. Manter layering `routes -> services -> repositories`.
2. Preservar envelope de erro `{ error: { status, code, message, details } }`.
3. Runtime de producao: Supabase/Postgres como autoridade de persistencia.
4. Nao permitir fallback JSON silencioso em request path de producao.
5. Manter handlers de rota finos; regra de negocio permanece em `backend/app/services`.

## Dependencias

- Story 1.1 concluida com baseline de persistencia autoritativa.
- Definicao de schema alvo conforme `new_database_architecture.md`.

## Escopo de Arquivos Alvo (Explicito)

- Repositorio/persistencia:
  - `backend/app/storage/product_assignment_repository.py`
  - `backend/app/storage/measurement_repository.py`
  - `backend/app/storage/checkpoint_repository.py`
  - `backend/app/storage/measurement_overall_repository.py`
- Servico:
  - `backend/app/services/indicator_carga_service.py`
- Rotas (handler fino + mapeamento de erro):
  - `backend/app/api/routes/admin_students.py`
- Config/runtime guard:
  - `backend/app/config/runtime.py`
- Testes obrigatorios desta story:
  - `backend/tests/unit/test_indicator_carga_service.py`
  - `backend/tests/api/test_admin_indicator_load_api.py`
  - `backend/tests/api/test_error_payload_api.py`
  - `backend/tests/integration/test_indicator_repositories.py`

## Criterios de Aceite (BDD)

### AC1 - Runtime authority em Supabase/Postgres

**Dado** que o operador executa fluxo de ingestao Batch G no ambiente de producao  
**Quando** o backend persistir dados aprovados da ingestao  
**Entao** as escritas autoritativas ocorrem em repositorios Supabase/Postgres  
**E** nenhum path de escrita de producao depende de JSON como system-of-record.

### AC2 - Contrato v1 preservado no boundary HTTP

**Dado** chamadas v1 existentes para os fluxos administrativos afetados  
**Quando** o runtime interno usar repositorios Postgres  
**Entao** endpoints, nomes de campos, tipos e semantica de resposta permanecem compativeis com `contracts-freeze-v1.md`  
**E** o envelope de erro padrao continua inalterado.

### AC3 - Sem fallback JSON silencioso em producao

**Dado** uma falha de acesso ao repositorio Postgres em ambiente de producao  
**Quando** a requisicao de ingestao for processada  
**Entao** o backend retorna erro padronizado explicito  
**E** nao tenta fallback automatico para repositorios JSON no mesmo request path.

### AC4 - Dominios nao resolvidos com gate explicito

**Dado** dominios ainda nao migrados totalmente para o schema alvo  
**Quando** um fluxo exigir esses dados em runtime de producao  
**Entao** o comportamento de bloqueio/degradacao e explicito e testado  
**E** nao existe fallback oculto para JSON que mascare o gap de migracao.

### AC5 - Regressao funcional e de contrato

**Dado** as suites de regressao de API/servico para os fluxos impactados  
**Quando** os testes executarem com runtime Postgres  
**Entao** os cenarios passam com contrato v1 preservado  
**E** quaisquer checks de JSON ficam apenas como artefato de migracao/offline, nao como criterio de runtime authority.

## Contrato de Modo de Producao (Obrigatorio e Testavel)

### Chaves de configuracao

- `APP_ENV`
- `SUPABASE_DB_URL`
- `SUPABASE_SYNC_ON_STARTUP`

### Regra de classificacao de ambiente

- Ambiente local/dev/test: `APP_ENV` em `{local, development, dev, test}`.
- Ambiente de producao-like: qualquer valor fora desse conjunto.

### Comportamento exigido por ambiente

1. Producao-like:
- Fluxos de runtime da ingestao Batch G devem usar repositorios Postgres como autoridade.
- `SUPABASE_DB_URL` ausente ou invalido deve falhar de forma explicita no fluxo (sem fallback para JSON no mesmo request path).
- Falha de acesso Postgres deve retornar erro padronizado (envelope v1) com codigo de runtime Postgres indisponivel.

2. Local/dev/test:
- Pode usar armazenamento local para fluxo de desenvolvimento e testes.
- Essa excecao nao pode mudar o comportamento de producao-like nem habilitar fallback silencioso no mesmo path quando `APP_ENV` for producao-like.

3. Bootstrap/sync:
- `SUPABASE_SYNC_ON_STARTUP=true` sem `SUPABASE_DB_URL` deve falhar no startup (comportamento ja alinhado ao runtime atual).
- Esse sync de startup nao autoriza fallback JSON em request-time para ambientes producao-like.

## Matriz de Dominios Nao Resolvidos (Gate Explicito)

| Dominio | Acao em runtime de producao-like | Codigo de erro |
| --- | --- | --- |
| `measurement_overalls` (resumo/projecao derivada) | Bloquear escrita autoritativa no path que dependa desse dominio sem implementacao Postgres completa; retornar falha explicita | `POSTGRES_DOMAIN_NOT_READY` |
| `checkpoints` (timeline operacional) | Se repositorio Postgres do dominio nao estiver pronto, bloquear carga/aplicacao que dependa dele; nao desviar para JSON | `POSTGRES_DOMAIN_NOT_READY` |
| `measurements` (medicoes base) | Se dependencia Postgres indisponivel, falhar operacao de ingestao com erro de runtime; nao executar persistencia parcial em JSON | `POSTGRES_RUNTIME_UNAVAILABLE` |
| `legacy json stores` (qualquer store `*.json`) | Tratar como artefato de migracao/offline; proibido como system-of-record em request-time producao-like | `JSON_FALLBACK_FORBIDDEN` |

## Tarefas / Subtarefas

- [x] Atualizar wiring de servicos da ingestao Batch G para repositorios Postgres (AC: 1, 3)
- [x] Garantir erro explicito sem fallback JSON em producao (AC: 3, 4)
- [x] Preservar mapping de DTOs/respostas no boundary v1 (AC: 2, 5)
- [x] Atualizar testes de servico e API para baseline Postgres (AC: 5)
- [x] Registrar gates de dominio nao resolvido sem fallback silencioso (AC: 4)

## Dev Notes

- Priorizar mudanca minima e localizada nas camadas de repositorio/servico ja existentes.
- Nao mover normalizacao de contrato para componentes frontend.
- Se houver necessidade de comportamento temporario, manter explicitamente isolado de paths de runtime de producao.

### Project Structure Notes

- Backend: `backend/app/api/routes`, `backend/app/services`, `backend/app/storage`.
- Testes backend: `backend/tests/unit`, `backend/tests/api`, `backend/tests/integration`.
- Sem criacao de nova arquitetura paralela; estender padroes existentes.

### Testes Minimos Obrigatorios

1. Teste de servico cobrindo falha de repositorio Postgres sem fallback JSON em producao.
2. Testes de API cobrindo preservacao de contrato v1 e envelope de erro padronizado.
3. Teste de integracao para escrita/leitura autoritativa no repositorio Postgres afetado.

### Comando Minimo de Validacao (primeiro passe)

`python -m pytest backend/tests/unit/test_indicator_carga_service.py backend/tests/api/test_admin_indicator_load_api.py backend/tests/api/test_error_payload_api.py backend/tests/integration/test_indicator_repositories.py -q`

### Referencias

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-05-11.md]
- [Source: docs/mvp-mentoria/contracts-freeze-v1.md]
- [Source: docs/mvp-mentoria/frontend-integration-architecture.md]
- [Source: _bmad-output/project-context.md]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References
- `Set-Location backend; $env:PYTHONPATH='.vendor;.'; python -m pytest tests/unit/test_indicator_carga_service.py tests/api/test_admin_indicator_load_api.py -q --basetemp .tmp_pytest_batchg`
- `Set-Location backend; $env:PYTHONPATH='.vendor;.'; python -m pytest tests/api/test_error_payload_api.py tests/integration/test_indicator_repositories.py -q --basetemp .tmp_pytest_batchg`

### Completion Notes List
- Implementado caminho explicito `JSON_FALLBACK_FORBIDDEN` no `load_initial_indicators` para runtime production-like quando repositorios de measurements/checkpoints ainda sao JSON-backed.
- Mantido envelope v1 no boundary HTTP com novo mapeamento `409` + `error.code=JSON_FALLBACK_FORBIDDEN`.
- Preservado gate existente `POSTGRES_RUNTIME_UNAVAILABLE` e cobertura de `POSTGRES_DOMAIN_NOT_READY` quando fallback JSON nao se aplica.
- Cobertura focada atualizada em unit e API para os caminhos de runtime production-like.
- Substituida deteccao heuristica por sinalizacao explicita e estavel de capacidade (`_uses_json_runtime_for_indicator_load`) para impedir acoplamento a atributos privados de repositorio.
- Renomeado teste de API para refletir corretamente o resultado esperado de `JSON_FALLBACK_FORBIDDEN`.
- Reforcadas assercoes de testes de API para validar envelope v1 completo (`status`, `code`, `message`, `details`) nos caminhos 409 desta story.
- Gate final da story executado com sucesso (`7 passed`): `test_error_payload_api` + `test_indicator_repositories`.
- Release note: request-time em ambiente production-like agora retorna `JSON_FALLBACK_FORBIDDEN` quando o path de carga inicial depender de repositórios JSON, preservando o envelope de erro v1.

### File List
- `backend/app/services/indicator_carga_service.py`
- `backend/app/api/routes/admin_students.py`
- `backend/tests/unit/test_indicator_carga_service.py`
- `backend/tests/api/test_admin_indicator_load_api.py`

## Post-Story Final Production-Like Validation (2026-05-12)

Validation scope executed:
- `backend/.env` (`SUPABASE_DB_URL` confirmed as PostgreSQL DSN; secret not printed)
- `backend/scripts/supabase/sql/009_runtime_measurements_checkpoints_v1.sql` (applied in real Supabase runtime)
- `scripts/validate-story-1-2.ps1 -SupabaseDbUrl "<REAL_SUPABASE_DB_URL>"`

Result highlights:
- `mentor_blocked_admin_endpoint`: pass (`403`, `AUTH_FORBIDDEN`)
- `production_like_uses_postgres_path`: pass with **`200` success path**
- `postgres_runtime_unavailable`: pass (`409`, `POSTGRES_RUNTIME_UNAVAILABLE`)
- `local_without_db_url_runtime_unavailable`: pass (`409`, `POSTGRES_RUNTIME_UNAVAILABLE`)
- `domain_not_ready_coverage_pytest`: pass (`2 passed`)

Final enforcement status:
- No-JSON policy remains active in production-like request path.
- Runtime fallback to JSON is not used in indicator initial load.

## Post-Review Hardening (2026-05-12)

- Validation script hardened: `production_like_uses_postgres_path` now passes only with `status=200` in Scenario 1 (real Supabase path).
- Robustness matrix rerun with real `SUPABASE_DB_URL`: all checks passed with strict Scenario 1 gate.
- Focused regression rerun completed:
  - `python -m pytest tests/unit/test_indicator_carga_service.py tests/api/test_admin_indicator_load_api.py -q --basetemp .tmp_pytest_story_1_2_review`
  - Result: `12 passed`.

Readiness note:
- Story 1.2 is ready for merge/release under the stricter runtime validation criteria.
