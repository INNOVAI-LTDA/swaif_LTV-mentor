# Migration Kit (para viagem)

Este pacote isola o núcleo portátil para bootstrap em outro repositório.

## Estrutura

- `sql/`
  - `migrations/`: schema SQL versionado
  - `runtime-stores/`: seeds e stores de runtime em JSON
- `backend-integration/`
  - `services/`: regras de negócio
  - `storage/`: persistência e repositórios
  - `schemas/`: DTOs/schemas backend
  - `config/runtime.py`: contrato de ambiente/runtime
  - `api/errors.py`: envelope padronizado de erro
- `contracts/`
  - `backend/`: contratos congelados v1
  - `frontend/`: DTOs de contrato do frontend
- `env.example`: variáveis centralizadas para backend/frontend

## Ordem recomendada de bootstrap no novo repositório

1. Copiar `migration-kit/` para a raiz do repositório destino.
2. Aplicar SQL de `sql/migrations/` em ordem numérica.
3. Importar dados iniciais de `sql/runtime-stores/` conforme a estratégia do destino (seed ou carga de runtime).
4. Integrar `backend-integration/` no backend destino mantendo a separação rota -> serviço -> repositório.
5. Integrar `contracts/` para manter compatibilidade de payload e DTO.
6. Configurar variáveis do `env.example` no ambiente alvo.

## Contrato de erros (obrigatório)

Manter envelope padrão:

```json
{
  "error": {
    "status": 409,
    "code": "MENTORIA_CONFLICT",
    "message": "...",
    "details": null
  }
}
```

## Remoção de acoplamentos locais no destino

Antes de publicar:

- remover branding e cópias específicas do projeto de origem
- remover defaults locais de demo/preview
- substituir URLs hardcoded por variáveis de ambiente
- validar conflitos de nomes de tabela/chave

## Smoke tests mínimos de portabilidade

1. **Auth**
   - login válido retorna token
   - token inválido retorna `401` no envelope padrão
2. **Endpoints críticos**
   - listar alunos no centro de comando
   - consultar radar por aluno
   - consultar matriz de renovação
3. **Carga inicial**
   - endpoint de carga inicial persiste dados esperados
   - validação de erro para payload inválido retorna `422` padrão

## Publicação no outro repositório

1. Subir o kit como módulo/pasta inicial (`migration-kit/`) na branch de implantação.
2. Documentar no README do destino a sequência oficial de setup (SQL -> seeds -> integração -> env -> smoke).
3. Executar smoke tests em ambiente integrado antes de merge para trunk.
