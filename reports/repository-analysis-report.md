# Relatório de Análise do Repositório

**Data:** 2026-04-14  
**Objetivo:** Estudo profundo e completo do repositório para entender o que o cliente está consumindo e identificar padrões por trás do que foi entregue.

---

## 1. Visão Geral do Repositório

### 1.1 Estrutura Principal

O repositório contém os seguintes diretórios principais:

```
/workspace/
├── backend/          # API FastAPI com persistência JSON
├── frontend/         # Aplicação React/Vite + TypeScript
├── origin/           # Código de referência/legado (não runtime)
├── docs/             # Documentação extensa (arquitetura, contratos, planos)
├── ops/              # BMAD Operator Kit (automação de desenvolvimento)
├── _bmad/            # Framework BMAD instalado
├── _bmad-output/     # Artefatos de implementação do BMAD
├── scripts/          # Scripts de automação e bootstrap
└── reports/          # Relatórios de análise (novo)
```

### 1.2 Volume de Código

- **Arquivos de código (.py, .js, .ts, .tsx, .jsx):** 1,958 arquivos
- **Arquivos de configuração (.json):** 341 arquivos
- **Documentação (.md):** 2,397 arquivos

Este é um repositório de grande porte com documentação extensa e código significativo.

---

## 2. O Que o Cliente Está Consumindo

### 2.1 Produto Principal: Plataforma de Mentoria White-Label

O cliente está consumindo uma **plataforma SaaS de gestão de programas de mentoria** com as seguintes características:

#### 2.1.1 Funcionalidades Core

1. **Centro de Comando** (`CommandCenter`)
   - Monitoramento da jornada ativa dos alunos por exceção
   - Destaque de risco (urgência), janela de renovação (D-45) e progresso do ciclo
   - Lista de alunos com status de urgência, dias restantes, engajamento
   - Painel de detalhe com métricas, checkpoints e narrativa de renovação

2. **Radar de Transformação** (`Radar`)
   - Visualização em radar das métricas por pilar do método
   - Scores baseline, current e projected por eixo
   - Insights narrativos por pilar

3. **Matriz de Renovação Antecipada** (`Matrix`)
   - Matriz 2D: progress_score x engagement_score
   - Bolhas representam alunos posicionados por desempenho
   - Quadrantes indicam prioridade de renovação
   - KPIs de receita (LTV) e narrativa de oferta sugerida

#### 2.1.2 Personas/Papéis Suportados

| Papel | Descrição | Acesso |
|-------|-----------|--------|
| `org_admin` | Administrador da organização/cliente | CRUD completo, configurações |
| `mentor` | Mentor/profissional responsável | Visão dos seus alunos, edição limitada |
| `student` | Aluno/participante do programa | Visão do próprio progresso (futuro) |

#### 2.1.3 Casos de Uso Principais

1. **Gestão de Ciclo de Mentoria**
   - Acompanhamento diário do progresso (day/totalDays)
   - Cálculo automático de days_left para renovação
   - Alertas de urgência baseados em múltiplos fatores

2. **Avaliação de Métricas**
   - Coleta de baseline e medições correntes
   - Cálculo de scores por pilar (0-100)
   - Tendência de melhoria (improving_trend)

3. **Decisão Comercial de Renovação**
   - Snapshot de renovação com quadrante e prioridade
   - Sugestão de oferta baseada em desempenho
   - Narrativa justificativa para ação

---

## 3. Modelo de Dados

### 3.1 Entidades Legacy (Atuais)

O backend atualmente opera com as seguintes entidades:

