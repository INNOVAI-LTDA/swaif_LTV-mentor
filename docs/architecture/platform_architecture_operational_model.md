# SWAIF Platform Architecture & Operational Model

Este documento complementa o **Repository Restructure Process** e
descreve:

1.  Arquitetura da plataforma (**Core + Skin + Client**)
2.  Modelo de organização do repositório
3.  Modelo operacional do **GitHub Project Kanban**
4.  Fluxo de entrega para novos clientes
5.  Processo de evolução do produto

O objetivo é garantir que o projeto evolua como **plataforma
multi‑segmento**, sem quebrar o núcleo da aplicação.

------------------------------------------------------------------------

# 1. Arquitetura da Plataforma (Core + Skin + Client)

``` mermaid
flowchart TB

subgraph Core Platform
A[Auth]
B[Users]
C[Programs]
D[Command Center]
E[Radar]
F[Renewal Matrix]
G[LTV Engine]
end

subgraph Skin Layer
H[Clinic Skin]
I[Mentorship Skin]
end

subgraph Client Configuration
J[Branding]
K[Pillars]
L[Metrics]
M[Thresholds]
N[Suggestions]
end

Core Platform --> Skin Layer
Skin Layer --> Client Configuration
```

### Interpretação

**Core** - lógica de negócio - módulos principais - engine de cálculo

**Skin** - identidade visual - terminologia de domínio - copy

**Client** - configuração do método - pilares - métricas - thresholds

------------------------------------------------------------------------

# 2. Estrutura Recomendada do Repositório

``` mermaid
flowchart LR

subgraph Runtime
backend
frontend
scripts
end

subgraph Platform
core_logic[core modules]
skins[skins]
methods[methods config]
end

subgraph Documentation
product_docs[docs/product]
arch_docs[docs/architecture]
client_docs[docs/clients]
ref_docs[docs/references]
end

Runtime --> Platform
Platform --> Documentation
```

### Estrutura esperada

    repo/
      backend/
      frontend/
      scripts/

      docs/
        architecture/
        product/
        clients/
        references/

      .github/
        ISSUE_TEMPLATE/
        workflows/

------------------------------------------------------------------------

# 3. Modelo do GitHub Project (Kanban)

``` mermaid
flowchart LR

Ideas --> Backlog
Backlog --> Next
Next --> InProgress
InProgress --> Testing
Testing --> ReadyForDemo
ReadyForDemo --> Done
```

### Colunas recomendadas

Ideas\
Backlog\
Next\
In Progress\
Testing\
Ready for Demo\
Done

------------------------------------------------------------------------

# 4. Tipos de Trabalho no Projeto

``` mermaid
flowchart TB

Work --> Core
Work --> Skin
Work --> Method
Work --> ClientDelivery
```

### Core

Mudanças no motor da plataforma.

### Skin

Customização visual ou terminológica.

### Method

Configuração do método do cliente.

### ClientDelivery

Entrega específica para cliente.

------------------------------------------------------------------------

# 5. Fluxo de Entrega para Novo Cliente

``` mermaid
sequenceDiagram

participant Sales
participant Product
participant Engineering
participant Client

Sales->>Product: Novo cliente fechado
Product->>Engineering: Criar skin + método

Engineering->>Engineering: Configurar pillars
Engineering->>Engineering: Configurar metrics

Engineering->>Engineering: Criar demo dataset

Engineering->>Client: Demo inicial

Client->>Engineering: Ajustes
Engineering->>Client: Versão final
```

------------------------------------------------------------------------

# 6. Estrutura de Entrega por Cliente

    docs/clients/<client-name>/
      brief.md
      branding.md
      vocabulary.md
      method.md
      demo-data.md
      delivery-checklist.md

### brief.md

escopo vendido

### branding.md

cores, logo e identidade

### vocabulary.md

terminologia

### method.md

pilares e métricas

### demo-data.md

dataset de demonstração

### delivery-checklist.md

lista de validação antes da entrega

------------------------------------------------------------------------

# 7. Evolução do Produto

``` mermaid
flowchart TB

MVP --> Hardening
Hardening --> WhiteLabelFoundation
WhiteLabelFoundation --> MultiClientPlatform
MultiClientPlatform --> AdvancedAnalytics
```

### Fases

**MVP** demo funcional

**Hardening** testes e estabilidade

**White‑Label Foundation** suporte a skins

**Multi‑Client Platform** vários clientes

**Advanced Analytics** comparações e histórico

------------------------------------------------------------------------

# 8. Resultado Esperado

Quando aplicado corretamente:

-   núcleo único da plataforma
-   múltiplas skins suportadas
-   entregas por cliente controladas
-   evolução segura do produto
-   GitHub organizado para desenvolvimento contínuo
