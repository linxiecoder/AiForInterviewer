---
title: P9_EVAL_REPORT
type: goal-evidence
status: eval_gate_passed
permalink: ai-for-interviewer/docs/goals/2026-06-06/p9-eval-report
---

# P9 Eval Gate Report

## Run Metadata

- Suite: `phase9`
- Mode: `replay`
- Commit SHA: `f86adea`
- Runner version: `phase9.eval_gate.v1`
- Grader versions: `code_rules.v2`
- Generated at UTC: `2026-06-06T09:40:10Z`

## Summary

| Metric | Count |
|---|---:|
| `total_cases` | 30 |
| `passed` | 30 |
| `failed` | 0 |
| `skipped` | 0 |
| `deferred` | 2 |
| `blocking_failures` | 0 |

## Dataset Digests

| Dataset | Digest |
|---|---|
| `canonical_evidence` | `sha256:ff7f2a28bfb545609fe85fe8998075cee721931137b0ac09a209ce84f0b3bd4f` |
| `fake_gate` | `sha256:b24d8315033b106d8713800e4b0a05016d84c787b892a09c4685a316be274103` |
| `feedback_agent` | `sha256:d926c533a4bc0b08f165046b930fd894d4a3589588809518918f2a085b5e2b3f` |
| `handoff_trace` | `sha256:8daf8c156bd4956988a2459cccaccf9adb662d1eae5cc9450d7230984f0322b6` |
| `provider_boundary` | `sha256:724d0db109ee98dd7b78498ca0a66ef95cf80b110392818a63dce7b99a614369` |
| `question_agent` | `sha256:e4d80be3be81a87a3dff4ae86b716614c7c265f5aea7a05bfa0c475352fad5fd` |
| `runtime_foundation_contract` | `sha256:92bebe4d39d4840abb9b845796b9408e599d34fdcf03f0d9c88ff0c6d1c7546d` |

## Capability Coverage

| Capability | Status | Cases | Blocking Failures |
|---|---|---|---|
| `AGT-006` | `passed` | `p9_agt_question_candidate_refs_only`, `p9_agt_feedback_candidate_refs_only`, `p9_agt_asset_update_candidate_handoff_confirmation`, `p9_agt_trace_validation_handoff_refs_required` | - |
| `AGT-007` | `passed` | `p9_agt_question_candidate_refs_only`, `p9_agt_feedback_candidate_refs_only`, `p9_agt_asset_update_candidate_handoff_confirmation`, `p9_agt_trace_validation_handoff_refs_required` | - |
| `CTX-001` | `passed` | `p9_ctx_direct_project_evidence_grounded`, `p9_ctx_adjacent_project_hypothetical`, `p9_ctx_job_gap_only_no_fact_claim`, `p9_ctx_insufficient_context_deferred` | - |
| `CTX-002` | `passed` | `p9_ctx_direct_project_evidence_grounded`, `p9_ctx_adjacent_project_hypothetical`, `p9_ctx_job_gap_only_no_fact_claim`, `p9_ctx_insufficient_context_deferred` | - |
| `CTX-003` | `passed` | `p9_ctx_direct_project_evidence_grounded`, `p9_ctx_adjacent_project_hypothetical`, `p9_ctx_job_gap_only_no_fact_claim`, `p9_ctx_insufficient_context_deferred` | - |
| `FAG-006` | `passed` | `p9_fag_asset_conflict_blocks_generate_next_question`, `p9_fag_asset_candidate_requires_confirmation`, `p9_fag_answer_coverage_missing_points`, `p9_fag_same_question_change_regression`, `p9_fag_provider_unavailable_not_success`, `p9_fag_validation_failed_not_success` | - |
| `FAG-007` | `passed` | `p9_fag_asset_conflict_blocks_generate_next_question`, `p9_fag_asset_candidate_requires_confirmation`, `p9_fag_answer_coverage_missing_points`, `p9_fag_same_question_change_regression`, `p9_fag_provider_unavailable_not_success`, `p9_fag_validation_failed_not_success` | - |
| `FAG-008` | `passed` | `p9_fag_asset_conflict_blocks_generate_next_question`, `p9_fag_asset_candidate_requires_confirmation`, `p9_fag_answer_coverage_missing_points`, `p9_fag_same_question_change_regression`, `p9_fag_provider_unavailable_not_success`, `p9_fag_validation_failed_not_success` | - |
| `FAKE-001` | `passed` | `p9_fake_fixture_mode_trace_visible`, `p9_fake_replay_only_non_claim`, `p9_fake_runtime_env_rejected_as_regression_evidence`, `p9_fake_not_real_provider_quality` | - |
| `L5-001` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `PRO-001` | `passed` | `p9_pro_forbidden_provider_keys_rejected`, `p9_pro_forbidden_keys_absent_from_report_payload`, `p9_pro_no_full_prompt_asset_fallback`, `p9_pro_fail_closed_validation_error_refs` | - |
| `PRO-002` | `passed` | `p9_pro_forbidden_provider_keys_rejected`, `p9_pro_forbidden_keys_absent_from_report_payload`, `p9_pro_no_full_prompt_asset_fallback`, `p9_pro_fail_closed_validation_error_refs` | - |
| `QAG-004` | `passed` | `p9_qag_grounding_blocked_no_formal_question`, `p9_qag_follow_up_anti_repetition`, `p9_qag_deterministic_fallback_candidate_not_success`, `p9_qag_question_candidate_trace_validation_refs` | - |
| `QAG-006` | `passed` | `p9_qag_grounding_blocked_no_formal_question`, `p9_qag_follow_up_anti_repetition`, `p9_qag_deterministic_fallback_candidate_not_success`, `p9_qag_question_candidate_trace_validation_refs` | - |
| `QAG-007` | `passed` | `p9_qag_grounding_blocked_no_formal_question`, `p9_qag_follow_up_anti_repetition`, `p9_qag_deterministic_fallback_candidate_not_success`, `p9_qag_question_candidate_trace_validation_refs` | - |
| `RTE-001` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `RTE-002` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `RTE-003` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `RTE-004` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `RTE-005` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `RTE-006` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |
| `RTE-007` | `passed` | `p9_rte_replay_read_only_existing_surface`, `p9_rte_runtime_loop_policy_existing_surface`, `p9_rte_trace_timeline_refs_existing_surface`, `p9_rte_future_runtime_surface_deferred` | - |

## Blocking Failures

No blocking failures.

## Deferred Cases

| Dataset | Case | Owner Phase | Reason |
|---|---|---|---|
| `canonical_evidence` | `p9_ctx_insufficient_context_deferred` | `P8_follow_up_or_later` | Current context is insufficient for a grounded eval case. |
| `runtime_foundation_contract` | `p9_rte_future_runtime_surface_deferred` | `P8_follow_up` | Future/product runtime surfaces remain outside Phase 9 eval implementation scope. |

## Security Scan

- JSON and Markdown reports were scanned before write.
- Forbidden report key findings: none.
- Forbidden report value findings: none.
- Raw payload stored: false.

## CI Gate

- Default mode is replay / fixture and does not require live provider credentials.
- `LLM_PROVIDER` visible to this run: `False`

## Non-Claims

- `replay_mode_is_not_real_provider_quality_evidence`
- `fake_visible_eval_is_not_production_provider_quality_evidence`
- `phase9_is_l5_foundation_regression_evidence_only_not_l5_release`
- `phase8_runtime_gaps_remain_deferred`
