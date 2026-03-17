# Frontend Integration Audit

Data: 2026-03-09

## Referencias usadas
- `docs/mvp-mentoria/contracts-freeze-v1.md`
- `docs/mvp-mentoria/contracts-command-center.md`
- `docs/mvp-mentoria/contracts-radar.md`
- `docs/mvp-mentoria/contracts-renewal-matrix.md`
- `docs/mvp-mentoria/frontend-backend-gap-analysis.md`
- `docs/mvp-mentoria/frontend-integration-architecture.md`
- `docs/mvp-mentoria/frontend-integration-plan.md`
- `docs/mvp-mentoria/frontend-test-strategy.md`
- `docs/mvp-mentoria/backend-readiness-for-frontend.md`
- `docs/mvp-mentoria/naming-and-domain-notes.md`

## Analise objetiva

### Mapeamento de endpoints consumidos
- Auth:
  - `POST /auth/login` (`domain/services/authService.ts:7`)
  - `GET /me` (`domain/services/authService.ts:14`, `:33`)
- Centro:
  - `GET /admin/centro-comando/alunos` (`commandCenterService.ts:6`)
  - `GET /admin/centro-comando/alunos/{student_id}` (`:11`)
  - `GET /admin/centro-comando/alunos/{student_id}/timeline-anomalias` (`:16`)
- Radar:
  - `GET /admin/radar/alunos/{student_id}` (`radarService.ts:10`)
- Matriz:
  - `GET /admin/matriz-renovacao?filter=...` (`matrixService.ts:7`)

Conclusao: os endpoints consumidos estao alinhados ao congelamento v1 e ao readiness atual do backend.

### Adaptadores de contrato
- Centro: `adaptCommandCenterListPayload`, `adaptCommandCenterDetail`, `adaptTimelineAnomalies`.
- Radar: `adaptRadarPayload` com fallback de `projected`.
- Matriz: `adaptMatrixPayload` + `normalizeMatrixFilter` + fallback de aliases.
- Naming legado (`client/patient`) tratado centralmente em `domainAdapter.ts:39`.

Conclusao: ha camada de adaptacao adequada e coerente com a arquitetura planejada.

### Dependencia de dados hardcoded
- Nao foram encontradas dependencias estruturais de mock dataset nas features.
- Observacao: a tela de login mantem credenciais pre-preenchidas para ambiente local (`LoginPage.tsx:8-9`).

## Problemas encontrados

| ID | Problema | Evidencia | Risco |
|---|---|---|---|
| INT-01 | Semantica de `avgEngagement` da matriz esta ambigua no dominio (0..1 vs 0..100). | `matrixAdapter.ts:82` usa payload bruto; `deriveMatrixKpis` em `:93` calcula media 0..1; `MatrixPage.tsx` precisou criar `formatPercentKpi`. | Medio |
| INT-02 | Hub ignora `kpis` do contrato de matriz e recalcula localmente a partir dos itens. Pode divergir da regra oficial de backend no futuro. | `useHubSummary.ts:16` usa `deriveMatrixKpis(matrixResource.data)`. | Medio |
| INT-03 | Unidade de `ltv` segue ambigua (valor derivado de `ltv_cents` no backend) e front formata direto como moeda. | Gap/readiness documentam ambiguidade; uso direto em `formatCurrencyBRL(...)` nas telas. | Medio |
| INT-04 | Erro de refresh pode ficar silencioso quando ja existe dado carregado na tela (erro so aparece no estado vazio em partes da UI). | `RadarPage.tsx:128,167`; `MatrixPage.tsx:137`; `CommandCenterPage.tsx:105` condicionam erro em cenarios especificos. | Baixo |
| INT-05 | Falta teste automatizado de contrato de frontend para todos os DTOs e filtros. | Suite atual cobre apenas 2 adapters e smoke de rota. | Medio |

## Classificacao de risco
- **Risco de integracao geral: Medio**
- Motivo:
  - Integracao core com backend esta correta e completa para as 3 visoes.
  - Os riscos atuais estao em consistencia semantica (escala/unidade) e em ausencia de testes de contrato mais amplos.

## Recomendacoes de melhoria
1. Definir contrato canonico de escala para `avgEngagement` (recomendado: sempre 0..1 no dominio frontend).
2. No Hub, consumir `kpis` do backend como fonte primaria e usar derivacao local apenas como fallback declarado.
3. Formalizar unidade de `ltv` no contrato e normalizar no adapter (ex.: converter centavos para reais quando aplicavel).
4. Exibir feedback de erro de refresh mesmo quando houver dado previo (banner nao-bloqueante).
5. Adicionar testes de contrato de frontend para:
  - `matrix` (filtros + `kpis`)
  - `command-center` (timeline/anomaly)
  - `auth` (payload de erro padrao v1)

