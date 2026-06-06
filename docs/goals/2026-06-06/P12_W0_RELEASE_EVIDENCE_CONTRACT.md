---
title: P12_W0_RELEASE_EVIDENCE_CONTRACT
type: evidence-contract
status: release_gate_scope_locked_with_deferred_implementation
permalink: ai-for-interviewer/docs/goals/2026-06-06/p12-w0-release-evidence-contract
---

# P12-W0 Release Evidence Contract

Window ID: `P12-W0-RELEASE-GATE-SCOPE-LOCK`

## 1. Purpose

This document defines the evidence contract required before Phase 12 can make any release-gate claim.

P12-W0 defines the required evidence shape only. It does not implement eval datasets, graders, replay fixtures, runner behavior, CI behavior, trace emitters or release automation.

## 2. Eval Evidence Contract

A Phase 12 eval gate must provide a machine-readable multi-agent suite manifest with these fields:

| Field | Requirement |
| --- | --- |
| `suite_id` | stable Phase 12 suite ID |
| `manifest_version` | schema version for the suite contract |
| `capability_ids` | includes `L5-006` and any covered `L5-*`, `RTE-*`, `EVAL-*`, `PRO-*`, `FAKE-*`, `SRC-*`, `WIN-*` IDs |
| `case_ids` | stable case IDs for every dataset row |
| `input_refs` | refs-only input identifiers, never raw prompt / provider / resume / JD / asset body payloads |
| `expected_candidate_refs` | expected candidate refs for candidate-only outputs |
| `expected_handoff_refs` | expected typed handoff refs between agents |
| `expected_validation_refs` | validation refs required per case |
| `expected_HITL_refs` | interrupt / confirmation / review refs for HITL cases |
| `expected_failure_mode` | expected failure, blocked, interrupted, deferred or non-claim behavior |
| `expected_non_claims` | case-level non-claims, especially fake/replay/provider/release boundaries |
| `grader_refs` | deterministic grader IDs and versions |
| `minimum_pass_criteria` | blocking failure threshold, invalid case threshold and required negative-control behavior |

Required case coverage:

- happy path candidate product slice.
- insufficient context.
- asset conflict.
- formal write requested.
- low confidence.
- provider failure.
- validation failure.
- cross-agent handoff failure.
- replay mismatch.
- forbidden data.
- fake/replay non-claim.
- release non-claim.

Eval minimum gate:

- all blocking cases pass.
- invalid cases are zero.
- negative-control proves the gate can fail.
- deferred/non-blocking cases are explicit and cannot be counted as release evidence.
- fake-only, replay-only and unit-test-only evidence is labeled as non-release evidence.

## 3. Replay Evidence Contract

A Phase 12 replay gate must provide replay fixtures and replay reports with these required fields:

| Field | Requirement |
| --- | --- |
| `replay_fixture_refs` | stable fixture IDs |
| `checkpoint_refs` | checkpoint refs used by replay |
| `read_only` | must be `true` |
| `formal_write_blocked` | must be `true` |
| `provider_call_count` | must be `0` |
| `tool_call_count` | must be `0` unless separately declared as read-only deterministic local replay tooling |
| `repository_write_count` | must be `0` |
| `db_write_count` | must be `0` |
| `formal_write_count` | must be `0` |
| `trace_comparison` | expected vs actual refs-only trace comparison |
| `candidate_refs_preserved` | candidate refs must be preserved or mismatch must block |
| `validation_refs_preserved` | validation refs must be preserved or mismatch must block |
| `handoff_refs_preserved` | handoff refs must be preserved or mismatch must block |

Replay closure conditions:

- replay mismatch is a blocking failure unless explicitly marked non-blocking by Controller.
- replay reports include failure / fallback reasons where present.
- replay cannot be represented as real-provider quality evidence.

## 4. CI Evidence Contract

A Phase 12 CI gate must define:

| Field | Requirement |
| --- | --- |
| `ci_workflow_name` | explicit workflow name |
| `command_list` | exact commands and environment variables |
| `report_artifact_name` | uploaded artifact name |
| `artifact_retention_expectation` | retention expectation or platform default with citation |
| `blocking_failure_behavior` | blocking failures make the gate fail |
| `negative_control_behavior` | negative-control must observe expected failure |
| `default_live_provider_credentials_required` | must be `false` for default gate |
| `optional_real_provider_advisory_mode` | explicit, non-default and non-blocking unless separately authorized |

Remote CI success can be claimed only when a visible passing CI run and uploaded artifact are cited. A workflow file alone is not remote CI success evidence.

## 5. Observability Evidence Contract

A Phase 12 trace / observability report must provide a refs-only schema with:

- `trace_report_schema`
- `agent_id`
- `run_id`
- `plan_refs`
- `skill_refs`
- `tool_refs`
- `policy_refs`
- `candidate_refs`
- `handoff_refs`
- `validation_refs`
- `HITL_refs`
- `failure_reason`
- `fallback_reason`
- `forbidden_data_scan_result`

Forbidden data scan must cover:

- raw prompt and prompt body.
- provider payload and raw completion.
- full resume, full JD and full answer.
- full asset body.
- secrets, tokens, cookies and API keys.

## 6. Release Decision Evidence Contract

A release decision package must include:

| Field | Requirement |
| --- | --- |
| `human_controller_release_decision` | explicit approve / reject / defer decision |
| `accepted_risk_list` | risks accepted by Controller/user |
| `deferred_gaps_list` | gaps carried after release decision |
| `rollback_plan` | rollback trigger, owner and procedure |
| `release_version_or_tag_ref` | version, tag or explicit no-tag reason |
| `date_actor` | date and actor/controller |
| `evidence_links` | links to eval, replay, CI, observability and source-backfill evidence |
| `non_claims` | remaining non-claims after decision |

No release decision is valid without human/controller decision evidence.

## 7. Forbidden Data Rules

Phase 12 evidence must not store or publish:

- `raw_prompt`
- `system_prompt`
- `developer_prompt`
- `provider_payload`
- `raw_provider_payload`
- `raw_completion`
- `full_resume`
- `full_jd`
- `full_answer`
- `full_asset_body`
- `token`
- `secret`
- `cookie`
- `api_key`

Evidence must use refs, digests, schema IDs and summaries instead of raw sensitive payloads.

## 8. Non-Claims

Until separately proven:

- Phase 12 release gate is not complete.
- L5 release is not claimed.
- Real-provider quality certification is not claimed.
- Remote CI success is not claimed without visible artifact evidence.
- Formal write completion is not claimed.
- `L5-006` is not implemented, validated or done.
- Fake-only, replay-only and unit-test-only evidence are regression evidence only.

## 9. Closure Criteria

Phase 12 release gate can be considered for closure only if all of these are true:

1. Phase 11 closeout is accepted.
2. `L5-006` implementation is separately scoped and implemented.
3. Multi-agent eval suite exists.
4. Multi-agent replay fixtures exist.
5. Failure-mode cases exist.
6. CI gate runs and records an artifact.
7. Blocking failures fail the gate.
8. Negative-control proves the gate can fail.
9. Trace / observability report is generated.
10. Report output is scanned for forbidden data.
11. Fake/replay evidence is not represented as real-provider quality.
12. Real-provider quality, if claimed, has separately scoped evidence.
13. Formal writes remain blocked unless formal release scope explicitly authorizes and proves Application Service -> Domain Policy -> Handoff.
14. Human/controller release decision is recorded.
15. Rollback policy is documented.
16. L5 release is not claimed until all required evidence passes and Controller/user approves.

