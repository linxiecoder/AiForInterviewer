---
title: P8_W4_HANDOFF_TRACE_REPORT
type: goal-evidence
status: implemented_validated_with_deferred_end_to_end_handoff
owner: P8 Implementation Writer
permalink: ai-for-interviewer/docs/goals/2026-06-05/p8-w4-handoff-trace-report
---

# P8-W4 Handoff / Trace Report

Status: implemented_validated_with_deferred_end_to_end_handoff

## Scope

- Added typed handoff envelope and expanded trace DTO fields.
- Added typed Feedback runtime candidate payload evidence for the in-memory feedback path.
- Files changed:
  - `apps/api/app/application/agents/contracts/__init__.py`
  - `apps/api/app/application/agents/handoff/__init__.py`
  - `apps/api/app/application/agents/runtime/__init__.py`
  - `apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py`
  - `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py`
  - `tests/api/test_agent_contracts.py`
  - `tests/api/test_agent_fake_runtime.py`
  - `tests/api/test_agent_graph_runner.py`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py`

## What Changed

- Added `AgentHandoffEnvelope` with:
  - `candidate_ref`
  - `candidate_type`
  - `payload_schema_id`
  - `trace_refs`
  - `validation_refs`
  - `side_effect_key`
  - `idempotency_key`
  - optional refs-only asset update descriptor fields: `asset_update_candidate_ref`, `asset_body_ref`, `asset_schema_id`, `formal_write_blocked_until`, `user_confirmation_required`
- Expanded `AgentExecutionTrace` with:
  - `agent_version`
  - `ai_task_id`
  - `low_confidence_flags`
  - `failure_reason`
  - `fallback_reason`
- Trace and handoff metadata now recursively filter raw prompt / completion / provider payload / full asset body / full resume / secrets / tokens / cookies / API keys, including nested dict/list structures.
- Adapter traces now map graph version and AI task id.
- Adapter traces now map command metadata, runtime result metadata and candidate payloads into P8 trace categories:
  - `plan_refs`
  - `skill_refs`
  - `tool_refs`
  - `policy_refs`
  - `provider_refs`
  - `validation_refs`
  - `handoff_refs`
  - `low_confidence_flags`
  - `failure_reason`
  - `fallback_reason`
  - runtime event names from status / phase results / tool results
- Adapter execution results now expose mapped `handoff_refs` from the trace surface, and status snapshots expose handoff refs from status metadata / trace refs.
- Adapter execution results now expose refs-only `handoff_candidate_descriptors` from typed `AgentCandidatePayload` objects, without copying candidate payload bodies into handoff metadata.
- `build_agent_handoff_plan()` now creates a target `AgentExecutionPlan` from a source `AgentExecutionResult` and `HandoffContract`, using a schema-bound `AgentHandoffEnvelope`; the target plan receives only a `handoff_ref` input and refs-only metadata.
- `execute_agent_handoff()` now starts a target `AgentExecutor` from that typed handoff plan, keeping Agent A to Agent B candidate handoff inside the AgentExecutor / HandoffContract boundary without raw payload sharing or formal refs.
- Asset update handoff descriptors now carry refs-only `asset_body_ref` / `asset_schema_id`, confirmation and formal-write-blocked metadata; raw asset body and `formal_refs` remain excluded from handoff metadata.
- Handoff plan construction fails closed when the source candidate type or payload schema does not match the `HandoffContract`.
- Adapter timeline events now map command and event metadata into P8 trace categories, including command metadata `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_flags` and nested `handoff_envelope` refs on target executor commands; they split validation / handoff refs out of `output_refs` and expose event-level `candidate_refs`.
- Generic in-memory runtime start/resume/cancel timeline events, Feedback service-backed resume/cancel events and Polish question / Feedback concrete runtime start plus Polish question cancel timeline events now emit refs-only metadata for checkpoint / validation / candidate / interrupt / output refs where applicable, without raw payloads; generic direct `run_started`, `run_resumed` and `run_succeeded`, Feedback direct `run_started` and `run_succeeded`, and Question direct `run_started`, `interrupt_opened`, `run_resumed` and resumed `run_succeeded` timeline events now preserve the P8 command ref matrix where command metadata supplies it; follow-up Question cancel evidence separates checkpoint refs from validation refs in cancel metadata and timeline refs instead of treating validation refs as checkpoint refs.
- Feedback in-memory runtime status trace refs now include validation refs alongside checkpoint refs, and replay trace comparison covers both while resume/cancel control metadata remains checkpoint-only.
- Runtime DTOs now classify canonical status categories for run result/status/replay/task/interrupt refs and reject unknown status or success-like status carrying `failure_reason`; the adapter reuses this shared guard.
- Polish feedback in-memory runtime now emits a typed `AgentCandidatePayload` with:
  - `candidate_type=feedback_candidate`
  - `payload_schema_id=polish_feedback_candidate.v1`
  - `candidate_ref=feedback_candidate_ref_*`
  - validation refs and checkpoint-backed trace refs
  - `asset_update_candidate_refs=[asset_update_candidate_ref_*]` when refs-only asset update candidates are supplied
  - paired `asset_update_candidate` payloads with `user_confirmation_required=true` and `formal_write_blocked_until=user_confirmation`
  - no formal refs / no asset formal write

## Validation

- Red: typed handoff / trace test initially failed because `AgentHandoffEnvelope` did not exist.
- Red: adapter trace test initially failed because graph version and AI task id were not mapped.
- Red: `test_graph_runner_adapter_populates_phase8_trace_refs_from_runtime_result` initially failed because adapter traces did not populate validation / handoff / tool / policy / provider / low-confidence / failure / fallback refs from runtime metadata.
- Red: `test_graph_runner_adapter_populates_phase8_trace_refs_from_runtime_result` then failed because `AgentExecutionResult.handoff_refs` did not expose mapped handoff refs.
- Red: `test_pr4_in_memory_runtime_resume_timeline_preserves_p8_ref_matrix_from_command_metadata` failed with `KeyError: 'plan_refs'` because generic direct resume/succeeded timeline events did not preserve the P8 command ref matrix.
- Red: `test_pr6_feedback_start_timeline_preserves_p8_ref_matrix_from_command_metadata` failed with `RuntimeValidationError: PR6 fake runtime metadata accepts refs and digests only` because Feedback direct runtime start passed P8 command trace metadata into the PR6 payload validator instead of separating it for timeline propagation.
- Red: `test_question_runtime_start_resume_timeline_preserves_p8_ref_matrix_from_command_metadata` failed with `KeyError: 'plan_refs'` because Question direct runtime start/interrupted/resume/succeeded timeline events did not preserve the P8 command ref matrix.
- Red: `test_graph_runner_adapter_exposes_handoff_refs_on_status_snapshot` initially failed because `AgentExecutionStatus.handoff_refs` did not expose status metadata / trace handoff refs.
- Red: `test_agent_executor_handoff_plan_routes_candidate_to_target_executor_without_raw_payload` initially failed because `build_agent_handoff_plan()` did not exist and adapter results did not expose schema-bound handoff candidate descriptors.
- Red: `test_runtime_status_taxonomy_is_enforced_by_runtime_dtos` initially failed because `classify_agent_runtime_status` did not exist.
- Red: `test_graph_runner_adapter_maps_phase8_trace_refs_from_timeline_event_metadata` initially failed because timeline event mapping treated validation / handoff refs as output refs and did not merge event metadata `plan_refs`, `skill_refs`, `validation_refs`, `handoff_refs`, `candidate_refs` or `output_refs`.
- Red: `test_graph_runner_adapter_populates_phase8_trace_refs_from_runtime_result` and `test_graph_runner_adapter_maps_phase8_trace_refs_from_timeline_event_metadata` later failed because command metadata `tool_refs` were not merged into result trace / timeline trace `tool_refs`.
- Red: the same focused trace refs tests then failed because command metadata `policy_refs` / `provider_refs` were not merged into result trace / timeline trace `policy_refs` / `provider_refs`.
- Red: the same focused trace refs tests then failed because command metadata `validation_refs` / `handoff_refs` / `low_confidence_flags` were not merged into result trace / timeline trace refs and low-confidence flags.
- Red: `test_pr6_enabled_in_memory_integration_returns_refs_only_sanitized_schema` initially failed because Polish feedback in-memory runtime returned no typed candidate payload and used generic `candidate_ref_*`.
- Red: the same PR6 integration test then failed because the Feedback in-memory runtime did not emit a typed `asset_update_candidate` payload for refs-only asset update candidates.
- Red: `test_in_memory_runtime_polish_question_timeline_is_sanitized` initially failed because the Polish question concrete runtime `validation_recorded` event did not carry `validation_refs` metadata.
- Red: `test_pr6_asset_conflict_opens_checkpoint_bound_hitl_interrupt_without_formal_refs` initially failed because the Feedback concrete runtime `checkpoint_recorded` event did not carry `checkpoint_refs` metadata.
- Red: `test_pr4_in_memory_runtime_start_resume_and_timeline_are_sanitized` initially failed because the generic in-memory runtime `checkpoint_recorded` event did not carry `checkpoint_refs` metadata.
- Red: `test_pr6_asset_conflict_resume_validates_checkpoint_version_and_action_at_runner_boundary` then failed because `run_resumed` did not carry `interrupt_refs` / `checkpoint_refs` metadata.
- Red: `test_agent_executor_handoff_plan_routes_candidate_to_target_executor_without_raw_payload` later failed because target executor timeline events did not expose command `handoff_envelope` candidate / validation / handoff refs.
- Red: `test_agent_executor_asset_update_handoff_carries_body_ref_without_raw_asset_body` failed because adapter handoff candidate descriptors did not surface `asset_update_candidate_ref` / `asset_body_ref` / asset confirmation metadata.
- Red: `test_pr6_feedback_cancel_timeline_retains_candidate_and_validation_refs` failed because Feedback cancel timeline metadata mixed generic result output refs into `candidate_refs` and did not carry missing `validation_refs`.
- Red: `test_typed_handoff_envelope_and_trace_keep_phase8_refs_without_raw_metadata` failed when nested `raw_prompt`, `api_key`, `full_asset_body`, `provider_payload` and `full_resume` keys were left inside handoff / trace metadata structures.
- Red: `test_pr6_replay_is_read_only_and_does_not_mutate_checkpoint_or_timeline_refs` failed because Feedback status trace refs lacked validation refs, preventing replay trace comparison from covering validation refs.
- Red: `test_question_runtime_cancel_timeline_retains_separate_checkpoint_and_validation_refs` initially failed because Question cancel timeline metadata mixed validation refs into `checkpoint_refs` and did not expose separate `validation_refs`.
- Red: `test_execute_agent_handoff_starts_target_executor_with_typed_refs_only` failed because `execute_agent_handoff()` did not exist.
- Green:
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -k "execute_agent_handoff" -q` = `1 passed, 16 deselected in 0.09s`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py::test_pr6_replay_is_read_only_and_does_not_mutate_checkpoint_or_timeline_refs` = `1 passed`
  - `tests/api/test_polish_question_graph_integration.py -k "question_runtime_cancel_timeline"` = `1 passed, 12 deselected in 0.68s`
  - `tests/api/test_agent_contracts.py::test_typed_handoff_envelope_and_trace_keep_phase8_refs_without_raw_metadata` = `1 passed`
  - `tests/api/test_agent_contracts.py` = `15 passed`
  - `tests/api/test_agent_graph_runner.py::test_agent_executor_handoff_plan_routes_candidate_to_target_executor_without_raw_payload` = `1 passed`
  - `tests/api/test_agent_graph_runner.py::test_agent_executor_asset_update_handoff_carries_body_ref_without_raw_asset_body` = `1 passed`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py::test_pr6_feedback_cancel_timeline_retains_candidate_and_validation_refs` = `1 passed`
  - `tests/api/test_agent_contracts.py tests/api/test_agent_graph_runner.py` = `27 passed`
  - `tests/api/test_agent_fake_runtime.py` = `19 passed`
  - `tests/api/test_pr4_fake_runtime_replay_resume.py` = `5 passed`
  - `tests/api/test_pr6_polish_fake_runtime_integration.py` = `13 passed`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -k "phase8_trace_refs" -q` = `2 passed in 0.16s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -k "nested_runtime_trace_metadata_refs" -q` = `1 passed, 17 deselected in 0.20s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -k "formal_refs_from_runtime_metadata_surfaces" -q` = `1 passed, 18 deselected in 0.12s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -k "formal_write_counter_variants" -q` = `1 passed, 19 deselected in 0.14s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -k "repository_and_db_write_counters" -q` = `1 passed, 20 deselected in 0.13s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_agent_graph_runner.py -q` = `23 passed in 0.27s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_pr4_fake_runtime_replay_resume.py -k "resume_timeline_preserves_p8_ref_matrix" -q` = `1 passed, 10 deselected in 0.56s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_pr4_fake_runtime_replay_resume.py -q` = `11 passed in 0.52s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_pr6_polish_fake_runtime_integration.py -k "feedback_start_timeline_preserves_p8_ref_matrix" -q` = `1 passed, 15 deselected in 0.52s`
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_pr6_polish_fake_runtime_integration.py -q` = `16 passed in 0.69s`

