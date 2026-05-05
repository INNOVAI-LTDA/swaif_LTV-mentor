# Modelo de Dados (Mermaid)

Este documento descreve o modelo atual dos dados JSON em formato de:

1. Diagrama de classes
2. Modelo Entidade-Relacionamento (ER)

## 1) Diagrama de Classes

```mermaid
classDiagram
  class Student {
    +string id
    +string full_name
    +string email
    +string status
    +bool is_active
    +date start_enrollment_date
    +date end_enrollment_date
  }

  class Mentor {
    +string id
    +string full_name
    +string email
    +bool is_active
  }

  class Organization {
    +string id
    +string name
    +string slug
    +string code
    +string client_id
    +string mentor_id
    +string delivery_model
    +string status
    +bool is_active
  }

  class Enrollment {
    +string id
    +string student_id
    +string organization_id
    +string mentor_id
    +float progress_score
    +float engagement_score
    +string urgency_status
    +int day
    +int total_days
    +int days_left
    +int ltv_cents
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
    +json metadata
    +bool is_active
  }

  class Metric {
    +string id
    +string protocol_id
    +string pillar_id
    +string name
    +string code
    +string direction
    +string unit
    +json scoring_rules
    +string score_type
    +float min_score
    +float max_score
    +bool is_active
  }

  class Measurement {
    +string id
    +string enrollment_id
    +string metric_id
    +float value_baseline
    +float value_current
    +float value_projected
    +bool improving_trend
  }

  class MeasurementOverall {
    +string enrollment_id
    +string protocol_id
    +MetricOverall[] metrics
    +PillarOverall[] pillars
    +DecisionMatrix decision_matrix
  }

  class MetricOverall {
    +string metric_id
    +float goal
    +float base
    +float real
  }

  class PillarOverall {
    +string pillar_id
    +float goal
    +float base
    +float real
  }

  class DecisionMatrix {
    +float product_score
    +float engagement_score
    +float prd_thr
    +float eng_thr
  }

  Student "1" --> "0..*" Enrollment : has
  Mentor "1" --> "0..*" Enrollment : guides
  Organization "1" --> "0..*" Enrollment : offers
  Organization "1" --> "0..*" Mentor : owner/context

  Enrollment "1" --> "0..*" Measurement : records
  Metric "1" --> "0..*" Measurement : measured_by

  Pillar "1" --> "0..*" Metric : groups

  Enrollment "1" --> "1" MeasurementOverall : aggregates
  MeasurementOverall "1" --> "0..*" MetricOverall : per metric
  MeasurementOverall "1" --> "0..*" PillarOverall : per pillar
  MeasurementOverall "1" --> "1" DecisionMatrix : matrix
```

## 2) Modelo Entidade-Relacionamento (ER)

```mermaid
erDiagram
  STUDENTS {
    string id PK
    string full_name
    string email
    string status
    boolean is_active
    date start_enrollment_date
    date end_enrollment_date
  }

  MENTORS {
    string id PK
    string full_name
    string email
    boolean is_active
  }

  ORGANIZATIONS {
    string id PK
    string name
    string slug
    string code
    string client_id
    string mentor_id FK
    string delivery_model
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
    int day
    int total_days
    int days_left
    int ltv_cents
    boolean is_active
    datetime created_at
    datetime updated_at
  }

  PILLARS {
    string id PK
    string protocol_id
    string name
    string code
    int order_index
    boolean is_active
  }

  METRICS {
    string id PK
    string protocol_id
    string pillar_id FK
    string name
    string code
    string direction
    string unit
    float min_score
    float max_score
    boolean is_active
  }

  MEASUREMENTS {
    string id PK
    string enrollment_id FK
    string metric_id FK
    float value_baseline
    float value_current
    float value_projected
    boolean improving_trend
  }

  MEASUREMENT_OVERALLS {
    string enrollment_id PK, FK
    string protocol_id
    json metrics
    json pillars
    json decision_matrix
  }

  STUDENTS ||--o{ ENROLLMENTS : "has"
  MENTORS ||--o{ ENROLLMENTS : "guides"
  ORGANIZATIONS ||--o{ ENROLLMENTS : "offers"

  PILLARS ||--o{ METRICS : "contains"
  ENROLLMENTS ||--o{ MEASUREMENTS : "tracks"
  METRICS ||--o{ MEASUREMENTS : "measured_as"

  ENROLLMENTS ||--|| MEASUREMENT_OVERALLS : "aggregates"
```

## Observações

- `measurement_overalls` é uma estrutura agregada para leitura rápida (denormalizada).
- `measurements` é o nível de granularidade por enrollment + métrica.
- Pilares e métricas são estruturados por protocolo.
