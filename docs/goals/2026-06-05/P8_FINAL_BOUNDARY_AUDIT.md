---
title: P8_FINAL_BOUNDARY_AUDIT
type: goal-evidence
status: warn_foundation_partial
owner: P8 Boundary Audit Agent
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-final-boundary-audit
---

# P8 Final Boundary Audit

## Verdict

WARN

本审计未发现当前 tracked diff 修改 prompt/provider/DB/API/frontend/domain-policy 路径，也未发现 fake provider 被新增进 production runtime。当前 P8 证据只能支持 `partial_with_deferred_gaps` / foundation partial，不能声明 P8 done、F8/M8 release、Phase 11 Supervisor / Orchestrator 或 Phase 12 L5 release gate。

WARN 原因：`AgentSideEffectGuard.authorize_tool_call()` 已经要求 registered runtime `ToolDefinition` 并消费 `ToolDefinition.forbidden_data`；Polish question concrete tool calls 和 Feedback PR8 provider trace gate 也已证明 registry lookup；Polish question concrete tool calls 已补充 loop-policy caller / side-effect / tool-declared forbidden-data enforcement；Feedback PR8 provider trace gate 已补充 caller / permission / owner / side-effect / tool-declared forbidden-data 负向覆盖；Feedback direct in-memory runner start 已补充 descriptor policy metadata fail-closed gate；所有当前 facade start surfaces 已路由到 `AgentGraphRunnerExecutorAdapter` 并携带 descriptor-derived runtime policy metadata，facade-created status/timeline/cancel 已通过 adapter read/cancel surface 且保留 owner-scope guard，facade resume 已通过 adapter formal-ref guard，runtime result/status/timeline metadata 也会对非空 `formal_refs` 或非零 formal-write counters fail closed，包括 `formal_write_count` / `formal_writes` 这类常见 counter 变体，runtime result metadata 也会对 fake-provider 或 fallback-as-generated-success 标记 fail closed；Polish question concrete HITL resume now uses service-backed checkpoint/base/idempotency/action validation；新增 architecture gate 覆盖了当前 direct production `authorize_tool_call()` call sites。剩余风险转为 covered facade start surfaces 与 Question/Feedback direct paths 之外的 future / indirect graph tool-loop expansion、remaining product/future graph paths，不是已观察到的 production bypass。

## Files reviewed

### Governance / goal source

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/03-implementation/DELIVERY_PLAN.md`
- `docs/03-implementation/BACKLOG.md`
- `docs/tmp/goal0605/phase8_codex_goal_pack/docs/P8_MASTER_GOAL.md`

### Current diff and related changed files

- `.env.example`
- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/agents/handoff/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `apps/api/app/application/ai_runtime/contracts.py`
- `apps/api/app/application/ai_runtime/facade.py`
- `apps/api/app/application/ai_runtime/interrupts.py`
- `apps/api/app/application/ai_runtime/registry.py`
- `apps/api/app/application/ai_runtime/side_effect_guard.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
- `apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
- `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py`
- `tests/api/test_agent_contracts.py`
- `tests/api/test_agent_fake_runtime.py`
- `tests/api/test_agent_graph_runner.py`
- `tests/api/test_agent_interrupt_replay.py`
- `tests/api/test_agent_runtime_flags.py`
- `tests/api/test_ai_orchestration_facade.py`
- `tests/api/test_pr4_fake_runtime_replay_resume.py`
- `tests/api/test_pr6_polish_fake_runtime_integration.py`
- `tests/api/test_pr8_polish_provider_trace_gate.py`
- `tests/architecture/test_agent_platform_c1_boundary.py`
- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/12_ACCEPTANCE_GATES.md`
- `docs/project-sources/13_DECISION_LOG.md`
- `docs/project-sources/14_RISK_REGISTER.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`
- `docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md`

### P8 evidence reports

- `docs/goals/2026-06-05/P8_W0_AGENT_RUNTIME_RECON.md`
- `docs/goals/2026-06-05/P8_W0_AGENT_CONTRACT_RECON.md`
- `docs/goals/2026-06-05/P8_W0_AGENT_QF_RECON.md`
- `docs/goals/2026-06-05/P8_W0_AGENT_TEST_RECON.md`
- `docs/goals/2026-06-05/P8_W0_AGENT_RISK_RECON.md`
- `docs/goals/2026-06-05/P8_W0_SCOPE_LOCK.md`
- `docs/goals/2026-06-05/P8_W1_RUNTIME_ADAPTER_REPORT.md`
- `docs/goals/2026-06-05/P8_W2_CONTROLLED_TOOL_LOOP_REPORT.md`
- `docs/goals/2026-06-05/P8_W3_RESUME_REPLAY_INTERRUPT_REPORT.md`
- `docs/goals/2026-06-05/P8_W4_HANDOFF_TRACE_REPORT.md`
- `docs/goals/2026-06-05/P8_W5_VALIDATION_AND_BACKFILL_REPORT.md`