## Deferred Gap

- Typed handoff is validated as a contract surface and as an AgentExecutor-bound foundation path: source `AgentExecutionResult` candidate descriptors can be converted into a target `AgentExecutionPlan` through `HandoffContract` / `AgentHandoffEnvelope` without raw payload sharing, and `execute_agent_handoff()` can start the target `AgentExecutor` from that typed handoff plan while preserving refs-only metadata; asset update descriptors now carry refs-only `asset_body_ref` / `asset_schema_id`, confirmation and formal-write-blocked metadata; trace and handoff DTO metadata recursively filters nested forbidden keys; and the target executor timeline can surface the command handoff envelope's candidate / validation / handoff refs without copying raw prompt, raw asset body or candidate payload body. Adapter-level traces and timeline events now carry the P8 ref matrix when the runner provides those refs, including command metadata and nested runtime `metadata.trace_refs` `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_refs` merged with runtime result / timeline event refs; adapter result/status/timeline surfaces now fail closed if runtime metadata exposes non-empty `formal_refs`, non-zero formal-write counters or non-zero repository / DB business write counters, including common `formal_write_count` / `formal_writes` and repository / DB counter variants; generic runtime start/resume/cancel events, Feedback service-backed resume/cancel events and Polish question / Feedback concrete runtime start plus Polish question cancel events now emit refs-only checkpoint / validation / candidate / interrupt / output metadata where applicable, and generic direct start/resume/succeeded, Feedback direct start/succeeded and Question direct start/interrupted/resume/succeeded timeline events now preserve P8 command refs without raw/provider/full payload leakage when supplied; Feedback status trace refs and replay comparison include validation refs; adapter result/status surfaces expose mapped handoff refs; and Feedback in-memory runtime now emits typed refs-only `feedback_candidate` and `asset_update_candidate` payloads. Product-level Supervisor / L5 orchestration, raw asset body transfer, formal asset composition/write semantics and proving complete trace population for remaining product/future runtime events remain deferred; this does not imply Phase 11 Supervisor / Orchestrator or L5 workflow completion.
