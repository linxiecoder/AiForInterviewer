---
title: P4_W0_DECISION_OPTIONS
type: decision-options
status: evidence-only
owner: P4-W0-AGENT-CONTRACTS-SKILLS-TOOLS-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/p4-w0-decision-options
---

# P4-W0 Decision Options

本文件只给出 Phase 4 Agent Contracts / Skills / Tools 的后续执行选项。任何选项都不能在 P4-W0 中实施；进入 P4-W1 前必须由 Controller / user 明确选择。

## 1. Decision Boundary

| Boundary | Value |
| --- | --- |
| Current window | P4-W0 docs-only planning / governance |
| Implementation in P4-W0 | No |
| Option selection in P4-W0 | No |
| Runtime wiring | No |
| Prompt/provider/DB/API changes | No |
| Formal writes | No |
| Required next action | Controller/user chooses Option A / B / C before P4-W1. |

## 2. Source Evidence

- `docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md` locks Agent Platform target C and candidate/formal boundary.
- `docs/project-sources/04_AGENT_DEFINITION_STANDARD.md` defines required AgentDefinition, SkillDefinition, ToolDefinition, Trace, Eval, and Handoff fields.
- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md` tracks `QAG-005/006/007`, `FAG-006/007/008`, `AGT-002/003/004/006/007`.
- `docs/project-sources/12_ACCEPTANCE_GATES.md` requires candidate-only, tool no repository exposure, provider fail-closed, traceability, and done gates.
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md` assigns Phase 4 to Agent Contracts / Skills / Tools and defers Question / Feedback planned workflows to Phase 5 / 6.
- `docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md` places Phase 4 in C1: definitions, skills, tools, trace and handoff contract alignment.
- `docs/goals/2026-06-03/PHASE_4_ENTRY_SCOPE_LOCK.md` authorizes only future scope-lock / planning and keeps implementation not started.
- Current code has C0-style contracts/registry skeletons under `apps/api/app/application/agents/**`; P4-W0 does not modify or extend them.

## 3. Option A - AgentDefinition First

Question + Feedback AgentDefinition first, no Skill / Tool registry entries yet.

| Field | Value |
| --- | --- |
| Candidate capability IDs | `QAG-005`, `FAG-006`, `AGT-002`, `AGT-006`, `AGT-007` |
| Scope shape | Produce docs-only AgentDefinition planning for Question and Feedback, including candidate outputs, formal write boundary, trace, eval, and handoff references. |
| Pros | Safest, definition-first, low diff. |
| Cons | Skill/Tool traceability still deferred. |
| Risk controls | Keep Skill / Tool sections as references only; do not create registry entries or runtime wiring. |
| Next window fit | Best fit for `P4-W1 AgentDefinition Registry Planning / Definition Docs`. |

## 4. Option B - AgentDefinition + SkillDefinition Skeleton Docs

AgentDefinition + SkillDefinition skeleton docs first, ToolDefinition deferred.

| Field | Value |
| --- | --- |
| Candidate capability IDs | `QAG-005`, `QAG-006`, `FAG-006`, `FAG-007`, `AGT-002`, `AGT-003`, `AGT-006`, `AGT-007` |
| Scope shape | Produce docs-only AgentDefinition and SkillDefinition planning for Question and Feedback; defer ToolDefinition planning until tool boundary is explicit. |
| Pros | Maps capability to reusable skills early. |
| Cons | May over-design skills before tool boundary is clear. |
| Risk controls | Mark SkillDefinition content as contract plan only; no skill execution, DB access, provider calls, or formal write path. |
| Next window fit | Combines `P4-W1` and `P4-W2` planning scope; should not be chosen unless Controller accepts larger docs surface. |

## 5. Option C - AgentDefinition + SkillDefinition + ToolDefinition Contract Plan

AgentDefinition + SkillDefinition + ToolDefinition contract plan together, docs-only.

| Field | Value |
| --- | --- |
| Candidate capability IDs | `QAG-005`, `QAG-006`, `QAG-007`, `FAG-006`, `FAG-007`, `FAG-008`, `AGT-002`, `AGT-003`, `AGT-004`, `AGT-006`, `AGT-007` |
| Scope shape | Produce one integrated docs-only contract plan covering definitions, reusable skills, tools, trace, handoff, and eval references. |
| Pros | Best Phase 4 completeness planning. |
| Cons | Highest design surface; must avoid implementation. |
| Risk controls | ToolDefinition plan must explicitly reject repository exposure, provider payload exposure, prompt leakage, and runtime calls. |
| Next window fit | Useful if Controller wants Phase 4 C1 planned as one contract package before source backfill. |

## 6. Recommendation

Recommended option: Option A.

Reason: Phase 4 entry is currently `implementation_not_started`, and the safest next decision is to lock Question / Feedback AgentDefinition boundaries before expanding to SkillDefinition or ToolDefinition. This keeps the next diff small, preserves candidate-only semantics, and reduces the chance that graph-local tool schemas are mistaken for project `ToolRegistry`.

## 7. Required Controller Decision

Stop here before implementation.

Before P4-W1, Controller / user must choose exactly one:

- Option A: AgentDefinition first.
- Option B: AgentDefinition + SkillDefinition skeleton docs.
- Option C: AgentDefinition + SkillDefinition + ToolDefinition contract plan together.

No P4-W1 implementation, source backfill, registry entry, skill entry, tool entry, runtime wiring, provider work, DB work, API work, or tests may start until that decision is explicit.
