# Investigação: falha ao extrair métricas a partir dos pilares no Radar

Data: 2026-05-07

## Escopo
Testes e análise focados no fluxo: acessar Radar de Evolução -> visualizar pilares -> acessar métricas.

## Resultado principal
O fluxo de **drill-down de métricas por pilar não está implementado na tela de Radar do mentor**.

- A página `RadarPage` renderiza apenas os eixos/pilares retornados por `useStudentRadar`, sem nenhuma ação de seleção de pilar para carregar métricas.
- O serviço de radar chama apenas `GET /mentor/radar/alunos/{student_id}`.
- Não existe chamada para endpoints de métricas na feature `frontend/src/features/radar`.

## Evidências técnicas

1. `RadarPage` lista os pilares (`axisScores`) e exibe base/real/meta, mas não dispara carregamento de métricas por pilar.
2. `getStudentRadar` consulta apenas `/mentor/radar/alunos/{student_id}`.
3. Endpoints de métricas existentes estão no namespace admin (`/admin/pilares/{pillar_id}/metricas`) e no workspace do aluno (`/aluno/workspace/pilares/{pillar_id}/metricas`), mas não são consumidos pela tela de Radar do mentor.

## Interpretação
A percepção de “consigo ver os pilares, mas não consigo extrair as métricas” é consistente com o código atual: o radar mentor entrega visão agregada por eixo e **não possui UX nem integração para abrir métricas do pilar**.

## Próxima correção sugerida (menor patch seguro)
1. Definir no produto qual endpoint deve alimentar o drill-down no Radar do mentor (admin vs mentor-scoped).
2. Adicionar interação de seleção de pilar na `RadarPage`.
3. Criar hook/resource específico para carregar métricas por pilar.
4. Cobrir com teste de UI no `frontend/src/test` garantindo fluxo completo de drill-down.
