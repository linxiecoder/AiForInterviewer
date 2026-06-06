---
title: 04_AGENT_DEFINITION_STANDARD
type: note
permalink: ai-for-interviewer/docs/project-sources/04-agent-definition-standard
---

# 04 Agent Definition Standard

## 目的

建立项目级 Agent Definition Standard，支持未来很多 Agent，而不是只支持 Polish Question / Feedback。

适用 Agent 包括但不限于：

- polish_question_agent
- polish_feedback_agent
- resume_analysis_agent
- job_match_agent
- progress_agent
- report_agent
- review_agent
- asset_candidate_agent
- weakness_agent
- training_plan_agent
- pressure_interview_agent

## Agent Definition 必填字段

每个 Agent 必须定义：

- agent_id
- agent_name
- domain
- version
- maturity_level
- lifecycle_status
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

## Agent Identity

必须包含：

```yaml
agent_id:
agent_name:
domain:
version:
maturity_level:
lifecycle_status:
owner:
```

maturity_level 可选值：

- L0 单 prompt endpoint
- L1 structured LLM workflow
- L2 guarded workflow
- L3 tool-using agent
- L4 goal-directed autonomous agent
- L5 multi-agent system

当前默认判断：

- Question Agent：L1.5-L2，不是成熟 autonomous Agent。
- Feedback Agent：L1.5-L2，不是成熟 autonomous Agent。

短期目标：

- L2 planned guarded workflow。

长期目标：

- 在 Agent Platform C 下支持 L3+，但必须受控。

## Mission / Goals

必须包含：

```yaml
mission:
user_goal:
autonomous_goal:
non_goals:
success_definition:
```

规则：

- mission 描述 Agent 的业务使命。
- user_goal 描述用户希望得到的结果。
- autonomous_goal 描述 Agent 在受控范围内可自主优化的目标。
- non_goals 必须明确禁止行为。
- success_definition 必须可验证。

## Input Contract

必须包含：

```yaml
input_schema_id:
required_refs:
optional_refs:
required_context:
canonical_evidence_dependency:
missing_context_policy:
owner_scope:
privacy_policy:
```

规则：

- 输入只能通过受控 context / ref / DTO 提供。
- 不得直接传 full resume / full JD / raw prompt / provider payload。
- 动态输入必须被视为 untrusted data。
- CanonicalEvidencePack 是 Question / Feedback / Progress / Scoring / Training loop 的最高优先级事实契约。

## Output Contract

必须包含：

```yaml
output_schema_id:
candidate_outputs:
formal_outputs_disallowed:
confidence_fields:
reason_codes:
validation_fields:
trace_refs:
```

规则：

- Agent 只能输出 candidate / suggestion。
- candidate 不等于正式业务事实。
- output 必须 schema-valid。
- low_confidence / missing_context / blocking_reason 必须结构化。
- 不得把 fallback 伪装成 generated success。

## Candidate / Formal Write Boundary

必须包含：

```yaml
candidate_type:
formal_write_boundary:
handoff_required:
domain_policy_required:
application_service_required:
user_confirmation_required_when:
```

规则：

- Agent 不得直接写正式业务对象。
- 正式写入必须经过 Application Service + Domain Policy。
- 资产更新必须 user_confirmation_required=true。
- 资产冲突时不得推进下一题。
- Progress update candidate 不等于 progress formal state。
- Score candidate 不等于正式评分记录。

原则：

AI propose, Domain dispose.

## Skills

每个 Skill 必须定义：

```yaml
skill_id:
skill_name:
owner_agent_ids:
input_schema_id:
output_schema_id:
implementation_type:
deterministic_policy_refs:
llm_refs:
tool_refs:
timeout_policy:
retry_policy:
failure_semantics:
trace_events:
eval_refs:
```

implementation_type 可选：

- deterministic
- llm
- tool_workflow
- hybrid

规则：

- Skill 是可复用能力单元。
- Skill 不得直接持久化正式业务对象。
- Skill 不得访问 DB，除非通过受控 Tool / Application Service。
- Skill 输出必须是 candidate / decision / classification / validation result。

## Tools

每个 Tool 必须定义：

```yaml
tool_id:
tool_name:
input_schema_id:
output_schema_id:
permission_scope:
owner_scope:
side_effect_policy:
timeout_seconds:
retry_policy:
allowed_callers:
forbidden_data:
trace_events:
```

