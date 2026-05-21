---
description: Kick off an Agent Team from the active PRD while respecting AiForInterviewer governance and avoiding parallel planning systems.
allowed-tools: Read Grep Glob Bash
---

# Governance-safe Agent Team Kickoff

Use this skill to start project-level Agent Teams from the active PRD.

## Required pre-read

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD, usually `docs/01-product/PRD.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`, if present

## Recommended team

Ask Codex to create a team with:

1. `product-agent`
2. `api-contract-agent`
3. `backend-architect`
4. `frontend-architect`
5. `qa-agent`
6. `security-reviewer`
7. `devops-agent`
8. `integration-reviewer`

## Global constraints

- Current phase is design and decomposition unless the user explicitly approves implementation.
- Do not implement business code.
- Do not modify migration, deployment config, secrets, credentials, private keys, or production data.
- Do not create new parallel roadmap, plan, task, or phase systems.
- API contract is the center of backend/frontend coordination.
- Every proposed task must map to active PRD acceptance criteria or an explicit engineering prerequisite.
- Security reviewer can issue no-go.
- Integration reviewer must resolve contradictions.

## Required output

Return a consolidated proposal in conversation:

- PRD interpretation
- open questions
- proposed API contract direction
- backend architecture direction
- frontend flow direction
- QA/test strategy direction
- security risks
- devops/release gate direction
- proposed updates to existing governance docs:
  - `docs/03-delivery/DELIVERY_PLAN.md`
  - `docs/03-delivery/BACKLOG.md`
  - `docs/01-product/REQUIREMENT_TRACEABILITY.md`
  - `docs/04-decisions/ADR-*.md` only if needed

Do not write these docs unless the user explicitly approves.
