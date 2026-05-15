# Story 1.1: Add Authoritative Assignment Fact Persistence

Status: review

## Story

Como mantenedor da plataforma,
quero persistir fatos de assignment em uma camada autoritativa de repositório,
para que as superfícies analíticas deixem de depender de estado derivado ad hoc.

## Fontes Autoritativas (Normativas para esta Story)

- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/command-center-radar-decision-matrix-architecture.md`
- `_bmad-output/planning-artifacts/command-center-radar-decision-matrix-epics-and-stories.md`
- `_bmad-output/planning-artifacts/implementation-readiness-report-2026-05-09-rerun.md`

## Escopo (In)

1. Introduzir persistencia autoritativa de `product_assignments` na camada de repositorio, mantendo handlers de rota finos e orquestracao em servicos.
2. Garantir que servicos consigam resolver o estado de negocio de assignment sem ler tabelas de projecao como fonte de verdade.
3. Preservar contratos v1 congelados (paths, payloads, tipos e semantica) para Command Center, Radar e Decision Matrix.
4. Preparar o caminho para seed/backfill conforme Appendix C sem executar a migracao completa nesta story.

## Fora de Escopo (Out)

1. Implementar `metric_measures_current`, `journey_checkpoints_current` ou `assignment_score_state` (Stories 1.2 e 1.3).
2. Introduzir historico append-only (Epic 2) ou projecoes Radar/Command Center/Decision Matrix (Epics 3 e 4).
3. Alterar shape de endpoint, envelope de erro, naming de campo ou contratos frontend.
4. Definir tecnologia de fila/worker para refresh assíncrono.

## Restrições de Arquitetura e Contrato (Obrigatórias)

1. Brownfield estrito: manter layering `routes -> services -> repositories`.
2. Contrato v1 congelado: nenhuma mudanca em endpoints, campos e tipos (Appendix B + `contracts-freeze-v1.md`).
3. `product_assignments` passa a ser fonte autoritativa de lifecycle de assignment; projecoes continuam descartaveis e nao-autoritativas.
4. `decision_matrix_status` pode permanecer helper de compatibilidade, nunca estado autoritativo de workflow.
5. Campos derivados devem manter compatibilidade de semantica com adaptadores atuais (`student`, `programName`, `plan`) sem mover normalizacao para componentes.

## Dependências

- Nenhuma story previa (primeira do plano).
- Esta story desbloqueia: 1.2, 1.3 e toda cadeia posterior.

## Critérios de Aceite (BDD)

### AC1 - Persistencia autoritativa atras de fronteira de repositorio

**Dado** que os servicos analiticos ainda assumem partes de armazenamento legado
**Quando** a persistencia autoritativa para `product_assignments` for introduzida atras da fronteira de repositorio
**Então** handlers de rota continuam chamando servicos sem conhecimento de persistencia
**E** os paths de endpoint e nomes de campo DTO v1 permanecem inalterados.

### AC2 - Linha minima de campos de assignment

**Dado** um create ou update de assignment para relacao mentor-aluno-produto ativa
**Quando** o repositorio autoritativo persistir a mudanca
**Então** a linha contem os campos baseline da arquitetura (`assignment_id`, `product_id`, `provider_id`, `end_user_id`, `status`, `start_at`, `end_at`, `days_left`, `ltv_cents`, `created_at`, `updated_at`)
**E** a semantica de ciclo/seed segue Appendix C.

### AC3 - Fonte de verdade sem dependencia de projecao

**Dado** um assignment ja persistido em `product_assignments`
**Quando** um servico de negocio precisar resolver estado atual do assignment
**Então** ele usa o repositorio de fatos autoritativos
**E** nao depende de tabela de projecao como truth source.

### AC4 - Preservacao de contrato congelado em superfícies analíticas

**Dado** chamadas v1 para Command Center, Radar e Decision Matrix
**Quando** a story for integrada
**Então** os payloads seguem mapeamento de Appendix B (mesmos campos/tipos)
**E** o envelope de erro continua `{ error: { status, code, message, details } }`.

### AC5 - Prontidao para migracao seed_backfill

**Dado** a necessidade de migrar dados legados na Wave 5
**Quando** a story 1.1 estiver concluida
**Então** o mapeamento de seed de `enrollments.json -> product_assignments` (Appendix C.1) esta implementavel sem reinterpretacao de regra
**E** cardinalidade e regra de desambiguacao por `updated_at` permanecem explicitas para o passo de backfill.

## Slice Boundary

Story pertencente ao Slice A (write model foundation) do sprint plan.

Critério de fronteira:
- altera apenas fundacao de facts para `product_assignments`
- nao acopla historico, projecoes ou migracao executavel
- preserva comportamento externo v1

## Checkpoints de Preservação de Contrato

### C0 - Baseline pre-change (obrigatorio antes do merge)

1. Capturar payloads de referencia para:
   - `GET /admin/centro-comando/alunos`
   - `GET /admin/radar/alunos/{student_id}`
   - `GET /admin/matriz-renovacao?filter=all`
2. Registrar snapshot de campos e tipos observados.

### C1 - Post-story gate (obrigatorio para aceitar 1.1)

1. Validar que campos de identidade/contexto montados a partir de assignment continuam compativeis com Appendix B:
   - `items[].id`, `context.mentorId`, `studentId`, `programName`, `plan`.
2. Confirmar zero drift em paths, nomes de campo e tipos nas tres familias de endpoint.
3. Confirmar manutencao do envelope padrao de erro v1.

## Checkpoints de Migração (Preparação, sem executar Wave 5)

### M1 - Source fidelity (Appendix C.1)

- Validar que o design do repositorio aceita seed direto de `enrollments.json` para os campos de `product_assignments` sem mapeamento ambiguo.

### M2 - Seed-order readiness (Appendix C.2)

- Garantir que a implementacao de 1.1 nao bloqueia a ordem obrigatoria futura:
  1) assignments
  2) current facts
  3) score state
  4) history `seed_backfill`
  5) projection rebuild + run log.

### M3 - Compatibility reconstruction readiness (Appendix C.3)

- Confirmar que `product_assignments` expõe chaves suficientes para reconstruir `name`, `initials`, `programName`, `plan`, `mentorName`, `protocolId` e `protocolName` no boundary de servico.

## Riscos e Mitigações

1. Risco: regressao silenciosa de payload em campos de identity/context.
   Mitigação: checkpoints C0/C1 com comparacao de snapshot e testes de contrato API.

2. Risco: servico continuar lendo estado derivado legado por caminho paralelo.
   Mitigação: testes de servico exigindo leitura de `product_assignments` como source-of-truth.

3. Risco: mapeamento de seed inconsistente para `status`, `start_at`, `end_at`, `days_left`.
   Mitigação: testes de repositorio cobrindo regras de Appendix C.1 e casos de fallback.

4. Risco: escopo inflar para projecoes/historico antes da hora.
   Mitigação: enforcement de slice boundary e explicit out-of-scope.

## Testes Mínimos Obrigatórios

### Repositório (backend/tests/integration ou camada equivalente)

1. Persistencia create/update de `product_assignments` com todos os campos baseline obrigatorios.
2. Regra de cardinalidade para multiplos assignments ativos do mesmo aluno (desambiguacao por `updated_at` na selecao de relevancia).
3. Compatibilidade de leitura para chaves necessarias de reconstrução de campos v1.

### Serviço (backend/tests/unit)

1. Servico resolve estado de assignment via repositorio de fatos, sem consultar projecao.
2. Orquestracao preserva semantica de negocio para create/update sem quebrar contratos externos.

### API/Contrato (backend/tests/api)

1. Guard tests para estabilidade de shape e tipos em:
   - Command Center list basico
   - Radar payload basico
   - Decision Matrix list basico.
2. Guard test para envelope de erro v1 padronizado.

## Arquivos Prováveis de Mudança (Guia para Dev Story)

- `backend/app/storage/*` (novo/ajuste de repositorio de facts de assignment)
- `backend/app/services/*` (orquestracao para usar repositorio autoritativo)
- `backend/app/api/routes/*` (apenas wiring fino se necessario; sem regra de negocio)
- `backend/tests/integration/*`, `backend/tests/unit/*`, `backend/tests/api/*`

## Definition of Done

1. AC1-AC5 aprovados.
2. Checkpoints C0 e C1 registrados.
3. Checkpoints M1-M3 marcados como prontos para Wave 5.
4. Suite minima de testes obrigatorios verde nas camadas afetadas.
5. Nenhum drift de contrato v1 detectado.

## Dev Agent Record

### Execution Evidence

Contract-preservation checkpoints:

- C0 Baseline pre-change: captured by contract guard suites for Command Center, Radar, and Decision Matrix endpoints before/after wiring changes.
   - Evidence: `backend/tests/api/test_command_center_api.py`
   - Evidence: `backend/tests/api/test_radar_api.py`
   - Evidence: `backend/tests/api/test_matrix_api.py`
- C1 Post-story gate: validated zero drift on field shapes and standardized error envelope.
   - Evidence: `backend/tests/api/test_command_center_api.py`
   - Evidence: `backend/tests/api/test_radar_api.py`
   - Evidence: `backend/tests/api/test_matrix_api.py`
   - Evidence: `backend/tests/api/test_error_payload_api.py`

Migration-readiness checkpoints:

- M1 Source fidelity: `product_assignments` seeds from `enrollments.json` source when authoritative store is empty.
   - Evidence: `backend/tests/integration/test_product_assignment_repository.py`
- M2 Seed-order readiness: Story 1.1 introduces assignment fact persistence only and does not block later Appendix C seed order.
   - Evidence: `backend/app/storage/product_assignment_repository.py`
- M3 Compatibility reconstruction readiness: assignment row preserves identity aliases required by v1 assembly (`organization_id`, `mentor_id`, `student_id`, and assignment linkage fields).
   - Evidence: `backend/app/storage/product_assignment_repository.py`
   - Evidence: `backend/app/services/indicator_carga_service.py`

Minimum test suite executed for Story 1.1:

- `tests/integration/test_product_assignment_repository.py`
- `tests/unit/test_command_center_service.py`
- `tests/unit/test_admin_student_service.py`
- `tests/unit/test_admin_student_link_service.py`
- `tests/unit/test_student_vinculo_service.py`
- `tests/api/test_command_center_api.py`
- `tests/api/test_radar_api.py`
- `tests/api/test_matrix_api.py`
- `tests/api/test_error_payload_api.py`

Result: 39 passed, 0 failed.

### Completion Notes

- Persistencia autoritativa de `product_assignments` ativa no boundary de repositorio.
- Fluxos de escrita (create/reassign/unlink/link) sincronizam fatos autoritativos de assignment.
- Leitura analitica em Command Center/Radar/Matriz prioriza `product_assignments` quando disponivel, com fallback legado controlado.
- Contrato v1 congelado e envelope padrao de erro preservados com guard tests.

### File List

- `_bmad-output/implementation-artifacts/1-1-add-authoritative-assignment-fact-persistence.md`
- `backend/app/storage/product_assignment_repository.py`
- `backend/app/services/indicator_carga_service.py`
- `backend/app/services/admin_student_service.py`
- `backend/app/services/admin_student_link_service.py`
- `backend/app/services/student_vinculo_service.py`
- `backend/app/api/routes/admin_students.py`
- `backend/app/api/routes/mentor.py`
- `backend/app/api/routes/student_workspace.py`
- `backend/tests/integration/test_product_assignment_repository.py`
- `backend/tests/unit/test_command_center_service.py`
- `backend/tests/unit/test_admin_student_service.py`
- `backend/tests/unit/test_admin_student_link_service.py`
- `backend/tests/unit/test_student_vinculo_service.py`
