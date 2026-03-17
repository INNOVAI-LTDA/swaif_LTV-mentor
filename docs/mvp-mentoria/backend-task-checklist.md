# Backend FastAPI - checklist de implantacao e codificacao

## Regras de execucao (obrigatorias)
- [ ] Em cada marco: criar testes primeiro (TDD)
- [ ] Confirmar falha inicial esperada (red)
- [ ] Implementar o minimo necessario (green)
- [ ] Rodar testes novos do marco
- [ ] Rodar suite completa existente
- [ ] Nao fechar marco sem suite completa verde

## Marco 0 - Bootstrap tecnico
- [ ] Criar estrutura de pastas (`api`, `service`, `repo`, `schemas`, `tests`)
- [ ] Configurar app FastAPI e `GET /health`
- [ ] Configurar pytest e TestClient
- [ ] Criar repositorio JSON base com escrita atomica
- [ ] Criar teste de healthcheck 200
- [ ] Criar teste de erro de rota inexistente (404)

## Marco 1 - Autenticacao simples
- [ ] Definir schema de login (usuario, senha)
- [ ] Implementar endpoint de login
- [ ] Implementar geracao/validacao de token
- [ ] Proteger endpoint de exemplo com dependencia auth
- [ ] Teste login invalido -> 401
- [ ] Teste login valido -> 200 com token
- [ ] Teste rota protegida sem token -> 401
- [ ] Teste rota protegida com token -> 200

## Marco 2 - Mentoria e mentor
- [ ] Criar schema de mentoria
- [ ] Criar schema de mentor
- [ ] Implementar endpoint criar mentoria
- [ ] Implementar endpoint criar mentor
- [ ] Implementar endpoint de vinculo mentor -> mentoria
- [ ] Testar vinculo com IDs inexistentes -> 404
- [ ] Testar leitura da mentoria com mentor vinculado

## Marco 3 - Pilares e metricas
- [ ] Criar schema de pilar
- [ ] Criar schema de metrica/indicador
- [ ] Implementar endpoint cadastrar pilar
- [ ] Implementar endpoint cadastrar metrica
- [ ] Implementar vinculo metrica -> pilar
- [ ] Testar rejeicao de metrica sem pilar
- [x] Testar listagem da estrutura do metodo

## Marco 4 - Alunos e vinculos
- [ ] Criar schema de aluno com campos minimos das visoes
- [ ] Implementar endpoint cadastrar aluno
- [ ] Implementar endpoint vincular aluno -> mentoria
- [ ] Validar faixas de progresso/engajamento (0..1)
- [ ] Testar rejeicao de vinculo com mentoria inexistente
- [ ] Testar consulta de alunos por mentoria

## Marco 5 - Carga inicial de indicadores
- [ ] Criar schema de carga inicial de indicadores
- [ ] Implementar persistencia de baseline/current/projected
- [ ] Implementar persistencia de checkpoints
- [ ] Testar rejeicao de indicador nao cadastrado
- [ ] Testar leitura de detalhe do aluno com indicadores carregados

## Marco 6 - Calculo para Centro de Comando
- [ ] Implementar endpoint agregado de lista do Centro
- [ ] Implementar endpoint de detalhe do aluno
- [ ] Implementar derivacoes: progresso%, risco, D-45, score de valor
- [ ] Testar contrato de lista com campos obrigatorios
- [ ] Testar contrato de detalhe com `metricValues` e `checkpoints`
- [ ] Testar casos limite (`daysLeft=45`, `engagement=0`, `totalDays=0` protegido)

## Marco 7 - Calculo para Radar
- [ ] Implementar endpoint de `axisScores` por aluno
- [ ] Garantir campos `axisKey`, `axisLabel`, `axisSub`, `baseline`, `current`, `projected`
- [ ] Tratar `projected` ausente com fallback para `current`
- [ ] Testar calculo de media baseline/current/projected
- [ ] Testar compativel com contratos `useStudentRadar/useClientRadar`

## Marco 8 - Calculo para Matriz
- [ ] Implementar endpoint agregado da matriz
- [ ] Implementar classificacao de quadrante
- [ ] Implementar KPIs (LTV total, D-45 criticos, resgate, engajamento medio)
- [ ] Testar filtros (`all`, `topRight`, `critical`, `rescue`)
- [ ] Testar estabilidade dos campos usados em bolha/drawer

## Marco 9 - Hardening final
- [x] Padronizar payload de erro (401/404/409/422)
- [x] Revisar naming de dominio (mentor/aluno/mentoria/metodo)
- [x] Revisar semantica de labels e mensagens de erro
- [x] Criar smoke tests E2E do fluxo completo
- [x] Executar suite completa final sem falhas
- [x] Congelar contrato inicial para integracao frontend

## Evidencias automatizadas (2026-03-09)
- [x] Teste de estrutura do metodo: `tests/api/test_admin_method_config_api.py::test_admin_can_read_method_structure`
- [x] Teste E2E de erro critico: `tests/e2e/test_smoke_mvp_flow.py::test_smoke_e2e_critical_error_invalid_indicator`
- [x] Teste de concorrencia basica JSON/lock: `tests/test_bootstrap.py::test_json_repository_serializes_writes_with_lock`
- [x] Regressao do bloco de fechamento: `python -m pytest tests/api/test_admin_method_config_api.py tests/e2e/test_smoke_mvp_flow.py tests/test_bootstrap.py tests/unit/test_method_config_service.py -q` -> `12 passed`
- [x] Suite completa backend: `python -m pytest tests -q` -> `51 passed`

## Checklist de implantacao local (simples)
- [ ] Definir versao Python alvo
- [ ] Instalar dependencias minimas (`fastapi`, `uvicorn`, `pytest`)
- [ ] Definir pasta de dados JSON e arquivo de seed
- [ ] Criar script de start local
- [ ] Criar script unico de execucao de testes
