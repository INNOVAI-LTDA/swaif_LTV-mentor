# Auditoria — Clients, Organizations e Protocols (Aplicada em `data_new`)

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

