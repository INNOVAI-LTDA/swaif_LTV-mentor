# Admin CRUD Spec

## Objetivo

Definir a especificacao funcional da Fase 2 do MVP: operacoes administrativas reais.

Esta fase nao implementa tudo de uma vez. O objetivo e destravar uma trilha incremental, consumivel e testavel para transformar a tela Admin de superficie visual em operacao real.

## Escopo canonico

Hierarquia alvo da fase:

- Cliente/Empresa -> Produto/Mentoria -> Mentor -> Aluno
- Produto/Mentoria -> Pilar -> Metrica

Escopo administrativo coberto por esta especificacao:

1. Cliente/Empresa
2. Produto/Mentoria
3. Mentor
4. Aluno
5. Pilares
6. Metricas
7. Vinculos entre entidades
8. Ingestao de indicadores

## Premissas obrigatorias da fase

- Entregas pequenas, testaveis e navegaveis.
- Um bloco por vez.
- Soft delete como padrao.
- Nenhuma tela validada deve ser redesenhada; apenas adaptada ao CRUD.
- Fluxos administrativos devem preservar rastreabilidade.
- Cada operacao de update e desativacao exige justificativa.

## Regras transversais

### 1. Operacoes permitidas por etapa

Cada bloco deve seguir a ordem abaixo, salvo necessidade tecnica pontual:

1. Read
2. Create
3. Update
4. Delete

Nao e obrigatorio concluir as quatro operacoes no mesmo bloco de entrega. O esperado e fechar uma unidade util, abrivel e validavel.

### 2. Auditoria minima

Campos operacionais obrigatorios sempre que houver alteracao de estado:

| Campo | Regra |
|---|---|
| `responsavel` | preenchido automaticamente com o usuario autenticado |
| `justificativa` | obrigatorio em update, desativacao e reativacao |
| `requested_at` | timestamp da operacao |

Observacao: em create, `justificativa` e opcional no MVP inicial.

### 3. Remocao

- Nao usar remocao fisica como comportamento padrao.
- O padrao da fase e `is_active=false` e `status=inactive` quando aplicavel.
- Registros inativos continuam legiveis em historico e para consistencia relacional.

### 4. Busca e selecao administrativa

Toda operacao administrativa deve partir de contexto selecionado, evitando alteracao solta:

1. selecionar Cliente/Empresa
2. selecionar Produto/Mentoria
3. selecionar entidade filha aplicavel

Excecao: cadastro de Cliente/Empresa, por ser a raiz da hierarquia.

### 5. Chaves unicas

| Entidade | Chave unica minima |
|---|---|
| Cliente/Empresa | `cnpj` e `slug` |
| Produto/Mentoria | `client_id + code` ou `client_id + slug` |
| Mentor | `cpf` e `email` |
| Aluno | `cpf` e, quando houver, `email` |
| Pilar | `product_id + code` |
| Metrica | `pillar_id + code` |

### 6. Politica de update

- Update parcial e permitido para campos nao estruturais.
- Campos de identidade fiscal ou relacional principal nao devem mudar sem justificativa.
- Mudancas de vinculo entre entidades devem ser tratadas no bloco de Vinculos, nao como update simples.

## Especificacao por entidade

## 1. Cliente/Empresa

### Papel

Raiz administrativa do ambiente. Define o contexto para produtos, mentores e alunos.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `name` | nome empresarial ou nome principal de exibicao |
| `cnpj` | unico, validado e imutavel apos ativacao inicial |
| `slug` | unico e tecnico |
| `status` | default `active` |

### Campos opcionais de create

- `brand_name`
- `logo_url`
- `timezone`
- `currency`
- `notes`

### Regras de update

- Pode atualizar `name`, `brand_name`, `logo_url`, `timezone`, `currency`, `notes`.
- `cnpj` so pode ser corrigido com justificativa e trilha de auditoria.
- `slug` so pode mudar antes de haver produtos ativos vinculados.

### Regras de remocao/desativacao

- Sempre via soft delete.
- Nao pode desativar se houver Produto/Mentoria ativa vinculada.
- Reativacao exige justificativa.

### Dependencias

- Nenhuma para create.
- E pre-requisito para Produto/Mentoria.

## 2. Produto/Mentoria

### Papel

Oferta operada dentro do Cliente/Empresa. E o centro da estrutura pedagogica e operacional.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `client_id` | Cliente/Empresa ativo obrigatorio |
| `name` | nome comercial da mentoria |
| `code` | identificador tecnico unico dentro do cliente |
| `status` | default `active` |

