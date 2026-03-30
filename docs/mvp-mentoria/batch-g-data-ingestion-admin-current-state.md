# Batch G (Admin Data Ingestion) - Current State (Brownfield)



Date: 2026-03-30

Scope: document only the current repo state that is relevant to the proposed admin-facing data-ingestion flow described in `docs/discovery/data-ingestion-admin-brief.md`.



This is intentionally narrow. It does not propose the implementation, and it does not re-document unrelated parts of the project.



## 1) Current admin entry and access boundary



There is already an authenticated admin surface in the frontend and backend.



Current repo evidence:



- [routes.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/app/routes.tsx) exposes `/app/admin` behind `RequireAdmin`

- [routes.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/app/routes.tsx) redirects non-admin authenticated users to `/app/acesso-negado`

- [admin_mentoria.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_mentoria.py) defines `require_admin_user`

- [admin_mentoria.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_mentoria.py) enforces:

  - `401` when the bearer token is missing or invalid

  - `403` when the authenticated user is not `admin`



Current implication:



- The repo already has the correct boundary for an admin-only ingestion feature.

- The access rule is role-based, not tied to the literal email `admin@swaif.local`.

- A future ingestion feature should reuse this boundary instead of inventing a parallel auth check.



## 2) What ingestion capability already exists



The repo already contains a real admin-only ingestion flow, but it is much narrower than the new brief.



Current frontend evidence:



- [AdminPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/admin/pages/AdminPage.tsx) exposes a `Carga inicial` action only inside the `Alunos` panel

- [AdminPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/admin/pages/AdminPage.tsx) describes the Admin screen as operating "carga inicial de indicadores com contexto real por aluno"

- [adminStudentService.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/domain/services/adminStudentService.ts) posts the ingestion payload to `/admin/alunos/{student_id}/indicadores/carga-inicial`

- [adminStudent.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/contracts/adminStudent.ts) defines the frontend contract as:

  - `metric_values[]`

  - `checkpoints[]`

  - result `{ student_id, enrollment_id, measurement_count, checkpoint_count }`



Current backend evidence:



- [admin_students.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_students.py) exposes `POST /admin/alunos/{student_id}/indicadores/carga-inicial`

- [indicator_load.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/schemas/indicator_load.py) defines only one request mode and one result shape

- [indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/services/indicator_carga_service.py) persists measurement and checkpoint rows for the selected student enrollment



Current implication:



- The brownfield already supports a production-style admin-triggered write flow into JSON-backed runtime data.

- The implemented ingestion is not a generic "Data Ingestion" feature. It is a scoped "initial indicator load for one selected student".

- The current UI entry is contextual inside the student workflow, not a standalone admin operation menu or page.



## 3) Exact current ingestion flow in the repo



Current user flow:



1. Admin navigates to the Admin area and opens the `Alunos` panel.

2. Admin selects a student already linked to a product and mentor.

3. Admin clicks `Carga inicial`.

4. The modal loads active metrics for the selected product.

5. Admin enters baseline/current/projected values plus one checkpoint payload.

6. Admin moves to a confirmation step.

7. The frontend submits directly to the backend apply endpoint.

8. The modal shows a success state if the write succeeds.



Current repo evidence:



- [AdminPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/admin/pages/AdminPage.tsx) renders the `Carga inicial` button only when a student context exists

- [AdminPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/admin/pages/AdminPage.tsx) shows a two-step modal:

  - form step

  - confirm step

- [AdminPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/admin/pages/AdminPage.tsx) success copy says the student now has initial indicators ready for Centro, Radar, and Matriz



Current implication:



- There is already an explicit confirmation step before writing.

- There is no separate preview endpoint or dry-run mode. The current confirmation is a UI confirmation over local form data, not a validated backend preview.

- There is no source selection for file upload, server-side path, or structured batch payload origin.



## 4) Current backend contract and validation depth



The current backend validates the existence of the target context and active metrics, then writes the new payload.



Current repo evidence:



- [admin_students.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_students.py) maps missing student, enrollment, or metric conditions to the standard API error envelope

- [indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/services/indicator_carga_service.py) requires:

  - existing student

  - active enrollment for that student

  - existing active metric for every submitted metric row

- [indicator_load.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/schemas/indicator_load.py) enforces the basic shape of:

  - metric IDs and numeric values

  - checkpoint `week`

  - checkpoint `status` in `green|yellow|red`



What the current contract does not yet cover:



- no `dry_run` flag

- no `apply` versus `preview` split

- no execution identifier in the response

- no report of accepted vs rejected rows

- no conflict list

- no affected-file list

- no source metadata such as uploaded filename, internal path, or operator-entered origin

- no explicit duplication strategy (`reject`, `update`, or `merge`) at the API contract level



Current implication:



- The repo already has a validated write contract, but it is not yet the richer operational contract described in the new brief.



## 5) Current persistence behavior



The current ingestion flow writes directly into the JSON-backed measurement and checkpoint stores for one enrollment.



Current repo evidence:



- [measurement_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/measurement_repository.py) uses `replace_for_enrollment(...)`

- [checkpoint_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/checkpoint_repository.py) uses `replace_for_enrollment(...)`

- [indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/services/indicator_carga_service.py) calls both replace operations in sequence during `load_initial_indicators(...)`



Current behavior that follows from that implementation:



- existing measurement rows for the enrollment are removed and recreated

- existing checkpoint rows for the enrollment are removed and recreated

- generated record IDs are reassigned on write

- the flow behaves as "replace current initial set for this enrollment", not as append-only history



Current implication:



- The repo already has a simple, deterministic persistence model for this ingestion slice.

- The current model does not preserve version history per load and does not keep a row-level audit trail of replacements.

