# Contrato Inicial Congelado (v1)

Data de congelamento: 2026-03-09

## Escopo
Este documento congela o contrato inicial de integracao do frontend com o backend MVP de mentoria para:
- autenticacao
- operacoes administrativas (mentoria, mentor, metodo, aluno, carga de indicadores)
- visoes de Centro de Comando, Radar e Matriz
- payload padrao de erro

## Politica de compatibilidade
- Nao remover campos existentes das respostas v1.
- Nao alterar tipo de campos existentes das respostas v1.
- Nao renomear endpoints v1.
- Qualquer mudanca breaking devera abrir nova versao de contrato.

## Naming de dominio (v1)
- Dominio funcional padronizado em: `mentor`, `aluno`, `mentoria`, `metodo`.
- Chaves tecnicas legadas e estaveis para v1:
  - `organization_id` (mentoria)
  - `protocol_id` (metodo)
- Textos de erro e semantica devem usar linguagem de mentoria.

## Payload padrao de erro (v1)
Todos os erros HTTP retornam:

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

Status alvo do hardening v1:
- `401` (nao autenticado / token invalido)
- `404` (recurso nao encontrado)
- `409` (conflito de estado/regra de negocio)
- `422` (payload de requisicao invalido)

## Contratos funcionais congelados
- Centro de Comando: `docs/mvp-mentoria/contracts-command-center.md`
- Radar: `docs/mvp-mentoria/contracts-radar.md`
- Matriz: `docs/mvp-mentoria/contracts-renewal-matrix.md`

## Testes de guarda do contrato
- `backend/tests/api/test_error_payload_api.py`
- `backend/tests/e2e/test_smoke_mvp_flow.py`
