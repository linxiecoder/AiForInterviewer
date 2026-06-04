---
title: P4_W0_ACCEPTANCE_GATES
type: acceptance-gates
status: evidence-only
owner: P4-W0-AGENT-CONTRACTS-SKILLS-TOOLS-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/p4-w0-acceptance-gates
---

# P4-W0 Acceptance Gates

本文件定义 Phase 4 Agent Contracts / Skills / Tools 后续窗口的 candidate acceptance gates。它不实现 gate，不创建测试，不修改代码。

## 1. Candidate-Only Rule

AgentDefinition / SkillDefinition / ToolDefinition planning must preserve candidate-only semantics.

Allowed Agent outputs remain:

- `question_candidate`
- `feedback_candidate`
- `asset_update_candidate`
- `progress_update_candidate`
- `weakness_candidate`
- `training_plan_candidate`
- `report_candidate`
- `review_candidate`

Gate:

- PASS only if every planned output is candidate / suggestion / validation / plan / trace.
- FAIL if any planned output is treated as formal business fact.

## 2. No Formal Write Rule

Formal write path remains:

```text
Application Service -> Domain Policy -> Handoff -> Repository / Transaction
```

Gate:

- PASS only if Agent, Skill, and Tool plans do not directly write formal question, feedback, asset, score, progress, report, or weakness records.
- PASS only if asset update remains user-confirmation-gated.
- FAIL if an Agent, Skill, Tool, registry, executor, or trace contract is described as directly writing formal facts.

## 3. Tool No Repository Exposure Rule

ToolDefinition planning must treat Tool as a controlled capability interface, not a repository handle.

Gate:

- PASS only if ToolDefinition includes `permission_scope`, `owner_scope`, `side_effect_policy`, `allowed_callers`, `forbidden_data`, and trace events.
- PASS only if default `side_effect_policy` remains `read_only` unless explicitly justified as `candidate_write` or `formal_write_handoff_only`.
- FAIL if Tool exposes repository, DB session, transaction object, ORM model, or unscoped owner data.
- FAIL if graph-local `TOOL_SCHEMAS` are treated as project `ToolRegistry`.

## 4. No Provider Payload / Prompt Leakage Rule

Provider-facing and trace-facing planning must not carry raw provider or prompt material.

Forbidden data includes:

- `raw prompt`
- system prompt
- developer prompt
- provider payload
- raw provider payload
- full resume
- full JD
- secrets
- tokens
- cookies

Gate:

- PASS only if planned input/output contracts use refs, summaries, schema IDs, and redacted payloads.
- FAIL if any planned Agent / Skill / Tool contract returns provider payload or full prompt material.

## 5. Trace No Raw Prompt / Raw Completion Rule

Trace contract planning must preserve redaction.

Forbidden trace content includes:

- `raw prompt`
- system prompt
- developer prompt
- raw provider payload
- `raw completion`
- full resume
- full JD
- secrets

Gate:

- PASS only if trace stores refs, event IDs, policy refs, provider refs, candidate refs, validation refs, and failure reason codes.
- FAIL if trace stores raw prompt text, raw completion text, raw provider payload, full resume, full JD, or secrets.

## 6. Eval Contract Required / Eval Gate Deferred

Every planned AgentDefinition and Capability ID must include eval contract references.

Gate:

- PASS only if AgentDefinition planning names `eval_suite_ids`, dataset refs, grader refs, regression cases, minimum pass criteria, and failure triage policy as required contract fields.
- PASS only if P4 windows explicitly mark eval runner / CI gate implementation as deferred.
- FAIL if a capability is marked done with only unit tests or docs and no eval contract requirement.

## 7. No Runtime Wiring

Phase 4 planning may define contracts and registry expectations, but not runtime execution.

Gate:

- PASS only if Question / Feedback runtime continues to be treated as current implementation fact and not modified by P4 planning.
- FAIL if a P4 planning window wires Question / Feedback runtime to `AgentExecutor`, LangGraph runtime, Tool loop, replay, interrupt, or multi-agent handoff implementation.

## 8. No Prompt / Provider / DB / API Changes

P4 planning must not change prompt content, provider request behavior, database schema, API behavior, or frontend behavior.

Gate:

- PASS only if diffs are limited to authorized docs.
- FAIL if any prompt file, provider / LLM transport file, migration, SQLAlchemy schema, API route, frontend, runtime, or test file changes.

## 9. No Phase 5 / 6 Planned Workflow Implementation

Phase 5 is Question Agent Planned Workflow. Phase 6 is Feedback Agent Planned Workflow. P4-W0 and proposed P4 windows do not implement either.

Gate:

- PASS only if Question / Feedback planned workflow implementation remains deferred to separately authorized later windows.
- FAIL if P4 scope includes planner execution, provider invocation, candidate persistence behavior change, handoff execution, eval runner, or runtime migration.

## 10. Done Gate

No Phase 4 capability may be marked done unless a later authorized closeout verifies all required evidence.

For P4-W0, done means only:

- scope lock created;
- decision options produced;
- window catalog produced;
- acceptance gates produced;
- final report produced;
- stale `Audit / Diff Agent` wording corrected if present;
- allowed-file diff only;
- Phase 4 implementation remains not started;
- Controller/user decision requested before P4-W1.
