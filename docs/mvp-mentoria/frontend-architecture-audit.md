# Frontend Architecture Audit

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

### Estrutura geral
- A estrutura atual esta coerente com o desenho por camadas definido em `frontend-integration-architecture.md`:
  - `shared/api` para client HTTP e erros.
  - `domain/services` para chamadas de endpoint.
  - `domain/adapters` para normalizacao de payload.
  - `domain/hooks` para estado assinado por recurso.
  - `features/*` para composicao de tela.
  - `app/routes.tsx` para roteamento principal.
- Pontos positivos:
  - Separacao clara entre contrato (`src/contracts`) e modelo de dominio (`src/domain/models.ts`).
  - Adaptadores por visao (centro, radar, matriz) implementados.
  - Rotas das 3 visoes principais ativas.

### Organizacao por eixo solicitado
- `components`: existe em `features/hub`, `features/radar`, `features/matrix`.
- `screens/pages`: `features/*/pages` com 1 pagina por modulo.
- `api`: client centralizado em `shared/api/httpClient.ts`.
- `adapters`: `domain/adapters/*` cobrindo centro/radar/matriz.
- `hooks`: `domain/hooks/*` + hook de resumo do hub.
- `state`: `useAsyncResource` + estado local por pagina + `AuthProvider`.
- `routing`: `app/routes.tsx` com paths para hub/centro/radar/matriz.

## Problemas encontrados

| ID | Problema | Evidencia | Risco |
|---|---|---|---|
| ARC-01 | Paginas muito grandes, com logica de view + calculos + render no mesmo arquivo. | `CommandCenterPage.tsx` (289 linhas), `MatrixPage.tsx` (266), `RadarPage.tsx` (235). | Medio |
| ARC-02 | Padrao de estados de recurso foi duplicado em cada tela, sem uso do componente compartilhado ja existente. | `ResourceStatePanel.tsx:11` existe, mas telas implementam loading/error/empty manualmente. | Medio |
| ARC-03 | Falta de guard de rota para area `/app/*`; controle esta so no nivel de chamada de API (401). | `app/routes.tsx:18-21` expoe rotas privadas sem wrapper de autenticacao. | Medio |
| ARC-04 | Hook base de recurso nao protege contra resposta fora de ordem em mudancas rapidas (race de requests). | `useAsyncResource.ts:45-49` aplica `setData(result)` sem token de requisicao atual. | Medio |
| ARC-05 | `AppLayout` usa estilo inline e linguagem visual diferente das features, reduzindo consistencia arquitetural de UI. | `app/layout/AppLayout.tsx` inteiro (estilos inline). | Baixo |

## Classificacao de risco
- **Risco arquitetural geral: Medio**
- Motivo:
  - A base em camadas esta correta.
  - Os principais riscos sao de escalabilidade/manutencao (componentes grandes, duplicacao de padrao de estado e falta de guard de rota), nao de bloqueio funcional imediato.

## Recomendacoes de melhoria
1. Introduzir `ProtectedRoute` para `/app/*` e redirecionar sessao invalida para `/login`.
2. Refatorar `CommandCenterPage`, `RadarPage`, `MatrixPage` em subcomponentes de secao + hooks de view-model.
3. Padronizar loading/error/empty usando `ResourceStatePanel` (ou remover se nao for usar).
4. Evoluir `useAsyncResource` com controle de concorrencia (request id/abort) para evitar stale updates.
5. Padronizar `AppLayout` com CSS de app shell (sem inline) para melhorar coerencia visual e manutencao.