## Evidence table

| Check | Evidence | Result | Notes |
|---|---|---|---|
| Worktree scope | `git diff --name-only`; `git diff --stat`; `git ls-files --others --exclude-standard` | WARN | Tracked diff is 33 files / +5573 / -86 lines. Untracked `.codegraph/`, P8 goal reports and `tests/application/` exist. No staged diff. |
| Forbidden path drift | `git diff --name-only` checked against prompt/provider/DB/API/frontend/domain-policy/dependency patterns | PASS | No changed file under prompt assets, provider implementation, DB/infrastructure DB, API routes, frontend, domain policy, dependency or lockfile paths. |
| Runtime config | `.env.example` diff | PASS with note | Only additive default-off `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED=false`; no `LLM_PROVIDER=fake` addition. |
| Formal write boundary | `AgentGraphRunnerExecutorAdapter._result_from_run()` rejects non-empty `formal_refs`; runtime result/status/timeline metadata rejects non-empty `formal_refs` or non-zero formal-write counters, including common counter key variants; facade start routes through the adapter; facade-created status/timeline/cancel route through the adapter for known runs with owner-scope guard; facade resume validates returned runtime refs through the adapter; replay requires `read_only` and `formal_write_blocked`; facade replay repeats the same guard | PASS | Adapter/facade surfaces return candidate refs / trace refs, not formal refs. |
| Runtime/tool/agent formal facts | `AgentExecutionResult` remains candidate-ref based; tests add `_FormalWritingRunner` negative case | PASS with gap | No new formal fact writer is added. Existing formal write handoff path remains outside runtime direct write. |
| Infrastructure business policy | `git diff -- apps/api/app/infrastructure/**` is limited to `infrastructure/ai_runtime/langgraph/in_memory_runtime.py` runner resume validation | PASS | No infrastructure DB policy, repository policy, SQLAlchemy or migration change is present in tracked diff. |
| ToolRegistry boundary | Existing `ToolRegistry.register()` blocks direct exposure; `AgentSideEffectGuard.authorize_tool_call()` now requires registered `ToolDefinition` and consumes `ToolDefinition.forbidden_data`; Polish question concrete tool calls resolve runtime `ToolDefinition` and enforce loop-policy caller / side-effect compatibility plus tool-declared forbidden-data blocking before execution; Feedback PR8 provider trace gate resolves runtime `ToolDefinition` before execution and proves caller / permission / owner / side-effect / tool-declared forbidden-data fail-closed behavior; Feedback direct in-memory runner start requires descriptor-matching `runtime_loop_policy` metadata; architecture gate checks current direct production `authorize_tool_call()` call sites | PASS with future-expansion gap | Guard no longer permits `tool=None`; current direct call sites require non-`None` `tool=`; Feedback direct in-memory runner rejects missing or mismatched loop-policy metadata; future / indirect graph tool-loop expansion outside covered facade start surfaces and Question/Feedback direct paths still needs shared policy / registry evidence before P8 can be marked done. |
| Fake provider isolation | `rg` over changed files and runtime fake tests; `.env.example` keeps fake only as comment/test warning; `test_graph_runner_adapter_blocks_fake_provider_metadata_from_runtime_result`; `test_graph_runner_adapter_blocks_fail_open_fallback_success_metadata` | PASS with existing gap | No new production fake provider path. Adapter now fails closed when runtime result metadata reports fake-provider use or fallback-as-generated-success metadata. Existing feedback fake-runtime/skeleton semantics are documented as deferred and were not introduced by this diff. |
| Source backfill wording | Project-source diffs use `partial_with_deferred_gaps` / `validated_with_deferred_gaps` and non-claim wording | PASS | Backfill does not mark P8 done, L5 release, Phase 11/12 complete, or formal F8/M8 release. |
| Validation claims | `P8_W5_VALIDATION_AND_BACKFILL_REPORT.md` records focused, architecture, Q/F, API and full backend pass | PASS with non-claim note | Current controller validation reran focused, architecture, API and full-suite gates; `git diff --check` passed. These results support foundation partial only. |

