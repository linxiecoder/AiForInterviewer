---
title: P8_W2_CONTROLLED_TOOL_LOOP_REPORT
type: goal-evidence
status: implemented_validated_with_deferred_cross_graph_wiring
owner: P8 Implementation Writer
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w2-controlled-tool-loop-report
---

# P8-W2 Controlled Tool Loop Report

Status: implemented_validated_with_deferred_cross_graph_wiring

## Scope

- Added reusable runtime loop policy and ToolDefinition-side authorization checks.
- Files changed:
  - `apps/api/app/application/agents/contracts/__init__.py`
  - `apps/api/app/application/ai_runtime/registry.py`
  - `apps/api/app/application/ai_runtime/facade.py`
  - `apps/api/app/application/ai_runtime/side_effect_guard.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
  - `tests/api/test_agent_contracts.py`
  - `tests/api/test_agent_fake_runtime.py`
  - `tests/api/test_agent_graph_runner.py`
  - `tests/api/test_ai_orchestration_facade.py`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py`
  - `tests/api/test_pr8_polish_provider_trace_gate.py`
  - `tests/architecture/test_agent_platform_c1_boundary.py`

## What Changed

- Added `AgentRuntimeLoopPolicy` with fail-closed validation for:
  - `max_steps`
  - `max_retries`
  - `timeout_seconds`
  - complete P8 `stop_conditions`: `max_steps_exceeded`, `timeout`, `validation_failed`, `tool_not_allowed`, `formal_write_requested`, `interrupt_required`, `provider_failed`
  - `allowed_tools`
  - `allowed_callers`
  - `side_effect_policy`
- `AgentGraphRunnerExecutorAdapter.start()` now requires a runtime loop policy.
- Generic direct `InMemoryLangGraphRuntime.start()` now also requires `runtime_loop_policy` metadata and validates it through `AgentRuntimeLoopPolicy` before a generic run can start.
- `GraphDescriptor` now carries runtime policy primitives for facade-created commands.
- `AiOrchestrationFacade` now validates those descriptor policy fields through `AgentRuntimeLoopPolicy` and injects `runtime_loop_policy` into start/resume/replay command metadata; missing facade descriptor bounds fail closed before runner invocation.
- `AgentSideEffectGuard.authorize_tool_call()` validates `ToolDefinition` caller, permission scope, owner scope, side-effect policy and forbidden payloads, consumes `ToolDefinition.forbidden_data` keys recursively, and now fails closed when no registered `ToolDefinition` is supplied.
- Polish question concrete phase tools now resolve a registered runtime `ToolDefinition` before execution, fail closed with `tool_not_allowed` when the runtime registry is missing the tool, and fail closed when a tool-declared forbidden-data payload key reaches the concrete tool path.
- Feedback PR8 provider trace gate now resolves a registered runtime `ToolDefinition`, consumes descriptor-backed `AgentRuntimeLoopPolicy`, and fail-closes on unregistered trace gate nodes, caller mismatch, permission-scope mismatch, owner-scope mismatch, side-effect mismatch and tool-declared forbidden-data payloads.
- Feedback direct in-memory runner start now requires descriptor-matching `runtime_loop_policy` metadata, rejects missing or mismatched fields before fake payload construction, and strips that control-plane metadata before PR6 refs/digest payload validation.
- Architecture gate now scans current production `authorize_tool_call()` call sites under `application/ai_runtime` and requires each direct call site to pass a non-`None` `tool=` keyword.

## Validation

