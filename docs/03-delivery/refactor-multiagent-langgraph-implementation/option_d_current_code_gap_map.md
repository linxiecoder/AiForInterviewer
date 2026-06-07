---
title: option_d_current_code_gap_map
type: implementation-gap-map
status: active-d-w1
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/option-d-current-code-gap-map
---

# Option D 当前代码 Gap Map

本文档是 `D-W1 — Recon and Gap Classification` 的当前代码事实记录。它只记录本地 recon、测试证据、能力缺口和后续窗口边界，不声明任何 L5 capability `done`，也不替代 active Project sources、代码或测试结果。

## 1. Source Priority

本轮按 canonical goal 的事实优先级执行：

1. USER_CONFIRMED：用户确认 Option D = Local Complete Multi-Agent Capability。
2. GITHUB_CODE：当前工作树和 `origin/main` 刷新后的代码事实。
3. TEST_RESULT：本地当前测试、eval、replay 命令结果。
4. PROJECT_SOURCE：`docs/project-sources/**` 架构和 guardrails。
5. GOAL_SOURCE：GOAL0531 仅作历史 intent。
6. SUBWINDOW_OUTPUT：仅作线索，经本轮总控 recon 后才能引用。

## 2. Preflight Evidence

| 检查 | 结果 | 结论 |
| --- | --- | --- |
| `git fetch origin main` | completed | `origin/main` 已刷新 |
| `git status --short --branch --untracked-files=all` | `## refactor/option-d-local-multi-agent...origin/refactor/option-d-local-multi-agent [ahead 2]` | 工作树 clean，无未跟踪改动 |
| `git rev-parse HEAD` | `933604ebc0439a17c3293b6cfd678fe95c2537b3` | 当前本地 HEAD |
| `git rev-parse origin/main` | `12a140eeaf9ba89f3e475e7e81973623f15fd7d5` | 当前 `origin/main` |
| `git rev-list --left-right --count HEAD...origin/main` | `3 0` | 当前分支相对 `origin/main` ahead 3 |
| CodeGraph status | 680 files / 12294 nodes / 32396 edges | 索引可用 |
| `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture tests/evals -q` | 74 passed | canonical W1 smoke 通过 |
| `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/application/agents tests/architecture -q` | 55 passed | Agent / architecture focused baseline 通过 |
| `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/api -k "agent or handoff or runtime or multi_agent or l5" -q` | 244 passed, 481 deselected | API focused baseline 通过 |
| `git diff --check` | pass | 当前无 whitespace diff issue |

## 3. Trigger Package Reconciliation

canonical goal 中 `D-W1` 是 audit-first recon / gap classification，并要求产出本文档；trigger package 中的 “W1 tests first” 是后续 tests-first implementation prompt。二者窗口编号存在偏差。

本轮以 canonical goal 为准：

- W1 不修改 implementation files。
- W1 不修改 tests，除非发现 trivial architecture / boundary assertion 需要记录当前事实。本轮未发现必须立即改测试才能完成 gap map。
- tests-first runtime wiring 将在后续窗口重新 scope lock 后执行。

## 4. Current Code Facts

### 4.1 Orchestrator / Catalog

`apps/api/app/application/agents/definitions/catalog.py` 当前提供：

- `build_default_agent_platform_c1_registries()`：只注册 `polish_question_agent` 和 `polish_feedback_agent`。
- `build_default_agent_platform_l5_contract_registries()`：组合 C1 agent、`interview_orchestrator_agent`、`asset_candidate_agent` 和 `training_plan_agent`。

`apps/api/app/application/agents/definitions/orchestrator.py` 当前的 `build_interview_orchestrator_agent_definition()` 仍是 contract-only：

- mission 是 `Plan cross-agent candidate handoffs without executing product workflow`。
- non-goals 明确包含 `no runtime execution`、`no product workflow execution`、`no direct DB or repository write`、`no prompt/provider/API/DB/domain behavior change`、`no real-provider quality certification`。

结论：`L5-002` 有注册和 contract evidence，但尚无 executable Supervisor / Orchestrator runtime evidence。

### 4.2 Cross-Agent Handoff / Runtime Boundary

`apps/api/app/application/agents/handoff/__init__.py` 当前提供：

- `build_agent_handoff_plan()`：从 source `AgentExecutionResult` 构造 target `AgentExecutionPlan`，使用 `AgentHandoffEnvelope`、`HandoffContract` 和 `CrossAgentHandoffRoute`。
- `execute_agent_handoff()`：通过 `target_executor.start(target_plan)` 启动 target executor。
- handoff metadata 会过滤 unsafe key，并要求 trace refs / validation refs / side effect / idempotency refs。

`apps/api/app/application/agents/runtime/__init__.py` 当前的 `AgentGraphRunnerExecutorAdapter` 已有：

- formal refs 拒绝。
- replay read-only / formal-write-blocked 校验。
- runtime loop policy 校验：`max_steps`、`max_retries`、`timeout_seconds`、`stop_conditions`。
- HITL trigger 校验。
- Tool call repository / DB exposure 拒绝。

