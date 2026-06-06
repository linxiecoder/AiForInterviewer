---
title: P8_W1_RUNTIME_ADAPTER_REPORT
type: goal-evidence
status: implemented_validated
owner: P8 Implementation Writer
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w1-runtime-adapter-report
---

# P8-W1 Runtime Adapter / Executor Integration Report

Status: implemented_validated

## Scope

- Implemented an AgentExecutor-compatible adapter without changing prompt, provider, API, DB, frontend or domain policy behavior.
- Files changed:
  - `apps/api/app/application/agents/runtime/__init__.py`
  - `apps/api/app/application/agents/contracts/__init__.py`
  - `apps/api/app/application/ai_runtime/facade.py`
  - `tests/api/test_agent_graph_runner.py`
  - `tests/api/test_ai_orchestration_facade.py`

## What Changed

- Added `AgentGraphRunnerExecutorAdapter`.
- Marked `AgentExecutor` runtime-checkable for boundary assertions.
- Extended `AgentExecutionPlan` with optional runtime context fields: run id, AI task id, actor id, graph name/version, input refs, requested outputs, idempotency key and runtime loop policy.
- Adapter maps start / resume / replay / status / timeline / cancel into project-owned AgentExecution DTOs.
- `AiOrchestrationFacade._start_run()` now builds an `AgentExecutionPlan` and routes all current facade start surfaces through `AgentGraphRunnerExecutorAdapter` while preserving external `AgentTaskStatusRef` behavior.
- `AiOrchestrationFacade.get_agent_run_status()` / `get_agent_run_timeline()` / `cancel_agent_run()` now route facade-created runs through the adapter status / timeline / cancel surface, while unknown runs keep the existing runner fallback path.
- Facade-created adapter read/cancel routing preserves owner scope with a facade-local run owner guard before calling the adapter.
- `AgentExecutionResult` now preserves runner `output_refs`, `interrupt_refs` and typed candidate payloads so facade status mapping can consume the AgentExecutor-compatible result without losing refs.
- Adapter blocks non-empty runtime `formal_refs` and blocks replay that is not read-only / formal-write-blocked.

## Validation

- Red: `test_graph_runner_adapter_exposes_agent_executor_boundary` initially failed because `AgentGraphRunnerExecutorAdapter` did not exist.
- Red: `test_graph_runner_adapter_blocks_formal_refs_from_runtime_result` initially failed because formal refs were not blocked.
- Red: `test_graph_runner_adapter_preserves_facade_status_payload_refs` initially failed because `AgentExecutionResult` did not preserve runner `output_refs`, `interrupt_refs` or typed candidate payloads.
- Red: `test_facade_direct_start_routes_through_agent_executor_plan_metadata` initially failed because facade start called the runner directly and did not emit AgentExecutionPlan metadata.
- Red: `test_facade_created_status_timeline_and_cancel_route_through_agent_executor_adapter` initially failed with missing `source_boundary` metadata because facade-created status / timeline / cancel still bypassed the adapter and called the runner directly.
- Green: `tests/api/test_agent_graph_runner.py tests/api/test_agent_contracts.py` = `31 passed in 0.21s`.
- Green: `tests/api/test_ai_orchestration_facade.py -k "adapter_route"` = `1 passed, 22 deselected in 0.16s`.
- Green: `tests/api/test_ai_orchestration_facade.py` = `23 passed in 0.12s`.

## Gaps

- This is still C4 foundation. Facade-created start/status/timeline/cancel now route through the AgentExecutor-compatible adapter for known runs, but product-level Supervisor / L5 orchestration and richer business asset handoff remain deferred.
- No Phase 11 Supervisor / Orchestrator or L5 workflow is implemented.
