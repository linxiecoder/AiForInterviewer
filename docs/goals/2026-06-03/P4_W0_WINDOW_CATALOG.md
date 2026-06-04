---
title: P4_W0_WINDOW_CATALOG
type: window-catalog
status: evidence-only
owner: P4-W0-AGENT-CONTRACTS-SKILLS-TOOLS-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/p4-w0-window-catalog
---

# P4-W0 Window Catalog

本文件只定义 proposed next windows。它不是执行授权，不替代 `BACKLOG.md`、`DELIVERY_PLAN.md`、ADR、Project source 或代码事实。

## 1. Catalog Boundary

| Boundary | Value |
| --- | --- |
| Current status | proposed only |
| Implementation authorized | No |
| Behavior change allowed | No |
| Prompt/provider/DB/API/runtime/frontend change allowed | No |
| Source pack backfill | Deferred unless a later window explicitly authorizes it |
| Required gate | Controller/user must choose Option A / B / C before P4-W1 |

## 2. P4-W1 AgentDefinition Registry Planning / Definition Docs

| Field | Value |
| --- | --- |
| Goal | Plan Question and Feedback AgentDefinition boundaries, lifecycle status, candidate outputs, formal write boundary, trace/eval/handoff references, and registry mapping expectations. |
| Capability IDs | `QAG-005`, `FAG-006`, `AGT-002`, `AGT-006`, `AGT-007` |
| Allowed files | Future `docs/goals/2026-06-03/P4_W1_*.md`; optionally Project source files only if Controller explicitly authorizes source backfill. |
| Forbidden files | `apps/**`, `tests/**`, prompt/provider/DB/API/runtime/frontend files, implementation files, real registry artifacts. |
| Behavior change allowed | No |
| Validation commands | `git diff --check`; `git diff --name-only`; forbidden diff allowlist check; existence checks for P4-W1 docs. |
| Done criteria | AgentDefinition planning docs exist, candidate-only and formal write boundaries are explicit, no Skill / Tool entries are implemented, Controller decision is recorded. |
| Stop conditions | Need to create AgentDefinition code/JSON/YAML artifact; need to modify registry implementation; need to route Question / Feedback through AgentExecutor; source evidence conflicts materially with current code. |
| Rollback | Revert P4-W1 docs and README index changes; no application rollback applicable. |

## 3. P4-W2 SkillDefinition Contract Planning

| Field | Value |
| --- | --- |
| Goal | Plan reusable SkillDefinition contracts for Question and Feedback without executing skills or writing registry entries. |
| Capability IDs | `QAG-006`, `FAG-007`, `AGT-003`, `AGT-006`, `AGT-007` |
| Allowed files | Future `docs/goals/2026-06-03/P4_W2_*.md`; optionally Project source files only if Controller explicitly authorizes source backfill. |
| Forbidden files | `apps/**`, `tests/**`, prompt/provider/DB/API/runtime/frontend files, SkillRegistry implementation, skill execution code. |
| Behavior change allowed | No |
| Validation commands | `git diff --check`; forbidden wording scan; forbidden diff allowlist check; README index check. |
| Done criteria | SkillDefinition candidates are mapped to capability IDs, owner agents, input/output schema refs, policy refs, trace events, and eval refs; all entries remain docs-only candidates. |
| Stop conditions | Need to execute a skill; need DB/repository access; need LLM/provider calls; need to persist formal facts; need to define a workflow runner. |
| Rollback | Revert P4-W2 docs and index changes; no runtime rollback applicable. |

## 4. P4-W3 ToolDefinition Contract Planning

