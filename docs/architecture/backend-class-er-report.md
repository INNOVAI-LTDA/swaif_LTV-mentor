# Relatório — Diagrama de Classes e Entidade-Relacionamento (Backend)

Este relatório descreve a modelagem principal do backend com base nos schemas e no modelo canônico da aplicação.

## 1) Diagrama de Classes (domínio + contratos principais)

```mermaid
classDiagram

class UserOut {
  +id: str
  +email: str
  +role: admin|mentor|client|aluno
}

class ClientOut {
  +id: str
  +name: str
  +brand_name: str
  +cnpj: str
  +slug: str
  +status: str
  +is_active: bool
  +timezone: str
  +currency: str
}

class OrganizationOut {
  +id: str
  +name: str
  +slug: str
  +mentor_id: str?
  +is_active: bool
}

class ProtocolOut {
  +id: str
  +organization_id: str
  +name: str
  +code: str
  +metadata: dict
  +is_active: bool
}

class MentorOut {
  +id: str
  +full_name: str
  +email: str
  +cpf: str?
  +phone: str?
  +status: str?
  +is_active: bool
  +organization_id: str?
}

class StudentOut {
  +id: str
  +full_name: str
  +initials: str
  +email: str?
  +cpf: str?
  +phone: str?
  +status: str
  +is_active: bool
}

class EnrollmentOut {
  +id: str
  +student_id: str
  +organization_id: str
  +mentor_id: str?
  +progress_score: float
  +engagement_score: float
  +urgency_status: str
  +day: int
  +total_days: int
  +days_left: int
  +ltv_cents: int
  +is_active: bool
}

class PillarOut {
  +id: str
  +protocol_id: str
  +name: str
  +code: str
  +order_index: int
  +metadata: dict
  +is_active: bool
}

class MetricOut {
  +id: str
  +protocol_id: str
  +pillar_id: str
  +name: str
  +code: str
  +direction: higher_better|lower_better|target_range
  +unit: str?
  +scoring_rules: list
  +is_active: bool
}

class ProductOut {
  +id: str
  +client_id: str
  +name: str
  +code: str
  +slug: str
  +status: str
  +is_active: bool
  +mentor_id: str?
}

class ProductAssignmentRecord {
  +id: str
  +client_id: str?
  +product_id: str
  +provider_id: str?
  +end_user_id: str
  +progress_score: float
  +engagement_score: float
  +urgency_status: str
  +ltv_cents: int
  +is_active: bool
}

class MetricMeasureRecord {
  +id: str
  +product_assignment_id: str
  +pillar_metric_id: str
  +value_baseline: float?
  +value_current: float
  +value_projected: float?
  +improving_trend: bool?
}

class JourneyCheckpointRecord {
  +id: str
  +product_assignment_id: str
  +week: int
  +status: green|yellow|red
  +label: str?
}

OrganizationOut "1" --> "0..*" ProtocolOut : owns
ProtocolOut "1" --> "0..*" PillarOut : has
ProtocolOut "1" --> "0..*" MetricOut : has
PillarOut "1" --> "0..*" MetricOut : groups
MentorOut "1" --> "0..*" OrganizationOut : linked_to
StudentOut "1" --> "0..*" EnrollmentOut : enrolled_by
OrganizationOut "1" --> "0..*" EnrollmentOut : context
MentorOut "0..1" --> "0..*" EnrollmentOut : follows
ClientOut "1" --> "0..*" ProductOut : offers
ProductOut "1" --> "0..*" ProductAssignmentRecord : assigns
MetricOut "1" --> "0..*" MetricMeasureRecord : measured_as
ProductAssignmentRecord "1" --> "0..*" MetricMeasureRecord : has_measures
ProductAssignmentRecord "1" --> "0..*" JourneyCheckpointRecord : has_checkpoints
```

## 2) Diagrama Entidade-Relacionamento (ER)

