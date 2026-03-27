.PHONY: bmad-smoke bmad-route bmad-story bmad-dev bmad-review bmad-fix

bmad-smoke:
	bash ops/preflight_check.sh
	python ops/run_bmad_phase.py --workflow plan_solution --batch A --phase route --dry-run

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
