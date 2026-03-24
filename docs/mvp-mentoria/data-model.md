# MVP Mentoria - modelo de dados inicial

> Canonical platform note: the long-term backend source of truth is now documented in `docs/architecture/canonical-data-architecture.md`. This file remains useful as a legacy MVP data-model reference, but `organization`, `protocol`, `enrollment`, `mentor`, and `student` should be interpreted through the canonical mapping defined there.

## Objetivo
Definir modelos iniciais para backend FastAPI com persistencia simples em JSON, alinhados aos contratos inferidos das 3 visualizacoes:
- Centro de Comando
- Radar de Transformacao
- Matriz de Renovacao Antecipada

## Convencoes de linguagem (padrao mentoria)
- `mentor`: profissional responsavel pela mentoria.
- `aluno`: pessoa acompanhada.
- `mentoria`: programa comercial/operacional.
- `protocolo` ou `metodo`: estrutura de pilares e metricas.
- No codigo: manter nomes tecnicos estaveis em ingles (`Student`, `Protocol` etc.), com labels de UI em portugues de mentoria.

## Convencoes tecnicas
- IDs string com prefixo (`usr_`, `org_`, `mtr_`, `std_`, `prt_`, `plr_`, `met_`, `enr_`, `mea_`, `rad_`, `rns_`).
- Datas em ISO-8601 UTC (`2026-03-08T14:30:00Z`).
- Valores percentuais normalizados em `0..1` no backend (`progress_score`, `engagement_score`).
- Dinheiro em centavos (`ltv_cents`) para evitar erro de ponto flutuante.

---

## 1) User
Conta de autenticacao.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `organization_id` | string | FK -> Organization |
| `email` | string | unico por organizacao |
| `password_hash` | string | senha nunca em texto plano |
| `role` | string enum | `org_admin` \| `mentor` |
| `is_active` | boolean | bloqueio logico |
| `created_at` | datetime | auditoria |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `display_name` | string | nome de exibicao |
| `last_login_at` | datetime | ultimo acesso |

### Relacionamentos
- N:1 com `Organization`
- 1:0..1 com `Mentor` (perfil)

### Uso nas visualizacoes
- Indireto (controle de acesso das 3 telas).

---

## 2) Organization
Tenant de white label.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `name` | string | nome interno |
| `slug` | string | identificador unico |
| `timezone` | string | ex: `America/Sao_Paulo` |
| `currency` | string | ex: `BRL` |
| `created_at` | datetime | auditoria |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `brand_name` | string | nome publico |
| `vocabulary` | object | override de termos (`aluno`, `mentor`) |
| `logo_url` | string | branding |

### Relacionamentos
- 1:N com `User`, `Mentor`, `Student`, `Protocol`, `Enrollment`

### Uso nas visualizacoes
- Filtragem multi-tenant dos dados das 3 visoes.

---

## 3) Mentor
Perfil operacional do mentor.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `organization_id` | string | FK -> Organization |
| `user_id` | string | FK -> User |
| `full_name` | string | nome completo |
| `email` | string | contato |
| `is_active` | boolean | status |
| `created_at` | datetime | auditoria |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `phone` | string | contato |
| `bio` | string | descricao curta |

### Relacionamentos
- N:1 com `Organization`
- 1:1 com `User`
- 1:N com `Enrollment`

### Uso nas visualizacoes
- Segmentacao por mentor (filtro futuro em Centro/Matriz).

---

## 4) Student
Cadastro base do aluno.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `organization_id` | string | FK -> Organization |
| `full_name` | string | nome do aluno |
| `status` | string enum | `active` \| `paused` \| `churned` |
| `created_at` | datetime | auditoria |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `initials` | string | para bolhas da matriz |
| `email` | string | contato |
| `phone` | string | contato |
| `tags` | array[string] | segmentacao |

### Relacionamentos
- N:1 com `Organization`
- 1:N com `Enrollment`

### Uso nas visualizacoes
- Base identitaria nas 3 visoes (`name`, `initials`).

---

## 5) Protocol
Metodo/protocolo da mentoria.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `organization_id` | string | FK -> Organization |
| `name` | string | nome do metodo |
| `version` | string | ex: `v1` |
| `is_active` | boolean | status |
| `created_at` | datetime | auditoria |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `description` | string | resumo |

