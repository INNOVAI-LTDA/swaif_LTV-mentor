# Frontend Test Strategy (MVP Mentoria)

Data: 2026-03-09

## 1) Objetivo de qualidade

Garantir integracao confiavel do frontend com backend v1 sem alterar assinatura visual das telas:
- Centro de Comando
- Radar de Transformacao
- Matriz de Renovacao Antecipada

Foco:
- estabilidade de contrato
- robustez de adapters e transformacoes
- seguranca de regressao visual/funcional

## 2) Principios

1. Contrato primeiro:
- toda integracao frontend deve validar payloads contra contratos v1 congelados.

2. Teste por camada:
- adapters/utilitarios (unit)
- hooks cliente API (integracao)
- fluxo de telas (e2e)

3. Sem redesign:
- testes devem proteger estrutura e comportamento, nao impor refator visual.

4. Regressao obrigatoria:
- sem fechar marco sem rodar suite completa frontend.

## 3) Piramide de testes sugerida

## 3.1 Unitarios (base)
Cobrir:
- adapter de entidade (`patient/client/student -> student`)
- adapter de programa (`programName` com fallback `plan`)
- parser numerico (`baseline/current/projected`, `ltv`, `progress`, `engagement`)
- formatadores de percentual e moeda
- funcoes puras de calculo local:
  - simulacao do radar (`active`)
  - quadrante na matriz
  - agregados de topo quando derivados localmente

## 3.2 Integracao frontend (hooks + API client)
Cobrir:
- auth token injection
- tratamento do payload de erro padrao
- respostas 200/401/403/404/409/422
- resiliencia para campos opcionais ausentes:
  - `insight` no radar
  - `valueProjected`/`optimal` no centro
- query de filtro da matriz (`all|topRight|critical|rescue`)

## 3.3 E2E (jornada)
Cobrir fluxo minimo:
1. login
2. abrir Centro e selecionar aluno
3. abrir Radar para aluno selecionado
4. abrir Matriz e alternar filtros
5. validar render de dados sem erro de runtime

Cobrir fluxo de erro critico:
- token invalido durante navegacao -> comportamento esperado (logout/erro guiado)

## 4) Matriz de testes por visao

## Centro de Comando
- lista renderiza campos obrigatorios do contrato
- detalhe renderiza `metricValues` e `checkpoints`
- estados vazio/erro/carregando estaveis
- ausencia de anomalia/timeline nao quebra tela
- contadores de topo coerentes com lista

## Radar de Transformacao
- `axisScores` renderizado com N eixos dinamico
- fallback de `projected` quando ausente
- slider altera valores ativos e medias
- `insight` opcional nao gera crash

## Matriz de Renovacao Antecipada
- bolhas posicionadas por `progress x engagement`
- filtros sincronizados com backend
- KPIs topo batem com payload
- drawer renderiza `renewalReason`, `suggestion`, `markers`
- compatibilidade `programName/plan`

## 5) Dados de teste

Fixtures obrigatorias:
- 1 aluno `normal`
- 1 aluno `watch`
- 1 aluno `rescue`
- 1 aluno com `daysLeft <= 45` em `topRight`
- radar com eixo sem `projected`
- centro com aluno sem `checkpoints`

Regras:
- dados deterministas (sem aleatoriedade)
- payloads proximos aos contratos oficiais

## 6) Riscos de teste e mitigacao

1. CORS nao habilitado inviabiliza teste browser real.
- Mitigacao: gate de ambiente antes dos E2E.

2. Drift de contrato entre backend e adapters frontend.
- Mitigacao: testes de contrato versionados com fixtures v1.

3. Nomes legados espalhados em varios componentes.
- Mitigacao: cobrir adapter central e bloquear uso direto de aliases no dominio interno.

4. Parsing numerico inconsistentes entre telas.
- Mitigacao: parser unico + unit tests dedicados.

## 7) Gates de qualidade por marco

Gate A - Unitarios:
- adapters, formatadores e calculos locais verdes.

Gate B - Integracao:
- hooks/API client verdes para todas respostas esperadas.

Gate C - E2E:
- fluxo feliz das 3 visoes + 1 fluxo de erro critico verde.

Gate D - Regressao final:
- suite completa frontend verde em CI/local.

## 8) Evidencias esperadas por entrega

- comandos executados (unit, integracao, e2e)
- quantidade de testes executados e aprovados
- registro de falhas conhecidas (se houver) com plano de correcao
- confirmacao de alinhamento com `contracts-freeze-v1.md`
