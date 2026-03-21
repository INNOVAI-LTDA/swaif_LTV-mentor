# BMAD Command Sheet

This sheet assumes the standard `bmm` workflow for product/software work.

## 1. Project Build From Scratch

Use this when you are starting from zero.

1. `bmad-brainstorming`
Prompt: `Help me brainstorm a new product: [idea], users: [audience], outcome: [goal].`

2. `bmad-bmm-create-product-brief`
Prompt: `Create a product brief for [product name]. It should solve [problem] for [users].`

3. `bmad-bmm-create-prd`
Prompt: `Create the PRD for [product name] based on the brief.`

4. `bmad-bmm-create-ux-design`
Prompt: `Create UX design for the main flows: [flow 1], [flow 2], [flow 3].`

5. `bmad-bmm-create-architecture`
Prompt: `Create the technical architecture for [product name] using [preferred stack if any].`

6. `bmad-bmm-create-epics-and-stories`
Prompt: `Create epics and stories from the PRD and architecture.`

7. `bmad-bmm-check-implementation-readiness`
Prompt: `Check implementation readiness for this project.`

8. `bmad-bmm-sprint-planning`
Prompt: `Generate the sprint plan from the epics and stories.`

9. `bmad-bmm-create-story`
Prompt: `Create the next story.`

10. `bmad-bmm-dev-story`
Prompt: `Implement the next story.`

11. `bmad-bmm-code-review`
Prompt: `Review the story implementation.`

## 2. Project Build From An Existing Folder Or Repo

Use this when you already have code, some screens, a partial frontend, or a prototype app.

1. `bmad-bmm-document-project`
Prompt: `Document this existing project from the repo. Identify architecture, flows, risks, and gaps.`

2. `bmad-bmm-generate-project-context`
Prompt: `Generate project context from this repo for future AI implementation.`

3. `bmad-bmm-quick-spec`
Prompt: `Create a quick spec for turning this partial project into a production-ready product. Existing assets: [screens/prototype/code]. Missing parts: [list].`

4. `bmad-bmm-technical-research`
Prompt: `Research the best implementation approach for evolving this existing repo into [target outcome].`

5. `bmad-bmm-create-architecture`
Prompt: `Create architecture for the current repo, preserving what exists and filling the missing pieces.`

6. `bmad-bmm-create-epics-and-stories`
Prompt: `Create epics and stories from the current repo state plus the target scope.`

7. `bmad-bmm-quick-dev-new-preview`
Prompt: `Implement the next brownfield improvement in this repo: [feature/change], preserving existing patterns.`

Optional UX-heavy path:

- `bmad-wds-product-evolution`
Prompt: `Improve this existing product. Current state: [repo/app/screens]. Target improvement: [goal].`

## 3. Project Refactoring

Use this when the product exists and the main goal is cleanup, restructuring, or hardening.

1. `bmad-bmm-document-project`
Prompt: `Document this project with focus on architecture debt, inconsistencies, and refactor risks.`

2. `bmad-bmm-generate-project-context`
Prompt: `Generate project context so future refactors follow existing rules and patterns.`

3. `bmad-bmm-technical-research`
Prompt: `Research the best refactor strategy for [area/module], preserving behavior and minimizing regressions.`

4. `bmad-bmm-quick-spec`
Prompt: `Create a quick spec for refactoring [module/feature]. Goals: [maintainability/performance/cleanup], constraints: [no regressions/public API stable/etc.].`

5. `bmad-bmm-correct-course`
Prompt: `We need a course correction. Current implementation has drift in [area]. Propose the safest refactor path.`

6. `bmad-bmm-quick-dev-new-preview`
Prompt: `Refactor [module/feature] in this repo while preserving behavior, tests, and existing architecture patterns.`

7. `bmad-review-edge-case-hunter`
Prompt: `Review this refactor plan/code for unhandled edge cases.`

8. `bmad-review-adversarial-general`
Prompt: `Critically review this refactor for risks, regressions, and weak assumptions.`

## Quick Rule Of Thumb

- New idea from zero: use `brief -> PRD -> UX -> architecture -> epics -> sprint`.
- Existing repo with partial assets: start with `document-project` and `generate-project-context`, then move to `quick-spec` or `architecture`.
- Refactor: start with `document-project`, `project-context`, and `technical-research`, then execute via `quick-dev-new-preview`.