### Campos opcionais de create

- `description`
- `start_date`
- `end_date`
- `delivery_model`
- `brand_icon_url`

### Regras de update

- Pode atualizar `name`, `description`, datas, `delivery_model`, `brand_icon_url`, `status`.
- `client_id` e imutavel apos create.
- `code` so muda com justificativa e sem dependencia externa ativa.

### Regras de remocao/desativacao

- Sempre via soft delete.
- Nao pode desativar se houver mentor ativo, aluno ativo, pilar ativo ou ingestao ativa vinculada.
- Antes de desativar, os filhos devem estar encerrados ou desativados.

### Dependencias

- Depende de Cliente/Empresa ativo.
- Desbloqueia Mentor, Pilar e vinculos posteriores.

## 3. Mentor

### Papel

Responsavel operacional pela carteira de alunos dentro da mentoria.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `product_id` | Produto/Mentoria ativo obrigatorio |
| `full_name` | nome completo |
| `cpf` | unico e validado |
| `email` | unico e normalizado |
| `status` | default `active` |

### Campos opcionais de create

- `phone`
- `bio`
- `notes`

### Regras de update

- Pode atualizar `full_name`, `email`, `phone`, `bio`, `notes`, `status`.
- `cpf` so pode ser corrigido com justificativa.
- Mudanca de produto principal deve ser tratada como operacao de vinculo controlado.

### Regras de remocao/desativacao

- Sempre via soft delete.
- Nao pode desativar se houver aluno ativo sob sua responsabilidade sem reatribuicao.
- Reatribuicao deve acontecer antes da desativacao.

### Dependencias

- Depende de Produto/Mentoria ativo.
- Desbloqueia cadastro e movimentacao de alunos.

## 4. Aluno

### Papel

Entidade acompanhada na operacao da mentoria.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `product_id` | Produto/Mentoria ativo obrigatorio |
| `mentor_id` | Mentor ativo obrigatorio |
| `full_name` | nome completo |
| `cpf` | unico e validado |
| `status` | default `active` |

### Campos opcionais de create

- `email`
- `phone`
- `birth_date`
- `origin`
- `notes`

### Regras de update

- Pode atualizar dados pessoais e de contato.
- Mudanca de mentor deve passar pelo bloco de Vinculos.
- `cpf` so pode ser corrigido com justificativa.

### Regras de remocao/desativacao

- Sempre via soft delete.
- Ao desativar, os vinculos ativos e ingestoes futuras devem ser bloqueados.
- Historico de indicadores e snapshots precisa permanecer acessivel.

### Dependencias

- Depende de Produto/Mentoria e Mentor ativos.
- E pre-requisito para ingestao de indicadores.

## 5. Pilar

### Papel

Camada estrutural do metodo da mentoria.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `product_id` | Produto/Mentoria ativo obrigatorio |
| `name` | nome de exibicao |
| `code` | identificador tecnico unico dentro do produto |
| `order_index` | ordenacao no radar e listagens |
| `status` | default `active` |

### Campos opcionais de create

- `description`
- `axis_sub`
- `icon_url`

### Regras de update

- Pode atualizar `name`, `description`, `axis_sub`, `icon_url`, `order_index`, `status`.
- `product_id` e `code` sao estruturais e exigem justificativa forte para alteracao.

### Regras de remocao/desativacao

- Sempre via soft delete.
- Nao pode desativar se houver metrica ativa vinculada.

### Dependencias

- Depende de Produto/Mentoria ativo.
- Desbloqueia Metricas.

## 6. Metrica

### Papel

Indicador operacional ligado a um pilar.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `pillar_id` | Pilar ativo obrigatorio |
| `name` | nome de exibicao |
| `code` | identificador tecnico unico dentro do pilar |
| `direction` | `higher_better`, `lower_better` ou `target_range` |
| `status` | default `active` |

### Campos opcionais de create

- `unit`
- `target_min`
- `target_max`
- `target_text`
- `weight`
- `description`

### Regras de update

- Pode atualizar rotulo, unidade, alvo, peso e descricao.
- `direction` nao deve mudar depois de existir medicao ativa sem migracao controlada.
- `code` so muda com justificativa e sem carga consolidada em uso.

### Regras de remocao/desativacao

