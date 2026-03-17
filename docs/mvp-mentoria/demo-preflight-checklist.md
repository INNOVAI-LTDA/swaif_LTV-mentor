# Demo Pre-Flight Checklist (MVP Mentoria)

Data: 2026-03-09  
Base: `docs/mvp-mentoria/frontend-final-audit.md`

## 0) Regra de operacao pre-demo
- [ ] Confirmar modo congelado: sem mudancas estruturais em frontend/backend.
- [ ] Permitir apenas ajuste bloqueador de estabilidade/apresentacao.
- [ ] Definir responsavel tecnico da demo (quem decide go/no-go final).

## 1) Verificacoes tecnicas antes de abrir a demo
- [ ] Backend responde `GET /health` com `200`.
- [ ] Smoke de autenticacao validado (`origin/scripts/f0-smoke-auth.mjs` ou equivalente) com retorno de `/me`.
- [ ] Runners criticos de frontend em `PASS`:
  - [ ] `node origin/tests/unit/f6-hardening-runner.mjs`
  - [ ] `node origin/tests/integration/f6-integration-runner.mjs`
  - [ ] `node origin/tests/e2e/f6-smoke-flow-runner.mjs`
- [ ] Sem erro de contrato visivel no console que impeça fluxo principal (Centro, Radar, Matriz).

## 2) Verificacoes de ambiente
- [ ] `API_BASE_URL` aponta para o backend alvo da demo.
- [ ] Backend ativo no host/porta esperados (ex.: `127.0.0.1:8000`).
- [ ] Frontend abre sem erro de carregamento do bundle.
- [ ] CORS funcional para origem do frontend (sem bloqueio no browser).
- [ ] Relogio/sistema estavel (evitar suspend/hibernacao durante apresentacao).

## 3) Verificacoes de autenticacao
- [ ] Login com usuario admin funciona.
- [ ] Token Bearer e aplicado nas chamadas protegidas.
- [ ] `GET /me` retorna usuario autenticado esperado.
- [ ] Logout/relogin funciona em menos de 30 segundos.
- [ ] Comportamento em token invalido segue fluxo esperado (erro guiado/logout).

## 4) Verificacoes de dados
- [ ] Existe pelo menos 1 aluno ativo para demonstracao.
- [ ] Centro retorna lista e detalhe sem payload vazio inesperado.
- [ ] Radar retorna `axisScores` com dados (incluindo `insight`).
- [ ] Matriz retorna `items` e `kpis` com valores coerentes.
- [ ] Filtros da Matriz (`all|topRight|critical|rescue`) retornam resposta valida.

## 5) Verificacoes das 3 visualizacoes

## 5.1 Centro de Comando
- [ ] Lista carrega sem erro.
- [ ] Selecao de aluno abre detalhe corretamente.
- [ ] KPIs de topo aparecem coerentes.
- [ ] Estados de loading/empty/error sem quebra de layout.

## 5.2 Radar de Transformacao
- [ ] Eixos renderizam com dados reais.
- [ ] Slider altera simulacao e agregados sem travar.
- [ ] Campos opcionais/fallbacks nao quebram render.

## 5.3 Matriz de Renovacao Antecipada
- [ ] Bolhas renderizam nos quadrantes.
- [ ] KPIs superiores aparecem corretos.
- [ ] Drawer abre com `renewalReason`, `suggestion` e `markers`.
- [ ] Troca de filtro nao gera erro visual/funcional.

## 6) Plano de contingencia rapido (backend local falhou)

Objetivo: recuperar demo em ate 5 minutos.

### Passo 1 - Isolar falha (60s)
- [ ] Confirmar se falha e backend (`/health` indisponivel) ou frontend.
- [ ] Verificar rede local/porta ocupada.

### Passo 2 - Reinicio rapido do backend (120s)
- [ ] Reiniciar backend com comando padrao do time.
- [ ] Revalidar `GET /health` e login admin.

### Passo 3 - Reentrada controlada na demo (60s)
- [ ] Recarregar frontend.
- [ ] Fazer logout/login.
- [ ] Validar rapidamente Centro -> Radar -> Matriz.

### Passo 4 - Fallback de apresentacao (se nao recuperar em 5 min)
- [ ] Seguir roteiro com evidencia ja validada (resultados `PASS` da auditoria final).
- [ ] Mostrar telas-chave e contratos ja comprovados em ambiente de teste.
- [ ] Registrar incidente e retomar demo ao vivo apenas apos backend estabilizar.

## 7) Gate final (go/no-go)
- [ ] **GO**: todos os itens criticos acima validados.
- [ ] **NO-GO**: falha em health/auth/dados base das 3 visoes.
