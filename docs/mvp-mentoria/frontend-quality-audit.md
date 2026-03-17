# Frontend Quality Audit

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

### 1) Qualidade de codigo (acoplamento, duplicacao, responsabilidades)
- Pontos positivos:
  - Existe separacao entre `service`, `adapter`, `hook` e `page`.
  - `httpClient` centraliza timeout, erro de rede e parse de payload de erro.
- Pontos de atencao:
  - Logica de view e regra derivada ainda concentradas em paginas longas.
  - Repeticao de mapeamentos de urgencia e estados de recurso entre telas.
  - Componente utilitario `ResourceStatePanel` nao foi incorporado no fluxo real.

### 2) Estados de interface (loading/error/empty)
- Estados estao implementados nas 3 visoes principais.
- Porem, o padrao nao esta uniformizado:
  - componentes e textos variam por tela,
  - alguns erros aparecem apenas em estado sem dados.

### 3) Robustez (falha de API e dados inesperados)
- Pontos positivos:
  - `httpClient` cobre timeout, network error, parse de erro padrao v1 e evento de 401.
  - adapters fazem coercao defensiva de tipos e fallbacks.
- Riscos:
  - `useAsyncResource` nao previne race de requests concorrentes por mudanca rapida de selecao.
  - Nao ha camada padrao de notificacao global para refresh com erro.

### 4) Consistencia visual
- Assinatura visual geral foi preservada:
  - Hub: linguagem mais clara/executiva.
  - Centro/Radar/Matriz: linguagem analitica em fundo escuro.
- Divergencia funcional/visual observada:
  - semantica de cor para `critical` na Matriz pode conflitar com leitura de risco (observacao ja antecipada no gap analysis).

### 5) Dependencias indevidas com `origin/`
- Auditoria de codigo nao encontrou import/referencia estrutural ao path `origin`.
- Conclusao: o frontend reconstruido esta estruturalmente independente.

### 6) Testes (cobertura e qualidade)
- Suite atual:
  - 3 arquivos de teste (`adapters`, `formatters`, `routes smoke`)
  - 6 casos no total.
- Lacunas em relacao a `frontend-test-strategy.md`:
  - faltam testes de hooks de integracao.
  - faltam testes de estados de tela (loading/error/empty).
  - faltam testes de contrato para matrix/command-center/auth error payload.
  - nao ha e2e do fluxo completo (login -> centro -> radar -> matriz).

## Problemas encontrados

| ID | Problema | Evidencia | Risco |
|---|---|---|---|
| QLT-01 | Componentes de pagina grandes e com muita responsabilidade. | `CommandCenterPage.tsx` (289), `MatrixPage.tsx` (266), `RadarPage.tsx` (235). | Medio |
| QLT-02 | Padrao de estado repetido em vez de componente compartilhado. | `ResourceStatePanel.tsx:11` existe, nao utilizado nas telas principais. | Medio |
| QLT-03 | Possivel inconsistencia por race condition em carga assincrona. | `useAsyncResource.ts:45-49` sem controle de request atual. | Medio |
| QLT-04 | Feedback de erro em refresh nao e totalmente consistente entre telas. | Condicionais de erro em `CommandCenterPage.tsx:105`, `RadarPage.tsx:128/167`, `MatrixPage.tsx:137`. | Baixo |
| QLT-05 | Semantica visual de urgencia `critical` na Matriz pode confundir prioridade. | `matrix.css:278` (`mx-bubble--critical`) vs `matrix.css:283` (`mx-bubble--rescue`). | Medio |
| QLT-06 | Cobertura de testes abaixo da estrategia definida para integracao MVP. | Apenas 6 testes em `src/test/*`. | Alto |

## Classificacao de risco
- **Risco de qualidade geral: Medio-Alto**
- Motivo:
  - Implementacao funcional e com boa base tecnica.
  - Principal fragilidade esta na profundidade dos testes e na padronizacao de estado/robustez da camada de UI.

## Recomendacoes de melhoria
1. Extrair subcomponentes e hooks de view-model das paginas grandes.
2. Padronizar estados com um unico componente utilitario (`ResourceStatePanel` ou equivalente).
3. Adicionar controle de concorrencia em `useAsyncResource` (request id/cancelamento).
4. Revisar paleta/semantica de `critical` x `rescue` na Matriz para reduzir ambiguidade operacional.
5. Expandir suite de testes em 3 frentes:
   - unitario de adapters faltantes,
   - integracao de hooks com mock de API,
   - e2e do fluxo completo das 3 visoes.

