# Auditoria — Clients, Organizations e Protocols (resolvido para Products) (Aplicada em `data_new`)

## Status

As alterações propostas foram aplicadas no diretório `backend/data_new`.

## O que mudou

- `clients` deixou de ser entidade principal neste recorte.
- `organizations.json` agora representa a empresa/tenant (dados oriundos de `clients`).
- Criada `products.json` para representar o nível que antes estava em `organizations`.
- `protocols.json` passou a carregar `organization_id` e `product_id`.

## Mapeamento aplicado

- `cli_1` -> `organization cli_1`
- `cli_2` -> `organization cli_2`
- `org_1|org_2|org_3` -> `products`
- `prt_*` -> vinculado a `product_id` e `organization_id`

## Objetivo atendido

Separação explícita:

`organization (empresa)` -> `product/program` -> `protocol` -> `pillar` -> `metric`



## Atualização aplicada agora

- IDs regenerados para padrão incremental por entidade (`org_0001`, `prd_0001`, `plr_0001`, `mtr_0001`, etc.).
- `pillars` e `metrics` migrados de `protocol_id` para `product_id`.
- `protocols.json` mantido apenas como artefato compatível temporário, com `items` vazio.

- `enrollments.json` e `measurements.json` foram migrados para `data_new` com IDs e FKs remapeados para o novo modelo orientado a produto.