side_effect_policy 可选：

- read_only
- candidate_write
- formal_write_handoff_only
- forbidden

规则：

- Tool 不得直接暴露 repository。
- Tool 不得越过 owner scope。
- Tool 不得返回 raw prompt / provider payload / secrets。
- Tool formal write 必须走 handoff，不得直接由 Agent 调用。

## Memory / State

必须定义：

```yaml
ephemeral_state:
durable_state:
state_schema_id:
state_transitions:
resume_policy:
replay_policy:
checkpoint_policy:
```

规则：

- checkpoint 不等于业务事实。
- replay 默认 read_only。
- resume 必须验证 base_version / owner_scope / interrupt_ref。
- memory 不得存 raw provider payload。

## Planning Strategy

必须定义：

```yaml
planning_strategy:
max_steps:
max_retries:
timeout_seconds:
allowed_loops:
stop_conditions:
repair_strategy:
fallback_strategy:
```

短期：

- controlled planner
- no open-ended autonomous loop

长期：

- controlled tool loop
- max_steps / trace / HITL / eval required

## Guardrails

必须定义：

```yaml
schema_validation:
factuality_policy:
source_support_policy:
provider_redaction:
forbidden_keys:
blocking_gates:
HITL_triggers:
score_range_policy:
owner_boundary_policy:
asset_confirmation_policy:
```

规则负责：

- 权限
- 状态机
- 事实确认
- 正式写入
- blocking gate
- schema validation
- provider redaction
- next action 硬约束
- asset confirmation
- score range
- owner boundary

AI 负责：

- 语义理解
- 候选总结
- 候选题目
- 候选反馈
- 候选参考回答
- 候选解释
- 候选计划

## HITL Triggers

必须定义何时要求用户确认：

- asset conflict
- asset update candidate
- low confidence factual update
- unsupported project claim
- score dispute
- ambiguous ownership
- progress completion uncertainty
- provider validation failed but partial result exists

## Failure Semantics

必须定义：

```yaml
failure_statuses:
retryable:
fallback_allowed:
fallback_visible:
failed_not_generated:
provider_unavailable_behavior:
validation_failed_behavior:
```

规则：

- provider unavailable 不得伪装成功。
- validation failed 不得伪装成功。
- deterministic fallback 不等于 generated success。
- fallback 必须 user visible 或 trace visible。

## Trace Contract

必须定义：

```yaml
trace_schema_id:
required_trace_refs:
timeline_events:
input_refs:
output_refs:
policy_refs:
provider_refs:
validation_refs:
handoff_refs:
```

Trace 禁止保存：

- raw prompt
- system prompt
- developer prompt
- raw provider payload
- raw completion
- full resume
- full JD
- secrets

## Eval Contract

必须定义：

```yaml
eval_suite_ids:
dataset_refs:
grader_refs:
regression_cases:
minimum_pass_criteria:
ci_gate:
failure_triage_policy:
```

规则：

- 单测不能替代 Eval。
- 每个 Capability ID 必须绑定 regression case。
- Eval failure 必须阻断 done 状态。

## Handoff Contract

必须定义：

```yaml
handoff_schema_id:
candidate_ref:
candidate_type:
validation_refs:
quality_gate:
side_effect_key:
idempotency_key:
formal_write_preconditions:
rollback_policy:
```

规则：

- Handoff 是 Agent candidate 到正式业务写入的唯一通道。
- Handoff 必须 fail-closed。
- 缺 trace / validation / side_effect_key 不得写入。

## Versioning Policy

必须定义：

```yaml
definition_version:
schema_version:
prompt_version_refs:
policy_version_refs:
migration_notes:
deprecation_policy:
compatibility_policy:
```

## L5 Supervisor / Orchestrator Addendum

P11-W0 locks the Phase 11 target as L5 Controlled Multi-Agent Orchestration.
P11-W1 adds a contract-only `interview_orchestrator_agent` definition and cross-agent contract dataclasses. This is contract foundation only: it does not execute Supervisor / Orchestrator at runtime and does not implement product multi-agent workflow.

Any `interview_orchestrator_agent`, future `supervisor_orchestrator_agent`, or equivalent Phase 11 definition must include:

