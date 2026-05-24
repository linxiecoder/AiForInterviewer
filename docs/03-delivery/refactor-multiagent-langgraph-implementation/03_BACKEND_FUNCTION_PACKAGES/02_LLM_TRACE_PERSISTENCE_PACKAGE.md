---
title: LLM Trace Persistence Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / 数据架构 / 安全隐私
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/llm-trace-persistence-package
---

# LLM Trace Persistence Package

## 1. Package 目标

本 package 冻结 PR2 / PR4 相关的 AI Runtime data model、repository、LLM trace、payload capture、retention、redaction 和 backend tests。PR2 只能实现本 package 中属于 exact scope lock 的 inert model / repository / tests。

## 2. Runtime tables

| Table | Category | Purpose | PR2 status |
|---|---|---|---|
| `agent_runs` | AI Runtime Tables | graph run lifecycle, task link, thread ref, idempotency | allowed in PR2 |
| `agent_node_runs` | AI Runtime Tables | node lifecycle, attempts, side-effect keys, LLM refs | allowed in PR2 |
| `agent_interrupts` | AI Runtime Tables | human interrupt and resume state | allowed in PR2 |
| `agent_checkpoint_refs` | AI Runtime Tables | checkpoint reference metadata only | allowed in PR2 |
| `llm_calls` | AI Runtime Tables | sanitized LLM call summary | allowed in PR2 |
| `llm_call_payloads` | AI Runtime Tables | sanitized payload summary or debug raw ref under strict gate | allowed in PR2 with raw default-off |

## 3. Field-level plan

### 3.1 Shared fields

All six tables must preserve `OwnedRecordMixin` semantics unless implementation proves a smaller equivalent is needed.

| Field | Type | Rule |
|---|---|---|
| `id` | `String(80)` | primary key, generated with table-specific prefix |
| `owner_id` | `String(80)` | required for every query and write |
| `actor_id` | `String(80)` | triggering actor or service actor summary |
| `record_version` | `Integer` | optimistic locking for resume/finalization |
| `status` | `String(64)` | table-specific enum |
| `created_at` / `updated_at` | `DateTime(timezone=True)` | lifecycle sorting and retention |
| `trace_ref_ids` / `evidence_ref_ids` | `JSON` | refs only, no raw payload |

### 3.2 Table-specific fields

| Table | Required fields | Index / unique requirements | API visibility |
|---|---|---|---|
| `agent_runs` | `ai_task_id`, `graph_name`, `graph_version`, `entrypoint_name`, `thread_id`, `idempotency_key_hash`, `input_refs_json`, `output_refs_json`, `pending_writes_json`, `error_summary_json`, `started_at`, `completed_at`, `interrupted_at` | indexes on owner/task/status/graph/thread; unique `(owner_id, thread_id)` and `(owner_id, graph_name, idempotency_key_hash)` | sanitized run id, graph name, status, timings, refs |
| `agent_node_runs` | `agent_run_id`, `graph_name`, `node_name`, `node_version`, `attempt_number`, `llm_call_ids_json`, `side_effect_keys_json`, `input_digest`, `output_digest`, `validation_summary_json`, `started_at`, `completed_at` | indexes on owner/run/node/status; unique `(owner_id, agent_run_id, node_name, attempt_number)` | sanitized timeline node event |
| `agent_interrupts` | `agent_run_id`, `agent_node_run_id`, `node_name`, `interrupt_type`, `resume_schema_id`, `prompt_summary_json`, `resume_payload_summary_json`, `expires_at`, `resumed_at`, `idempotency_key_hash` | indexes on owner/run/node/expires; unique `(owner_id, id, idempotency_key_hash)` when key exists | sanitized interrupt summary |
| `agent_checkpoint_refs` | `agent_run_id`, `agent_node_run_id`, `graph_name`, `node_name`, `checkpoint_namespace`, `thread_id`, `checkpoint_id`, `checkpoint_metadata_json`, `retention_expires_at` | indexes on owner/run/thread/retention; unique `(owner_id, checkpoint_namespace, thread_id, checkpoint_id)` | checkpoint ref only, never payload |
| `llm_calls` | `ai_task_id`, `agent_run_id`, `agent_node_run_id`, `graph_name`, `node_name`, `contract_ids_json`, `configured_model`, `provider_model`, `prompt_version`, `schema_id`, `request_hash`, `response_hash`, `evidence_hash`, `usage_json`, `fallback_reason`, `validation_errors_json`, `low_confidence_flags_json`, `error_summary_json`, `started_at`, `completed_at` | indexes on owner/task/run/status/model; no extra unique in PR2 | sanitized LLM summary and hashes |
| `llm_call_payloads` | `llm_call_id`, `payload_kind`, `capture_policy_version`, `sanitized`, `raw_enabled`, `payload_summary_json`, `payload_hash`, `raw_payload_ciphertext_ref`, `encryption_key_ref`, `retention_expires_at`, `access_audit_ref_id` | indexes on owner/call/kind/retention/raw; unique `(owner_id, llm_call_id, payload_kind)` | not directly visible; summary API never returns raw refs |

## 4. Status enums

