---
title: Interview Coach Refactor 合并前压缩摘要
type: migration-summary
status: round-6-merge-blocked
updated: 2026-06-12
source_directory: .codex-temp/interview-coach-refactor
permalink: ai-for-interviewer/interview-coach-refactor
---

# Interview Coach Refactor 合并前压缩摘要

本文是 `.codex-temp/interview-coach-refactor/` 的合并前压缩迁移结果，用于保留本分支仍需追踪的结论、边界、验证证据和 merge blocker。本文不替代 `docs/00-governance/DOCS_INDEX.md`、`BACKLOG.md`、`DELIVERY_PLAN.md`、ADR 或代码事实；在未被 `DOCS_INDEX.md` 正式登记前，不得把它当作新的长期执行入口。

## 1. Source Lock

| Source | Locked evidence |
|---|---|
| AIForInterviewer branch | `feature/interview-coach-refactor` |
| Initial AIForInterviewer source lock commit | `cc94db2d79365b021e33096a4988c4864fd743d8` |
| interview-coach-skill repository | `https://github.com/noamseg/interview-coach-skill.git` |
| analyzed interview-coach-skill commit | `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e` |
| source placement rule | interview-coach source stays outside this repository |

Evidence rules retained from the temporary workspace:

- Every adopted/adapted pattern must have both interview-coach evidence and an AIForInterviewer landing point.
- Capabilities without a current AIForInterviewer landing point remain `Defer`, `Reject`, or `Research-only`.
- Do not copy interview-coach command names, menu structure, prompt prose, workflow wording, output wording, flat `coaching_state.md`, or source scoring vocabulary.

## 2. Scope Summary

| Capability | Decision | AIForInterviewer landing point | Current status |
|---|---|---|---|
| `R3-CAP-002` persistent coaching state continuity | Adapt | existing Polish session detail, progress tree state, turns, current refs | Implemented through G-001 R-001 as response-local optional continuity metadata |
| `R3-CAP-010` long-context hygiene | Adapt | question/feedback metadata, prompt asset summaries, provider boundary, API response sanitizer | Implemented through G-001 R-002 as bounded safe metadata |
| `R3-CAP-003` capture / analysis separation | Adapt candidate | answer save path, feedback task path, repository answer/feedback separation | Drafted as G-002 only; not implemented or modified in Round 6 |
| `R3-CAP-005` evidence / confidence | Adapt candidate | evidence refs, trace refs, low confidence, validation | Not implemented in this branch beyond existing G-001 safe metadata boundary |
| `R3-CAP-006` scoring + root-cause alignment | Adapt candidate | `ScoringPolicy`, feedback payload loss points, score results | Not implemented |
| `R3-CAP-009` state-aware next action | Adapt candidate | next recommended actions, progress tree, workbench view models | Not implemented |
| `R3-CAP-004` transcript ingestion | Defer | no current transcript source model/API/UI/test landing point | Not implemented |
| `R3-CAP-007` storybank memory | Defer | no current storybank model/API/UI landing point | Not implemented |
| `R3-CAP-008` outcome/progress calibration | Defer | no outcome log or drift lifecycle | Not implemented |
| `R3-CAP-001` source-backed command routing | Research-only / Reject source shape | lightweight entry / service contract inspiration only | No command system copied |

## 3. G-001 Result

G-001 covers only:

- `R-001` session continuity: existing Polish session reopen / refresh responses may include backward-compatible optional `continuity_status`, `continuity_summary`, and `restored_refs`.
- `R-002` context hygiene: question/feedback metadata may expose bounded `context_hygiene_status`, `safe_context_metadata`, `fallback_reason`, and `validation_signals` without raw prompt/provider payload/full source exposure.

G-001 boundaries:

| Boundary | Result |
|---|---|
| DB migration | No |
| New endpoint | No |
| Provider-facing output schema change | No |
| Raw prompt exposure | No |
| Provider payload exposure | No |
| G-002 implementation | No |
| Storybank / transcript / command routing | No |

## 4. G-001 Validation

Latest validation evidence:

| Area | Evidence | Status |
|---|---|---|
| Backend T-001~T-006 | Round 5-C pytest selectors with `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` | exit `0` |
| Frontend T-006 | Round 6 `npm run web:test` | exit `0`; `tsc -p tsconfig.json --noEmit` passed |
| Frontend T-007 | Round 6 `npm run web:build` | exit `0`; `tsc -p tsconfig.json --noEmit && vite build` passed |
| Build warning | Vite chunk-size warning | known non-blocking warning |
| tmp leak guard | repo-root `tmp/` preexists | known environment risk; not cleaned or modified |

## 5. G-002 Status

G-002 remains a draft for capture / analysis separation. Round 6 did not modify or implement G-002.

Current G-002 draft scope:

- `R-003`: answer capture must succeed independently before feedback analysis.
- `R-004`: feedback analysis must attach to a saved answer and preserve failure/degraded boundaries.
- No external feedback taxonomy, outcome calibration, progress calibration, storybank, transcript ingestion, command routing, or source prompt prose is implemented.

## 6. Merge Review Result

Round 6 frontend validation passed, but merge to `main` is blocked by branch scope mismatch.

| Check | Result |
|---|---|
| G-001 complete for current scope | Pass |
| `change-ledger.md` / `CONTROL.md` updated | Pass |
| tmp leak guard risk recorded | Pass |
| G-002 untouched in Round 6 | Pass |
| `AGENTS.md` unaffected by Round 6 worktree edits | Pass |
| `AGENTS.md` unaffected by feature branch merge history | Fail / blocking |
| build/config unaffected by Round 6 worktree edits | Pass |
| production code/tests unaffected by Round 6 edits | Pass |

Blocking merge findings:

| Finding | Evidence | Required decision |
|---|---|---|
| Feature branch history includes `AGENTS.md` relative to `main` | `git diff main...HEAD -- AGENTS.md` shows a committed SPECKIT block | Approve it explicitly or split/rebase it out before merge |
| Feature branch history includes `.agents/.specify` relative to `main` | `git diff --name-status main...HEAD` lists `.agents/**`, `.claude/**`, `.specify/**` additions | Decide whether Spec Kit tooling belongs in this merge |
| Worktree contains uncommitted prior G-001 production code/test diffs | `git status --short` lists backend/frontend source and tests | Commit as G-001 after owner approval or split from this merge |
| Temporary `.codex-temp` should not remain on `main` | temporary workspace README requires final compression before merge | Use this compressed summary and remove/split temp workspace only in an authorized cleanup |

## 7. Next Merge-Safe Step

Before merging `feature/interview-coach-refactor` into `main`, resolve the scope mismatch:

1. Decide whether `AGENTS.md` SPECKIT block and `.agents/.specify` additions are approved for the same merge.
2. Decide whether prior G-001 production code/test diffs should be committed on this branch or split into a narrower branch.
3. If the target is a G-001-only merge, create a clean branch from `main`, cherry-pick or reapply only G-001 implementation + tests + this compressed summary, then rerun backend and frontend validation.
4. Do not start G-002 without explicit approval.
