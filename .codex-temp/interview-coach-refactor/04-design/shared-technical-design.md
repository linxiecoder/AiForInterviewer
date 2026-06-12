---
title: Shared Technical Design
type: shared-design
status: active
round: Round 3.5-E
updated: 2026-06-12
---

# Shared Technical Design

G-001 当前无新增跨 Goal shared design，详细设计留在 Goal 文件。

## Current Shared Boundary

| Item | Status | Notes |
|---|---|---|
| Cross-Goal shared abstraction | None added in Round 3.5-E | G-001 uses existing Polish API/use case/repository/schema/frontend paths and documents changes in its own goal file. |
| Reusable metadata principle | Existing local principle only | Any future safe metadata helper must remain optional, backward-compatible, bounded, and must not copy interview-coach command/state structures. |
| G-002 dependency | None introduced | Round 3.5-E does not modify or implement G-002. |

## Pointer

For G-001 details, read `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md`.