## Boundary findings

1. PASS: No prompt/provider/DB/API/frontend/domain-policy tracked file changes were found.
2. PASS: No dependency or lockfile changes were found; LangGraph dependency remains treated as existing.
3. PASS: Infrastructure diff is limited to allowed AI runtime runner resume validation; no DB, repository, SQLAlchemy or migration policy was introduced by the tracked patch.
4. PASS: Runtime adapter, facade start, facade-created status/timeline/cancel, facade resume and facade replay guard against direct formal refs; runtime result/status/timeline metadata also fails closed on non-empty `formal_refs` or non-zero formal-write counters, including common counter key variants; replay also requires read-only / formal-write-blocked semantics.
5. PASS: Fake provider was not added to production runtime. Adapter now rejects runtime result metadata that reports fake-provider use or fallback-as-generated-success metadata. Existing fake-related code remains in prior runtime/test surfaces and is recorded as a deferred gap where applicable.
6. PASS with future-expansion gap: ToolRegistry is not bypassed by an observed production call path; Polish question concrete tool calls and Feedback PR8 provider trace gate now require registry lookup, Polish question concrete tools enforce loop-policy caller / side-effect compatibility and tool-declared forbidden-data payload blocking, Feedback PR8 provider trace gate proves caller / permission / owner / side-effect / tool-declared forbidden-data fail-closed behavior, `authorize_tool_call()` fails closed without a registered `ToolDefinition`, and current direct production call sites are statically gated.
7. WARN: P8 is a validated foundation slice only. Deferred gaps remain for raw asset body transfer and formal asset composition/write semantics, future / indirect graph tool-loop expansion evidence outside covered facade start surfaces and Question/Feedback direct paths, remaining runner-bound HITL coverage outside the already covered facade/generic/Question/Feedback paths, product-level multi-agent handoff, and proving complete trace population for remaining product/future runtime events outside current generic start/resume/cancel plus Question start/resume/cancel, Feedback start/service-backed resume/cancel and target handoff timeline coverage.

## False-done risks

- P8 must not be reported as `done`; current evidence supports `partial_with_deferred_gaps` / foundation partial.
- `AgentGraphRunnerExecutorAdapter` proves compatibility foundation, not complete migration of every active runtime call site to `AgentExecutor`.
- `AgentRuntimeLoopPolicy` proves a shared contract plus consumption in all current facade start surfaces, facade resume/replay command metadata, Polish question concrete tool calls, Feedback PR8 provider trace gate and Feedback direct in-memory runner entry, including Polish question caller / side-effect / tool-declared forbidden-data enforcement, Feedback PR8 caller / permission / owner / side-effect / tool-declared forbidden-data enforcement and Feedback direct runner descriptor policy metadata fail-closed behavior; future / indirect graph tool-loop expansion outside covered facade start surfaces and Question/Feedback direct paths still need the same evidence.
- `AgentHandoffEnvelope`, `build_agent_handoff_plan()`, `execute_agent_handoff()` and target timeline handoff refs prove bounded typed AgentExecutor-bound Agent A to Agent B candidate handoff execution, not product-level Supervisor / L5 orchestration.
- `AiOrchestrationFacade.replay_agent_run()` proves facade replay guard, not public API endpoint behavior or F8 release readiness.
- Full backend validation recorded in `P8_W5_VALIDATION_AND_BACKFILL_REPORT.md` supports the implemented foundation slice only; it does not prove L5 release quality, Phase 11 Supervisor / Orchestrator, Phase 12 gate, or formal F8/M8 release.

## Required remediation

1. Extend shared policy / registry lookup to any future concrete production tool-loop expansion, with graph-path negative tests for unregistered tool, caller-disallowed, permission mismatched, owner-scope mismatched, side-effect mismatched, or forbidden-data payload.
2. Keep `authorize_tool_call()` mandatory-`ToolDefinition` behavior as a regression gate for future runtime tool-call work.
3. Keep P8 source wording at `partial_with_deferred_gaps` until all deferred gaps are closed with fresh implementation and validation evidence.
4. Do not add prompt/provider/API/DB/frontend/domain-policy changes to close P8 gaps. If those become necessary, stop and request a new controller decision.
5. Keep fake provider rejection tests in the required regression set for any future runtime-provider work; do not use fake runtime evidence as production provider proof.
