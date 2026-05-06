---
description: Governance-safe PRD decomposition for AiForInterviewer; uses existing delivery/backlog/traceability entries instead of creating parallel roadmap or task graph docs.
allowed-tools: Read Grep Glob Bash
---

# Governance-safe PRD Decomposition

Use this skill when starting from the active PRD.

## Governing rules

Before doing anything, read:

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- active PRD, usually `docs/01-product/PRD.md`

Do not create:

- `docs/plans/roadmap.md`
- `docs/plans/task-graph.md`
- `roadmap-v2.md`
- `latest-plan.md`
- any new parallel roadmap, task, phase, or plan entry

## Allowed target entries

Use existing governance locations:

- Stage/milestone proposals: `docs/03-delivery/DELIVERY_PLAN.md`
- Task proposals: `docs/03-delivery/BACKLOG.md`
- Requirement mapping: `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- Long-lived decisions only when needed: `docs/04-decisions/ADR-*.md`

## Output

Produce a governance-safe proposal in the conversation first:

1. PRD summary
2. open questions
3. proposed DELIVERY_PLAN changes
4. proposed BACKLOG changes
5. proposed REQUIREMENT_TRACEABILITY changes
6. risks
7. validation method
8. files that would be touched if user approves

Do not edit active delivery/backlog/traceability files unless the user explicitly approves.
