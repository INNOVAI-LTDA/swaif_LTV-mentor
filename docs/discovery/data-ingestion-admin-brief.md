# Brief: Ingestão de Dados no Admin

## 1. Objetivo

Adicionar uma entrada de operacao no painel administrativo chamada `Ingestão de Dados` para permitir a carga controlada de dados no backend JSON, com validacao, previsao do impacto, confirmacao explicita e trilha de auditoria.

## 2. Contexto

Hoje a carga de dados é operacional/manual.
Queremos uma forma mais segura e repetivel de executar a ingestao a partir da area administrativa, reduzindo erro humano e evitando alteracoes diretas nos arquivos JSON sem validacao.

## 3. Problema

A carga de dados real precisa ser executada com:
- seguranca
- previsibilidade
- validacao previa
- rollback viavel
- restricao por papel administrativo

Uma acao direta de "carregar tudo" em um clique é arriscada demais sem preview, sem backup e sem relatorio de resultado.

## 4. Resultado Esperado

O admin deve conseguir:

- acessar a funcionalidade `Ingestão de Dados`
- selecionar ou informar a origem da carga
- executar um `dry-run`
- visualizar resumo da validacao
- confirmar a aplicacao da carga
- obter um relatorio final com sucessos, rejeicoes e conflitos
- manter evidencias minimas para operacao e suporte

## 5. Escopo

Incluido nesta iniciativa:

- botao/menu `Ingestao de Dados` visivel apenas para papel `admin`
- tela ou modal de ingestao
- fluxo de `dry-run`
- fluxo de confirmacao
- servico backend para validacao e aplicacao
- backup/snapshot antes da escrita
- resultado estruturado da operacao
- trilha de auditoria minima
- testes nas camadas relevantes
- documentacao operacional

Fora de escopo neste momento:

- agendamento automatico
- ingestao em lote recorrente por cron
- integracao com ETL externo
- upload multiusuario simultaneo
- permissao para perfis nao administrativos
- reprocessamento automatico inteligente
- dashboard analitico completo de historico de ingestao

## 6. Ator e Permissao

Ator principal:
- usuario com role `admin`

Regra de acesso:
- a funcionalidade deve ser protegida por role administrativa
- nao deve depender do email literal `admin@swaif.local`
- `admin@swaif.local` pode ser usado apenas como conta local de validacao

## 7. Proposta de UX

Fluxo recomendado:

1. admin acessa a area administrativa
2. encontra a acao `Ingestao de Dados`
3. abre tela/modal com descricao e alertas
4. informa a origem dos dados
5. executa `Validar / Dry-run`
6. visualiza:
   - quantidade de registros recebidos
   - quantidade valida
   - quantidade rejeitada
   - conflitos encontrados
   - arquivos/entidades afetadas
7. confirma a execucao
8. sistema cria backup/snapshot
9. sistema aplica a carga
10. sistema exibe relatorio final e identificador da execucao

## 8. Fonte de Dados

Definir uma das abordagens abaixo na arquitetura:

- arquivo estruturado enviado pelo admin
- arquivo localizado em path conhecido do servidor
- payload estruturado recebido por endpoint interno
- montagem manual assistida na propria interface

Formato inicial preferido:
- arquivo estruturado e validavel
- schema explicitamente conhecido
- suporte a validacao deterministica antes da escrita

## 9. Persistencia Alvo

A ingestao deve atualizar apenas os arquivos JSON explicitamente aprovados para esta operacao.

Exemplos:
- alunos
- mentores
- programas
- relacoes
- indicadores
- configuracoes associadas

Cada alvo deve ser listado explicitamente na story correspondente.
Nao permitir escrita generica ou irrestrita em qualquer JSON do repositorio.

## 10. Regras Funcionais

- deve existir modo `dry-run`
- `dry-run` nao persiste nada
- execucao real exige confirmacao explicita
- antes da escrita deve existir backup/snapshot
- a escrita deve produzir relatorio estruturado
- conflitos devem ser retornados de forma clara
- registros invalidos nao podem quebrar o lote inteiro sem diagnostico
- o comportamento para duplicidade deve ser definido por regra:
  - rejeitar
  - atualizar
  - mesclar
- a operacao deve registrar quem executou, quando e com qual origem

## 11. Regras de Validacao

Validar pelo menos:

- schema minimo do payload
- campos obrigatorios
- tipos
- unicidade de identificadores
- referencias cruzadas
- coerencia de relacionamentos
- valores fora de dominio permitido
- impacto em registros existentes
- consistencia final antes da persistencia

## 12. Seguranca e Operacao

- acesso restrito a `admin`
- registrar trilha de auditoria minima
- nao expor paths sensiveis na UI
- nao permitir sobrescrita silenciosa sem regra definida
- falhas devem usar envelope padrao de erro da API
- a UI deve exibir falha controlada e recuperavel
- a operacao deve ser pensada primeiro para ambiente local/staging
- uso em producao deve depender de validacao operacional

## 13. Backup e Rollback

Antes da aplicacao:

- gerar snapshot/backup dos JSON afetados
- registrar local do backup
- associar backup ao identificador da execucao

Rollback minimo esperado:

- restaurar os arquivos afetados a partir do backup
- registrar que houve rollback
- permitir verificacao posterior do estado restaurado

## 14. Observabilidade e Auditoria

Registrar por execucao:

- id da execucao
- timestamp
- operador
- origem dos dados
- modo `dry-run` ou `apply`
- total recebido
- total valido
- total aplicado
- total rejeitado
- conflitos encontrados
- arquivos afetados
- backup gerado
- status final

## 15. Criterios de Aceite

- somente `admin` acessa a funcionalidade
- existe botao/entrada `Ingestao de Dados` no admin
- o fluxo de `dry-run` funciona sem persistir dados
- o preview mostra contagens e erros de validacao
- a confirmacao real gera backup antes da escrita
- a aplicacao escreve somente nos alvos previstos
- a resposta final informa sucesso parcial ou total com detalhes
- erros seguem o envelope padrao da API
- existe cobertura de testes nas camadas relevantes
- existe documentacao operacional minima
- existe caminho de rollback documentado

## 16. Riscos Principais

- sobrescrita indevida de JSON
- inconsistencias entre entidades relacionadas
- falta de rollback confiavel
- UI permissiva demais
- validacao insuficiente antes da escrita
- acoplamento excessivo entre frontend e formato bruto da carga
- ausencia de auditoria minima

## 17. Abordagem Recomendada em Batches

### Batch 1 - Entrada administrativa
- adicionar botao/menu `Ingestao de Dados`
- proteger por role `admin`
- criar tela/modal base
- sem persistencia real ainda

### Batch 2 - Contrato backend de ingestao
- definir endpoint/schema/servico
- definir payload e validacoes
- padronizar resposta de preview e aplicacao

### Batch 3 - Dry-run e preview
- executar validacao sem escrita
- retornar resumo estruturado e conflitos

### Batch 4 - Apply com backup
- criar snapshot
- persistir carga
- retornar relatorio final

### Batch 5 - Auditoria e documentacao
- registrar execucoes
- documentar operacao
- documentar rollback
- adicionar smoke tests operacionais

## 18. Perguntas em Aberto

- qual sera a origem oficial dos dados?
- qual formato sera aceito no MVP da ingestao?
- duplicidade atualiza, rejeita ou mescla?
- quais arquivos JSON sao permitidos como alvo?
- a operacao sera apenas local/staging no inicio?
- o historico de execucoes sera persistido em JSON tambem?
- o rollback sera automatico ou manual assistido?
