# Roles And Access Visual Spec

## 1. Purpose

This document defines how Admin, Mentor, and Aluno should look and behave in the MVP validation phase.

Scope of this document:
- visual role differentiation
- navigation shape by role
- information priority by role
- simulated access behavior for review sessions

This document does not define:
- real RBAC
- real permissions enforcement
- authentication logic

## 2. Shared Rules Across Roles

All roles must:
- use the same visual shell and branding tokens
- feel part of the same product family
- expose only the navigation needed for the role validation
- use local mocked data

Shared shell expectations:
- dark branded app frame
- visible client branding in header or sidebar
- clear page title and page context
- consistent card, table, and chip language

## 3. Login Role Entry

The Login screen in this phase should support visual entry by profile.

Required behavior:
- fields for usuario and senha
- simulated entry action only
- explicit profile options for `Admin`, `Mentor`, and `Aluno`

Allowed simulation patterns:
- segmented control
- role cards
- select input

Preferred pattern:
- small role selector paired with the main login form

Reason:
- it validates the branded entry flow without pretending to be real auth

## 4. Mentor Visual Reading

### Core objective

Give the mentor an executive view focused on action, coaching, and decision support.

### Primary navigation

Main sections, in this order:
1. Matriz de Decisao
2. Centro de Comando
3. Radar de Evolucao
4. Produtos
5. Alunos
6. Usuario

### Information hierarchy

Highest priority:
- top KPIs
- current student portfolio health
- alerts or stalled progress
- quick access to decision views

Secondary priority:
- student list or grouped cards
- product context
- mentor profile shortcuts

### Density profile

Mentor should be:
- analytical
- moderately dense
- easy to scan in wide layouts

### Recommended signature blocks

- KPI strip with 3 to 5 summary metrics
- tabbed or segmented view for the 3 main analytical areas
- student summary table or board
- quick cards for pending follow-ups

## 5. Aluno Visual Reading

### Core objective

Give the student a personal, motivational, progress-centered experience.

### Primary navigation

Main sections, in this order:
1. Radar de Evolucao
2. Produtos
3. Mentores
4. Usuario

### Information hierarchy

Highest priority:
- own evolution snapshot
- current progress status
- immediate next milestone

Secondary priority:
- timeline or journey
- personal indicators
- mentor references

### Density profile

Aluno should be:
- lighter than Mentor
- less table-driven
- more narrative and progress-oriented

### Recommended signature blocks

- hero card with current stage and main callout
- central radar module
- timeline of progression
- compact indicators panel

## 6. Admin Visual Reading

### Core objective

Give the admin an operational control center that feels complete but not overloaded.

### Primary navigation

Main sections, in this order:
1. Cliente
2. Produtos
3. Mentores
4. Alunos
5. Operacoes
6. Usuario

### Information hierarchy

Highest priority:
- organizational context
- entity relationships
- operational action points
- data management paths

Secondary priority:
- support metrics
- queue states
- recent operations or pending confirmations

### Density profile

Admin can be the most information-dense role, but must maintain:
- strong tab boundaries
- clear action grouping
- stable layout rhythm

### Recommended signature blocks

- high-level status strip
- tabbed data views
- operational table with action column
- placeholders for create, update, and delete flows

## 7. Visual Differentiation Matrix

| Area | Mentor | Aluno | Admin |
|---|---|---|---|
| Primary tone | executive | personal progress | operational control |
| Main module | analysis tabs | radar + journey | data views + operations |
| Density | medium | low to medium | medium to high |
| Data style | KPI + roster | progress narrative | tables + management |
| CTA style | guided action | next step | structured operations |

## 8. Simulated Access Rules For This Phase

Access rules should be represented visually, not enforced technically.

Approved behavior:
- each role lands directly on its own screen
- hidden navigation items may differ by mock role
- buttons can open placeholder panels or no-op states if needed

Forbidden behavior in this phase:
- real permission checks
- backend-controlled navigation
- auth session complexity

## 9. Acceptance Criteria For Visual Role Readability

Each role is visually approved when:
- the role can be recognized in under 10 seconds by a reviewer
- the navigation matches the role purpose
- the first viewport makes the role's job obvious
- the layout density is appropriate to the role
- the branded shell remains consistent across all roles
