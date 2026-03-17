# Admin CRUD Checklist

## Objetivo

Checklist operacional para acompanhar a Fase 2 do MVP em blocos pequenos, sem misturar escopos.

## Regras da fase

- [ ] Executar um bloco por vez.
- [ ] Encerrar cada bloco com algo abrivel, testavel e validavel.
- [ ] Nao alterar telas validadas alem do necessario para suportar o CRUD.
- [ ] Priorizar soft delete em vez de remocao fisica.
- [ ] Registrar `task_id`, `task_title`, `started_at`, `finished_at`, `status`, `summary` e `artifacts`.
- [ ] Nao fechar bloco sem testes do proprio bloco.
- [ ] Manter abertura do `Centro Institucional` limpa, sem elementos concorrentes desnecessarios.
- [ ] Manter o CTA dedicado de create no topo direito do contexto raiz do bloco.
- [ ] Manter o seletor contextual `Cadastrar...` nas areas de apoio com contexto selecionado.
- [ ] Usar modal com confirmacao e sucesso curto para create administrativo.
- [ ] Nao reintroduzir painel deslizante como padrao da superficie administrativa.
- [ ] Evitar fichas expandidas residuais quando a leitura puder ser resolvida apenas por cards.

## Checklist transversal de modelagem

- [ ] Hierarquia canonica validada: Cliente -> Produto -> Mentor -> Aluno.
- [ ] Hierarquia de metodo validada: Produto -> Pilar -> Metrica.
- [ ] Politica de update com justificativa definida.
- [ ] Politica de desativacao logica definida.
- [ ] Chaves unicas definidas por entidade.
- [ ] Campos obrigatorios definidos por entidade.
- [ ] Dependencias entre blocos definidas.

## Bloco 1 - Cliente/Empresa

- [ ] Listagem administrativa definida.
- [ ] Detalhe administrativo definido.
- [ ] Campos obrigatorios de create definidos.
- [ ] Regra de update definida.
- [ ] Regra de desativacao definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 2 - Produto/Mentoria

- [ ] Dependencia de Cliente/Empresa confirmada.
- [ ] Card do cliente selecionado preservado como ancora visual.
- [ ] Listagem por cliente definida.
- [ ] Secao lateral ou adjacente de produtos substitui o estado vazio do Bloco 1.
- [ ] Area `Produtos` definida em ordem `Produto -> Mentor -> Pilar`.
- [ ] Card atual de produto sem ficha expandida residual.
- [ ] Card agregador de `Pilar` previsto para expandir/recolher verticalmente no bloco de pilares.
- [ ] Campos obrigatorios de create definidos.
- [ ] Regra de update definida.
- [ ] Regra de desativacao definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 3 - Mentor

- [ ] Dependencia de Produto/Mentoria confirmada.
- [ ] Listagem por produto definida.
- [ ] Campos obrigatorios de create definidos.
- [ ] Regra de update definida.
- [ ] Regra de desativacao definida.
- [ ] Regra de bloqueio por alunos ativos definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 4 - Aluno

- [ ] Dependencia de Produto/Mentoria confirmada.
- [ ] Dependencia de Mentor confirmada.
- [ ] Listagem por produto e por mentor definida.
- [ ] Campos obrigatorios de create definidos.
- [ ] Regra de update definida.
- [ ] Regra de desativacao definida.
- [ ] Preservacao de historico definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 5 - Pilar

- [ ] Dependencia de Produto/Mentoria confirmada.
- [ ] Listagem por produto definida.
- [ ] Campos obrigatorios de create definidos.
- [ ] Regra de update definida.
- [ ] Regra de desativacao definida.
- [ ] Regra de ordenacao definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 6 - Metrica

- [ ] Dependencia de Pilar confirmada.
- [ ] Listagem por pilar definida.
- [ ] Campos obrigatorios de create definidos.
- [ ] Regras de `direction` definidas.
- [ ] Regra de update definida.
- [ ] Regra de desativacao definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 7 - Vinculos

- [ ] Operacoes de vinculo cobertas.
- [ ] Regras de reatribuicao definidas.
- [ ] Regras de desvinculo logico definidas.
- [ ] Exigencia de justificativa definida.
- [ ] Preservacao de historico definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Bloco 8 - Ingestao de indicadores

- [ ] Dependencias de Aluno e Metricas confirmadas.
- [ ] Payload minimo de ingestao definido.
- [ ] Regras de checkpoint definidas.
- [ ] Regra de recarga/correcao definida.
- [ ] Regra de historico definida.
- [ ] Criterio de pronto definido.
- [ ] Testes minimos do bloco definidos.

## Gate de inicio de implementacao

- [ ] `docs/admin-crud-spec.md` revisado.
- [ ] `docs/admin-crud-implementation-plan.md` revisado.
- [ ] `docs/admin-crud-checklist.md` revisado.
- [ ] Ordem dos blocos aprovada.
- [ ] Primeira entrega escolhida.

## Gate de encerramento de cada bloco

- [ ] UI abrivel e navegavel.
- [ ] Funcionalidade do bloco operando sem mock local para o escopo coberto.
- [ ] Testes do bloco executados.
- [ ] Evidencias registradas.
- [ ] Log de execucao atualizado.
- [ ] Baseline visual do Admin preservada ou evoluida sem regressao de limpeza.
- [ ] Se houver area de apoio, o `Cadastrar...` deve permanecer coerente com o escopo ja implementado e com os proximos blocos.