| Entidade | Arquivo JSON | Descrição |
|----------|--------------|-----------|
| `Client` | `clients.json` | Tenant contratante (white-label) |
| `Organization` | `organizations.json` | Produto/programa de mentoria |
| `Mentor` | `mentors.json` | Profissional responsável |
| `Student` | `students.json` | Aluno/participante |
| `Protocol` | `protocols.json` | Método/versão do programa |
| `Pillar` | `pillars.json` | Pilares do método |
| `Metric` | `metrics.json` | Indicadores por pilar |
| `Enrollment` | `enrollments.json` | Vínculo aluno-mentor-protocolo |
| `Measurement` | `measurements.json` | Medições de indicadores |
| `Checkpoint` | `checkpoints.json` | Marcos semanais da jornada |
| `User` | `users.json` | Contas de autenticação |

### 3.2 Modelo Canonical (Futuro)

Existe uma camada de abstração canonical em preparação:

| Legacy | Canonical |
|--------|-----------|
| `Client` | `Client` (mantido) |
| `Organization` | `Product` |
| `Mentor` | `Provider` |
| `Student` | `EndUser` |
| `Enrollment` | `ProductAssignment` |
| `Protocol` + `Pillar` | `ProductPillar` |
| `Metric` | `PillarMetric` |
| `Measurement` | `MetricMeasure` |
| `Checkpoint` | `JourneyCheckpoint` |

**Nota:** A arquitetura canonical está documentada em `docs/architecture/canonical-data-architecture.md` e parcialmente implementada em `backend/app/storage/canonical_repositories.py`.

### 3.3 Relacionamentos Chave

```
Client 1:N Product (Organization)
Product 1:N ProductPillar (Pillar + Protocol context)
ProductPillar 1:N PillarMetric (Metric)

Client 1:N EndUser (Student)
Client 1:N Provider (Mentor)

Product 1:N ProductAssignment (Enrollment)
Provider 1:N ProductAssignment
EndUser 1:N ProductAssignment

ProductAssignment 1:N MetricMeasure (Measurement)
ProductAssignment 1:N JourneyCheckpoint (Checkpoint)
```

### 3.4 Campos Operacionais Críticos

Em `Enrollment`/`ProductAssignment`:
- `progress_score` (0..1): Progresso no ciclo
- `engagement_score` (0..1): Nível de engajamento
- `urgency_status`: `normal` | `watch` | `critical` | `rescue`
- `day` / `total_days` / `days_left`: Controle temporal
- `ltv_cents`: Valor econômico em centavos

---

## 4. Padrões Identificados

### 4.1 Padrão de Persistência

**JSON File Storage com Repositórios**

- Cada entidade tem seu próprio arquivo JSON
- Estrutura padronizada: `{"version": 1, "items": [...]}`
- Camada de repositório em `backend/app/storage/`
- Escrita atômica com lock file (`.storage-io.lock`)
- Sem banco de dados relacional no MVP

**Vantagens:**
- Simplicidade para demo/MVP
- Fácil inspeção manual dos dados
- Portabilidade

**Limitações:**
- Não escala para produção real
- Sem transações complexas
- Consultas limitadas

### 4.2 Padrão de Arquitetura Backend

**FastAPI Modular por Features**

```
backend/app/
├── api/routes/       # Handlers HTTP por recurso
├── schemas/          # Pydantic models (DTOs)
├── services/         # Lógica de negócio
├── storage/          # Repositórios de persistência
├── config/           # Configurações
├── core/             # Utilitários core
└── operations/       # Scripts operacionais
```

**Padrões observados:**
- Rotas agrupadas por domínio (admin_*, mentor, auth, health)
- Services como camada intermediária entre routes e repositories
- Schemas Pydantic para validação e serialização
- Injeção de dependência implícita via instanciação

### 4.3 Padrão de Arquitetura Frontend

**React + Vite + TypeScript Feature-Based**

```
frontend/src/
├── features/         # Módulos por funcionalidade
│   ├── admin/
│   ├── mentor/
│   ├── student/
│   ├── command-center/
│   ├── matrix/
│   ├── radar/
│   └── ...
├── pages/            # Páginas de roteamento
├── shared/           # Componentes compartilhados
├── domain/           # Tipos e lógica de domínio
├── contracts/        # Contratos de API
└── app/              # Shell da aplicação
```