结论：`L5-003` / `L5-005` 有 typed handoff primitive 和 runtime boundary hardening evidence，但尚无 product-level Supervisor 驱动的 cross-agent state / trace / replay。

### 4.3 Minimal Three-Agent Product Slice

`apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py` 当前提供 `build_minimal_three_agent_product_slice()`：

- 参与 agent refs：`polish_feedback_agent`、`asset_candidate_agent`、`training_plan_agent`。
- 输出 refs-only candidate：`feedback_candidate`、`asset_update_candidate`、`training_plan_candidate`。
- 构造 feedback -> asset、asset -> training typed handoff refs。
- formal write blocked，asset update 需要 user confirmation。
- 不调用 provider，不渲染 prompt，不读写 storage，不写 formal facts。

当前测试 `tests/application/agents/test_phase11_three_agent_product_slice.py` 和 `tests/architecture/test_agent_platform_l5_orchestrator_contract.py` 验证该 deterministic slice。

结论：`L5-004` 有 test-only refs-only slice evidence，但不是本地可执行 product runtime workflow。canonical goal 推荐的业务 agent 集包含 `polish_progress_agent`；当前 slice 使用 `training_plan_agent`，后续窗口必须决定是补 `polish_progress_agent`，还是在 Project sources 中明确训练计划 agent 的业务等价边界。当前不得视为 Option D workflow complete。

### 4.4 Runtime Facade / Flags

`apps/api/app/application/ai_runtime/facade.py` 当前 `AiOrchestrationFacade._start_run()`：

- 从 `AgentGraphRegistry` 读取 graph descriptor。
- 先检查 `AIFI_AI_RUNTIME_ENABLED` 和 descriptor graph flag。
- 构造 `AgentExecutionPlan` 后调用 `AgentExecutor.start()`。

`apps/api/app/application/ai_runtime/registry.py` 当前 default registry：

- 登记 `polish_question_graph`、`polish_feedback_graph`、`job_match_graph`、`resume_analysis_graph`、`report_generation_graph`、`review_generation_graph`。
- task map 没有 local multi-agent / orchestrator task。

`apps/api/app/application/ai_runtime/runtime_flags.py` 当前 flag 解析顺序：

- test override -> environment -> settings -> optional persisted config -> hardcoded default。
- 现有测试覆盖 runtime / graph / real-provider flag default-off。

结论：default-off runtime foundation 存在，但 Option D 的 `AIFI_ENABLE_LOCAL_MULTI_AGENT_ORCHESTRATION` 或 `AIFI_AGENT_RUNTIME_MODE=local_multi_agent` 尚未实现。

### 4.5 Polish Product Path

`PolishUseCases.create_question_task()` 当前调用 `run_question_planned_workflow()`。Feedback planned workflow 可构造 `feedback_candidate` / `asset_update_candidate` handoff metadata。

结论：Question / Feedback planned workflows 是 candidate-first local product components，但当前没有从 `PolishUseCases` 或 runtime facade 进入 Supervisor / Orchestrator 的 default-off local multi-agent product path。

### 4.6 Provider / Fake Boundary

`apps/api/app/application/llm/provider_boundary.py` 当前 `build_validated_transport_request()` 通过 `ProviderRequestValidator` 生成 compact `LlmTransportRequest`。Question / Feedback / progress tree / job match / feedback graph trace 都使用该边界。

当前测试和静态检查覆盖：

- forbidden provider payload keys：`raw_prompt`、`raw_provider_payload`、`raw_completion`、`full_resume`、`full_jd`、`full_answer`、`full_asset_body`、secret/token/cookie/api key 等。
- `FeedbackGenerationService` 对 deterministic fake transport 返回 `fake_transport_not_runtime_provider`。
- fake boundary 测试限制 `LLM_PROVIDER=fake` 只在受控测试路径使用。

结论：provider compact / fail-closed 基础存在；后续 Option D runtime path 不得绕过该边界，也不得把 fake 用到 tests / evals / replay 之外。

## 5. Capability Gap Map

| Capability | 当前证据 | Gap | 后续窗口 |
| --- | --- | --- | --- |
| `L5-002` Supervisor / Orchestrator Agent | `interview_orchestrator_agent` contract catalog 已注册，candidate-only，ToolRegistry 无 direct repository exposure | contract-only，明确 no runtime execution；缺 executable local Supervisor / Orchestrator path | D-W2 / D-W3 |
| `L5-003` Cross-agent handoff / state / trace / replay | `CrossAgentPlan` / `CrossAgentHandoffRoute` / `AgentHandoffEnvelope` / `execute_agent_handoff()`；runtime adapter 映射 handoff refs | 缺 product-level Orchestrator 驱动的 cross-agent state / trace / replay；当前 replay 不是完整 local multi-agent product replay | D-W2 / D-W4 |
| `L5-004` Multi-agent product workflow | deterministic three-agent refs-only slice：feedback -> asset -> training | 无 default-off product/runtime caller；agent set 与 canonical goal 的 `polish_progress_agent` 存在 mismatch；当前 tests 仍禁止 runtime wiring | D-W2 / D-W3 |
| `L5-005` Controlled loop / HITL | runtime adapter 校验 bounds、stop conditions、HITL、tool exposure；minimal slice 覆盖 asset conflict / formal write / low confidence | 这些校验尚未被 executable Orchestrator product path 贯穿；ownership ambiguity 仍需在 local runtime/replay fixtures 中验证 | D-W2 / D-W4 |
| `L5-006A` Local eval / replay / failure hardening | Phase 12 eval foundation 本地通过；`tests/evals/phase12/**` 有 deterministic cases；`run_l5_eval_suite.py` 存在 | Project sources 仍记录 replay/resume/failure fixtures、local trace report 和 gap closure 未完成 | D-W4 / D-W5 |
| `L5-006B` Production release gate | D-W0 已拆分 | out of scope / deferred；不得在 Option D 中关闭 | D-W5 只 backfill deferred |

