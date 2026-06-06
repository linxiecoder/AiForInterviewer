---
title: 03_AGENT_PLATFORM_ARCHITECTURE
type: note
permalink: ai-for-interviewer/docs/project-sources/03-agent-platform-architecture
---

# 03 Agent Platform Architecture

## 目标

建立可支持未来多个 Agent 的项目级 Agent Platform，而不是只为 Question / Feedback 写局部 workflow。

目标 Agent 包括但不限于：

- ResumeAnalysis
- JobMatch
- Question
- Feedback
- Progress
- Report
- Review
- AssetCandidate
- Weakness
- TrainingPlan
- PressureInterview

## 核心决策

### DEC-AGT-001 Agent Platform Target

Status: confirmed

Agent Platform 的目标态是 C：

- AgentExecutor
- AgentDefinitionRegistry
- SkillRegistry
- ToolRegistry
- AgentExecutionPlan
- AgentExecutionTrace
- HandoffContract
- EvalContract
- Question / Feedback 最终接入该平台

不得把仅有 contracts + registry skeleton 的状态当作最终目标。
B 只能作为 C 的过渡切片，不得作为验收终态。

### DEC-AGT-002 Phase 1 Agent Platform Slice

Status: confirmed

Phase 1 只执行 C0：

- 建立项目级 Agent contracts / registry / executor port skeleton。
- 建立 DDD rails。
- 收敛 PolishUseCases facade。
- 不把 Question / Feedback runtime 全量改接 AgentExecutor。
- 不改 prompt / provider / DB / API 行为。

Phase 1 的目标不是完成 Agent Platform C，而是确保后续 Phase 自然走向 C。

## 平台层

### 1. Agent Definition Layer

负责定义：

- agent_id
- mission
- user_goal
- autonomous_goal
- non_goals
- input_contract
- output_contract
- candidate_outputs
- formal_write_boundary
- skills
- tools
- memory_state
- planning_strategy
- guardrails
- HITL triggers
- failure_semantics
- trace_contract
- eval_contract
- handoff_contract
- versioning_policy

### 2. Skill Layer

Skill 是可复用能力单元，可由以下方式实现：

- deterministic policy
- LLM call
- tool workflow
- hybrid

Skill 必须定义：

- skill_id
- skill_name
- owner_agent_ids
- input_schema_id
- output_schema_id
- implementation_type
- timeout_policy
- retry_policy
- failure_semantics
- trace_events
- eval_refs

Skill 不得直接写正式业务事实。

### 3. Tool Layer

Tool 是受控能力接口，不是 repository 的直接暴露。

Tool 必须定义：

- tool_id
- tool_name
- input_schema_id
- output_schema_id
- permission_scope
- owner_scope
- side_effect_policy
- timeout_seconds
- retry_policy
- allowed_callers
- forbidden_data
- trace_events

Tool 规则：

- Tool 不得暴露未授权数据。
- Tool 不得绕过 Application Service。
- Tool 不得直接写正式业务对象，除非该 Tool 本身就是受控 formal write handoff，并经过 Domain Policy。
- Tool 不得返回 raw prompt、system prompt、developer prompt、provider payload、full resume、full JD、secret、token、cookie。

### 4. Planning Layer

短期采用 controlled planner。

长期支持受控 tool loop，但必须满足：

- max_steps
- max_retries
- timeout
- stop_conditions
- repair_strategy
- loop_policy
- trace_required
- HITL triggers

Question / Feedback 的短期目标是 L2 planned guarded workflow，不直接追求 L4 autonomous agent。

### 5. Execution Layer

目标组件：

- AgentExecutor
- AgentRunContext
- AgentCommandEnvelope
- AgentRunResult
- AgentRunStatus
- AgentTimelineEvent
- AgentTaskStatusRef

AgentExecutor 只负责执行 Agent Plan，不能直接写正式业务状态。

正式写入必须通过：

Application Service -> Domain Policy -> Handoff -> Repository / Transaction

### 6. Trace Layer

Trace 必须记录：

- agent_id
- agent_version
- run_id
- ai_task_id
- input_refs
- plan_refs
- skill_refs
- tool_refs
- policy_refs
- provider_refs
- candidate_refs
- validation_refs
- handoff_refs
- output_refs
- low_confidence_flags
- failure_reason
- fallback_reason

Trace 中禁止保存：

- raw prompt
- system prompt
- developer prompt
- raw provider payload
- raw completion
- full resume
- full JD
- secrets

### 7. Eval Layer

每个 Agent 必须绑定：

- eval_suite_ids
- dataset_refs
- grader_refs
- regression_cases
- CI gate
- minimum pass criteria
- failure triage policy

Eval 不等于单测。
单测证明工程路径；Eval 证明 AI 行为质量。

### 8. Handoff Layer

Agent 只能输出 candidate。

允许 candidate 类型：

- question_candidate
- feedback_candidate
- asset_update_candidate
- progress_update_candidate
- weakness_candidate
- training_plan_candidate
- report_candidate
- review_candidate

Formal write 必须经过 Application Service + Domain Policy。

Handoff 必须包含：

- candidate_ref
- candidate_type
- payload_schema_id
- trace_refs
- validation_refs
- quality_gate
- side_effect_key
- idempotency_key
- user_confirmation_required when applicable

