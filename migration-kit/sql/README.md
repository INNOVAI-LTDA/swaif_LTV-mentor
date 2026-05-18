# SQL e Runtime Stores

## Migrações versionadas
Execute os arquivos de `migrations/` em ordem numérica:

1. `001_contacts_users_v2.sql`
2. `002_organizations_v2.sql`
3. `003_link_users_organizations_v2.sql`
4. `004_products_v1.sql`
5. `005_enrollments_v1.sql`
6. `006_product_pillars_v2.sql`
7. `007_product_metrics_v1.sql`
8. `008_product_metrics_scoring_v2.sql`
9. `009_runtime_measurements_checkpoints_v1.sql`

## Seeds / runtime stores
A pasta `runtime-stores/` contém os JSONs de carga inicial e stores de runtime para bootstrap no repositório de destino.