## 6. Test Gap Map

当前通过的测试证明基础不坏，但也暴露下一窗口需要调整的断言：

| 测试文件 | 当前事实 | 后续需要 |
| --- | --- | --- |
| `tests/application/agents/test_phase11_three_agent_product_slice.py` | 验证 deterministic refs-only slice，并断言 Orchestrator 不出现在 `ai_runtime` / `polish` / `api` / `domain` / `infrastructure` roots | runtime wiring 后该断言需要改为允许 default-off local path，并验证 flag-off 不变 |
| `tests/architecture/test_agent_platform_l5_orchestrator_contract.py` | 验证 contract-only Orchestrator、no runtime/provider binding、three-agent slice evidence | 后续需要从 “not runtime wired” 改为 “only local default-off runtime wiring allowed；no provider/API/DB/frontend/domain behavior change” |
| `tests/api/test_agent_runtime_flags.py` | 只覆盖现有 runtime / graph / real-provider flags | 需要新增 local multi-agent mode / flag default-off、test override、env、no A/B semantics |
| `tests/api/test_ai_orchestration_facade.py` | 覆盖 existing graph start surfaces route through `AgentExecutor` | 需要新增 flag-on local multi-agent orchestrator descriptor / plan metadata / candidate refs；flag-off 保持 GraphDisabled 或 existing path |
| `tests/evals/phase12/**` | local deterministic eval foundation 存在 | 需要补 replay / resume / failure fixture execution 与 local trace report evidence |

## 7. W1 Output Boundary

本 W1 只新增本文档。

Allowed write:

- `docs/03-delivery/refactor-multiagent-langgraph-implementation/option_d_current_code_gap_map.md`

Forbidden write:

- `apps/**`
- `tests/**`
- `scripts/**`
- `evals/**`
- `.github/**`
- `apps/web/**`
- DB schema / migration / model files
- API route / public contract behavior
- provider / prompt behavior files
- production config
- lockfiles
- archive docs

## 8. Expected Behavior Change

本 W1 无运行时行为变化、无测试行为变化、无 provider / prompt / API / DB / frontend 行为变化。

后续窗口的预期行为变化必须重新 scope lock：

- flag off：existing Question / Feedback paths 继续 unchanged。
- flag on：local product path 可进入 Supervisor / Orchestrator。
- 所有输出仍为 candidate / suggestion / validation / trace。
- formal write 仍必须经 `Application Service -> Domain Policy -> Handoff`。

## 9. Stop Conditions Carried Forward

后续窗口必须在以下条件停止：

- 需要修改 forbidden files 才能继续。
- 需要 DB schema / migration、API contract behavior、frontend behavior、prompt rewrite、real provider config 或 production deployment config。
- 需要 A/B testing、traffic split、canary、online experiment metrics、production observability/SLO、remote CI hard claim 或 real-provider production certification。
- Agent 直接写 formal business facts。
- Tool 直接暴露 repository / DB / SQLAlchemy session / unit-of-work / formal writer。
- Runtime 绕过 `Application Service -> Domain Policy -> Handoff`。
- Provider request 需要 raw prompt、full resume、full JD、full answer、full asset body、raw provider payload 或 secrets。
- Fake provider 需要用于 tests / evals / replay 之外。
- 当前代码和 Project sources 冲突且无法作为 gap 记录。
- validation 失败且修复需要 forbidden scope。

## 10. Next Window Recommendation

下一窗口应以 tests-first scope lock 进入 default-off local multi-agent runtime wiring，最小目标是先改/新增测试证明：

1. local multi-agent flag / mode 默认关闭。
2. flag off 不改变 existing Question / Feedback behavior。
3. flag on 可从 local product path 构造 Supervisor / Orchestrator `AgentExecutionPlan`。
4. 至少三个业务 agent 通过 typed handoff 参与，且 candidate refs / handoff refs / validation refs / trace refs 可见。
5. formal write、repository exposure、provider payload、fake runtime use 均 fail-closed。
6. HITL 覆盖 asset conflict、formal write、low confidence、ownership ambiguity。

下一窗口不得直接跳到 production release、A/B、remote CI hard claim 或 real-provider certification。
