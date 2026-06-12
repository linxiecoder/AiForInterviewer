---
title: Functional Spec Index
type: functional-spec-index
status: active
round: Round 3.5-E
updated: 2026-06-12
---

# Functional Spec Index

本文件只记录 functional spec 的入口。G-001 的完整行为定义、字段契约、状态枚举和测试矩阵必须回到 G-001 目标文件阅读。

## Functional Specs

| Spec ID | Requirement | Goal | Status | Source |
|---|---|---|---|---|
| FS-001 | R-001 | G-001 | Deep gap analysis ready for GPT Project audit | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#functional-spec` |
| FS-002 | R-001 | G-001 | Deep gap analysis ready for GPT Project audit | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#to-be-behavior-contract` |
| FS-003 | R-002 | G-001 | Deep gap analysis ready for GPT Project audit | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#to-be-behavior-contract` |
| FS-004 | R-002 | G-001 | Deep gap analysis ready for GPT Project audit | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#data-flow-and-call-chain` |

## Test Matrix Pointer

| Requirement | Test matrix source | Notes |
|---|---|---|
| R-001 | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#test-matrix` | Includes session detail, legacy fallback, progress refresh fallback, frontend optional fields. |
| R-002 | `.codex-temp/interview-coach-refactor/05-goals/G-001-session-continuity-context-hygiene.md#test-matrix` | Includes bounded context, safe metadata, raw prompt/provider payload non-exposure. |

## Scope Note

Round 3.5-E does not update G-002 and does not enter implementation. Any future functional spec work must preserve the G-001 boundary documented in the goal file.
