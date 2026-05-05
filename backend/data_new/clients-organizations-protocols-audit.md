# Auditoria — Clients, Organizations e Protocols

## Objetivo

Extrair e expor as três entidades do dataset original para evidenciar o problema de modelagem e propor ajuste.

## Extração (origem: `backend/data`)

- `clients.json`
- `organizations.json`
- `protocols.json`

Também foram copiados para `backend/data_new/` para análise isolada.

## Leitura atual das relações

1. `clients` (2 registros) parecem representar a empresa/conta raiz.
2. `organizations` (3 registros) parecem representar produtos/programas comercializados.
3. `protocols` (3 registros) estão vinculados a `organization_id` (1:1 no estado atual).

### Mapeamento observado

- `cli_2` -> `org_1` -> `prt_1`
- `cli_1` -> `org_2` -> `prt_2`
- `cli_1` -> `org_3` -> `prt_3`

## Problema identificado

A semântica atual está conflitando com o domínio esperado:

- A entidade `organization` está se comportando como **produto/programa**.
- A entidade `client` está se comportando como **organização/empresa real**.
- Isso gera ambiguidade de nomenclatura e confusão de regra de negócio.

## Proposta de ajuste (recomendado)

### Opção A (recomendada pelo relato)

- **Remover `clients`** como entidade de negócio explícita.
- **Promover `organizations`** para entidade raiz (tenant/empresa).
- Criar entidade explícita para o nível que hoje está em `organizations`:
  - `products` ou `programs` (novo nome)
- Vincular `protocols` a `products/programs`.

Fluxo alvo:

`organization (empresa)` -> `product/program` -> `protocol` -> `pillar` -> `metric`

### Opção B (se quiser manter `clients`)

- Renomear:
  - `clients` -> `organizations`
  - `organizations` -> `products` (ou `programs`)
- Mantém dados, muda contrato de nomenclatura para refletir o domínio real.

## Migração sugerida

1. Introduzir nova tabela lógica `products` (ou `programs`) com dados atuais de `organizations`.
2. Ajustar FKs:
   - `enrollments.organization_id` -> `enrollments.product_id` (ou `program_id`)
   - Introduzir `enrollments.organization_id` real da empresa raiz.
3. Atualizar `protocols.organization_id` para `protocols.product_id`.
4. Atualizar serviços e adapters frontend/backend para nova semântica.
5. Deprecar/remover `clients` após migração e compatibilidade.

## Decisão pendente para validação

Escolher entre:

- A) eliminar `clients` e simplificar com `organization` como raiz + `product/program` explícito
- B) manter ambos, com renomeação semântica (`clients`=organization, `organizations`=product)

