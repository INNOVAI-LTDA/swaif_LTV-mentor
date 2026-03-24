# Canonical Data Architecture

## Purpose

This document defines the canonical platform-facing backend domain for a client-agnostic product, while preserving client-specific vocabulary at the UI, reporting, and API-compatibility layers.

## Canonical domain

The backend canonical entities are:

- `Client`
- `Product`
- `Provider`
- `EndUser`
- `ProductPillar`
- `PillarMetric`
- `MetricMeasure`
- `ProductAssignment`
- `JourneyCheckpoint`

These names are the source of truth for future backend architecture, migration planning, and storage evolution.

## Current legacy-to-canonical mapping

| Legacy/current term | Canonical meaning |
| --- | --- |
| `client` | `Client` |
| `organization` | `Product` |
| `mentor` | `Provider` |
| `student` | `EndUser` |
| `enrollment` | `ProductAssignment` |
| `protocol` | product method/version metadata |
| `pillar` | `ProductPillar` |
| `metric` | `PillarMetric` |
| `measurement` | `MetricMeasure` |
| `checkpoint` | `JourneyCheckpoint` |

## Relationship model

- `Client 1:N Product`
- `Client 1:N Provider`
- `Client 1:N EndUser`
- `Product 1:N ProductPillar`
- `ProductPillar 1:N PillarMetric`
- `Product 1:N ProductAssignment`
- `Provider 1:N ProductAssignment`
- `EndUser 1:N ProductAssignment`
- `ProductAssignment 1:N MetricMeasure`
- `ProductAssignment 1:N JourneyCheckpoint`

Operational lifecycle fields such as progress, engagement, urgency, days-left, and LTV belong to `ProductAssignment`.

## Vocabulary policy

Client-facing wording can change without redefining backend canonical names.

For AccMed:

- `Client` -> `Cliente`
- `Product` -> `Produto`
- `Provider` -> `Mentor`
- `EndUser` -> `Aluno`
- `ProductPillar` -> `Pilar`
- `PillarMetric` -> `Indicador` or `Metrica`
- `MetricMeasure` -> `Valor do indicador`

## Incremental migration strategy

This repo now supports a non-destructive canonical migration path:

1. Legacy stores remain active for the running backend and current frontend contracts.
2. Canonical repository adapters expose generic records over the same JSON files.
3. `python -m app.operations.export_canonical_data --output-dir <dir>` exports the future target store set:
   - `clients.json`
   - `products.json`
   - `providers.json`
   - `end_users.json`
   - `product_pillars.json`
   - `pillar_metrics.json`
   - `product_assignments.json`
   - `metric_measures.json`
   - `journey_checkpoints.json`
4. A later phase may switch services and APIs from legacy names to canonical names behind compatibility adapters.

## Implementation note

The current backend still exposes legacy API contracts such as `OrganizationOut`, `MentorOut`, `StudentOut`, `EnrollmentOut`, and `ProtocolOut`. Those remain compatibility surfaces for now. The canonical layer is introduced as an internal architecture and migration boundary, not as a breaking API rename.
