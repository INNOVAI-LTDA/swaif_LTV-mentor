.PHONY: \
	bmad-smoke bmad-status \
	bmad-route bmad-story bmad-dev bmad-review bmad-fix bmad-run bmad-resume bmad-sessionize \
	bmad-help bmad-brainstorming bmad-market-research bmad-domain-research bmad-technical-research \
	bmad-create-product-brief bmad-create-prd bmad-create-ux-design bmad-create-architecture \
	bmad-create-epics-and-stories bmad-check-implementation-readiness bmad-sprint-planning bmad-sprint-status \
	bmad-create-story bmad-validate-story bmad-dev-story bmad-code-review bmad-retrospective \
	bmad-document-project bmad-generate-project-context bmad-quick-spec bmad-quick-dev \
	bmad-quick-dev-new-preview bmad-correct-course \
	bmad-flow-agile bmad-flow-batching bmad-flow-greenfield bmad-flow-brownfield \
	bmad-flow-build-from-pieces bmad-flow-quick bmad-flow-correct-course

RUN_MODE = $(if $(EXECUTE),--execute,--dry-run)
RUN_PROMPT_PROFILE = $(if $(PROFILE),--prompt-profile $(PROFILE),)
RUN_EVENT_ROOT = $(if $(EVENT_ROOT),--event-log-root $(EVENT_ROOT),)
RUN_APPROVAL_MODE = $(if $(APPROVAL),--approval-mode $(APPROVAL),)
RUN_SESSION_ROOT = $(if $(SESSION_ROOT),--session-root $(SESSION_ROOT),)
RUN_RESUME_SESSION = $(if $(RESUME),--resume-session $(RESUME),)
RUN_RESUME_EVENT = $(if $(RESUME_EVENT),--resume-event $(RESUME_EVENT),)
RUN_COMMAND = python ops/run_bmad_command.py --command $(1) $(if $(CONTEXT),--context-file $(CONTEXT),) $(if $(OUTPUT),--output-last-message $(OUTPUT),) $(if $(INSTRUCTION),--instruction "$(INSTRUCTION)",) $(RUN_PROMPT_PROFILE) $(RUN_EVENT_ROOT) $(RUN_MODE)
RUN_WORKFLOW = python ops/run_bmad_workflow.py --workflow $(1) $(RUN_RESUME_SESSION) $(RUN_RESUME_EVENT) $(if $(CONTEXT),--context-file $(CONTEXT),) $(if $(INSTRUCTION),--instruction "$(INSTRUCTION)",) $(RUN_PROMPT_PROFILE) $(RUN_EVENT_ROOT) $(RUN_SESSION_ROOT) $(RUN_APPROVAL_MODE) $(RUN_MODE)

bmad-smoke:
	bash ops/preflight_check.sh
	python ops/run_bmad_phase.py --workflow plan_solution --batch A --phase route --dry-run

bmad-status:
	python ops/get_bmad_status.py

bmad-route:
	python ops/run_bmad_phase.py --workflow $(WORKFLOW) --batch $(BATCH) --phase route

bmad-story:
	python ops/run_bmad_phase.py --workflow $(WORKFLOW) --batch $(BATCH) --phase story

bmad-dev:
	python ops/run_bmad_phase.py --workflow $(WORKFLOW) --batch $(BATCH) --phase dev

bmad-review:
	python ops/run_bmad_phase.py --workflow $(WORKFLOW) --batch $(BATCH) --phase review

bmad-fix:
	python ops/run_bmad_phase.py --workflow $(WORKFLOW) --batch $(BATCH) --phase fix

bmad-run:
	python ops/run_bmad_workflow.py $(if $(WORKFLOW),--workflow $(WORKFLOW),) $(RUN_RESUME_SESSION) $(RUN_RESUME_EVENT) $(if $(CONTEXT),--context-file $(CONTEXT),) $(if $(INSTRUCTION),--instruction "$(INSTRUCTION)",) $(RUN_PROMPT_PROFILE) $(RUN_EVENT_ROOT) $(RUN_SESSION_ROOT) $(RUN_APPROVAL_MODE) $(RUN_MODE)

