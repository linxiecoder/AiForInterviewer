---
description: Review architecture, API contract, frontend flow, backend plan, QA strategy, and risks under AiForInterviewer governance rules.
allowed-tools: Read Grep Glob Bash
---

# Governance-safe Design Review

Use this skill after PRD decomposition and before implementation.

## Read first

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- relevant ADRs under `docs/04-decisions/`, if present

## Checks

1. PRD coverage
2. missing requirements
3. API/frontend mismatch
4. backend feasibility
5. data and migration risk
6. security risk
7. test coverage
8. overengineering
9. implementation sequencing
10. go / no-go recommendation

## Governance-safe output

Return a proposed review report in the conversation. If persistent documentation is needed:

- decision: propose an ADR under `docs/04-decisions/ADR-*.md`
- stage changes: propose edits to `docs/03-delivery/DELIVERY_PLAN.md`
- task changes: propose edits to `docs/03-delivery/BACKLOG.md`
- requirement mapping: propose edits to `docs/01-product/REQUIREMENT_TRACEABILITY.md`

Do not create `docs/plans/*` or any parallel plan/task entry.
Do not edit files without explicit user approval.
