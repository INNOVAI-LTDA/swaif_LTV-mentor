# Modelo de Dados (Mermaid)

Este documento descreve o **redesenho proposto** para validar o reajuste estrutural do domínio.

## Premissas de negócio (alinhadas)

- Uma **Organization** pode possuir **N Protocols**, **N Mentors**, **N Students** e **N Enrollments**.
- Não existe relação obrigatória direta entre Mentor, Student e Protocol fora de Enrollment.
- **Enrollment** é o vínculo que conecta: **Student + Mentor + Protocol** (e o contexto organizacional).
- **Protocol** possui **Pillars**.
- **Pillar** possui **Metrics**.
- Cálculo e apresentação usam a entidade **Measurement** com diferentes escopos:
  - medição de **Metric** (valor base do domínio)
  - medição de **Pillar** (agregação geométrica das métricas)
  - medição de **Protocol** para matriz de decisão (agregação dos pilares por método próprio)
- O conceito de `measurement_overalls` é substituído por medições explícitas por escopo + método.

---

## 1) Diagrama de Classes (Modelo Alvo)

```mermaid
classDiagram
  class Organization {
    +string id
    +string name
    +string slug
    +bool is_active
  }

  class Student {
    +string id
    +string full_name
    +string email
    +bool is_active
  }

  class Mentor {
    +string id
    +string full_name
    +string email
    +bool is_active
  }

  class Protocol {
    +string id
    +string organization_id
    +string name
    +string code
    +bool is_active
  }

  class Enrollment {
    +string id
    +string organization_id
    +string student_id
    +string mentor_id
    +string protocol_id
    +bool is_active
    +datetime created_at
    +datetime updated_at
  }

  class Pillar {
    +string id
    +string protocol_id
    +string name
    +string code
    +int order_index
    +bool is_active
  }

  class Metric {
    +string id
    +string pillar_id
    +string name
    +string code
    +string direction
    +string unit
    +bool is_active
  }

  class Measurement {
    +string id
    +string enrollment_id
    +string level_type  // metric|pillar|protocol
    +string level_id    // metric_id|pillar_id|protocol_id
    +float value_base
    +float value_current
    +float value_target
    +bool improving_trend
    +string method_id
    +datetime calculated_at
  }

  class CalculationMethod {
    +string id
    +string scope_type // metric|pillar|protocol
    +string code
    +string name
    +json config
    +bool is_active
  }

  class MeasurementInput {
    +string id
    +string source_measurement_id
    +string input_measurement_id
    +float weight
  }

  Organization "1" --> "0..*" Protocol : owns
  Organization "1" --> "0..*" Mentor : has
  Organization "1" --> "0..*" Student : has
  Organization "1" --> "0..*" Enrollment : contextualizes

  Student "1" --> "0..*" Enrollment : enrolls
  Mentor "1" --> "0..*" Enrollment : mentors
  Protocol "1" --> "0..*" Enrollment : applies

  Protocol "1" --> "0..*" Pillar : defines
  Pillar "1" --> "0..*" Metric : defines

  Enrollment "1" --> "0..*" Measurement : records
  CalculationMethod "1" --> "0..*" Measurement : computes

  Measurement "1" --> "0..*" MeasurementInput : depends_on
```

---

## 2) Modelo Entidade-Relacionamento (ER) Alvo

```mermaid
erDiagram
  ORGANIZATIONS {
    string id PK
    string name
    string slug
    boolean is_active
  }

  STUDENTS {
    string id PK
    string full_name
    string email
    boolean is_active
  }

  MENTORS {
    string id PK
    string full_name
    string email
    boolean is_active
  }

  PROTOCOLS {
    string id PK
    string organization_id FK
    string name
    string code
    boolean is_active
  }

  ENROLLMENTS {
    string id PK
    string organization_id FK
    string student_id FK
    string mentor_id FK
    string protocol_id FK
    boolean is_active
    datetime created_at
    datetime updated_at
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
    string pillar_id FK
    string name
    string code
    string direction
    string unit
    boolean is_active
  }

  CALCULATION_METHODS {
    string id PK
    string scope_type
    string code
    string name
    json config
    boolean is_active
  }

  MEASUREMENTS {
    string id PK
    string enrollment_id FK
    string level_type
    string level_id
    float value_base
    float value_current
    float value_target
    boolean improving_trend
    string method_id FK
    datetime calculated_at
  }

  MEASUREMENT_INPUTS {
    string id PK
    string source_measurement_id FK
    string input_measurement_id FK
    float weight
  }

  ORGANIZATIONS ||--o{ PROTOCOLS : "owns"
  ORGANIZATIONS ||--o{ MENTORS : "has"
  ORGANIZATIONS ||--o{ STUDENTS : "has"
  ORGANIZATIONS ||--o{ ENROLLMENTS : "context"

  STUDENTS ||--o{ ENROLLMENTS : "enrolls"
  MENTORS ||--o{ ENROLLMENTS : "mentors"
  PROTOCOLS ||--o{ ENROLLMENTS : "applies"

  PROTOCOLS ||--o{ PILLARS : "defines"
  PILLARS ||--o{ METRICS : "defines"

  ENROLLMENTS ||--o{ MEASUREMENTS : "records"
  CALCULATION_METHODS ||--o{ MEASUREMENTS : "computes"

  MEASUREMENTS ||--o{ MEASUREMENT_INPUTS : "source"
  MEASUREMENTS ||--o{ MEASUREMENT_INPUTS : "input"
```

---

## 3) Fluxo de cálculo por escopo

```mermaid
flowchart TD
  A[Metric Measurements<br/>level_type=metric] --> B[Pillar Measurement<br/>level_type=pillar<br/>method=geometric_mean]
  B --> C[Protocol Measurement<br/>level_type=protocol<br/>method=decision_matrix_aggregation]
  C --> D[Matriz de Decisão]
```

---

## 4) Estratégia de transição recomendada

1. Introduzir `protocol_id` explícito em `enrollments`.
2. Migrar `measurement_overalls` para `measurements(level_type=pillar|protocol)`.
3. Registrar método de cálculo em `calculation_methods` e vínculo em `measurements.method_id`.
4. Persistir rastreabilidade de agregação em `measurement_inputs`.
5. Atualizar serviços de leitura para consumir medições por escopo.