```mermaid
erDiagram
    USERS {
      string id PK
      string email
      string role
    }

    CLIENTS {
      string id PK
      string name
      string cnpj
      string slug
      string status
      boolean is_active
    }

    ORGANIZATIONS {
      string id PK
      string name
      string slug
      string mentor_id FK
      boolean is_active
    }

    PROTOCOLS {
      string id PK
      string organization_id FK
      string name
      string code
      boolean is_active
    }

    MENTORS {
      string id PK
      string full_name
      string email
      string cpf
      string organization_id FK
      boolean is_active
    }

    STUDENTS {
      string id PK
      string full_name
      string email
      string cpf
      string status
      boolean is_active
    }

    ENROLLMENTS {
      string id PK
      string student_id FK
      string organization_id FK
      string mentor_id FK
      float progress_score
      float engagement_score
      string urgency_status
      int ltv_cents
      boolean is_active
    }

    PILLARS {
      string id PK
      string protocol_id FK
      string name
      string code
      int order_index
      boolean is_active
    }

    METRICS {
      string id PK
      string protocol_id FK
      string pillar_id FK
      string name
      string code
      string direction
      boolean is_active
    }

    PRODUCTS {
      string id PK
      string client_id FK
      string name
      string code
      string slug
      string status
      boolean is_active
    }

    PRODUCT_ASSIGNMENTS {
      string id PK
      string client_id FK
      string product_id FK
      string provider_id FK
      string end_user_id FK
      float progress_score
      float engagement_score
      int ltv_cents
      boolean is_active
    }

    METRIC_MEASURES {
      string id PK
      string product_assignment_id FK
      string pillar_metric_id FK
      float value_baseline
      float value_current
      float value_projected
      boolean improving_trend
    }

    JOURNEY_CHECKPOINTS {
      string id PK
      string product_assignment_id FK
      int week
      string status
      string label
    }

    MENTORS ||--o{ ORGANIZATIONS : linked
    ORGANIZATIONS ||--o{ PROTOCOLS : owns
    PROTOCOLS ||--o{ PILLARS : has
    PROTOCOLS ||--o{ METRICS : has
    PILLARS ||--o{ METRICS : groups

    STUDENTS ||--o{ ENROLLMENTS : enrolled
    ORGANIZATIONS ||--o{ ENROLLMENTS : context
    MENTORS o|--o{ ENROLLMENTS : follows

    CLIENTS ||--o{ PRODUCTS : offers
    PRODUCTS ||--o{ PRODUCT_ASSIGNMENTS : has
    MENTORS o|--o{ PRODUCT_ASSIGNMENTS : provider
    STUDENTS ||--o{ PRODUCT_ASSIGNMENTS : end_user

    PRODUCT_ASSIGNMENTS ||--o{ METRIC_MEASURES : has
    METRICS ||--o{ METRIC_MEASURES : metric

    PRODUCT_ASSIGNMENTS ||--o{ JOURNEY_CHECKPOINTS : has
```

## 3) Observações de modelagem

- O backend atual usa persistência em arquivos JSON via repositórios, mas as entidades e chaves acima já permitem mapear uma migração para banco relacional sem alterar o contrato de API.
- Há duas visões complementares de domínio: a visão MVP (`organization`, `mentor`, `student`, `enrollment`) e a visão canônica (`client`, `product`, `provider`, `end_user`, `product_assignment`).
- O diagrama ER acima unifica ambas porque elas coexistem no backend atual.


## 4) Avaliação de impacto: migração de JSON para Supabase (Postgres)

### 4.1 Impactos positivos esperados