### Relacionamentos
- N:1 com `Organization`
- 1:N com `Pillar`
- 1:N com `Enrollment`

### Uso nas visualizacoes
- Contexto de exibição (nome da mentoria/metodo no Centro e Matriz).

---

## 6) Pillar
Pilar do metodo.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `protocol_id` | string | FK -> Protocol |
| `code` | string | chave estavel |
| `name` | string | label do pilar |
| `order_index` | integer | ordenacao no radar |
| `is_active` | boolean | status |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `description` | string | texto |
| `axis_sub` | string | subtitulo do eixo no Radar |

### Relacionamentos
- N:1 com `Protocol`
- 1:N com `Metric`
- 1:N com `RadarScore`

### Uso nas visualizacoes
- Radar: eixos (`axisLabel`/`axisSub`).

---

## 7) Metric
Indicador vinculado a um pilar.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `pillar_id` | string | FK -> Pillar |
| `code` | string | chave estavel |
| `name` | string | label exibido |
| `direction` | string enum | `higher_better` \| `lower_better` \| `target_range` |
| `is_active` | boolean | status |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `unit` | string | ex: `%`, `pts` |
| `target_min` | number | alvo inferior |
| `target_max` | number | alvo superior |
| `target_text` | string | texto de alvo para UI |
| `weight` | number | peso no score do pilar |

### Relacionamentos
- N:1 com `Pillar`
- 1:N com `Measurement`

### Uso nas visualizacoes
- Centro: detalhe (`metricValues`).
- Matriz: barras de indicadores (`markers`).

---

## 8) Enrollment
Vinculo do aluno na mentoria (com mentor e protocolo).

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `organization_id` | string | FK -> Organization |
| `student_id` | string | FK -> Student |
| `mentor_id` | string | FK -> Mentor |
| `protocol_id` | string | FK -> Protocol |
| `start_date` | date | inicio do ciclo |
| `total_days` | integer | duracao planejada |
| `current_day` | integer | dia atual do ciclo |
| `progress_score` | number | 0..1 |
| `engagement_score` | number | 0..1 |
| `urgency_status` | string enum | `normal` \| `watch` \| `critical` \| `rescue` |
| `ltv_cents` | integer | valor economico |
| `status` | string enum | `active` \| `completed` \| `cancelled` |
| `created_at` | datetime | auditoria |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `end_date` | date | fechamento do ciclo |
| `renewal_due_date` | date | data alvo de renovacao |

### Relacionamentos
- N:1 com `Organization`, `Student`, `Mentor`, `Protocol`
- 1:N com `Measurement`, `RadarScore`, `RenewalSnapshot`

### Uso nas visualizacoes
- Centro: linha principal (`day/totalDays`, urgencia, engajamento, D-45).
- Matriz: posicao da bolha (`progress_score`, `engagement_score`) e KPIs.

---

## 9) Measurement
Medicao de indicador por aluno (snapshot inicial e evolucao).

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `enrollment_id` | string | FK -> Enrollment |
| `metric_id` | string | FK -> Metric |
| `collected_at` | datetime | momento da coleta |
| `value_current` | number | valor atual |
| `is_baseline` | boolean | marca carga inicial |
| `created_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `value_baseline` | number | redundancia util para leitura rapida |
| `value_projected` | number | opcional |
| `improving_trend` | boolean | tendencia |
| `note` | string | anotacao |

### Relacionamentos
- N:1 com `Enrollment`, `Metric`

### Uso nas visualizacoes
- Centro: detalhe de metricas por aluno.
- Matriz: resumo de indicadores no drawer/painel.

---

## 10) RadarScore
Score agregado por pilar para o radar.

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `enrollment_id` | string | FK -> Enrollment |
| `pillar_id` | string | FK -> Pillar |
| `baseline_score` | number | 0..100 |
| `current_score` | number | 0..100 |
| `updated_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `projected_score` | number | 0..100 |
| `insight` | string | narrativa curta por eixo |

### Relacionamentos
- N:1 com `Enrollment`, `Pillar`

### Uso nas visualizacoes
- Radar: contrato direto para `axisScores`.

---

## 11) RenewalSnapshot
Snapshot de renovacao para decisao comercial (D-45, quadrante, recomendacao).

