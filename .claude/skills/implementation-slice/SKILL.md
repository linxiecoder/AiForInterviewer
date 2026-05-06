---
description: Implement one bounded AiForInterviewer slice from active backlog/delivery entries with small diff, tests, and risk summary.
allowed-tools: Read Grep Glob Bash Edit Write MultiEdit
---

# Governance-safe Implementation Slice

Use this skill only after the relevant active backlog/delivery entries are approved.

## Read first

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- relevant ADRs

## Rules

1. Implement only one bounded slice.
2. Before editing, produce:
   - backlog item or delivery phase reference
   - scope
   - files likely affected
   - tests to run
   - risk level
3. Keep diff small.
4. Do not modify protected areas without explicit approval:
   - database migrations
   - auth-critical code
   - billing
   - deployment config
   - secrets
   - infra
5. Do not create parallel planning docs.
6. After editing, run relevant tests.
7. Final response must include:
   - files changed
   - tests run
   - failing tests, if any
   - risks
   - next step
   - governance residue check
