---
title: P8_W0_AGENT_CONTRACT_RECON
type: execution-evidence
status: recon_only_no_patch
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w0-agent-contract-recon
---

# P8-W0 Agent Contract / Handoff / Trace Recon

Status: warn

本报告是 P8-W0 只读 recon 证据，不声明 Phase 8 done，不声明 C4 runtime 已完成，不声明 L5 release。

## Files read

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/SEMANTICS_GLOSSARY.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/README.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/codex_goal_objective.txt`
- `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_MASTER_GOAL.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_WINDOW_CATALOG.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_ACCEPTANCE_AND_NO_FALSE_DONE_GATES.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/agents/B_CONTRACT_HANDOFF_TRACE_RECON.md`
- `apps/api/app/application/agents/__init__.py`
- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/agents/handoff/__init__.py`
- `apps/api/app/application/agents/registry/__init__.py`
- `apps/api/app/application/agents/definitions/__init__.py`
- `apps/api/app/application/agents/definitions/catalog.py`
- `apps/api/app/application/agents/definitions/common.py`
- `apps/api/app/application/agents/definitions/versions.py`
- `apps/api/app/application/agents/definitions/polish/__init__.py`
- `apps/api/app/application/agents/definitions/polish/question.py`
- `apps/api/app/application/agents/definitions/polish/feedback.py`
- `apps/api/app/application/ai_runtime/contracts.py`
- `apps/api/app/application/ai_runtime/handoff.py`
- `apps/api/app/application/ai_runtime/side_effect_guard.py`
- `apps/api/app/application/ai_runtime/trace_bridge.py`
- `tests/api/test_agent_contracts.py`
- `tests/api/test_agent_graph_runner.py`
- `tests/architecture/test_agent_platform_c0_boundary.py`

## Findings

1. [PROJECT_SOURCE] P8 目标要求 AgentExecutor 边界支持 `start`、`resume`、`replay`、`get_status`、`get_timeline`、`cancel`，并返回 candidate refs 和 trace refs，不得直接 formal write。P8 还要求完整 trace/timeline、typed handoff、read-only replay、controlled tool loop、HITL interrupt 和 no-false-done gate。

2. [GITHUB_CODE] `apps/api/app/application/agents/runtime/__init__.py` 中的 `AgentExecutor` 已声明 `start`、`resume`、`replay`、`get_status`、`get_timeline`、`cancel`，但它只是 `Protocol`，并返回 `AgentExecutionResult` / `AgentExecutionStatus` / `AgentExecutionTimeline`。该子树内未发现 `AgentRunResult` 命名。

3. [GITHUB_CODE] 当前 `AgentRunResult`、`AgentRunStatus`、`AgentRunTimelinePage` 位于 `apps/api/app/application/ai_runtime/contracts.py`，与 `application/agents` 的 `AgentExecution*` contract-only 类型并存。`tests/architecture/test_agent_platform_c0_boundary.py` 还显式断言 `AgentGraphRunner is not AgentExecutor`，说明两套端口当前被刻意分离，而非已合并的 P8 runtime boundary。

4. [GITHUB_CODE] `AgentExecutionResult` 是 candidate-first：字段包含 `run_id`、`status`、`candidate_refs`、`trace`、`handoff_refs`、`metadata`，没有 `formal_refs`。但它缺少 P8 trace/status 所需的 `ai_task_id`、`agent_version`、`interrupt_refs`、`low_confidence_flags`、`failure_reason`、`fallback_reason`、`formal_write_blocked` 等运行期语义。

5. [GITHUB_CODE] `AgentExecutionTrace` 和 `TraceContract` 已覆盖 `input_refs`、`plan_refs`、`skill_refs`、`tool_refs`、`policy_refs`、`provider_refs`、`candidate_refs`、`validation_refs`、`handoff_refs`、`output_refs`、`events`。缺口是 P8 要求的 `agent_version`、`ai_task_id`、`low_confidence_flags`、`failure_reason`、`fallback_reason` 未成为强字段。

6. [GITHUB_CODE] `apps/api/app/application/agents/handoff/__init__.py` 只是重新导出 `HandoffContract`。`HandoffContract` 有 `candidate_ref_types`、`payload_schema_id`、`validation_refs`、`side_effect_key`、`idempotency_key`、`formal_write_preconditions`、`allowed_formal_targets`，但没有完整 typed handoff envelope 实例字段，例如具体 `candidate_ref`、`candidate_type`、`trace_refs`。