- **Consistência transacional**: operações hoje distribuídas em múltiplos arquivos JSON (por exemplo vínculo aluno/mentoria + medições + checkpoints) passam a poder usar transações atômicas.
- **Integridade referencial nativa**: FKs, constraints e índices passam a garantir relações (`enrollments.student_id`, `metrics.pillar_id`, etc.) no nível do banco.
- **Escalabilidade de leitura/escrita**: elimina contenção de I/O em arquivo e reduz risco de corrupção por escrita concorrente.
- **Consultas analíticas melhores**: joins, agregações e filtros complexos para Centro/Radar/Matriz ficam mais simples e performáticos.
- **Operação e observabilidade**: Supabase fornece backup gerenciado, monitoramento e trilha de auditoria mais robusta que armazenamento local em arquivo.

### 4.2 Impactos técnicos no backend atual

1. **Camada de storage**
   - Repositórios em `backend/app/storage/*` deixariam de usar `json_repository.py` como backend primário.
   - Necessário criar adaptadores/repositórios SQL mantendo a mesma interface de serviço para reduzir impacto na API.

2. **Serviços de domínio**
   - Serviços em `backend/app/services/*` tendem a precisar de ajustes para operações transacionais (create/update/link/unlink/reassign).
   - Regras de idempotência e conflito (`409`) devem continuar inalteradas na superfície HTTP.

3. **Contratos e rotas**
   - Endpoints e payloads podem permanecer estáveis (objetivo recomendado), preservando o contrato v1 e envelope de erro.
   - Alterações devem ser internas (storage/repository), sem breaking change para frontend.

4. **Testes**
   - Parte dos testes de integração hoje focados em JSON deverá ganhar equivalentes com banco real (ou container Postgres).
   - Deve-se manter testes de API para garantir paridade de comportamento e de payload de erro.

### 4.3 Riscos e pontos de atenção

- **Migração de dados legados**: risco de inconsistência entre estruturas MVP e canônicas se o mapeamento não for validado com reconciliação.
- **Mudança semântica involuntária**: defaults e campos opcionais atuais podem divergir ao virar colunas NOT NULL/NULL sem regra explícita.
- **Quebra de fluxos operacionais**: rotinas de backup/restore atuais baseadas em arquivos precisam de equivalente operacional no Supabase.
- **Custos e latência de rede**: acesso remoto ao banco traz novo perfil de latência e custo (egresso, pooling, limites do plano).
- **Segurança e compliance**: revisão de políticas RLS, gestão de segredos e segregação de ambientes (dev/staging/prod) passa a ser obrigatória.

### 4.4 Estratégia recomendada (menor risco)

1. **Fase 0 — Congelamento de contrato**
   - Confirmar invariantes: endpoints, schemas de saída, códigos de erro e semântica.

2. **Fase 1 — Esquema relacional alvo**
   - Gerar DDL a partir do ER deste documento.
   - Definir constraints mínimas (PK, FK, unique e índices por chaves de busca frequentes).

3. **Fase 2 — Repositórios dual-write controlado (opcional)**
   - Escrita em Postgres + JSON temporariamente para validação de paridade.
   - Comparação automática de outputs críticos (ex.: listagens administrativas e projeções).

4. **Fase 3 — Cutover de leitura**
   - Mover leituras para Postgres por feature flag.
   - Monitorar divergências e performance.

5. **Fase 4 — Desativação JSON**
   - Remover escrita JSON após janela de estabilização.
   - Manter plano de rollback com snapshot consistente.

### 4.5 Esforço relativo por área (estimativa qualitativa)

- **Storage/repositories**: alto.
- **Services (transações e conflitos)**: médio-alto.
- **API/rotas/contratos**: baixo (se mantidos estáveis).
- **Testes e validação de paridade**: alto.
- **DevOps/segurança/observabilidade**: médio-alto.

### 4.6 Critérios de sucesso da migração

- Zero breaking change nos contratos v1.
- Paridade funcional nos fluxos críticos (auth, vínculo aluno, carga de indicadores, Centro/Radar/Matriz).
- Redução de falhas por concorrência e melhoria mensurável de tempo de resposta em consultas agregadas.
- Processo de backup/restore homologado no novo ambiente.