## Candidate / Formal Boundary

Agent 只能输出 candidate：

- question_candidate
- feedback_candidate
- asset_update_candidate
- progress_update_candidate
- weakness_candidate
- training_plan_candidate

Formal write 必须经过 Application Service + Domain Policy。

原则：

AI propose, Domain dispose.

## Provider Boundary

Provider-facing request 必须 compact and fail-closed。

必须禁止：

- full prompt asset fallback
- raw prompt
- system prompt
- developer prompt
- provider payload
- full resume
- full JD
- secrets
- token
- cookie

CompactProviderRequestBuilder 是目标组件。
Phase 1 只加 boundary tests / gates，不重构 provider 行为。
Provider 行为重构留到 Phase 7。

## Phase Alignment

| Phase | Agent Platform Scope |
|---|---|
| Phase 0 | Project source pack / Agent Definition / Traceability Matrix |
| Phase 0.1 | Source Backfill，锁定 C target 和 Phase 1 C0 |
| Phase 1 | C0：Agent contracts / registry / executor port skeleton + DDD rails |
| Phase 2 | Canonical Evidence / Interview Context |
| Phase 3 | Domain Policies |
| Phase 4 | Agent Contracts / Skills / Tools 实体化 |
| Phase 5 | Question Agent planned workflow |
| Phase 6 | Feedback Agent planned workflow |
| Phase 7 | Provider request fail-closed |
| Phase 8 | LangGraph / 多 Agent runtime |
| Phase 9 | Eval / CI / Regression gate |
| Phase 10 | 阶段收口和 Project sources 回填 |
| Phase 11 | L5 Controlled Multi-Agent Orchestration |
| Phase 12 | L5 Eval, Hardening, and Release Gate |

## Phase 11 / Phase 12 Scope Lock Addendum

P11-W0 reconciliation result:

- Phase 0-10 is L5 Foundation `closed_with_deferred_gaps`, not L5 release.
- Phase 8 runtime gaps remain deferred.
- `deferred_remote_ci_gap` remains open unless a visible passing GitHub Actions run and artifact are cited.
- Committed Phase 9 eval report metadata short SHA `f86adea` remains residual risk until a separate report refresh window is authorized.
- Supervisor / Orchestrator implementation has not started.
- Phase 12 release gate has not started.

P11-W1 Contract-first Orchestrator result:

- `interview_orchestrator_agent` exists as a contract-only AgentDefinition in the L5 contract catalog.
- Cross-agent plan, handoff route, state/checkpoint/replay and trace/timeline contracts exist as immutable dataclasses under `app.application.agents.contracts`.
- Orchestrator SkillDefinition and ToolDefinition records are contract-only and registered only by the L5 contract catalog builder.
- Existing Phase 4 C1 Question / Feedback catalog behavior remains backward-compatible.
- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

### Phase 11: L5 Controlled Multi-Agent Orchestration

Required target capabilities:

- registered Supervisor / Orchestrator Agent
- typed cross-agent goal decomposition
- cross-agent plan contract
- typed cross-agent handoff contract
- cross-agent state / checkpoint / replay contract
- cross-agent trace timeline
- bounded tool loop with `max_steps` / `max_retries` / `timeout` / `stop_conditions`
- HITL triggers for asset conflict, formal write, low confidence, ambiguous ownership, and validation failed but partial result exists
- at least one end-to-end product workflow with three or more business agents
- candidate-only output boundary
- formal write remains Application Service -> Domain Policy -> Handoff

Forbidden in Phase 11 unless separately scoped:

- L5 release claim
- unbounded autonomous swarm
- Agent direct DB / repository write
- Tool direct repository exposure
- infrastructure business policy
- provider full prompt / full resume / full JD fallback
- prompt/provider/API/DB/frontend/domain behavior changes
- committed eval report rewrite
- remote CI claim without visible run/artifact

### Phase 12: L5 Eval, Hardening, and Release Gate

Required target capabilities:

- multi-agent regression suite
- cross-agent replay fixtures
- failure-mode regression cases
- L5 CI gate
- observability / trace report
- rollback policy
- failure triage policy
- remote CI artifact evidence
- human release decision

Forbidden in Phase 12:

- claiming L5 with unit tests only
- claiming L5 with fake-only or replay-only eval
- skipping replay / trace evidence
- release with unresolved candidate/formal boundary gaps
- release with unresolved provider fail-open gaps
- release without human/controller decision

## 禁止偏移

以下情况视为偏移：

1. 把 B，即 contracts + registry skeleton，当作 Agent Platform 终态。
2. 为 Question / Feedback 写局部 Skill / Tool 机制，但不纳入项目级 registry。
3. Agent 直接写正式业务事实。
4. Prompt 承载业务不变量。
5. Tool 直接暴露 repository。
6. Provider request 从 prompt asset fallback。
7. Fake runtime 污染生产路径。
8. Eval 只停留在 seed 样本，不进入 regression gate。
9. 将 Phase 11 / Phase 12 target wording 当作当前实现事实。
10. 将 replay / fake eval evidence 当作 real-provider quality certification。
11. 将 P11-W1 contract-only Orchestrator 当作 product workflow、runtime execution、Phase 8 runtime gap closure 或 L5 release。
