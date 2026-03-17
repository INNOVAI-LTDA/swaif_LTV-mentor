# Backend FastAPI - estrategia de testes (TDD)

## Objetivo de qualidade
Garantir entrega rapida com confiabilidade alta, evitando erros basicos:
- sintaxe e imports quebrados
- endpoints que nao sobem
- contratos inconsistentes
- nomenclatura confusa no dominio de mentoria

## Principios TDD para todos os marcos
Fluxo obrigatorio por historia:
1. Escrever teste do comportamento esperado.
2. Executar teste e confirmar falha (red).
3. Implementar o minimo para passar (green).
4. Refatorar sem quebrar comportamento (refactor).
5. Rodar testes novos.
6. Rodar suite completa.

Regra de bloqueio:
- marco nao conclui se somente teste local do modulo novo passar.
- marco conclui apenas com regressao completa verde.

## Estrutura recomendada de testes
- `tests/unit/`
  - regras de calculo (quadrante, score, derivacoes)
  - validacoes de schema
- `tests/integration/`
  - API + repositorio JSON
  - auth + persistencia + contratos de resposta
- `tests/e2e/`
  - fluxo completo do MVP (login ate dados das 3 visoes)

## Escopo minimo por tipo
- Unitarios:
  - funcoes puras de calculo
  - mapeamentos de nomenclatura e enum
- Integracao:
  - endpoints com TestClient
  - leitura/escrita JSON real em pasta temporaria
- E2E:
  - cenario feliz completo
  - cenario de erro mais critico por modulo

## Dados de teste (simples e deterministico)
- usar fixtures pequenas em JSON temporario
- congelar seed minima:
  - 1 mentoria
  - 1 mentor
  - 2-3 alunos em quadrantes distintos
  - 2 pilares e 4 indicadores
- evitar aleatoriedade para estabilidade da regressao

## Contratos a validar (minimo obrigatorio)
- Auth:
  - `POST /auth/login` retorna token em sucesso
- Centro:
  - lista retorna campos da linha principal
  - detalhe retorna `metricValues` e `checkpoints`
- Radar:
  - endpoint retorna `axisScores` com campos esperados
- Matriz:
  - endpoint retorna dados para bolhas e KPIs de topo

## Matriz de regressao por marco parcial

| Marco | Testes novos obrigatorios | Regressao minima a reexecutar | Criterio de pronto do marco |
|---|---|---|---|
| M0 Bootstrap | healthcheck, import app, repositorio JSON base | 100% dos testes de bootstrap | app sobe + suite verde |
| M1 Auth | login 200/401, rota protegida 200/401 | M0 + M1 completos | auth funcional sem quebrar base |
| M2 Mentoria/Mentor | criar/vincular mentoria-mentor, erros 404 | M0..M2 | vinculos consistentes |
| M3 Pilares/Metricas | criar pilar/metrica, vinculo valido/invalido | M0..M3 | estrutura do metodo estavel |
| M4 Alunos | cadastro, vinculo, validacoes de faixa | M0..M4 | alunos prontos para calculo |
| M5 Carga inicial indicadores | carga valida/invalida, leitura detalhe | M0..M5 | detalhe com dados completos |
| M6 Centro de Comando | lista/detalhe, regras D-45 e risco | M0..M6 | contrato do Centro atendido |
| M7 Radar | `axisScores`, fallback projected, medias | M0..M7 | contrato do Radar atendido |
| M8 Matriz | quadrantes, filtros, KPIs | M0..M8 | contrato da Matriz atendido |
| M9 Hardening | smoke E2E completo e erros padrao | M0..M9 | suite final verde e estavel |

## Gates de qualidade por PR/entrega
- Gate 1: linter/sintaxe/imports ok
- Gate 2: testes do marco ok
- Gate 3: regressao completa ok
- Gate 4: validacao de contrato (campos e tipos) ok
- Gate 5: nomenclatura de dominio consistente (mentor/aluno/mentoria/metodo)

## Riscos e mitigacoes de teste
- Risco: drift entre contrato frontend atual e backend novo.
  - Mitigacao: testes de contrato para cada visao (Centro/Radar/Matriz).
- Risco: persistencia JSON gerar condicao de escrita.
  - Mitigacao: escrita atomica e testes com concorrencia basica.
- Risco: formulas mudarem sem alinhamento.
  - Mitigacao: snapshot tests de calculo e aprovacao explicita de mudanca.

## Simplificacoes assumidas nesta fase
- sem testes de carga/performance no primeiro corte
- sem testes de seguranca avancada (apenas auth basica)
- sem banco relacional no MVP inicial (JSON apenas)
