---
title: Design Index
type: design-index
status: active
round: Round 3.5-E
updated: 2026-06-12
---

# Design Index

本文件只作为设计入口索引。G-001 的完整 As-Is / To-Be / Gap / Data Flow / Implementation Boundary 设计留在 G-001 目标文件。

## Goal Designs

| Goal | Status | Primary design source | Key sections |
|---|---|---|---|
| G-001 session continuity / context hygiene | Ready for GPT Project audit, not approved for implementation | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md` | `As-Is Code Behavior`, `To-Be Behavior Contract`, `As-Is / To-Be Gap Matrix`, `Data Flow and Call Chain`, `Technical Design`, `Implementation Boundary`, `Test Matrix` |
| G-002 capture / analysis separation | Not part of Round 3.5-E | `.codex-temp/interview-coach-refactor/05-goals/G-002-capture-analysis-separation.md` | Not modified in this round |

## Shared Design Pointer

| Shared design file | Current use |
|---|---|
| `.codex-temp/interview-coach-refactor/04-design/shared-technical-design.md` | Records that G-001 introduces no new cross-Goal shared design in Round 3.5-E. |
| `.codex-temp/interview-coach-refactor/04-design/decisions.md` | Records G-001 boundary decisions: no DB migration, no new endpoint, no provider-facing output schema change, no raw prompt/provider payload exposure, optional backward-compatible metadata only. |