| Table | Allowed status values |
|---|---|
| `agent_runs` | `queued`, `running`, `interrupted`, `succeeded`, `failed`, `cancelled`, `timed_out`, `replayed_debug` |
| `agent_node_runs` | `pending`, `running`, `interrupted`, `succeeded`, `failed`, `skipped`, `replayed_debug` |
| `agent_interrupts` | `open`, `resumed`, `cancelled`, `expired`, `failed` |
| `agent_checkpoint_refs` | `created`, `superseded`, `expired`, `restore_failed` |
| `llm_calls` | `planned`, `running`, `succeeded`, `failed`, `validation_failed`, `replay_reused`, `replay_blocked` |
| `llm_call_payloads` | `captured`, `redacted`, `expired`, `access_denied`, `deleted` |

## 5. Repository method plan

| Repository | Methods | Contract |
|---|---|---|
| `AgentRunRepository` | `create_run`, `get_run_for_owner`, `get_by_ai_task`, `mark_running`, `mark_interrupted`, `mark_succeeded`, `mark_failed`, `list_timeline_runs`, `cleanup_expired_runs` | owner scoped; state transitions validate `record_version` |
| `AgentNodeRunRepository` | `start_node`, `finish_node`, `fail_node`, `append_llm_call_ref`, `record_side_effect_key`, `list_by_run` | side-effect key duplicates return existing ref |
| `AgentInterruptRepository` | `create_interrupt`, `get_open_interrupt_for_owner`, `resume_interrupt_once`, `expire_interrupts` | resume requires owner, base version and idempotency hash |
| `AgentCheckpointRefRepository` | `record_checkpoint_ref`, `list_refs_by_run`, `get_latest_ref`, `expire_refs` | refs and metadata only; no checkpoint payload read as business result |
| `LlmCallRepository` | `create_planned_call`, `mark_running`, `mark_succeeded`, `mark_failed`, `mark_replay_reused`, `get_summary_for_owner`, `list_by_run` | returns sanitized model/usage/hash/validation/fallback summary only |
| `LlmCallPayloadRepository` | `capture_sanitized_summary`, `capture_debug_raw_ref`, `expire_payloads`, `audit_payload_access` | raw requires feature flag, encryption, TTL and audit; production summary never reads raw |
| `AgentSideEffectRepository` | `persist_question_once`, `persist_feedback_once`, `persist_report_once`, `persist_candidate_once`, `record_pending_write`, `finalize_pending_write`, `mark_pending_write_failed` | deterministic side-effect keys prevent duplicate formal writes |

## 6. LLM Trace implementation plan

| Symbol | Type | Inputs | Outputs | Side effects | Tests |
|---|---|---|---|---|---|
| `LlmTraceContext` | dataclass / DTO | owner, task, run, node, contract ids, replay mode | context object | none | missing owner blocks capture |
| `LlmPayloadCapturePolicy.resolve` | method | settings, context, environment | capture policy | audit when raw enabled | raw default false |
| `PersistedLlmTransport.generate` | method | `LlmTransportRequest`, trace context | structured response | write `llm_calls` lifecycle and sanitized summary | provider failure sanitized |
| `capture_payload` | method | request, response, error, policy | payload refs | write payload rows | forbidden markers absent |
| `get_llm_call_summary` | method | owner, llm_call_id | sanitized summary | read only and audit denied access | no prompt/completion/provider body |

## 7. Replay / resume policy

| Mode | Rule |
|---|---|
| production resume | reuse existing sanitized LLM result summary, `output_refs_json` and Core Business Tables; if source/version/hash/checkpoint mismatch, fail closed |
| debug replay | dev/test only, read-only by default, no formal business write, fake transport unless explicitly authorized |
| side-effect replay | use deterministic side-effect keys; duplicate returns existing business ref; pending write without proof must fail closed |

## 8. Retention / security rules

| Object | Cleanup |
|---|---|
| `agent_runs` / `agent_node_runs` / `agent_interrupts` | keep minimal status/hash/timing summary or delete non-essential timeline after retention |
| `agent_checkpoint_refs` | expire refs after checkpoint store cleanup |
| `llm_calls` | retain sanitized summary, hash, model, usage, validation/fallback |
| `llm_call_payloads` sanitized | delete or expire summary while retaining hash if needed for audit |
| `llm_call_payloads` debug raw refs | short TTL only; delete encrypted raw object ref and mark expired |
| `pending_writes_json` | compress to finalized refs after success; short TTL after failure |

## 9. PR2 tests

| Test file | Required assertions |
|---|---|
| `tests/api/test_model_imports.py` | imports runtime model module and table metadata without LangGraph imports |
| `tests/api/test_db_schema_bootstrap.py` | SQLAlchemy bootstrap creates runtime tables |
| `tests/api/test_agent_run_repository.py` | timeline sorted, owner isolation, interrupts recorded, no checkpoint payload |
| `tests/api/test_agent_interrupt_repository.py` | resume once, stale version conflict, owner isolation |
| `tests/api/test_llm_call_repository.py` | summary saved without raw prompt/completion/provider payload; retention/owner scope |
| `tests/api/test_sensitive_payload_redaction.py` | forbidden markers never reach summary/API-like DTO |
| `tests/api/test_agent_side_effect_idempotency.py` | same side-effect key reuses existing ref; different body conflicts |
| `tests/api/test_agent_replay_resume_policy.py` | production resume reuses existing sanitized result; debug replay does not write formal object |
| `tests/api/test_architecture_boundaries.py` | runtime models/repositories do not import LangGraph; Core does not import runtime internals |

## 10. Forbidden in PR2

本 package 不授权 PR2 新增 facade、runner、adapter、graph、checkpointer、serializer、runtime flags、real provider calls、frontend files、dependencies、migrations 或 business graph code。
