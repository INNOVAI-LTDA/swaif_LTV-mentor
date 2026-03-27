# Operating Model

## One sentence version
Use **GitHub as control plane**, **Codex cloud as executor**, and **BMAD as protocol**.

## Roles by device
### PC
Use once for:
- bootstrap repo
- install BMAD
- create or refine `project-context.md`
- add scripts/templates
- run one local sanity check

### Phone
Use daily for:
- create/update BMAD issues
- trigger Codex work in the cloud
- review summaries / PRs
- approve, merge, or request follow-up loop

## Execution modes
### 1. Manual mode
Best when:
- you want direct control
- the project is still unstable
- you are learning the flow

Main loops:
- Normal Story Loop
- Fix Loop
- Correct-Course Loop
- Quick-Dev Loop
- UI Cleanup Loop
- Deploy Boundary Loop

### 2. Team mode
Best when:
- you want cleaner handoffs
- one person is still supervising, but the work is split into lanes

Typical team:
- Router
- Mapper / Analyst
- Story Manager
- Developer
- Reviewer
- Doc / Ops updater

### 3. Automated mode
Best when:
- your loops are already stable
- you want strict order and less copy-paste

Automate:
- workflow choice hints
- model mapping
- prompt template loading
- run logging
- sequence control
- state update

Do not automate:
- risky decisions
- architecture sign-off
- UX sign-off
- release approval

## Default loop selection
- Small low-risk local change -> Quick-Dev Loop
- Standard bounded change -> Normal Story Loop
- Review failed but scope still right -> Fix Loop
- Review failed because scope/boundary is wrong -> Correct-Course Loop
- Screen cleanup needs approval first -> UI Cleanup Loop
- Deploy or hardening batched release -> Deploy Boundary Loop
