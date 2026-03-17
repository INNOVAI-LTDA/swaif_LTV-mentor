# Reorganização Segura do Repositório --- Plataforma + Skin

Este documento descreve o **processo seguro de reconstrução da estrutura
de diretórios**, seguido pelo **fluxo sequencial de execução das
tarefas**, e finaliza com **prompts operacionais para o Codex‑CLI**,
incluindo *guardrails* para evitar alterações indevidas no código ou
quebra da demo.

------------------------------------------------------------------------

# 1. Reconstrução da Estrutura de Diretórios (Visão Alvo)

``` mermaid
flowchart TB

A[Original Demo Directory] --> B[Clone Seguro do Projeto]
B --> C[Auditoria Estrutural]
C --> D[Classificação de Arquivos]

D --> E1[Runtime Crítico]
D --> E2[Referência Histórica]
D --> E3[Documentação]
D --> E4[Artefatos Gerados]
D --> E5[Cache / Temp]

E1 --> F1[Manter Estrutura Atual]
E2 --> F2[Documentar em docs/references]
E3 --> F3[Organizar docs]
E4 --> F4[Ignorar via .gitignore]
E5 --> F5[Ignorar via .gitignore]

F1 --> G[Nova Estrutura Preparada]
F2 --> G
F3 --> G
F4 --> G
F5 --> G

G --> H[Preparação GitHub]
H --> I[Repo + Issue Templates + Project Kanban]
```

------------------------------------------------------------------------

# 2. Estrutura Final Esperada (Alvo)

``` mermaid
flowchart LR

subgraph Runtime
backend
frontend
scripts
end

subgraph Documentation
docs_product[docs/product]
docs_arch[docs/architecture]
docs_clients[docs/clients]
docs_refs[docs/references]
end

subgraph GitHub
github_templates[.github/ISSUE_TEMPLATE]
github_ci[.github/workflows]
end

subgraph Reference
origin_ref[origin - reference source]
end

Runtime --> Documentation
Documentation --> GitHub
Reference --> Documentation
```

------------------------------------------------------------------------

# 3. Sequência das Etapas de Reconstrução

``` mermaid
sequenceDiagram

participant User
participant Codex
participant OriginalRepo
participant NewWorkspace
participant Docs

User->>Codex: Solicita auditoria estrutural
Codex->>OriginalRepo: Analisa estrutura atual

Codex->>Docs: Gera relatório de auditoria
Codex->>Docs: Gera plano de reorganização

User->>Codex: Autoriza fase segura

Codex->>NewWorkspace: Cria cópia do projeto
Codex->>NewWorkspace: Aplica organização não invasiva

Codex->>Docs: Cria documentação estrutural
Codex->>NewWorkspace: Adiciona README e .gitignore
Codex->>NewWorkspace: Cria .github templates

Codex->>User: Confirma preservação da demo

User->>Codex: Preparar repositório GitHub
Codex->>NewWorkspace: Estrutura final pronta
```

------------------------------------------------------------------------

# 4. Guardrails Essenciais

Durante todas as etapas, o Codex deve obedecer:

-   Não alterar nenhuma linha de código existente
-   Não modificar caminhos de execução
-   Não mover pastas runtime críticas
-   Não apagar arquivos
-   Trabalhar sempre em uma **nova pasta de reorganização**
-   Priorizar documentação sobre reorganização física
-   Manter demo executável

Diretórios considerados **runtime críticos**:

-   backend/
-   frontend/
-   scripts/
-   backend/data
-   frontend/src
-   frontend/package.json

------------------------------------------------------------------------

# 5. Sequência de Prompts para Codex‑CLI

## Prompt 1 --- Auditoria Estrutural

``` text
Analise a estrutura do projeto atual.

Regras:
- NÃO alterar nenhum arquivo
- NÃO mover pastas
- NÃO executar scripts

Objetivo:
classificar cada pasta como:

runtime crítico
referência
documentação
artefato gerado
cache/temp

Gerar:

docs/repository-structure-audit.md
docs/runtime-critical-paths.md
docs/repository-risk-analysis.md
```

------------------------------------------------------------------------

## Prompt 2 --- Plano de Reorganização

``` text
Com base na auditoria estrutural, proponha uma reorganização segura do repositório.

Regras:

não alterar código
não alterar paths runtime
não mover backend ou frontend

Gerar:

docs/repository-restructure-plan.md

O plano deve indicar:

estrutura alvo
itens que podem ser reorganizados agora
itens que devem permanecer intactos
itens que devem ser apenas documentados
```

------------------------------------------------------------------------

## Prompt 3 --- Criação de Workspace Seguro

``` text
Criar nova pasta de trabalho para reorganização.

Nome sugerido:
../swaif-platform-prep

Copiar todo o projeto para essa pasta.

A partir daqui, trabalhar apenas nesta nova pasta.
A pasta original deve permanecer intacta.
```

------------------------------------------------------------------------

## Prompt 4 --- Aplicar Organização Não Invasiva

``` text
Aplicar apenas mudanças estruturais seguras na nova pasta.

Permitido:

criar README.md
criar .gitignore
criar estrutura docs
criar .github/ISSUE_TEMPLATE

Proibido:

alterar código
mover runtime
alterar scripts
```

------------------------------------------------------------------------

## Prompt 5 --- Preparação para GitHub

``` text
Preparar a estrutura do repositório para publicação.

Criar:

README.md
LICENSE
.github/ISSUE_TEMPLATE
docs/product
docs/architecture
docs/clients
docs/references

Garantir que a demo continua executável.
```

------------------------------------------------------------------------

## Prompt 6 --- Validação Final

``` text
Validar a reorganização.

Confirmar:

nenhuma linha de código alterada
paths runtime intactos
demo executa normalmente
pasta original preservada

Gerar:

docs/repository-final-report.md
```

------------------------------------------------------------------------

# 6. Resultado Esperado

Após execução das etapas:

-   estrutura do projeto preparada para GitHub
-   documentação clara de arquitetura
-   base pronta para **core + skins + clientes**
-   demo intacta
-   processo reproduzível
