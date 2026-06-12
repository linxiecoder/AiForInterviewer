---
title: Requirements Index
type: requirements-index
status: active
round: Round 3.5-E
updated: 2026-06-12
---

# Requirements Index

本文件只作为临时 requirements 索引，不复制完整 As-Is / To-Be / Gap 分析。G-001 的可执行契约以目标文件中的 `To-Be Behavior Contract` 与 `As-Is / To-Be Gap Matrix` 为准。

## Current Requirements

| Requirement ID | Goal | Status | Contract source | Notes |
|---|---|---|---|---|
| R-001 | G-001 session continuity | Deep gap analysis ready for GPT Project audit | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#to-be-behavior-contract` and `#as-is--to-be-gap-matrix` | Defines optional backward-compatible continuity metadata for session detail/reopen/refresh. |
| R-002 | G-001 context hygiene | Deep gap analysis ready for GPT Project audit | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#to-be-behavior-contract` and `#as-is--to-be-gap-matrix` | Defines bounded safe metadata and no raw prompt/provider payload exposure. |
| R-003 | G-002 capture / analysis separation | Out of scope for this round | `.codex-temp/interview-coach-refactor/05-goals/G-002-capture-analysis-separation.md` | Not modified in Round 3.5-E. |

## G-001 Requirement Boundary

| Boundary | Result | Source |
|---|---|---|
| DB migration | No | G-001 `Implementation Boundary` |
| New endpoint | No | G-001 `Implementation Boundary` |
| Provider-facing output schema change | No | G-001 `Implementation Boundary` |
| Raw prompt/provider payload exposure | No | G-001 `Implementation Boundary` |
| G-002 implementation | No | G-001 `Implementation Boundary` |
| Defer / Reject / Research-only items | No implementation | `.codex-temp/interview-coach-refactor/02-scope/scope-lock.md` |

## Index Rule

If a requirement detail in this index conflicts with G-001, G-001 wins for R-001/R-002. This file must remain an index and must not become a second source of truth.