**Padrões observados:**
- Separação clara entre features independentes
- CSS modular por feature (ex: `admin.css`, `matrix.css`)
- Hooks customizados por feature para estado
- Contratos de API definidos em TypeScript

### 4.4 Padrão de Desenvolvimento: BMAD Operator Kit

O repositório inclui um **sistema operacional de desenvolvimento** baseado em BMAD:

**Componentes:**
- `_bmad/`: Framework BMAD instalado
- `ops/`: Scripts do operador local
- `_bmad-output/`: Artefatos gerados pelo processo

**Fluxo de Trabalho:**
```
story → dev → review → fix (se necessário) → review → done
```

**Características:**
- Artifact-first: arquivos de story são a verdade da implementação
- Aprovação humana entre fases
- Logs de evento estruturados em `_bmad-output/operator-events/`
- Comandos contratuais com entrada/saída estruturada

### 4.5 Padrão de Multi-Tenancy

**White-Label com Isolamento por Client**

- Cada `Client` pode ter múltiplos `Product` (organizações)
- Vocabulário customizável por cliente (ex: "aluno" vs "paciente")
- Branding configurável (nome, logo, cores)
- Isolamento de dados via `client_id` em todas as entidades

**Exemplo de vocabulário (AccMed):**
```json
{
  "Client": "Cliente",
  "Product": "Produto", 
  "Provider": "Mentor",
  "EndUser": "Aluno",
  "ProductPillar": "Pilar",
  "PillarMetric": "Indicador"
}
```

### 4.6 Padrão de Contratos de API

**Frontend-Backend Contract-First**

Documentação extensa de contratos em `docs/mvp-mentoria/`:

- `contracts-command-center.md`: Contrato do Centro de Comando
- `contracts-radar.md`: Contrato do Radar (inferido)
- `contracts-matrix.md`: Contrato da Matriz (inferido)
- `data-model.md`: Modelo de dados completo

**Exemplo de contrato (Centro de Comando - Item de Lista):**
```json
{
  "id": "string",
  "name": "string",
  "programName": "string",
  "urgency": "rescue|watch|critical|normal",
  "daysLeft": 45,
  "day": 30,
  "totalDays": 180,
  "engagement": 0.72,
  "progress": 0.55,
  "hormoziScore": 63
}
```

### 4.7 Padrão de Origem de Dados

**Código de Referência em `/origin`**

O diretório `origin/` contém:
- `jpe-command-center.jsx`: Implementação original do Centro de Comando
- `jpe-hub.jsx`: Hub principal com módulos
- `matriz-renovacao.jsx`: Matriz de Renovação original
- `radar-longevidade.jsx`: Radar original
- `hooks/`, `services/`, `adapters/`: Utilitários de referência

**Propósito:**
- Preservar a essência/conceito original
- Servir como referência para reimplementação
- Não é executado em runtime (documentação viva)

---

## 5. Estado Atual da Solução

### 5.1 Backend

**Status:** Funcional com dados de demo

- API FastAPI rodando em `backend/app/main.py`
- 18 rotas de admin + rotas de mentor + auth + health
- Persistência JSON em `backend/data/`
- Serviços implementados para todas as entidades principais
- Camada canonical parcialmente implementada

**Dados de Demo:**
- 2 clients (Grupo Acelerador Médico, Innovai Solutions)
- 3 organizations/produtos
- 2 mentors
- ~1000+ students (dados reais anonimizados)
- ~1000+ enrollments
- ~10000+ measurements

### 5.2 Frontend

**Status:** Implementado com features principais

Features completas:
- ✅ Admin (CRUDs completos)
- ✅ Command Center (Centro de Comando)
- ✅ Matrix (Matriz de Renovação)
- ✅ Radar (Radar de Transformação)
- ✅ Mentor (Portal do Mentor)
- ✅ Student (Portal do Aluno - básico)

**Tecnologias:**
- React 18+
- TypeScript
- Vite
- CSS modular