7. [GITHUB_CODE] `apps/api/app/application/ai_runtime/handoff.py` 中的 `HandoffRequest` 要求 `candidate_refs`、`trace_refs`、`validation_result_ref`、`side_effect_key`，`prepare_handoff()` 返回空 `formal_refs`；但该请求缺少 P8 要求的 `candidate_type`、`payload_schema_id` 和显式 `idempotency_key` 字段。

8. [GITHUB_CODE] `AgentPersistenceHandoff.write_feedback_result()`、`write_report_result()`、`write_review_result()`、`write_candidate_result()`、`finalize_after_confirmation()` 对通用 `HandoffPlan` fail closed。`write_question_result()` 在传入 `QuestionResultWritePlan` 和 Core repository 时可以写 `PolishQuestion`，该路径是 Application Service / Handoff 方向的 formal write 候选，后续 P8 必须确认它不能被 runtime/replay/tool loop 直接调用或绕过。

9. [GITHUB_CODE] `AgentDefinitionRegistry` 限定 `candidate_outputs` 只能是候选类型；`ToolRegistry` 要求 `side_effect_policy` 只在 `read_only`、`candidate_write`、`formal_write_handoff_only`、`forbidden` 内，并阻断 repository / db / formal_write / raw payload 等直接暴露 token。这是当前 candidate-only 边界的正向证据。

10. [GITHUB_CODE] Question / Feedback definitions 都是 C1 contract-only / planned guarded workflow：Question 输出 `question_candidate`，Feedback 输出 `feedback_candidate` 和 `asset_update_candidate`，并声明 `no_runtime_wiring`。这不是 Phase 8 C4 runtime implementation。

11. [GITHUB_CODE] controlled tool loop 还不完整。`ToolDefinition` 有 `timeout_seconds`、`retry_policy`、`allowed_callers`、`side_effect_policy`，但 `AgentExecutionPlan` / registry 未强制 `max_steps`、`max_retries`、`stop_conditions`，也没有 P8 要求的 missing-bounds fail-closed 规则。

12. [PROJECT_SOURCE] `API_SPEC.md` 已登记 Agent Runtime API skeleton、AI task status、candidate/formal、low confidence 和 no raw payload 边界；但 P8 目标明确通常禁止 API contract change。当前 recon 未发现必须变更 API contract 才能继续的证据。

13. [PROJECT_SOURCE] `DELIVERY_PLAN.md` 仍显示 F8 `NOT_STARTED`，`BACKLOG.md` 中 `AIFI-REL-*` 是发布检查/runbook/rollback/security release 任务。当前 P8 goal pack 是受控执行证据输入，不替代 active delivery plan，也不能让 Phase 8 或 F8 自动进入 done。

14. [TEST_RESULT] 已执行 focused contract verification：`PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -q tests/api/test_agent_contracts.py tests/api/test_agent_graph_runner.py tests/architecture/test_agent_platform_c0_boundary.py -p no:cacheprovider`，结果 `20 passed in 0.20s`。该结果只证明当前合同/边界测试通过，不证明 P8 runtime done。

## Gaps

- `AgentExecutor` 与 `AgentGraphRunner` / `AgentExecution*` 与 `AgentRun*` 的端口命名和 DTO shape 分裂，P8-W1 需要 controller 决定 canonical boundary 或 adapter 映射。
- `AgentExecutionResult.status` 和 `AgentExecutionStatus.status` 是裸字符串，缺少 canonical status 集合、failure/fallback/interrupt semantics、owner / ai_task 映射和 formal-write-blocked invariant。
- `AgentRunResult` 有 `formal_refs` 字段，当前测试只覆盖 stub 返回空值，未强制 runtime result 不能携带 formal refs。
- `HandoffContract` 是元数据合同，不是完整 typed handoff envelope；`application/ai_runtime.HandoffRequest` 也缺少 `candidate_type`、`payload_schema_id`、显式 `idempotency_key`。
- `TraceContract` / `AgentExecutionTrace` 未完整覆盖 P8 `agent_version`、`ai_task_id`、`low_confidence_flags`、`failure_reason`、`fallback_reason`。
- `AgentExecutionTimeline` 使用 `AgentExecutionTrace` tuple 作为 events，缺少 event-level `event_id` / `event_type` / sanitized summary / `next_cursor` 一类运行期分页形状；`ai_runtime.AgentRunTimelinePage` 有相邻形状但未接入 `AgentExecutor`。
- `AgentSideEffectGuard.authorize_tool_call()` 只校验 owner、tool name、input refs，尚未承接 `ToolRegistry` 的 allowed callers、side effect policy、max loop bounds。
- controlled tool loop 的 `max_steps`、`max_retries`、`timeout_seconds`、`stop_conditions` 还没有形成 `AgentExecutionPlan` / runtime / tests 的闭环。
- `QuestionResultWritePlan` 可进入 formal question write；需要 P8 证明它只能由 Application Service -> Domain Policy -> Handoff 路由触发，不能被 runtime/replay/tool loop 直接触发。