| Field | Value |
| --- | --- |
| Goal | Plan ToolDefinition contracts and permission boundaries without exposing repositories or wiring runtime tools. |
| Capability IDs | `QAG-007`, `FAG-008`, `AGT-004`, `AGT-006`, `AGT-007` |
| Allowed files | Future `docs/goals/2026-06-03/P4_W3_*.md`; optionally Project source files only if Controller explicitly authorizes source backfill. |
| Forbidden files | `apps/**`, `tests/**`, provider/prompt/DB/API/runtime/frontend files, ToolRegistry implementation, tool executor code. |
| Behavior change allowed | No |
| Validation commands | `git diff --check`; forbidden data wording scan; forbidden diff allowlist check; README index check. |
| Done criteria | ToolDefinition plan includes permission scope, owner scope, side effect policy, forbidden data, allowed callers, trace events, and no repository exposure rule. |
| Stop conditions | Need to expose repository handles; need formal write tool behavior; need provider payload or prompt content; need runtime tool loop. |
| Rollback | Revert P4-W3 docs and index changes; no repository/runtime rollback applicable. |

## 5. P4-W4 Trace / Handoff / Eval Contract Alignment

| Field | Value |
| --- | --- |
| Goal | Align AgentDefinition, SkillDefinition, and ToolDefinition planning with trace, handoff, and eval contract requirements. |
| Capability IDs | `AGT-006`, `AGT-007`, `EVAL-001`, `QAG-005`, `FAG-006`, `QAG-006`, `FAG-007`, `QAG-007`, `FAG-008` |
| Allowed files | Future `docs/goals/2026-06-03/P4_W4_*.md`; optionally Project source files only if Controller explicitly authorizes source backfill. |
| Forbidden files | `apps/**`, `tests/**`, runtime, provider, prompt, DB, API, frontend, eval runner or CI files. |
| Behavior change allowed | No |
| Validation commands | `git diff --check`; scan for raw prompt / raw completion only in forbidden-rule context; forbidden diff allowlist check; README index check. |
| Done criteria | Trace excludes raw prompt/raw completion/provider payload; handoff remains candidate-to-formal boundary only; eval contract is required but eval gate implementation remains deferred. |
| Stop conditions | Need to store raw prompt/completion; need to implement eval runner or CI gate; need to authorize formal write; need runtime wiring. |
| Rollback | Revert P4-W4 docs and index changes. |

## 6. P4-W5 Phase 4 Closeout / Source Backfill

| Field | Value |
| --- | --- |
| Goal | Audit Phase 4 planning artifacts, close or defer gaps, and propose or perform explicitly authorized source backfill. |
| Capability IDs | `WIN-001`, `SRC-001`, `QAG-005`, `QAG-006`, `QAG-007`, `FAG-006`, `FAG-007`, `FAG-008`, `AGT-002`, `AGT-003`, `AGT-004`, `AGT-006`, `AGT-007` |
| Allowed files | Future `docs/goals/2026-06-03/P4_W5_*.md`; conditionally `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`, `12_ACCEPTANCE_GATES.md`, `13_DECISION_LOG.md`, `14_RISK_REGISTER.md` if explicitly scoped. |
| Forbidden files | `apps/**`, `tests/**`, prompt/provider/DB/API/runtime/frontend files, implementation artifacts, unapproved Project source files. |
| Behavior change allowed | No |
| Validation commands | `git diff --check`; forbidden diff allowlist check; stale status scan; matrix/status scan if Project source backfill is authorized. |
| Done criteria | Phase 4 planning status is honestly recorded, implementation remains not started unless a later authorized implementation window exists, deferred gaps are explicit, source backfill status is clear. |
| Stop conditions | Need to mark Phase 4 done without implementation/eval/source evidence; need to update unapproved Project source files; need to start Phase 5/6 workflows. |
| Rollback | Revert closeout/source-backfill docs; if Project source files were scoped and edited, revert only the P4-W5 entries. |

## 7. Sequence Rule

Default proposed sequence:

1. P4-W1 after Controller chooses Option A / B / C.
2. P4-W2 only if SkillDefinition planning remains in scope after P4-W1.
3. P4-W3 only after ToolDefinition boundary is explicit.
4. P4-W4 only after definition/skill/tool planning artifacts exist.
5. P4-W5 only for closeout/source backfill, not implementation.

No proposed window authorizes Phase 5 Question planned workflow, Phase 6 Feedback planned workflow, provider rewrite, DB migration, API behavior change, LangGraph runtime work, Agent runtime migration, frontend changes, or tests.
