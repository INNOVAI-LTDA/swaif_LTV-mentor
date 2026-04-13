# Proposta de Solução — Bug: Paginação em "Alunos monitorados" (Centro de Comando)

Data: 2026-04-13  
Autor: Codex (proposta técnica inicial)

## 1) Resumo do problema

Hoje a seção **Alunos monitorados** permite apenas os recortes **Top 10** e **Bottom 10**.
Para uma base com ~469 alunos, isso limita a operação diária e impede navegação progressiva sem alterar o layout da tela.

## 2) Objetivo da correção

Adicionar uma forma de navegação por **páginas** na listagem de alunos monitorados, preservando:

- os filtros atuais Top 10 / Bottom 10;
- a disposição visual existente do Centro de Comando;
- a arquitetura atual (service + adapter + hook/resource + componentes de estado).

## 3) Escopo funcional proposto (MVP da correção)

### 3.1 Comportamento na UI

- Manter botões:
  - `Top 10`
  - `Bottom 10`
- Adicionar opção:
  - `Todos (paginado)`
- Quando `Todos (paginado)` estiver ativo:
  - exibir lista paginada com **10 alunos por página** (mesmo bloco visual atual);
  - mostrar controles de paginação simples: `Anterior`, `Próxima` e indicador `Página X de Y`;
  - resetar para página 1 ao trocar filtro/critério de ordenação.

### 3.2 Regras

- Top 10 e Bottom 10 continuam retornando exatamente 10 itens (sem paginação).
- Modo `Todos` usa paginação para navegar no conjunto completo.
- Mudança de rota/refresh mantém comportamento determinístico (query string opcional para fase 2).

## 4) Opções técnicas (recomendação)

### Opção A — Paginação no frontend sobre dataset já carregado (**Recomendada para correção rápida**) 

Pré-condição: endpoint atual de Centro de Comando já retorna todos os alunos necessários para a tela.

- Implementar paginação em memória no domínio de frontend (service/hook), sem alterar contrato HTTP.
- Vantagens:
  - menor risco de regressão de contrato v1;
  - menor esforço de backend;
  - entrega mais rápida.
- Trade-off:
  - payload completo continua sendo transferido.

### Opção B — Paginação no backend (fase posterior de otimização)

- Evoluir endpoint para aceitar `page` e `page_size` no modo `Todos`.
- Vantagens:
  - menor tráfego por requisição;
  - escala melhor para bases maiores.
- Trade-off:
  - exige mudança de contrato (ou versão/compatibilidade), testes adicionais e coordenação FE/BE.

## 5) Critérios de aceite

1. Usuário consegue alternar entre `Top 10`, `Bottom 10` e `Todos (paginado)`.
2. Em `Todos (paginado)`, usuário navega páginas sem quebrar layout.
3. Cada página mostra quantidade consistente de cards/linhas (10 por página, exceto última).
4. Troca de filtro volta para página 1.
5. Estados de loading/erro/vazio permanecem padronizados e sem novos formatos de erro.

## 6) Impacto esperado

- **Operacional**: melhora imediata para gestão de carteiras grandes.
- **UX**: descoberta de mais alunos sem poluir a interface.
- **Risco técnico**: baixo, se aplicado pela Opção A com alterações localizadas.

## 7) Plano de implementação sugerido

1. Ajustar modelo de estado da listagem para suportar `viewMode` (`top10`, `bottom10`, `allPaged`) e `page`.
2. Incluir cálculo de `totalPages` e `paginatedItems` no hook/service de Centro de Comando.
3. Atualizar componente da seção de alunos monitorados com controles de paginação.
4. Garantir reset de página ao trocar modo.
5. Cobrir com testes de unidade/componente no frontend para:
   - troca de modo;
   - paginação;
   - reset de página;
   - preservação de Top/Bottom.

## 8) Riscos e mitigação

- **Risco**: regressão visual na seção.
  - **Mitigação**: manter mesma estrutura de container e altura de bloco; alterar apenas conteúdo interno.
- **Risco**: inconsistência entre ordenação e paginação.
  - **Mitigação**: aplicar ordenação antes de fatiar páginas e fixar regra.
- **Risco**: perda de performance com listas maiores.
  - **Mitigação**: manter page size fixo e avaliar backend pagination se volume crescer.

## 9) Estimativa inicial

- Implementação frontend (Opção A): **0,5 a 1 dia**.
- Testes + validação manual: **0,5 dia**.
- Total: **1 a 1,5 dia útil**.

## 10) Recomendação final

Seguir com **Opção A (paginação no frontend)** nesta issue para resolver a dor do cliente rapidamente, sem quebrar contratos congelados v1. Abrir uma issue técnica separada para avaliar paginação server-side caso o volume continue crescendo.