## Recommended patch scope

- `apps/api/app/application/agents/runtime/__init__.py`：明确 `AgentExecutor` 与现有 `AgentGraphRunner` 的关系；优先做 adapter / compatibility mapping，而不是复制第二套 runtime port。
- `apps/api/app/application/agents/contracts/__init__.py`：补齐 P8 需要的 run/status/timeline/trace/handoff字段，或显式桥接到 `application.ai_runtime.contracts`，避免 `AgentExecution*` 与 `AgentRun*` 语义漂移。
- `apps/api/app/application/agents/handoff/**`：从 re-export 升级为 typed handoff envelope / contract surface，至少包含 `candidate_ref`、`candidate_type`、`payload_schema_id`、`trace_refs`、`validation_refs`、`side_effect_key`、`idempotency_key`。
- `apps/api/app/application/agents/registry/__init__.py`：增加新字段后的 registry validation，包括 status allowlist、candidate-only outputs、tool side-effect policy 和 no direct formal write exposure。
- `apps/api/app/application/agents/definitions/common.py`、`definitions/polish/question.py`、`definitions/polish/feedback.py`：同步 trace/handoff metadata，保留 candidate-only 和 no runtime wiring 边界。
- 如 controller 选择现有 `application/ai_runtime` 为 runtime canonical port，再纳入 `apps/api/app/application/ai_runtime/contracts.py`、`handoff.py`、`side_effect_guard.py`、`trace_bridge.py` 做兼容 patch；该动作应由 P8 scope lock 明确授权。
- Focused tests：`tests/api/test_agent_contracts.py`、`tests/api/test_agent_graph_runner.py`、`tests/architecture/test_agent_platform_c0_boundary.py`，并建议新增或扩展 `tests/architecture/test_agent_runtime_phase8_boundary.py` 和 `tests/application/agents/**` 来锁 P8-W1/W2/W4 gaps。
- 文档回填仅限验证后更新 `docs/goals/2026-06-05/**` 和必要的 `docs/project-sources/**`；不得把本 recon 当作 active design 或 done 证据。

## Recommended forbidden files

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/application/polish/*prompt*`
- `apps/api/app/application/ai_provider/**`，除非只读 recon
- `apps/api/app/infrastructure/llm/**`，除非只读 recon
- `apps/api/app/infrastructure/db/**`
- `apps/api/app/api/v1/**`，除非 controller 先记录 API-compatible wiring 决策且确认不改变 API contract
- `apps/web/**`、`frontend/**`
- `apps/api/app/domain/polish/policies/**`，除非只读 recon
- migration / Alembic / database schema 相关文件
- prompt/provider behavior、production fake provider wiring、CI、hooks、dependency lock files，除非 controller stop-and-report 后另行授权

## Stop-condition findings

- 当前没有发现必须立即停止 P8-W0 recon 的 blocker；本报告可交给 controller 合并 scope lock。
- 如果 controller 要求以 `application/agents.AgentExecutor` 作为唯一 P8 runtime boundary，则必须先解决它与 `application/ai_runtime.AgentGraphRunner` 的 DTO/port 分裂；否则 P8-W1 应标记 `blocked_needs_controller_decision`。
- 如果后续实现需要修改 API contract、prompt/provider、DB schema、frontend 或 domain policy 文件，应按 P8 stop condition 停止并记录 deviation，不应直接 patch。
- 如果 runtime adapter 需要返回非空 `formal_refs`，或 replay/tool loop 可以触发 `QuestionResultWritePlan` / Core repository 写入，应停止并标记 P8-W4 blocked。
- 如果无法把 replay 保持 read-only default，或无法把 formal write 限定在 Application Service -> Domain Policy -> Handoff 路由，应停止。
- 如果后续只完成 contracts、docs 或 fake-only tests，不得声明 Phase 8 done；最多可按证据标记 `partial_with_deferred_gaps` 或 `recon_only_no_patch`。
- 当前 worktree 有既有未跟踪文件 `docs/goals/2026-06-05/P8_W0_AGENT_RISK_RECON.md`；本 agent 未修改该文件，controller 合并时需区分来源。

Confidence: high
