---
title: P11_W2_IMPLEMENTATION_REPORT
type: implementation-report
status: runtime_hardening_slice_complete_with_deferred_product_workflow
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w2-implementation-report
---

# P11-W2 Implementation Report

Window ID: `P11-W2-RUNTIME-HARDENING-SLICE`

## Root Cause

P11-W1 已完成 contract-first Orchestrator 和 cross-agent contract foundation，但 runtime-facing primitives 仍缺少面向未来 cross-agent orchestration 的窄范围 fail-closed guard。P11-W2 需要在不实现产品多 Agent workflow、不执行 Orchestrator、不触碰 `ai_runtime/**` / `polish/**` / provider / prompt / API / DB / domain / frontend 的前提下，补齐 handoff、resume、replay、trace/timeline 和 HITL 的内部硬化。

## What Changed

- `app.application.agents.contracts` 增加 cross-agent side-effect policy、HITL trigger 和 resume action 常量。
- `CrossAgentHandoffRoute` 现在校验 side-effect policy 和 HITL / candidate confirmation condition。
- `HandoffContract` 可选绑定 `CrossAgentHandoffRoute`，用于 route-bound cross-agent handoff strict validation。
- `build_agent_handoff_plan()` 在 route 存在时校验 source/target、candidate type、payload schema、required trace refs、required validation refs、unsafe metadata 和 formal refs。
- `app.application.agents.runtime` 增加 cross-agent resume、replay、trace/timeline、HITL validation helper。
- `AgentGraphRunnerExecutorAdapter.resume*()` 对 `cross_agent_resume` opt-in payload 执行严格 resume validation；既有非 cross-agent resume 行为不升级为产品 workflow。
- `AgentGraphRunnerExecutorAdapter._result_from_replay()` 对 `cross_agent_replay` metadata 执行 read-only / formal-write-blocked validation。

## Files Changed

- `apps/api/app/application/agents/contracts/__init__.py`
- `apps/api/app/application/agents/handoff/__init__.py`
- `apps/api/app/application/agents/runtime/__init__.py`
- `tests/application/agents/test_phase11_runtime_hardening.py`
- `tests/application/agents/test_phase8_agent_executor_adapter.py`
- `tests/architecture/test_agent_platform_l5_orchestrator_contract.py`
- `tests/api/test_agent_contracts.py`
- P11-W2 allowed source backfill docs and execution reports.

## Behavior Before / After

Before:

- `build_agent_handoff_plan()` could build a handoff plan from a typed candidate descriptor without route-bound source/target validation.
- Missing descriptor trace refs could be hidden by adding the source trace id.
- Cross-agent resume/replay/trace/HITL validation existed only as broader P8 runtime/facade behavior, not as future cross-agent strict primitives under `application/agents`.

After:

- Route-bound handoff fails closed on source/target mismatch, invalid candidate type, schema mismatch, missing required trace refs, missing required validation refs, unsafe metadata and formal refs.
- Cross-agent resume strict mode requires checkpoint/base/idempotency/owner/interrupt/action fields.
- Cross-agent replay strict mode requires `read_only`, `formal_write_blocked` and zero provider/tool/repository/DB/formal-write counters.
- Cross-agent trace/timeline helper keeps plan, handoff, validation and candidate refs separate.
- HITL trigger helper rejects success-like formal-write, asset-conflict and validation-failed partial-result semantics.

## Runtime Hardening Added

- Cross-agent handoff execution guard.
- Cross-agent checkpoint / resume validation helper.
- Cross-agent replay read-only / formal-write-blocked validation helper.
- Cross-agent trace / timeline refs-only mapping helper.
- HITL trigger validation for `formal_write_requested`, `asset_conflict`, `low_confidence`, `ambiguous_ownership` and `validation_failed_partial_result`.
- Success-like status with `failure_reason` remains fail-closed through the shared runtime status taxonomy.

## Tests Added / Updated

- Added `tests/application/agents/test_phase11_runtime_hardening.py`.
- Updated P8 application adapter gate for strict cross-agent resume opt-in.
- Updated API contract gate for cross-agent side-effect and HITL condition validation.
- Updated L5 architecture gate for route side-effect and HITL condition validation.

## Non-Claims

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not wire Orchestrator into `AgentExecutor`, LangGraph, `AiOrchestrationFacade`, API routes, Question workflow, Feedback workflow, provider, prompt, DB, frontend or domain policies.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.
