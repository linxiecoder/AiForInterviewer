---
title: P4_W0_SCOPE_LOCK
type: scope-lock
status: evidence-only
owner: P4-W0-AGENT-CONTRACTS-SKILLS-TOOLS-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/p4-w0-scope-lock
---

# P4-W0 Scope Lock

本文件记录 `P4-W0-AGENT-CONTRACTS-SKILLS-TOOLS-SCOPE-LOCK` 的 docs-only scope lock。它只锁定 Phase 4 Agent Contracts / Skills / Tools 后续规划边界，不授权任何实现。

## 1. Window

| Item | Value |
| --- | --- |
| Window ID | `P4-W0-AGENT-CONTRACTS-SKILLS-TOOLS-SCOPE-LOCK` |
| Phase | Phase 4 - Agent Contracts / Skills / Tools |
| Goal | Create Phase 4 scope lock, window catalog, decision options, and acceptance gates. |
| Operation | docs-only planning / governance |
| Behavior change allowed | No |
| Prompt/schema/provider change allowed | No |
| DB schema change allowed | No |
| Runtime change allowed | No |
| Implementation allowed | No |
| Commit expected | `phase4(P4-W0): lock agent contracts scope` after validation pass |

## 2. Current Evidence

| Evidence | Current interpretation |
| --- | --- |
| User confirmation | This window authorizes planning/governance docs only and explicitly prohibits Phase 4 implementation. |
| Current branch | `main` at `84d71ba phase3(pre-p4-w5): reconcile recovered phase2 evidence` during recon. |
| Worktree entry state | `git status --short --untracked-files=all` was clean before writing. |
| Project source pack | `docs/project-sources/**` is active Project source pack for target architecture and governance intent. |
| Goal evidence | `docs/goals/**` remains execution evidence only and does not become active requirement, design, delivery plan, ADR, or code fact. |
| Phase 2 closeout evidence | `recovered_and_reconciled`; historical status remains `close_with_deferred_source_pack_gap` / `partial_deferred`, not clean done. |
| SRC-001 | `repo_backfilled_from_project_sources`. |
| CTX-002 | `repaired_with_ctx002_bridge`; `SourceSupportSummary` remains evidence contract input for later planning. |
| Phase 3 | `closed_with_recovered_phase2_evidence`. |
| Phase 4 | `entry_scope_lock_created` / `implementation_not_started`. |
| Current code skeleton | `apps/api/app/application/agents/contracts` and `registry` skeletons exist; `ai_runtime` graph-local tool schemas exist and are not project `ToolRegistry` substitutes. |

## 3. Allowed Files

| Path | Allowed operation |
| --- | --- |
| `docs/goals/2026-06-03/P4_W0_SCOPE_LOCK.md` | Create / update this scope lock. |
| `docs/goals/2026-06-03/P4_W0_DECISION_OPTIONS.md` | Create decision options only. |
| `docs/goals/2026-06-03/P4_W0_WINDOW_CATALOG.md` | Create proposed next-window catalog only. |
| `docs/goals/2026-06-03/P4_W0_ACCEPTANCE_GATES.md` | Create docs-only acceptance gates only. |
| `docs/goals/2026-06-03/P4_W0_FINAL_REPORT.md` | Create final report. |
| `docs/goals/2026-06-03/PHASE_4_ENTRY_SCOPE_LOCK.md` | Update only if needed to preserve P4 planning boundary. |
| `docs/goals/2026-06-03/PHASE_3_FINAL_CLOSEOUT_ASSESSMENT.md` | Correct stale `Audit / Diff Agent` wording only if present. |
| `docs/goals/README.md` | Register P4-W0 evidence files. |

## 4. Conditionally Allowed Files

The following Project source files are allowed only if this window needs to record P4-W0 governance status without creating a new architecture decision:

- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/12_ACCEPTANCE_GATES.md`
- `docs/project-sources/13_DECISION_LOG.md`
- `docs/project-sources/14_RISK_REGISTER.md`

This P4-W0 lock does not currently require Project source writes. Any future source-pack backfill must be separately authorized or explicitly scoped by a later closeout window.

## 5. Forbidden Files

No writes are allowed to:

- `apps/**`
- `tests/**`
- database migrations
- prompt files
- provider / LLM transport files
- API route files
- LangGraph runtime files
- Agent runtime files
- frontend files
- any Phase 4 implementation file
- any new AgentDefinition / SkillDefinition / ToolDefinition code file
- any registry / executor / handoff / trace implementation file

## 6. Forbidden Operations

- Do not implement Phase 4.
- Do not create code files.
- Do not modify `apps/**` or `tests/**`.
- Do not create real AgentDefinition / SkillDefinition / ToolDefinition JSON, YAML, or code artifacts.
- Do not make Question / Feedback runtime call `AgentExecutor`.
- Do not create or change registry implementation.
- Do not change prompts, providers, DB, API, LangGraph, Agent runtime, or frontend.
- Do not mark Phase 4 implemented, done, or validated.
- Do not choose an architecture option on behalf of the controller/user.

## 7. Rollback

If validation fails, rollback is docs-only:

1. Revert the P4-W0 docs added in this window.
2. Revert the `docs/goals/README.md` P4-W0 index update.
3. Revert the stale wording correction in `PHASE_3_FINAL_CLOSEOUT_ASSESSMENT.md` only if the correction itself is wrong.
4. Re-run forbidden diff audit before any commit.

No application rollback, DB rollback, provider rollback, runtime rollback, or API rollback is applicable because this window must not change those areas.

## 8. Validation Commands

```bash
git diff --check
rg -n "implementation_started|Phase 4 done|Agent runtime migrated|provider rewrite|DB migration|API behavior change|LangGraph runtime completed|formal write authorized|raw prompt|raw completion" docs/goals/2026-06-03/P4_W0_SCOPE_LOCK.md docs/goals/2026-06-03/P4_W0_DECISION_OPTIONS.md docs/goals/2026-06-03/P4_W0_WINDOW_CATALOG.md docs/goals/2026-06-03/P4_W0_ACCEPTANCE_GATES.md docs/goals/2026-06-03/P4_W0_FINAL_REPORT.md docs/goals/2026-06-03/PHASE_4_ENTRY_SCOPE_LOCK.md || true
test -f docs/goals/2026-06-03/P4_W0_SCOPE_LOCK.md
test -f docs/goals/2026-06-03/P4_W0_DECISION_OPTIONS.md
test -f docs/goals/2026-06-03/P4_W0_WINDOW_CATALOG.md
test -f docs/goals/2026-06-03/P4_W0_ACCEPTANCE_GATES.md
test -f docs/goals/2026-06-03/P4_W0_FINAL_REPORT.md
git diff --name-only
git diff --name-only | rg -v '^(docs/goals/2026-06-03/|docs/goals/README.md$|docs/project-sources/(09_REFACTOR_TRACEABILITY_MATRIX|12_ACCEPTANCE_GATES|13_DECISION_LOG|14_RISK_REGISTER)\.md$)' && echo 'FORBIDDEN_DIFF' || true
git status --short --untracked-files=all
```

## 9. Stop Conditions

Stop immediately if any next action requires:

- modifying `apps/**` or `tests/**`;
- implementing AgentDefinition / Skill / Tool files;
- wiring `AgentExecutor`;
- provider, prompt, DB, API, runtime, or frontend changes;
- choosing Option A / B / C without controller/user confirmation;
- treating graph-local tool schema as project `ToolRegistry`;
- current code materially contradicting Project source pack.

## 10. Done Criteria

P4-W0 is done only when:

- scope lock is written;
- decision options are written and stop before implementation;
- proposed next-window catalog is written;
- acceptance gates are written;
- final report is written;
- `docs/goals/README.md` indexes the P4-W0 artifacts;
- stale `Audit / Diff Agent = pending_validation` wording is corrected if present;
- forbidden diff audit shows only allowed docs changed;
- validation commands are run and recorded;
- Phase 4 remains `implementation_not_started`;
- controller/user is explicitly asked to choose Option A / B / C before P4-W1.