```yaml
agent_id:
agent_name:
maturity_level: L5 multi-agent system
lifecycle_status:
goal_decomposition_contract:
cross_agent_plan_contract:
cross_agent_handoff_contract:
cross_agent_state_contract:
checkpoint_replay_contract:
trace_timeline_contract:
bounded_tool_loop:
HITL_triggers:
candidate_outputs:
formal_write_boundary:
eval_contract:
```

P11-W1 contract-only current shape:

- `agent_id`: `interview_orchestrator_agent`
- `lifecycle_status`: `contract_only`
- `maturity_level`: L5 target contract foundation, not L5 release.
- `candidate_outputs`: `cross_agent_plan_candidate`, `cross_agent_handoff_candidate`, `cross_agent_state_candidate`, `cross_agent_trace_candidate`.
- `formal_write_boundary`: direct formal writes disallowed; Application Service -> Domain Policy -> Handoff remains the formal write boundary.
- `skills`: Orchestrator goal decomposition, route planning, handoff validation, state/checkpoint planning, trace/timeline planning and HITL trigger planning.
- `tools`: contract-only read/validate tools; no repository, DB, SQLAlchemy session, unit of work or formal writer exposure.
- `catalog`: registered only through `build_default_agent_platform_l5_contract_registries()`, not through the Phase 4 C1 builder.

Required rules:

- Supervisor / Orchestrator may coordinate agents, but still cannot write formal business facts directly.
- Every business-agent output remains candidate / suggestion / validation / plan / trace.
- Cross-agent handoff must carry refs, schema IDs, validation refs, trace refs, side-effect keys and idempotency keys.
- State / checkpoint / replay is orchestration control state, not business fact persistence.
- Tool loops must define `max_steps`, `max_retries`, `timeout_seconds`, allowed tools, allowed callers, side-effect policy and stop conditions.
- HITL must cover asset conflict, formal write, low confidence, ambiguous ownership and validation failed with partial result.
- At least one Phase 11 product workflow must prove three or more business agents before any L5 workflow claim.

Forbidden:

- unbounded autonomous swarm
- Agent direct DB / repository write
- Tool direct repository exposure
- provider full prompt / full resume / full JD fallback
- prompt/provider/API/DB/frontend/domain behavior changes unless separately scoped
- marking L5-002 to L5-006 implemented, validated or done without fresh code/test/eval evidence

P11-W1 non-claims:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

## Phase 12 Eval / Release Contract Addendum

Phase 12 target is L5 Eval, Hardening, and Release Gate. It requires:

```yaml
multi_agent_eval_suite_ids:
capability_ids:
case_ids:
input_refs:
expected_candidate_refs:
expected_handoff_refs:
expected_validation_refs:
expected_HITL_refs:
expected_failure_mode:
expected_non_claims:
grader_refs:
minimum_pass_criteria:
cross_agent_replay_fixture_refs:
checkpoint_refs:
read_only: true
formal_write_blocked: true
zero_provider_calls: true
zero_db_writes: true
zero_formal_writes: true
trace_comparison:
failure_mode_regression_cases:
trace_report_refs:
forbidden_data_scan_result:
ci_workflow_name:
ci_command_list:
remote_ci_artifact_refs:
blocking_failure_behavior:
negative_control_behavior:
rollback_policy:
failure_triage_policy:
human_release_decision:
accepted_risks:
deferred_gaps:
release_version_or_tag_ref:
evidence_links:
```

Rules:

- Unit tests cannot certify L5 release.
- Replay/fake eval cannot certify real-provider quality.
- Remote CI must cite visible run and artifact evidence.
- Release is blocked while candidate/formal boundary, provider fail-closed or Phase 8 runtime gaps remain unresolved or explicitly accepted by the release controller.
- P12-W0 records the evidence contract only; it does not implement eval, replay, CI, trace, release decision or real-provider quality behavior.
- Optional real-provider advisory mode must be explicit, non-default and separately scoped before it can be used as quality evidence.
- AgentDefinition `eval_contract` refs may point to Phase 12 evidence only after a later implementation window creates the suite / replay / CI artifacts.

## 禁止事项

- Agent 不得直接写正式业务对象。
- Prompt 不得承载业务不变量。
- Tool 不得暴露未授权数据。
- Tool 不得直接暴露 repository。
- Fallback 不得伪装成功。
- Provider request 不得携带 full prompt asset fallback。
- Fake 只能用于 tests / evals / replay。
- 未达到 L4 时不得称 autonomous agent。
