# Demo Data Review (MVP Mentoria)

Data: 2026-03-09  
Base: `docs/mvp-mentoria/frontend-final-audit.md`

## 0) Estado atual dos dados de demonstracao

- A base persistida em `backend/data/*.json` esta vazia para mentoria/alunos/indicadores (somente `users.json` tem seed).
- Na pratica, sem carga previa, a demo abre em estados vazios.
- Conclusao: para narrativa coerente entre Centro, Radar e Matriz, e necessario seed minimo dedicado de demo.

## 1) Ajustes recomendados nos dados de demo

## 1.1 Ajustes de coerencia narrativa (recomendados agora)

1. Criar um conjunto fixo de 4 alunos com perfis distintos e previsiveis:
- 1 foco renovacao (topRight + D-45)
- 1 watch (alto engajamento, progresso medio)
- 1 rescue (baixo engajamento + checkpoints criticos)
- 1 normal (bom progresso, janela mais longa)

2. Garantir consistencia de timeline:
- `day <= total_days`
- `days_left` coerente com o ciclo e com a mensagem da tela.

3. Padronizar escala dos indicadores de radar:
- `baseline`, `current`, `projected` em faixa 0..100 para leitura visual clara.
- `projected` proximo de `current` (tipicamente +/- 5 a 12 pontos) para evitar projecao pouco crivel.

4. Preencher checkpoints com historia simples por aluno:
- casos estaveis: maioria `green`
- caso rescue: `yellow/red` com labels claras.

5. Amarrar anomalias somente onde faz sentido narrativo:
- usar `improving_trend=false` e/ou regressao de `current` vs `baseline` no aluno rescue.
- evitar anomalias em todos os alunos para nao poluir a narrativa.

6. Uniformizar nomenclatura de mentoria nos dados:
- `programName/plan` com mesmo valor para todos os alunos da mesma mentoria.

7. Ajustar LTV para faixa visual plausivel no frontend atual:
- manter valores que aparecam como ticket high-ticket sem exagero (ex.: 12.000 a 35.000 no render atual).

8. Definir ordem de criacao dos alunos:
- criar primeiro o aluno "caso principal" da demo (o primeiro tende a ser selecionado por padrao em fluxos atuais).

## 2) Ajustes que sao apenas cosmeticos

- Nome/iniciais dos alunos (mais naturais para apresentacao).
- Textos de checkpoint (`label`) e sugestao de renovacao (`suggestion`) com linguagem mais executiva.
- Balanceamento de numeros para evitar casas decimais excessivas.
- Distribuicao visual de indicadores (evitar todos os valores muito altos ou muito baixos).
- Preenchimento de `axisSub` no radar para enriquecer leitura sem alterar logica.

## 3) Ajustes arriscados nesta fase (deixar para depois)

1. Mudar formula de urgencia, quadrante, score ou KPI.
- Alto risco de quebrar coerencia com testes e contratos congelados.

2. Alterar unidade/semantica de LTV no contrato agora.
- Tema estrutural; deve ser tratado em ciclo pos-demo com validacao frontend+backend.

3. "Mascarar" inconsistencias de escala com dados artificiais extremos.
- Exemplo: distorcer `engagement` para compensar eventual diferenca de escala no KPI medio.
- Risco de incoerencia entre telas e perda de credibilidade.

4. Introduzir campos fora de contrato v1 para melhorar apresentacao.
- Vai contra congelamento de contrato.

5. Criar cenarios de excecao complexos na seed de demo.
- Aumenta risco operacional sem ganho para narrativa principal.

## 4) Plano minimo de seed/demo data (recomendado)

## 4.1 Estrutura minima

- 1 mentoria
- 1 mentor vinculado
- 1 protocolo/metodo
- 3 pilares (ex.: Compromisso, Execucao, Retencao)
- 6 metricas (2 por pilar)
- 4 alunos ativos
- carga inicial de indicadores e checkpoints para cada aluno

## 4.2 Perfis sugeridos (coerentes entre Centro, Radar e Matriz)

1. Aluno A (caso principal da demo):
- `progress_score` ~0.80, `engagement_score` ~0.78, `days_left` 18, `ltv_cents` 22000
- objetivo: aparecer em `critical` (Matriz) e com bom potencial no Radar.

2. Aluno B (watch):
- `progress_score` ~0.50, `engagement_score` ~0.72, `days_left` 45, `ltv_cents` 17000
- objetivo: mostrar gap de progresso com engajamento ainda bom.

3. Aluno C (rescue):
- `progress_score` ~0.60, `engagement_score` ~0.08, `days_left` 36, `ltv_cents` 14000
- objetivo: alimentar narrativa de recuperacao no Centro (anomalias/checkpoints criticos).

4. Aluno D (normal):
- `progress_score` ~0.68, `engagement_score` ~0.66, `days_left` 62, `ltv_cents` 26000
- objetivo: caso estavel para comparacao e previsibilidade.

## 4.3 Regras de qualidade para a seed

- Manter todos os percentuais no intervalo 0..1 nos campos de enrollment.
- Evitar `total_days = 0` na seed de demo (usar apenas em testes tecnicos).
- Garantir pelo menos 1 aluno em cada filtro relevante da Matriz:
  - `all` (todos)
  - `topRight` (>= 1)
  - `critical` (>= 1)
  - `rescue` (>= 1)
- Garantir `axisScores` com pelo menos 3 eixos para o aluno principal.
- Garantir `insight` presente no radar do aluno principal.

## 4.4 Recomendacao operacional pre-demo

- Nao mudar arquitetura nem contrato; apenas carregar seed deterministica.
- Rodar preflight apos carga para validar:
  - Centro com lista+detalhe
  - Radar com eixos e projecoes
  - Matriz com filtros e drawer
- Se algum valor parecer "estranho", ajustar apenas payload de seed (nao codigo) e revalidar.
