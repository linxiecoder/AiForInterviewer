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
2. 跨模块理解、调用链分析、DDD / Agent / `PolishUseCases` 重构前，必须先经过 `aifi-context-index-gate`，用 Understand-Anything / CodeGraph 获取压缩上下文，再最小化 `Read` / `Grep`。
3. Before editing, produce:
   - backlog item or delivery phase reference
   - scope
   - files likely affected
   - tests to run
   - risk level
4. Keep diff small.
5. Do not modify protected areas without explicit approval:
   - database migrations
   - auth-critical code
   - billing
   - deployment config
   - secrets
   - infra
6. Do not create parallel planning docs.
7. After editing, run relevant tests.
8. Final response must include:
   - files changed
   - tests run
   - failing tests, if any
   - risks
   - next step
   - governance residue check
