---
title: P8_W3_RESUME_REPLAY_INTERRUPT_REPORT
type: goal-evidence
status: implemented_validated_with_deferred_runner_bound_hitl
owner: P8 Implementation Writer
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w3-resume-replay-interrupt-report
---

# P8-W3 Resume / Replay / Interrupt Report

Status: implemented_validated_with_deferred_runner_bound_hitl

## Scope

- Added application facade replay surface without API contract changes.
- Hardened application facade resume control fields without API contract changes.
- Preserved existing owner-scoped interrupt / resume / checkpoint services and tests.
- Files changed:
  - `apps/api/app/application/ai_runtime/contracts.py`
  - `apps/api/app/application/ai_runtime/interrupts.py`
  - `apps/api/app/application/ai_runtime/facade.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py`
  - `tests/api/test_agent_interrupt_replay.py`
  - `tests/api/test_ai_orchestration_facade.py`
  - `tests/api/test_agent_fake_runtime.py`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py`

## What Changed

- Added `AiOrchestrationFacade.replay_agent_run()`.
- Replay builds a read-only command context and calls runner replay.
- Replay fails closed unless `read_only=True` and `formal_write_blocked=True`.
- `AgentReplayResult` now carries sanitized refs-only metadata. `InMemoryLangGraphRuntime.replay()` and `PolishQuestionGraphRuntime.replay()` preserve the original failed / blocked / interrupted / cancelled status category as `replayed_*`, carry `original_status`, `failure_reason`, `fallback_reason`, `replay_compared_trace_refs`, `replay_trace_match`, and zero provider/tool/repository/DB/formal-write counters. `AgentGraphRunnerExecutorAdapter` and `AiOrchestrationFacade.replay_agent_run()` preserve that metadata instead of dropping it.
- `AgentReplayResult` now fails closed when replay metadata reports provider/tool/repository/DB/formal-write side-effect counters above zero or as unparseable non-zero values; this blocks replay outputs that indicate provider calls, external tool calls, repository access, DB business writes or formal business writes.
- `AiOrchestrationFacade.resume_interrupted_run()` now requires `checkpoint_ref`, strict non-negative integer `base_version` and `idempotency_key`, carries them in resume command input/metadata, injects them into the runner resume payload, routes the runner result through `AgentGraphRunnerExecutorAdapter`, and fails closed on unsupported resume actions before runner invocation or runtime formal refs after runner return.
- Facade resume/replay now also fail closed before runner invocation when the graph descriptor does not declare the requested `supported_entrypoints`; `polish_question_graph` now declares the already-implemented `resume` entrypoint instead of relying on an implicit facade path.
- Added P8 HITL interrupt trigger matrix for:
  - `formal_write_attempt`
  - `asset_conflict`
  - `low_confidence_formal_update`
  - `ambiguous_ownership`
  - `validation_failed_partial_result`
- HITL interrupts now require a runtime checkpoint ref and keep `formal_refs=()`.
- HITL resume now validates checkpoint ref, base version and allowed resume action before returning a task status ref.
- Feedback in-memory runtime now opens checkpoint-bound HITL interrupts when refs-only metadata contains `formal_write_attempt_ref`, `asset_conflict_ref`, `low_confidence_formal_update_ref`, `ambiguous_ownership_ref` or `validation_failed_partial_result_ref`. The interrupted run keeps candidate refs / validation refs available, keeps `formal_refs=()`, and does not report the path as succeeded.
- Low-confidence HITL trigger refs are now reflected in `trace_refs.low_confidence_refs` and the HITL drawer payload `low_confidence_flags`.
- Service-backed `InMemoryLangGraphRuntime.resume()` now routes HITL resume through `AgentInterruptService.resume_interrupt()` and requires `checkpoint_ref`, `base_version`, `idempotency_key` and an allowed HITL action before the graph resumes. Non-service-backed legacy fake interrupts keep the old compatibility path.
- Generic in-memory runtime start now registers its user-confirmation interrupt through `AgentInterruptService` with checkpoint/base-version state, so generic runtime resume also requires `checkpoint_ref`, `base_version`, `idempotency_key` and an allowed user-confirmation action before graph continuation; resume control fields are not copied into sanitized run metadata.
- Polish question concrete runtime now opens checkpoint-bound HITL interrupts from refs-only `formal_write_attempt_ref`, `asset_conflict_ref`, `low_confidence_formal_update_ref`, `ambiguous_ownership_ref` and `validation_failed_partial_result_ref` metadata. Dedicated Question runtime resume validates checkpoint ref / base version / idempotency / allowed HITL action through `AgentInterruptService`, returns the same candidate-only refs, and keeps `formal_refs=()`.

## Validation

- Red: `test_facade_replay_agent_run_is_read_only_and_formal_write_blocked` initially failed because facade replay did not exist.
- Red: `test_hitl_interrupt_matrix_requires_checkpoint_refs_and_sanitizes_payloads` initially failed because P8 HITL trigger definitions did not exist.
- Red: `test_hitl_resume_validates_checkpoint_ref_base_version_and_allowed_action` initially failed because resume did not validate checkpoint refs for HITL interrupts.
- Red: `test_pr6_asset_conflict_opens_checkpoint_bound_hitl_interrupt_without_formal_refs` initially failed because the Feedback in-memory runner did not accept an `AgentInterruptService` or emit HITL interrupts from graph metadata.
- Red: `test_pr6_asset_conflict_resume_validates_checkpoint_version_and_action_at_runner_boundary` initially failed because `InMemoryLangGraphRuntime.resume()` accepted the service-created HITL interrupt without runner-bound checkpoint / version / action validation.
- Red: `test_pr6_remaining_hitl_triggers_open_checkpoint_bound_interrupts_and_resume` initially failed because `low_confidence_formal_update_ref` did not populate `trace_refs.low_confidence_refs` / drawer `low_confidence_flags`.
- Red: `test_facade_resume_injects_checkpoint_control_fields_and_shared_loop_policy` initially failed because facade resume did not accept `checkpoint_ref`.
- Red: `test_facade_resume_fails_closed_for_unsupported_action_before_runner_call` initially failed because facade resume did not validate allowed actions before invoking the runner.
- Red: `test_facade_resume_requires_strict_base_version_before_runner_call` initially failed because facade resume accepted `bool` as `base_version`.
- Red: `test_facade_resume_blocks_runtime_formal_refs_through_agent_executor_boundary` initially failed because facade resume called the runner directly and hid returned runtime `formal_refs`.
- Red: `test_facade_replay_fails_closed_when_descriptor_does_not_support_replay_before_runner_call` and `test_facade_resume_fails_closed_when_descriptor_does_not_support_resume_before_runner_call` initially failed because facade resume/replay could invoke the runner even when the descriptor did not support that entrypoint.
- Red: `test_pr4_in_memory_runtime_resume_requires_checkpoint_version_and_allowed_action` initially failed because generic in-memory resume accepted missing checkpoint/base/action controls without service-backed validation.
- Red: `test_pr4_in_memory_runtime_start_resume_and_timeline_are_sanitized` initially failed after adding schema-bound resume controls because generic runtime copied control fields into `run_resumed` metadata instead of keeping only sanitized action metadata and refs.
- Red: `test_polish_question_runtime_formal_write_attempt_uses_checkpoint_bound_hitl_resume` initially failed because Polish question concrete runtime reported `formal_write_attempt_ref` as a succeeded candidate path with no interrupt refs.
- Red: `test_pr4_in_memory_runtime_replay_preserves_failure_status_and_trace_comparison` initially failed because concrete replay returned generic `replayed` and had no replay metadata for original failure status or trace comparison.
- Red: `test_graph_runner_adapter_preserves_replay_failure_status_and_trace_comparison` initially failed because `AgentReplayResult` did not accept metadata and the adapter dropped replay failure/trace-comparison fields.
- Red: `test_graph_runner_adapter_rejects_replay_with_provider_or_repository_side_effects` and `test_facade_replay_agent_run_rejects_provider_tool_or_repository_side_effects` initially failed because replay side-effect counters were passed through instead of failing closed.
- Green:
  - `tests/api/test_agent_interrupt_replay.py` = `6 passed`
  - `tests/api/test_agent_fake_runtime.py` = `14 passed`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py` = `7 passed`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py` = `11 passed`
  - `tests/api/test_ai_orchestration_facade.py -k "unsupported_replay or unsupported_resume or descriptor_does_not_support"` = `2 passed, 23 deselected in 0.19s`
  - `tests/api/test_ai_orchestration_facade.py` = `25 passed in 0.24s`
  - replay failure-status / trace-comparison focused tests = `2 passed in 0.53s`
  - replay side-effect fail-closed focused tests = `2 passed in 0.20s`
  - impacted runtime / replay / resume regression = `43 passed in 1.93s`
  - `tests/api/test_agent_interrupt_replay.py` included in `tests/api/test_agent*` = pass
  - `tests/api/test_agent_replay_resume_policy.py` included in `tests/api/test_agent*` = pass

## Deferred Gap

- P8 HITL trigger types and checkpoint-bound resume validation are implemented at the interrupt service boundary. Facade resume now requires checkpoint / strict base version / idempotency control fields, validates allowed actions before runner invocation, rejects descriptor-unsupported `resume` before runner invocation, and blocks returned runtime formal refs through the AgentExecutor adapter boundary. Facade replay rejects descriptor-unsupported `replay` before runner invocation. Generic in-memory runtime user-confirmation resume, Polish question concrete HITL resume, and Feedback in-memory five-trigger HITL resume now use service-backed checkpoint / base version / idempotency / action validation before graph continuation. Replay now preserves original failure/interruption status metadata and trace-comparison refs for the covered generic/Question runtime replay paths. Remaining product-level runtime wiring and concrete graph paths outside these covered facade/generic/Question/Feedback paths remain deferred, so this still does not close full RTE-003.