- Sempre via soft delete.
- Nao remove historico; apenas bloqueia novas ingestoes e novas exibicoes padrao.
- Se houver historico, a metrica continua legivel em visoes antigas.

### Dependencias

- Depende de Pilar ativo.
- E pre-requisito para ingestao de indicadores.

## 7. Vinculos entre entidades

### Papel

Operacoes relacionais que nao devem ser tratadas como edicao simples.

### Vinculos cobertos

| Vinculo | Regra inicial do MVP |
|---|---|
| Cliente/Empresa -> Produto/Mentoria | obrigatorio |
| Produto/Mentoria -> Mentor | obrigatorio |
| Produto/Mentoria -> Pilar | obrigatorio |
| Pilar -> Metrica | obrigatorio |
| Mentor -> Aluno | obrigatorio |
| Produto/Mentoria -> Aluno | obrigatorio |

### Campos obrigatorios por operacao

| Campo | Regra |
|---|---|
| `source_id` | entidade origem |
| `target_id` | entidade destino |
| `responsavel` | usuario autenticado |
| `justificativa` | obrigatoria em troca, desvinculo ou reatribuicao |

### Regras de update

- Reatribuicao de Aluno entre mentores deve preservar historico.
- Troca de Produto/Mentoria principal de Mentor ou Aluno exige validacao de compatibilidade.
- Nao pode existir filho ativo sem pai ativo.

### Regras de remocao/desativacao

- Desvinculo nao apaga historico.
- Vinculo principal ativo deve ser unico quando a regra de negocio exigir contexto unico.
- No MVP inicial, cada Aluno tem um vinculo primario ativo com um Mentor e uma Mentoria.

### Dependencias

- Depende das entidades ja cadastradas e ativas.

## 8. Ingestao de indicadores

### Papel

Carregar mediacoes e checkpoints do aluno para alimentar Centro, Radar e Matriz.

### Campos obrigatorios de create

| Campo | Regra |
|---|---|
| `student_id` ou `enrollment_id` | contexto alvo da ingestao |
| `product_id` | validacao de contexto |
| `metric_values[]` | ao menos uma linha valida |
| `metric_values[].metric_id` | metrica ativa obrigatoria |
| `metric_values[].value_current` | valor numerico obrigatorio |
| `checkpoints[]` | lista inicial obrigatoria no primeiro carregamento |
| `checkpoints[].week` | inteiro nao negativo |
| `checkpoints[].status` | `green`, `yellow` ou `red` |
| `checkpoints[].label` | descricao curta |

### Campos opcionais de create

- `metric_values[].value_baseline`
- `metric_values[].value_projected`
- `metric_values[].improving_trend`
- `source_type`
- `batch_reference`

### Regras de update

- Reprocessamento de baseline exige justificativa.
- Metrica inativa nao pode receber novo valor.
- Alteracao de checkpoint deve preservar historico quando o dado ja alimentou calculos.

### Regras de remocao/desativacao

- Nao apagar medicao historica no MVP.
- Ajustes devem ocorrer por nova versao de carga ou por inativacao logica do registro incorreto.

### Dependencias

- Depende de Aluno ativo, vinculo ativo e Metricas ativas.
- Desbloqueia visoes reais de Centro, Radar e Matriz.

## Matriz de dependencias

| Bloco | Depende de |
|---|---|
| Cliente/Empresa | nenhum |
| Produto/Mentoria | Cliente/Empresa |
| Mentor | Produto/Mentoria |
| Aluno | Produto/Mentoria, Mentor |
| Pilar | Produto/Mentoria |
| Metrica | Pilar |
| Vinculos | entidades base ativas |
| Ingestao | Aluno, Vinculos, Metricas |

## Criterio funcional de pronto por entidade

Uma entidade so deve ser considerada pronta quando:

1. possui listagem e detalhe administrativo
2. possui create validado com regras minimas
3. possui update controlado com justificativa
4. possui desativacao logica com bloqueios coerentes
5. possui testes de unidade, API e fluxo administrativo principal

## Observacao de alinhamento com o backend atual

O backend atual ja cobre parte de Produto/Mentoria, Mentor, Aluno, Pilares, Metricas, Vinculos e Ingestao em modelo simplificado.

Para a Fase 2, a especificacao acima passa a ser a referencia canonica da camada administrativa. Qualquer bloco de implementacao deve explicitar:

- o que ja existe e sera reaproveitado
- o que precisa ser expandido
- o que sera mantido como simplificacao do MVP
