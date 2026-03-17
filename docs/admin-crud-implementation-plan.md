# Admin CRUD Implementation Plan

## Objetivo

Definir a ordem de implementacao da Fase 2 em blocos pequenos, consumiveis e testaveis, sem tentar fechar todo o CRUD administrativo de uma vez.

## Estrategia de fase

Principios operacionais:

- cada bloco entrega uma capacidade utilizavel
- cada bloco deve terminar com UI abrivel e teste executado
- manter a tela Admin atual e substituir apenas o minimo necessario
- priorizar blocos que destravam dependencias reais
- usar soft delete como padrao

## Baseline de interface reaproveitavel

Os proximos blocos devem preservar o padrao consolidado no Bloco 1:

- a abertura do `Centro Institucional` mostra apenas o contexto ativo principal do bloco
- no contexto raiz, o CTA dedicado de create fica no topo direito da secao principal
- nas areas de apoio com contexto selecionado, usar `Cadastrar...` no canto esquerdo como seletor unico de entidade
- o create acontece por modal com confirmacao e sucesso curto
- a leitura da entidade pai e das entidades filhas acontece na area central
- paineis deslizantes nao devem voltar como recurso padrao
- estados vazios podem anunciar o proximo bloco, sem antecipar implementacao fora do escopo
- a area `Clientes` deve manter o par `cliente selecionado + cards de produtos`, usando apenas `Cadastrar Produto...` quando ainda nao houver produto
- a area `Produtos` deve manter leitura sequencial `Produto -> Mentor -> Pilar`, com card agregador de pilar antes do CRUD real de pilares

## Ordem recomendada

## Bloco 1 - Cliente/Empresa: selecao, listagem e detalhe

### Objetivo

Criar o contexto raiz da administracao real.

### Escopo

- listagem de clientes/empresas
- detalhe institucional do cliente selecionado
- estado vazio, loading e erro
- create individual minimo

### Fora do escopo

- update completo
- desativacao
- importacao em lote

### Dependencias

- nenhuma

### Entrega consumivel

- Admin abre em contexto real de Cliente/Empresa
- usuario consegue cadastrar e selecionar um cliente
- abertura limpa mostra apenas clientes ativos
- area `Clientes` vira o molde base para Cliente -> Produto

### Criterio de pronto

- API de list/detail/create disponivel
- frontend com selecao funcional
- testes de API e smoke de navegacao aprovados

## Bloco 2 - Produto/Mentoria: listagem, detalhe e create

### Objetivo

Destravar a primeira camada operacional dependente do cliente.

### Escopo

- listar produtos por cliente
- detalhar produto selecionado
- create individual de produto/mentoria

### Fora do escopo

- update
- desativacao
- multiproduto por lote

### Dependencias

- Bloco 1

### Entrega consumivel

- cliente selecionado exibe seus produtos
- admin consegue criar uma nova mentoria para o cliente
- a secao de produtos substitui o estado vazio hoje reservado ao Bloco 2
- a area `Produtos` reaproveita o bloco em leitura sequencial para preparar `Mentor` e `Pilar` sem introduzir painel lateral ou detalhe expandido

### Criterio de pronto

- relacao Cliente -> Produto navegavel
- validacao de unicidade por cliente
- testes API e frontend aprovados

## Bloco 3 - Mentor: listagem, create e vinculo principal

### Objetivo

Operacionalizar a estrutura humana da mentoria.

### Escopo

- listar mentores por produto
- create individual de mentor
- vinculo principal mentor -> produto

### Fora do escopo

- redistribuicao complexa
- multiplos produtos por mentor

### Dependencias

- Bloco 2

### Entrega consumivel

- produto passa a ter mentores reais vinculados
- o card `Mentor` da area `Produtos` deixa de ser placeholder e passa a refletir o mentor principal sem alterar a ordem visual `Produto -> Mentor -> Pilar`

### Criterio de pronto

- create e vinculacao funcionando
- bloqueio para IDs invalidos
- testes unitarios, API e smoke aprovados

## Bloco 4 - Aluno: listagem, create e vinculo principal

### Objetivo

Colocar a base acompanhada em operacao real.

### Escopo

- listar alunos por produto e por mentor
- create individual de aluno
- vinculo primario aluno -> mentor -> produto

### Fora do escopo

- reatribuicao entre mentores
- update amplo de cadastro

### Dependencias

- Bloco 3

### Entrega consumivel

- Admin consegue cadastrar aluno e ve-lo na carteira do mentor

### Criterio de pronto

- fluxo create completo sem dados mockados
- listagens coerentes por produto e mentor
- testes API e smoke aprovados

## Bloco 5 - Pilares: listagem, create e ordenacao

### Objetivo

Transformar a estrutura do metodo em cadastro administravel.

### Escopo

- listar pilares do produto
- create individual de pilar
- definir `order_index`

### Fora do escopo

- update de reposicionamento em massa
- desativacao de pilares com metricas ativas

