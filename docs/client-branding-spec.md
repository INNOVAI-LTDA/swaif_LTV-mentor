# Client Branding Spec: Acelerador Medico

## 1. Scope

This document defines the visual skin for the MVP validation phase of the Acelerador Medico client adaptation.

This phase is limited to:
- visual validation
- navigable surfaces
- local mocks and hard-coded data
- brand consistency across Login, Mentor, Aluno, and Admin

This phase excludes:
- new backend flows
- real authentication
- real RBAC
- structural redesign of the platform

## 2. Source Of Truth

Primary source used in this stage:
- `docs/branding/design-system-acelerador-medico.md`

Supporting references used:
- `docs/branding/briefing-visual-codex-paralelo.md`
- `docs/branding/arquitetura_mvp.md`
- assets in `docs/branding/`

Note:
- the requested path `docs/branding/acelerador-medico-design-system.md` was not found in the repository
- the equivalent file currently present is `docs/branding/design-system-acelerador-medico.md`

## 3. Brand Reading

The client visual language is consistent in the local assets and can be summarized as:
- premium
- dark
- high contrast
- performance-oriented
- executive
- assertive, without visual noise

The interface should communicate:
- authority
- progress
- clarity
- selective use of emphasis

## 4. Asset Inventory And Intended Use

Available brand assets:
- logos: `logo v1.png` to `logo v5.png`
- icons: `ícone v1.png` to `ícone v4.png`
- visual references: `examplos_id_vis_01.png` to `examplos_id_vis_03.png`

Recommended usage for this MVP phase:
- use the full logo on dark surfaces for Login and major headers
- use the icon mark in compact navigation areas such as sidebar and mobile header
- preserve the original files; do not redraw, crop, recolor, or recreate the brand mark

Practical preference based on the inspected assets:
- primary full-brand expression: white typography with gold mark on black background
- primary compact brand expression: gold icon mark on black background
- avoid logo variants that depend on light backgrounds until such surfaces are intentionally introduced

## 5. Visual Tokens

Base color tokens derived from the design system:

| Token | Hex | Primary usage |
|---|---|---|
| `bg-primary` | `#090909` | page background |
| `bg-secondary` | `#121212` | secondary areas |
| `surface-primary` | `#1A1A1A` | cards and panels |
| `surface-secondary` | `#242424` | nested surfaces and hover blocks |
| `border-default` | `#333333` | separators and outlines |
| `text-primary` | `#FFFFFF` | primary text |
| `text-secondary` | `#BFBFBF` | support text |
| `accent-primary` | `#FAB800` | CTA, active states, highlights |
| `accent-secondary` | `#FFBD00` | hover and emphasis variation |
| `success` | `#39B56A` | positive feedback |
| `warning` | `#D9A100` | warning state |
| `danger` | `#D64545` | destructive or critical feedback |

Brand application rules:
- black and graphite must dominate the page area
- gold is a signal, not a fill strategy
- white carries reading priority
- gray is used to build depth, not to flatten the UI

## 6. Typography

Approved type direction from the design system:
- `Montserrat`, fallback `Inter`, then `sans-serif`

Visual hierarchy:
- page title: 28px to 36px, strong weight
- section title: 20px to 24px
- subsection or KPI label: 14px to 16px
- body: 14px to 16px
- support copy: 12px to 13px

Application rules:
- prioritize large, clean headlines on high-value areas
- avoid long paragraph blocks
- keep line length controlled, especially on dark backgrounds

## 7. Surface And Layout Rules

Layout principles:
- dark immersive background
- generous spacing using an 8px rhythm
- cards with contrast separation instead of heavy shadows
- strong hierarchy between page shell, section shell, and local modules

Recommended spacing:
- card padding: 16px to 24px
- section gaps: 20px to 32px
- internal stacks: 8px, 12px, or 16px

Visual density rules:
- Mentor can be medium density
- Aluno must be the lightest view
- Admin can be dense, but only with clear section framing

## 8. Component-Level Guidance

Buttons:
- primary button uses gold background and black text
- secondary button uses transparent background with gold border
- only one dominant CTA per section when possible

Inputs:
- dark field background
- white input text
- subtle gray border
- gold focus state

Cards:
- primary dark surface
- subtle border
- rounded corners
- no heavy elevation

Sidebar and tabs:
- black or near-black foundation
- active item clearly marked with gold
- inactive items remain readable, not low-contrast

Tables and status chips:
- use white for core values
- gray for support details
- status colors must stay semantic and sparing

## 9. Image And Atmosphere Direction

The inspected reference pieces reinforce a specific mood:
- black background as the main stage
- gold blocks or gold text only in strategic moments
- editorial composition with focal images
- premium event or performance aesthetic

Allowed atmosphere devices:
- subtle gradients on dark backgrounds
- faint texture or image overlay in login hero area
- restrained use of portrait or event imagery if already present in the repo

Avoid:
- bright backgrounds
- generic SaaS gradients unrelated to the client identity
- over-decoration
- adding colors outside the approved palette

## 10. Do And Do Not

Do:
- keep the interface sober and premium
- preserve strong contrast
- use brand assets exactly as delivered
- make gold carry intentional meaning

Do not:
- invent a new visual language
- spread gold across every border, title, and surface
- overload cards with multiple CTA styles
- create a bright, playful, or generic dashboard look

## 11. Implementation Readiness Checklist

This branding spec is ready to guide the next steps if each new screen:
- starts from the approved token set
- uses the delivered logo and icon files
- preserves black, graphite, white, and gold as the dominant palette
- keeps typography restrained and high-contrast
- differentiates Mentor, Aluno, and Admin by information structure, not by changing the brand