### 5.3 Documentação

**Status:** Excepcionalmente completa

- 2,397 arquivos Markdown
- Arquitetura detalhada
- Contratos de API documentados
- Planos de implementação
- Auditorias e relatórios
- Runbooks operacionais

---

## 6. Essência da Solução (Core Value)

### 6.1 Problema que Resolve

**Para Gestores de Programas de Mentoria:**
- Visibilidade completa do progresso dos alunos
- Detecção precoce de riscos de abandono
- Decisão informada sobre renovação de contratos
- Padronização de método com métricas objetivas

### 6.2 Diferenciais Competitivos

1. **Gestão por Exceção**
   - Foco nos casos que precisam de atenção (urgency_status)
   - Reduz ruído e sobrecarga cognitiva

2. **Renovação Antecipada**
   - Janela D-45 para ação comercial proativa
   - Quadrantes de prioridade baseados em dados

3. **Método Mensurável**
   - Pilares e métricas customizáveis por cliente
   - Scores objetivos de transformação

4. **White-Label Nativo**
   - Multi-tenant desde a arquitetura
   - Vocabulário e branding customizáveis

### 6.3 Núcleo Extraível (Kernel)

Se fosse isolar a **essência mínima** da solução:

```
kernel/
├── data-model/
│   ├── Client
│   ├── Product (Organization)
│   ├── Provider (Mentor)
│   ├── EndUser (Student)
│   ├── ProductAssignment (Enrollment)
│   ├── ProductPillar + PillarMetric
│   ├── MetricMeasure
│   └── JourneyCheckpoint
│
├── core-metrics/
│   ├── progress_score calculator
│   ├── engagement_score calculator
│   ├── urgency_status evaluator
│   └── days_left calculator
│
├── views/
│   ├── CommandCenter (lista + detalhe + timeline)
│   ├── Radar (scores por pilar)
│   └── Matrix (quadrantes de renovação)
│
└── contracts/
    ├── list-items contract
    ├── detail-view contract
    ├── radar-scores contract
    └── matrix-quadrants contract
```

---

## 7. Próximos Passos Sugeridos

### 7.1 Para Extrair o Kernel

1. **Identificar dependências mínimas**
   - Quais schemas são essenciais?
   - Quais serviços são core vs. administrativo?

2. **Separar camadas**
   - Domain entities (puro)
   - Application services (lógica)
   - Infrastructure (persistência, API)

3. **Preservar contratos**
   - Manter compatibilidade com frontend existente
   - Documentar interfaces públicas

### 7.2 Para Evoluir a Plataforma

1. **Migrar para banco relacional**
   - PostgreSQL ou SQLite production-ready
   - Manter camada de repositório

2. **Completar arquitetura canonical**
   - Migrar APIs legacy para canonical
   - Manter adapters para compatibilidade

3. **Expandir features**
   - Portal do aluno completo
   - Relatórios avançados
   - Integrações externas

---

## 8. Conclusão

Este repositório representa uma **solução completa de plataforma SaaS para gestão de programas de mentoria**, com:

- **Backend funcional** em FastAPI com persistência JSON (MVP)
- **Frontend completo** em React/TypeScript com 6 features principais
- **Documentação excepcional** com contratos, arquitetura e planos
- **Processo de desenvolvimento estruturado** via BMAD Operator Kit
- **Multi-tenancy nativo** com suporte a white-label

A **essência da solução** está na combinação de:
1. Gestão visual por exceção (Centro de Comando)
2. Avaliação objetiva de transformação (Radar)
3. Decisão comercial baseada em dados (Matriz de Renovação)

O núcleo extraível poderia servir como base para:
- Novos clientes com customizações específicas
- Evolução para produto multi-tenant em escala
- Licenciamento do kernel para integração em outras plataformas

---

**Próxima etapa:** Aguardar definição do usuário sobre qual essência específica deseja extrair para a nova branch.