bmad-resume:
	python ops/run_bmad_workflow.py --resume-session $(RESUME) $(if $(INSTRUCTION),--instruction "$(INSTRUCTION)",) $(RUN_PROMPT_PROFILE) $(RUN_EVENT_ROOT) $(RUN_SESSION_ROOT) $(RUN_APPROVAL_MODE) $(RUN_MODE)

bmad-sessionize:
	python ops/run_bmad_workflow.py --workflow $(WORKFLOW) --resume-event $(RESUME_EVENT) $(if $(CONTEXT),--context-file $(CONTEXT),) $(if $(INSTRUCTION),--instruction "$(INSTRUCTION)",) $(RUN_PROMPT_PROFILE) $(RUN_EVENT_ROOT) $(RUN_SESSION_ROOT) $(RUN_APPROVAL_MODE) --dry-run

bmad-help:
	$(call RUN_COMMAND,bmad-help)

bmad-brainstorming:
	$(call RUN_COMMAND,bmad-brainstorming)

bmad-market-research:
	$(call RUN_COMMAND,bmad-market-research)

bmad-domain-research:
	$(call RUN_COMMAND,bmad-domain-research)

bmad-technical-research:
	$(call RUN_COMMAND,bmad-technical-research)

bmad-create-product-brief:
	$(call RUN_COMMAND,bmad-create-product-brief)

bmad-create-prd:
	$(call RUN_COMMAND,bmad-create-prd)

bmad-create-ux-design:
	$(call RUN_COMMAND,bmad-create-ux-design)

bmad-create-architecture:
	$(call RUN_COMMAND,bmad-create-architecture)

bmad-create-epics-and-stories:
	$(call RUN_COMMAND,bmad-create-epics-and-stories)

bmad-check-implementation-readiness:
	$(call RUN_COMMAND,bmad-check-implementation-readiness)

bmad-sprint-planning:
	$(call RUN_COMMAND,bmad-sprint-planning)

bmad-sprint-status:
	$(call RUN_COMMAND,bmad-sprint-status)

bmad-create-story:
	$(call RUN_COMMAND,bmad-create-story)

bmad-validate-story:
	python ops/run_bmad_command.py --command bmad-create-story $(if $(CONTEXT),--context-file $(CONTEXT),) $(if $(OUTPUT),--output-last-message $(OUTPUT),) --instruction "Run bmad-create-story in Validate Mode and return a story readiness assessment." $(RUN_PROMPT_PROFILE) $(RUN_EVENT_ROOT) $(RUN_MODE)

bmad-dev-story:
	$(call RUN_COMMAND,bmad-dev-story)

bmad-code-review:
	$(call RUN_COMMAND,bmad-code-review)

bmad-retrospective:
	$(call RUN_COMMAND,bmad-retrospective)

bmad-document-project:
	$(call RUN_COMMAND,bmad-document-project)

bmad-generate-project-context:
	$(call RUN_COMMAND,bmad-generate-project-context)

bmad-quick-spec:
	$(call RUN_COMMAND,bmad-quick-spec)

bmad-quick-dev:
	$(call RUN_COMMAND,bmad-quick-dev)

bmad-quick-dev-new-preview:
	$(call RUN_COMMAND,bmad-quick-dev-new-preview)

bmad-correct-course:
	$(call RUN_COMMAND,bmad-correct-course)

bmad-flow-agile:
	$(call RUN_WORKFLOW,agile)

bmad-flow-batching:
	$(call RUN_WORKFLOW,batching)

bmad-flow-greenfield:
	$(call RUN_WORKFLOW,greenfield)

bmad-flow-brownfield:
	$(call RUN_WORKFLOW,brownfield)

bmad-flow-build-from-pieces:
	$(call RUN_WORKFLOW,build-from-pieces)

bmad-flow-quick:
	$(call RUN_WORKFLOW,quick)

bmad-flow-correct-course:
	$(call RUN_WORKFLOW,correct-course)
