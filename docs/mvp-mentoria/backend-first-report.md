# Backend First Report (MVP Mentoria)

Data: 2026-03-09

## Objetivo deste fechamento
Atender os 3 fechamentos tecnicos pendentes da revisao:
1. E2E com cenario de erro critico.
2. Hardening de concorrencia basica no repositorio JSON (lock simples + teste).
3. Listagem de estrutura do metodo (endpoint + teste de contrato).

## Entregas implementadas

### 1) E2E de erro critico
- Novo teste: `backend/tests/e2e/test_smoke_mvp_flow.py::test_smoke_e2e_critical_error_invalid_indicator`
- Cobre falha critica de carga de indicador invalido com payload padronizado (`404`, `INDICADOR_NOT_FOUND`).

### 2) Concorrencia basica no repositorio JSON
- Implementado lock por arquivo no repositorio:
  - `backend/app/storage/json_repository.py`
  - lock reentrante por path para serializar `read/write` e evitar corrida em `os.replace`.
- Novo teste de concorrencia:
  - `backend/tests/test_bootstrap.py::test_json_repository_serializes_writes_with_lock`
  - valida que writes concorrentes sao serializados.

### 3) Estrutura completa do metodo
- Novo caso de uso no service:
  - `backend/app/services/method_config_service.py::get_protocol_structure`
- Novo endpoint:
  - `GET /admin/protocolos/{protocol_id}/estrutura`
  - arquivo: `backend/app/api/routes/admin_method_config.py`
- Novo teste de contrato:
  - `backend/tests/api/test_admin_method_config_api.py::test_admin_can_read_method_structure`

## Evidencia TDD (red -> green)

### Red (antes da implementacao)
Comando:
`python -m pytest tests/api/test_admin_method_config_api.py tests/e2e/test_smoke_mvp_flow.py tests/test_bootstrap.py -q`

Resultado:
- `FAILED test_admin_can_read_method_structure` (`404` no endpoint ausente)
- `FAILED test_json_repository_serializes_writes_with_lock` (concorrencia sem serializacao)

### Green (apos implementacao)
Comando:
`python -m pytest tests/api/test_admin_method_config_api.py tests/e2e/test_smoke_mvp_flow.py tests/test_bootstrap.py tests/unit/test_method_config_service.py -q`

Resultado:
- `12 passed`

## Regressao final
Comando:
`python -m pytest tests -q`

Resultado:
- `51 passed`
- `2 warnings` (deprecacao `on_event` do FastAPI)

## Atualizacao do checklist
Arquivo atualizado:
- `docs/mvp-mentoria/backend-task-checklist.md`

Itens atualizados com evidencia:
- Marco 3: `Testar listagem da estrutura do metodo` marcado como concluido.
- Secao nova de evidencias automatizadas com testes e resultados dos comandos.