- Red: `test_runtime_loop_policy_fails_closed_and_guard_validates_tool_contract` initially failed because `AgentRuntimeLoopPolicy` did not exist.
- Red: the same focused contract test later failed with `DID NOT RAISE` because `AgentRuntimeLoopPolicy` accepted an incomplete P8 stop-condition set.
- Red: adapter missing-policy test initially failed because adapter did not require bounds.
- Red: `test_facade_direct_start_injects_shared_runtime_loop_policy` initially failed because direct facade start metadata did not include `runtime_loop_policy`.
- Red: `test_facade_direct_start_fails_closed_when_descriptor_runtime_policy_is_missing` initially failed because graph descriptors did not carry runtime policy fields.
- Red: `test_execute_polish_question_agent_requires_registered_runtime_tool` initially failed because the concrete Polish question runtime did not require a registered runtime tool definition.
- Red: `test_pr8_trace_gate_requires_registered_runtime_tool` initially failed because Feedback provider trace gate accepted an unregistered runtime node name.
- Red: `test_runtime_loop_policy_fails_closed_and_guard_validates_tool_contract` then failed because `AgentSideEffectGuard.authorize_tool_call()` still accepted a runtime tool call without a registered `ToolDefinition`.
- Red: `test_execute_polish_question_tool_enforces_tool_forbidden_data` initially passed with `developer_prompt`, proving that key was already covered by provider forbidden keys; after switching to `api_keys`, it failed because the concrete Polish question tool path did not consume `ToolDefinition.forbidden_data` beyond global sensitive payload detection.
- Red: `test_pr6_feedback_direct_runtime_requires_descriptor_runtime_loop_policy` initially failed because Feedback direct in-memory runner accepted a command with no `runtime_loop_policy`.
- Red: `test_pr6_feedback_direct_runtime_rejects_runtime_loop_policy_mismatch` initially failed with PR6 metadata validation rather than descriptor policy validation, proving policy metadata was not separated from refs/digest payload metadata at the runner boundary.
- Red: `test_pr4_in_memory_runtime_start_requires_runtime_loop_policy_metadata` failed with `DID NOT RAISE` because generic direct in-memory runtime start accepted a command with no `runtime_loop_policy`.
- Evidence-only: Feedback PR8 trace-gate caller mismatch, permission-scope mismatch, owner-scope mismatch, side-effect mismatch and tool-declared forbidden-data tests passed immediately, proving the existing trace-gate guard path already fail-closes those cases.
- Green:
  - `tests/api/test_agent_contracts.py` = `15 passed`
  - `tests/api/test_agent_contracts.py -k "runtime_loop_policy_fails_closed"` = `1 passed, 14 deselected in 0.17s`
  - `tests/api/test_agent_graph_runner.py` = `5 passed`
  - `tests/api/test_agent_fake_runtime.py` = `19 passed`
  - `tests/api/test_ai_orchestration_facade.py` = `13 passed`
  - `tests/api/test_pr8_polish_provider_trace_gate.py` = `16 passed`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py` = `15 passed`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py -k "requires_runtime_loop_policy_metadata"` = `1 passed, 10 deselected in 0.42s`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py` = `11 passed in 0.52s`
  - `tests/architecture/test_agent_platform_c1_boundary.py::test_runtime_tool_authorization_call_sites_require_tool_definition_keyword` = `1 passed`
  - `tests/architecture` = `24 passed`

## Deferred Gap

- The shared policy is enforced at the AgentExecutor adapter boundary and now reaches all current facade start surfaces plus facade-created resume/replay command metadata. Generic direct in-memory runtime start also rejects missing `runtime_loop_policy` metadata before graph invocation. Policy construction fails closed unless the full P8 stop-condition set is present, not merely a non-empty subset. Runtime tool authorization now requires a registered `ToolDefinition`; Polish question concrete tool calls and the Feedback PR8 provider trace gate resolve registered runtime ToolDefinitions before execution; Polish question concrete tool calls and Feedback PR8 trace gate now both prove caller / side-effect / tool-declared forbidden-data fail-closed behavior where applicable, and Feedback PR8 trace gate additionally proves permission-scope and owner-scope mismatch blocking. Feedback direct in-memory runner start now rejects missing or mismatched descriptor loop-policy metadata before fake payload construction. An architecture gate covers current direct `authorize_tool_call()` production call sites. Cross-graph closure remains deferred for future / indirect graph tool-loop expansion outside the covered facade start surfaces and Question/Feedback direct paths.
