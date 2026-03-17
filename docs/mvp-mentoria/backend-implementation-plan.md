# Backend FastAPI - plano de implementacao (MVP mentoria)

## Objetivo
Entregar backend Python com FastAPI para:
1. login e senha
2. criacao da mentoria
3. criacao e vinculo do mentor
4. cadastro dos pilares do metodo
5. cadastro das metricas/indicadores
6. cadastro e vinculo dos alunos
7. carga inicial dos indicadores
8. calculo dos dados para Centro de Comando, Radar e Matriz

Premissas:
- prioridade em simplicidade operacional e velocidade
- persistencia inicial em JSON (sem SQLite no primeiro corte)
- TDD obrigatorio em todos os marcos

## Arquitetura alvo (simples)
- Framework: FastAPI
- Servidor: Uvicorn
- Validacao: Pydantic
- Testes: pytest + TestClient
- Persistencia: arquivos JSON por agregado (auth, mentoria, mentor, aluno, indicadores, snapshots de calculo)
- Camadas:
  - `api` (routers)
  - `service` (regras de negocio e calculos)
  - `repo` (leitura/escrita JSON com lock simples)
  - `schemas` (DTOs de request/response)

## Marcos pequenos e verificaveis

### Marco 0 - Bootstrap tecnico
Escopo:
- estrutura inicial do projeto FastAPI
- healthcheck e roteamento base
- infraestrutura de testes
- repositorio JSON com escrita atomica basica

Criterio de pronto:
- `GET /health` retorna 200
- testes de bootstrap passando
- pipeline local de testes executa sem erro de import/sintaxe

Riscos:
- desenho de pastas excessivo para MVP

Simplificacoes:
- sem docker no primeiro corte
- sem migracoes de banco

---

### Marco 1 - Autenticacao simples (login/senha)
Escopo:
- cadastro inicial de usuario (seed local)
- login com senha
- emissao e validacao de token simples (JWT curto)
- dependencia de auth para rotas protegidas

Criterio de pronto:
- login invalido retorna 401
- login valido retorna token
- rota protegida falha sem token e passa com token valido

Riscos:
- aumento de complexidade se tentar RBAC agora

Simplificacoes:
- um perfil unico (mentor-admin)
- sem refresh token no MVP inicial

---

### Marco 2 - Mentoria e mentor
Escopo:
- criar mentoria
- criar mentor
- vincular mentor a mentoria
- leitura basica de mentoria com mentor vinculado

Criterio de pronto:
- nao permite vinculo para IDs inexistentes
- resposta inclui relacao mentoria-mentor consistente

Riscos:
- conflitos de nomenclatura (`programa`, `mentoria`, `protocolo`)

Simplificacoes:
- relacao 1 mentor principal por mentoria no MVP

---

### Marco 3 - Pilares e metricas do metodo
Escopo:
- cadastrar pilares da mentoria
- cadastrar metricas/indicadores
- vincular metricas a pilar
- listar estrutura completa do metodo

Criterio de pronto:
- nao aceita metrica sem pilar valido
- estrutura retornada preserva ordem e IDs

Riscos:
- excesso de flexibilidade no schema

Simplificacoes:
- sem versionamento de metodo nesta fase
- campos opcionais minimos

---

### Marco 4 - Alunos e vinculos
Escopo:
- cadastro de aluno
- vinculo aluno -> mentoria
- campos minimos para as 3 visoes (progress, engagement, urgency, day, totalDays, daysLeft, ltv)

Criterio de pronto:
- aluno sem mentoria nao entra nas consultas de visao
- validacoes de faixa (0..1 para progresso/engajamento)

Riscos:
- drift entre contrato de UI e contrato de API

Simplificacoes:
- uma mentoria ativa por aluno no MVP

---

### Marco 5 - Carga inicial de indicadores
Escopo:
- endpoint de carga inicial de indicadores por aluno
- persistencia de baseline + valor atual + projetado opcional
- checkpoints iniciais (status por semana/fase)

Criterio de pronto:
- carga rejeita indicadores nao cadastrados
- leitura detalhada do aluno retorna `metricValues` e `checkpoints`

Riscos:
- inconsistencias numericas por parse/string

Simplificacoes:
- sem historico temporal completo no primeiro corte
- apenas snapshot inicial

---

### Marco 6 - Calculos para Centro de Comando
Escopo:
- endpoint agregado da lista do Centro
- endpoint de detalhe do aluno para painel lateral
- regras derivadas: `progress%`, status de risco, gatilho D-45, score de valor

Criterio de pronto:
- lista e detalhe retornam campos consumidos pelas telas atuais
- dados derivados estao deterministicos em testes

Riscos:
- formulas de score sem especificacao fechada

Simplificacoes:
- manter formula atual inferida dos arquivos `origin/`

---

### Marco 7 - Calculos para Radar de Transformacao
Escopo:
- endpoint `axisScores` por aluno
- baseline/current/projected por eixo
- agregados de score medio para apoio de narrativa

Criterio de pronto:
- contrato compativel com `useStudentRadar/useClientRadar`
- campos ausentes tratados sem quebrar render

Riscos:
- divergencia entre nomes `axisLabel`/`pillar`

Simplificacoes:
- mapear internamente para um contrato unico e expor alias necessario

---

### Marco 8 - Calculos para Matriz de Renovacao
Escopo:
- endpoint agregado para matriz (bolhas + KPIs)
- classificacao de quadrante
- sinalizacao de prioridade de renovacao/resgate

Criterio de pronto:
- filtros `all/topRight/critical/rescue` suportados
- KPI totalLTV, D-45 criticos e resgate consistentes

Riscos:
- semantica de urgencia ambigua (`critical` vs `rescue`)

Simplificacoes:
- manter enums atuais e mapear rotulos no frontend

---

### Marco 9 - Hardening de confiabilidade
Escopo:
- padronizacao de erros
- validacoes de contrato (422/404/409)
- smoke suite final com fluxo ponta-a-ponta

Criterio de pronto:
- suite completa verde
- endpoints sobem limpos sem imports quebrados
- checklist de contratos sem divergencias conhecidas

Riscos:
- regressao tardia por mudancas de naming

Simplificacoes:
- sem otimizar performance alem do necessario para MVP

## Dependencias e ordem
- M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9
- cada marco so fecha com:
  - novos testes passando
  - reexecucao da suite completa passando