### Dependencias

- Bloco 2

### Entrega consumivel

- Admin consegue estruturar o metodo por pilares reais
- o card agregador de `Pilar` passa a abrir e recolher verticalmente a lista de pilares do produto na propria area `Produtos`

### Criterio de pronto

- ordem preservada em leitura
- validacao de chave unica por produto
- testes aprovados

## Bloco 6 - Metricas: listagem e create

### Objetivo

Completar a estrutura minima necessaria para ingestao real.

### Escopo

- listar metricas por pilar
- create individual de metrica
- validacoes de `direction`, alvo e unidade

### Fora do escopo

- edicao estrutural apos carga
- exclusao fisica

### Dependencias

- Bloco 5

### Entrega consumivel

- pilar passa a ter indicadores reais prontos para ingestao

### Criterio de pronto

- leitura por pilar estavel
- conflito por codigo coberto
- testes aprovados

## Bloco 7 - Vinculos administrativos

### Objetivo

Separar alteracoes relacionais das edicoes simples.

### Escopo

- reatribuicao de aluno entre mentores
- desvinculo logico controlado
- validacoes hierarquicas
- exigencia de justificativa

### Fora do escopo

- automacoes de redistribuicao
- bulk operations

### Dependencias

- Blocos 2, 3 e 4

### Entrega consumivel

- Admin consegue corrigir relacionamento sem quebrar historico

### Criterio de pronto

- historico preservado
- conflitos bloqueados
- testes cobrindo cenarios de reatribuicao e desvinculo

## Bloco 8 - Ingestao inicial de indicadores

### Objetivo

Fechar a ponte entre cadastro administrativo e visoes analiticas reais.

### Escopo

- carga inicial por aluno
- checkpoints iniciais
- validacao contra metricas ativas
- retorno consumivel para Centro, Radar e Matriz

### Fora do escopo

- importacao multiarquivo
- reconciliacao automatica
- versao historica completa

### Dependencias

- Blocos 4, 5 e 6

### Entrega consumivel

- aluno cadastrado passa a alimentar as visoes reais da plataforma

### Criterio de pronto

- carga valida refletida nas telas reais
- falhas de contrato cobertas
- testes API, integracao e smoke aprovados

## Blocos de consolidacao

Os blocos abaixo nao devem ser executados antes do fechamento do core acima.

## Bloco 9 - Update administrativo por entidade

### Objetivo

Adicionar edicao controlada apos a base estar utilizavel.

### Escopo

- formularios de update
- justificativa obrigatoria
- bloqueios para campos estruturais

### Dependencias

- Blocos 1 a 8 conforme a entidade alvo

## Bloco 10 - Desativacao administrativa por entidade

### Objetivo

Adicionar remocao segura sem comprometer integridade.

### Escopo

- desativacao logica
- mensagens de impacto
- bloqueios por filhos ativos
- reativacao com justificativa

### Dependencias

- Blocos 1 a 8 conforme a entidade alvo

## Sequenciamento tecnico recomendado

1. backend do bloco
2. testes de unidade e API do bloco
3. integracao frontend minima no Admin
4. smoke navegavel do bloco
5. registro de artefatos e evidencias

## Sequenciamento visual recomendado dentro do Admin

1. manter a abertura limpa do `Centro Institucional`
2. reaproveitar o card do contexto pai ja selecionado
3. preencher a coluna ou grade da entidade filha do bloco
4. adicionar create por modal no topo da secao raiz ou via `Cadastrar...` na area de apoio, conforme o contexto
5. validar estado vazio, sucesso, erro e retorno imediato na tela

## Dependencias de dados

| Bloco | Dependencia minima de dados |
|---|---|
| 1 | nenhum seed adicional obrigatorio |
| 2 | Cliente/Empresa ativo |
| 3 | Produto/Mentoria ativa |
| 4 | Produto/Mentoria e Mentor ativos |
| 5 | Produto/Mentoria ativa |
| 6 | Pilar ativo |
| 7 | entidades relacionadas ativas |
| 8 | Aluno vinculado e Metricas ativas |

## Testes minimos por bloco

Cada bloco deve encerrar com:

1. teste de unidade da regra de negocio principal
2. teste de API para sucesso e falha principal
3. teste frontend ou smoke que prove uso real da entrega

## Riscos e mitigacoes

| Risco | Mitigacao |
|---|---|
| misturar Cliente/Empresa com Produto/Mentoria no modelo atual | explicitar adaptacao ou migracao antes do bloco 1 |
| tentar fechar update e delete cedo demais | manter foco em list/detail/create primeiro |
| quebrar a tela Admin validada | introduzir CRUD apenas nas areas necessarias |
| hard delete gerar perda de rastreabilidade | manter desativacao logica como padrao |

## Regra de corte da fase

A fase so pode ser considerada operacionalmente iniciada quando o Bloco 1 estiver navegavel sem mock local para o contexto selecionado.