### Campos obrigatorios
| Campo | Tipo | Observacao |
|---|---|---|
| `id` | string | PK |
| `enrollment_id` | string | FK -> Enrollment |
| `snapshot_date` | date | data de referencia |
| `days_left` | integer | dias restantes |
| `quadrant` | string enum | `topRight` \| `topLeft` \| `bottomRight` \| `bottomLeft` |
| `renewal_priority` | string enum | `low` \| `medium` \| `high` |
| `renewal_reason` | string | justificativa |
| `suggested_offer` | string | proposta recomendada |
| `progress_score` | number | 0..1 |
| `engagement_score` | number | 0..1 |
| `urgency_status` | string enum | `normal` \| `watch` \| `critical` \| `rescue` |
| `ltv_cents` | integer | oportunidade de receita |
| `created_at` | datetime | auditoria |

### Campos opcionais
| Campo | Tipo | Observacao |
|---|---|---|
| `hormozi_score` | number | score auxiliar da narrativa |
| `indicator_summary` | array[object] | cache para `markers/metricValues` |

### Relacionamentos
- N:1 com `Enrollment`

### Uso nas visualizacoes
- Centro: gatilhos de renovacao e narrativa.
- Matriz: quadrante, prioridade, motivos e oferta.

---

## Relacionamentos (visao geral)
- `Organization` 1:N `User`, `Mentor`, `Student`, `Protocol`, `Enrollment`
- `User` 1:0..1 `Mentor`
- `Protocol` 1:N `Pillar`
- `Pillar` 1:N `Metric`
- `Student` 1:N `Enrollment`
- `Mentor` 1:N `Enrollment`
- `Enrollment` 1:N `Measurement`, `RadarScore`, `RenewalSnapshot`

## Observacoes por visualizacao

### Centro de Comando
- Base: `Enrollment` + `Student` + `Protocol`
- Detalhe: `Measurement` (com alvo e tendencia) + checkpoints/sinais em `RenewalSnapshot.indicator_summary` (ou estrutura dedicada futura)
- KPI rapido: contagens por `urgency_status` e `days_left`

### Radar de Transformacao
- Base: `RadarScore` + metadados de `Pillar`
- Contrato de saida: `axisScores` com `axisKey`, `axisLabel`, `axisSub`, `baseline`, `current`, `projected`, `insight`

### Matriz de Renovacao Antecipada
- Base: `RenewalSnapshot` + `Enrollment` + `Student`
- Posicao: `progress_score` x `engagement_score`
- Receita: `ltv_cents`
- Narrativa: `renewal_reason` + `suggested_offer`

---

## Sugestao de organizacao inicial em JSON

### Estrutura de pastas
```txt
data/
  users.json
  organizations.json
  mentors.json
  students.json
  protocols.json
  pillars.json
  metrics.json
  enrollments.json
  measurements.json
  radar_scores.json
  renewal_snapshots.json
```

### Estrutura padrao de cada arquivo
```json
{
  "version": 1,
  "items": []
}
```

### Exemplo minimo de vinculacao (resumido)
```json
{
  "organization": { "id": "org_001", "name": "Mentoria Alpha" },
  "mentor": { "id": "mtr_001", "organization_id": "org_001" },
  "student": { "id": "std_001", "organization_id": "org_001" },
  "protocol": { "id": "prt_001", "organization_id": "org_001" },
  "pillar": { "id": "plr_001", "protocol_id": "prt_001" },
  "metric": { "id": "met_001", "pillar_id": "plr_001" },
  "enrollment": {
    "id": "enr_001",
    "student_id": "std_001",
    "mentor_id": "mtr_001",
    "protocol_id": "prt_001"
  },
  "measurement": {
    "id": "mea_001",
    "enrollment_id": "enr_001",
    "metric_id": "met_001"
  },
  "radar_score": {
    "id": "rad_001",
    "enrollment_id": "enr_001",
    "pillar_id": "plr_001"
  },
  "renewal_snapshot": {
    "id": "rns_001",
    "enrollment_id": "enr_001"
  }
}
```

## Simplificacoes assumidas para o MVP
- Sem SQLite no primeiro corte; JSON com escrita atomica.
- Sem historico complexo de versoes de protocolo (apenas `version` textual).
- Campos derivados podem ser armazenados em `Enrollment`/`RenewalSnapshot` para acelerar leitura das telas.
- Evolucao futura prevista: mover para SQLite/PostgreSQL sem alterar contratos de API.
