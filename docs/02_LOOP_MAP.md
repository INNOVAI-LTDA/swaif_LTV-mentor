# Loop Map

## 1. Normal Story Loop
Use when one boundary is already chosen and a story-sized batch is ready.

Commands:
- bmad-create-story
- bmad-dev-story
- bmad-code-review

Default model map:
- story -> GPT 5.2 | Medium
- dev -> GPT 5.1 Codex Max | High
- review -> GPT 5.4 | High

## 2. Fix Loop
Use when review failed but the scope is still correct.

Commands:
- bmad-create-story
- bmad-dev-story
- bmad-code-review

Rule:
- smallest valid fix set only
- keep original batch boundary

## 3. Correct-Course Loop
Use when review exposed wrong scope, mixed boundaries, or architecture drift.

Commands:
- bmad-correct-course
- bmad-create-story
- bmad-dev-story
- bmad-code-review

## 4. Quick-Dev Loop
Use only for tiny, low-risk local changes.

Command:
- bmad-quick-dev

## 5. UI Cleanup Loop
Use when design clarification is needed before coding.

Commands:
- bmad-document-project
- bmad-create-ux-design
- bmad-create-story
- bmad-dev-story
- bmad-code-review

## 6. Deploy Boundary Loop
Use for batched deploy/hardening work.

Rule:
- for each batch, run all steps
- never for each step, run all batches
