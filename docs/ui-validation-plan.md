# UI Validation Plan

## 1. Objective

This plan defines how the next visual stages should be built and reviewed for the Acelerador Medico MVP validation cycle.

The goal is to deliver screens that can be:
- opened
- navigated
- reviewed with the client
- approved or adjusted

## 2. Stage Sequence

### Stage 2: Login

Expected outputs:
- navigable Login screen
- `docs/ui-login-report.md`

Validation focus:
- first impression
- logo application
- contrast of form fields
- clarity of role entry simulation

### Stage 3: Mentor

Expected outputs:
- navigable Mentor screen
- `docs/ui-mentor-report.md`

Validation focus:
- executive hierarchy
- clarity of the three main views
- readability of KPI and student sections
- branded consistency with Login

### Stage 4: Aluno

Expected outputs:
- navigable Aluno screen
- `docs/ui-student-report.md`

Validation focus:
- personal progress storytelling
- prominence of radar
- visual lightness compared to Mentor
- easy understanding of the next step

### Stage 5: Admin

Expected outputs:
- navigable Admin screen
- `docs/ui-admin-report.md`

Validation focus:
- operational clarity
- tab organization
- table readability
- action placement for future CRUD flows

### Stage 6: Visual Audit

Expected outputs:
- `docs/ui-visual-audit.md`
- `docs/ui-adjustments-priority.md`

Validation focus:
- cross-screen consistency
- branding fidelity
- hierarchy quality
- contrast and accessibility
- polish level

## 3. Review Criteria

Every screen should be reviewed against the same five criteria:

1. Branding fidelity
2. Layout clarity
3. Contrast and readability
4. Information hierarchy
5. Premium perception

## 4. Screen-Level Checklist

Use this checklist in each stage report:

- Is the client logo visible in an appropriate place?
- Are black, graphite, white, and gold balanced correctly?
- Is the main CTA obvious?
- Is the first viewport understandable without explanation?
- Are sections visually grouped with enough spacing?
- Is there any overuse of gold?
- Is any area visually crowded or under-contrasted?
- Does this screen feel coherent with the other roles?

## 5. Review Method

Recommended review flow for each stage:

1. Open the screen in desktop width.
2. Validate the first viewport in isolation.
3. Navigate the main interaction points.
4. Check whether the role purpose is immediately clear.
5. Capture issues in the stage report.

Secondary pass:

1. Open the screen in a narrower viewport.
2. Confirm the shell still reads clearly.
3. Verify that key actions remain visible and usable.

## 6. Severity Model For Findings

Use these severity levels in all stage reports:

- `High`: blocks client validation or breaks visual comprehension
- `Medium`: harms clarity, polish, or consistency
- `Low`: minor polish issue that does not block evaluation

## 7. Reporting Standard

Each stage report should contain:
- what was built
- which mocked interactions are available
- what matched the branding spec
- findings or tradeoffs still visible
- recommendation for the next stage

## 8. Non-Goals To Recheck In Every Stage

Before closing any stage, confirm that the implementation did not:
- add new backend flows
- add real authentication
- add real RBAC
- trigger large structural refactors
- introduce unrelated UI redesign

## 9. Exit Condition For The Validation Cycle

The visual validation cycle can be considered ready for client review when:
- Login, Mentor, Aluno, and Admin are all navigable
- the branding feels stable across screens
- each role has a distinct information reading
- major contrast and hierarchy issues have been audited
- the remaining adjustments are prioritized in writing
