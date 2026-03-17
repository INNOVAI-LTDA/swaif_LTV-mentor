# Frontend Risk Assessment

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

## Resumo executivo
- Status geral: **funcionalmente pronto para evolucao**, com **risco tecnico geral Medio**.
- Bloqueadores imediatos de contrato: **nao identificados**.
- Principais riscos para proxima fase:
  1. baixa cobertura de testes para regressao,
  2. consistencia semantica de indicadores da Matriz,
  3. robustez de estado assincrono em trocas rapidas.

## Matriz de riscos

| ID | Categoria | Descricao | Probabilidade | Impacto | Nivel |
|---|---|---|---|---|---|
| RSK-01 | Testes | Cobertura atual nao protege regressao de fluxo integrado (Centro/Radar/Matriz). | Alta | Alto | Alto |
| RSK-02 | Integracao | Escala/unidade de KPI (`avgEngagement`, `ltv`) pode gerar divergencia de exibicao. | Media | Alto | Medio-Alto |
| RSK-03 | UX de erro | Erros de refresh podem ficar pouco visiveis quando ha dado em tela. | Media | Medio | Medio |
| RSK-04 | Estado async | Hook de recurso sem controle de resposta fora de ordem. | Media | Medio | Medio |
| RSK-05 | Arquitetura | Paginas extensas dificultam evolucao e revisao de comportamento. | Alta | Medio | Medio |
| RSK-06 | Acesso | Rotas `/app/*` sem guard de autenticacao explicito. | Media | Medio | Medio |
| RSK-07 | Dependencia `origin` | Dependencia estrutural indevida com `origin`. | Baixa | Alto | Baixo (monitorado) |

## Problemas encontrados (consolidados)
- Nao ha dependencia estrutural com `origin/` (risco residual baixo).
- Endpoints consumidos estao alinhados ao contrato congelado v1.
- Faltam testes de integracao/e2e previstos na estrategia.
- Ha inconsistencias potenciais de semantica de indicadores na Matriz.
- Estado assincrono pode sofrer race condition em mudanca rapida de selecao.
- Componentes de tela concentram muitas responsabilidades.

## Classificacao de risco por eixo solicitado
- Arquitetura: **Medio**
- Integracao backend: **Medio**
- Qualidade de codigo: **Medio**
- Estados de interface: **Medio**
- Robustez: **Medio**
- Consistencia visual: **Baixo-Medio**
- Dependencias indevidas (`origin`): **Baixo**
- Testes: **Alto**

## Recomendacoes priorizadas

### P0 (antes de evolucoes de produto)
1. Expandir testes conforme `frontend-test-strategy.md`:
   - contrato/hook por visao,
   - fluxo e2e minimo das 3 telas.
2. Definir semantica canonica para `avgEngagement` e unidade de `ltv` no frontend.

### P1 (curto prazo)
1. Implementar guard de rota para `/app/*`.
2. Evoluir `useAsyncResource` com protecao contra requests fora de ordem.
3. Padronizar exibicao de erros de refresh com componente comum.

### P2 (proxima iteracao de manutencao)
1. Quebrar paginas grandes em subcomponentes/hook de view-model.
2. Ajustar semantica visual de urgencia na Matriz (`critical` x `rescue`).
3. Uniformizar shell visual do app (`AppLayout`) com padrao das features.

## Conclusao
- O frontend reconstruido esta coerente com os contratos principais e com a arquitetura base planejada.
- O maior risco para avancar rapido sem regressao esta na profundidade de testes e na consolidacao semantica de alguns indicadores.
- Recomendacao: executar P0 e P1 antes de iniciar mudancas amplas de produto.

