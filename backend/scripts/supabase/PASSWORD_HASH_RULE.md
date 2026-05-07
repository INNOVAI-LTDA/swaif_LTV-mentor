# Regra `password_hash` para importação Supabase (`contacts_users_v2`)

## Decisão adotada

Foi adotada a **Opção A**:

- `password_hash` é obrigatório apenas para entidades autenticáveis (`admin` e `provider`);
- contatos `client` não devem possuir senha neste dataset (`password_hash = NULL`).

## Efeito no DDL

A tabela `contacts_users_v2` aplica `CHECK` para garantir:

- `admin/provider` -> `password_hash` não nulo e não vazio;
- `client` -> `password_hash` nulo.

## Efeito no import script

O script `import_contacts_users_v2.py` rejeita linhas inconsistentes por role com mensagens explícitas de validação.