- A future generic ingestion feature should decide whether this replace semantics is acceptable or whether versioned/appended history is required.



## 6) Current backup and rollback posture



The repo already has snapshot tooling for the JSON storage layer, but the current ingestion endpoint does not call it.



Current repo evidence:



- [storage_maintenance.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/operations/storage_maintenance.py) provides:

  - `create_backup_snapshot(...)`

  - `verify_backup_snapshot(...)`

  - `restore_backup_snapshot(...)`

- [storage_maintenance.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/operations/storage_maintenance.py) snapshots the entire registered JSON store set and writes a `manifest.json`

- [backend-readiness-for-frontend.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/backend-readiness-for-frontend.md) already classifies JSON persistence as part of the operating backend posture

- [frontend/README.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/README.md) instructs operators to rehearse backup/restore before remote staging

- [backend/backups](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/backups) already contains committed snapshot manifests from prior operator rehearsals



What is not wired into the current ingestion path:



- no automatic snapshot before `/admin/alunos/{student_id}/indicadores/carga-inicial`

- no snapshot scoped to only the affected stores

- no rollback hook tied to an ingestion execution ID

- no operator-facing restore command surfaced inside the admin UI



Current implication:



- The project already has the technical building blocks for backup/restore.

- The new brief's backup-before-apply requirement is not currently satisfied by the ingestion endpoint itself.



## 7) Current auditability posture



The current ingestion slice has minimal operational traceability and no dedicated execution log.



Current repo evidence:



- [admin_mentoria.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_mentoria.py) can identify the authenticated admin user

- [admin_students.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_students.py) does not pass operator identity into `load_initial_indicators(...)`

- [indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/services/indicator_carga_service.py) does not persist:

  - operator

  - execution timestamp

  - source

  - dry-run/apply mode

  - backup location

  - final status

- [measurement_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/measurement_repository.py) and [checkpoint_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/checkpoint_repository.py) store only domain rows, not execution audit metadata



Current implication:



- The current implementation is sufficient for functional writes into the MVP analytics flow.

- It is not yet sufficient for the richer audit trail expected by the new brief.



## 8) Current alignment with the new brief



The brief asks for a broader operational capability than what exists today.



Already present in repo:



- admin-only access boundary

- admin UI entry point inside the student workflow

- explicit confirmation step before apply

- backend validation of target student enrollment and active metrics

- structured success result

- standard API error envelope

- JSON snapshot/restore utilities available elsewhere in the backend

- backend and frontend tests around the existing indicator-load flow



Still missing relative to the brief:



- dedicated `Ingestao de Dados` admin entry as an operation of its own

- source selection model

- backend dry-run mode

- preview summary before apply

- structured conflict and rejection reporting

- explicit affected-entity / affected-file report

- snapshot automatically tied to the apply execution

- persisted execution audit log

- documented rollback flow for this specific feature

- MVP contract for allowed JSON targets beyond the current measurement/checkpoint scope



Current implication:



- The brownfield is not starting from zero.

- The safest interpretation is that the existing indicator load can be reused as the seed pattern for the new feature, but the new feature is a broader capability and should not be described as "already done".



## 9) Current tests and evidence



There is already coverage at the nearest relevant layers for the existing ingestion slice.



Current repo evidence:



- [test_admin_indicator_load_api.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/api/test_admin_indicator_load_api.py) covers:

  - auth required

  - successful load

  - detail read after load

  - missing metric rejection

  - inactive metric rejection

- [test_indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/unit/test_indicator_carga_service.py) covers:

  - service success path

  - unknown metric rejection

- [admin-client-modal.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/admin-client-modal.test.tsx) covers:

  - opening the ingestion modal

  - successful modal confirmation flow



Current implication:



- The repo already has a stable baseline test surface for evolving this capability incrementally.

- New dry-run, backup, audit, and rollback behavior should extend these tests rather than replacing them.



## 10) Files most likely affected by a future implementation



Frontend entry and contract surface:



- [AdminPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/admin/pages/AdminPage.tsx)

- [adminStudentService.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/domain/services/adminStudentService.ts)

- [adminStudent.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/contracts/adminStudent.ts)

- [routes.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/app/routes.tsx) only if the team chooses a dedicated route instead of the current in-panel entry



Backend API and service surface:



- [admin_students.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/admin_students.py)

- [indicator_load.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/schemas/indicator_load.py)

- [indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/services/indicator_carga_service.py)



Persistence and operational support that may need extension:



- [measurement_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/measurement_repository.py)

- [checkpoint_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/checkpoint_repository.py)

- [storage_maintenance.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/operations/storage_maintenance.py)



Tests likely to grow:



- [test_admin_indicator_load_api.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/api/test_admin_indicator_load_api.py)

- [test_indicator_carga_service.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/unit/test_indicator_carga_service.py)

- [admin-client-modal.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/admin-client-modal.test.tsx)



## 11) Recommended brownfield reading order before implementation



For the next implementation step, the most relevant current anchors are:



1. [data-ingestion-admin-brief.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/discovery/data-ingestion-admin-brief.md)

2. [batch-g-data-ingestion-admin-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md)

3. [admin-crud-spec.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/admin-crud-spec.md)

4. [admin-crud-implementation-plan.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/admin-crud-implementation-plan.md)

5. [contracts-freeze-v1.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/contracts-freeze-v1.md)



Final brownfield summary:



- The repo already has a real admin-only ingestion write path for one student's initial indicators.

- The repo also already has snapshot tooling and standardized auth/error patterns that can support a broader ingestion feature.

- The requested "Ingestao de Dados" initiative is still materially larger than the current implementation because dry-run, source handling, execution audit, and backup-linked apply are not yet part of the active ingestion contract.
