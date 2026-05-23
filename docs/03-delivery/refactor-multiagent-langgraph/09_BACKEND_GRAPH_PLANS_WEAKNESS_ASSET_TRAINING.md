---
title: 薄弱项、资产、训练闭环 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-weakness-asset-training
---

# 薄弱项、资产、训练闭环 LangGraph 实施计划

## 1. 文档目的

本文规划 `weakness_candidate_graph`、`asset_candidate_graph`、`training_suggestion_graph`、`candidate_confirmation_interrupt_graph` 的 implementation-ready graph spec，重点冻结 candidate schema、confirmation interrupt schema、formal write handoff、audit event mapping、duplicate/merge suggestion policy、rejection/skip behavior 和 candidate / suggestion / formal object 边界。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md`
- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md`
- `docs/02-design/prompt-contracts/TRAINING_CONTRACTS.md`
- 代码 recon：`apps/api/app/application/polish/candidates.py`、`candidate_llm.py`、`ports.py`、`tests/api/test_polish_candidates.py`

## 3. 当前状态

Active docs 已要求 candidate / suggestion 不能静默升级 formal object。正式 `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation`、`TrainingTask` 必须来自用户确认、用户编辑、合并确认或显式业务 API。当前 Polish candidate tests 已覆盖 candidate sanitizer、owner-scoped duplicate merge key、confirm formal refs、dismiss/merge/archive no formal write、confirm rollback、training recommendation without task、training task explicit action。

## 4. Candidate schema

| Field | Required | Rule |
|---|---|---|
| `candidate_id` | 是 | Stable `cand_*` / typed id; owner-scoped duplicate handling |
| `candidate_type` | 是 | `weakness_candidate`, `asset_candidate`, `training_suggestion_candidate`, `oral_script_candidate`, `polished_answer_candidate` or PR8 registered subtype |
| `status` | 是 | `candidate`, `needs_confirmation`, `merge_suggested`, `low_confidence`, `confirmed`, `dismissed`, `merged`, `archived`, `rejected`, `skipped` |
| `owner_id` | 是 | Not exposed cross-owner; every action verifies owner |
| `source_type` | 是 | `job_match`, `polish_feedback`, `report`, `mock_review`, `real_review`, `training_result` |
| `source_refs[]` | 是 | Authorized refs only; no raw source body |
| `evidence_refs[]` | 否 | Evidence refs or redacted summaries |
| `trace_refs[]` | 是 | Sanitized trace refs |
| `title`, `summary`, `evidence_excerpt` | 是 | Redacted display fields; no raw prompt/provider payload |
| `confidence_level` | 是 | `high`, `medium`, `low` |
| `merge_key` | 是 | Owner-scoped normalized duplicate key |
| `target_formal_ref` | 否 | Null until Core formal write command succeeds |
| `candidate_payload` | 是 | Safe subset; must include `formal_write_intent=false` until confirmation |
| `base_candidate_version_ref` | 是 | Required for confirmation/edit/merge to prevent stale write |

## 5. Confirmation interrupt schema

| Field | Required | Rule |
|---|---|---|
| `interrupt_id` | 是 | Runtime resume id; not business truth |
| `candidate_ref` | 是 | Candidate being reviewed |
| `candidate_type` | 是 | Drives validation and target command |
| `source_refs[]` | 是 | Displayable source refs only |
| `evidence_summary` | 是 | Redacted summary for drawer |
| `confidence_flags[]` | 否 | Low confidence / source unavailable flags |
| `allowed_actions[]` | 是 | `confirm`, `edit`, `merge`, `reject`, `skip`, `request_more_evidence` |
| `base_candidate_version_ref` | 是 | Stale action protection |
| `edited_payload_ref` | 否 | Required for edit; payload must pass candidate validator |
| `target_formal_ref` | 否 | Required for merge/update |
| `audit_event_ref` | 否 | Written after action is accepted |
| `formal_write_result_ref` | 否 | Set only after Core command commits |

Checkpoint may keep `interrupt_id`, candidate refs, version refs and redacted summaries. It must not keep raw payload, raw prompt, raw completion, provider payload or unredacted source text.

## 6. Graph 总览

| Graph | 目标 | State 字段 | Edge / conditional edge | Persistence targets | Trace policy | Tests |
|---|---|---|---|---|---|---|
| `weakness_candidate_graph` | 从 job match / polish / review 提炼薄弱项候选 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `source_refs`, `existing_weakness_refs`, `candidate_refs`, `merge_suggestion_refs`, `severity_refs`, `trace_refs`, `evidence_refs`, `error_state` | duplicate -> merge suggestion; evidence missing -> low confidence; confirm -> external Core command | weakness_candidates, merge suggestions, trace/evidence | source refs and validation summary only | no formal Weakness, merge conflict, low confidence |
| `asset_candidate_graph` | 提炼资产候选和版本建议 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `source_refs`, `existing_asset_refs`, `asset_candidate_refs`, `version_suggestion_refs`, `trace_refs`, `evidence_refs`, `error_state` | existing asset -> version suggestion; insufficient facts -> low confidence; confirm -> Core command | asset_candidates, quality hints, version suggestions, trace/evidence | sanitized source refs | no formal Asset/AssetVersion |
| `training_suggestion_graph` | 基于 confirmed weakness/assets 生成训练建议 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `confirmed_weakness_refs`, `asset_refs`, `score_trend_refs`, `training_candidate_refs`, `priority_refs`, `trace_refs`, `evidence_refs`, `error_state` | no confirmed weakness -> blocked/low confidence; user starts task -> explicit API | training recommendation candidates, priority ranking, trace/evidence | ranking summary only | no auto TrainingTask, confirmed weakness required |
| `candidate_confirmation_interrupt_graph` | 管理 confirmation interrupt/resume 与 formal write handoff | `owner_id`, `actor_id`, `agent_run_id`, `candidate_ref`, `candidate_type`, `source_refs`, `confirmation_action`, `edited_payload_ref`, `base_candidate_version_ref`, `audit_ref`, `rollback_ref`, `trace_refs`, `error_state` | confirm/edit/merge -> Core command; skip/reject -> no formal write; validation failed -> drawer error | user_confirmations, audit_events, formal via Core command only | confirmation graph default non-LLM | confirm once, skip no formal, audit required, rollback |

## 7. Node contract 表

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `weakness_candidate_graph` | `load_weakness_sources` | `CandidateExtractionInput`, `_base_source_refs`; PR8 source loaders | owner/source refs | compact sources | set source refs | read-only | `weakness_candidate:{owner_id}:{source_hash}:load` | none | source summary | no retry | source unavailable -> low confidence | `source_unavailable` | owner/source |
| `weakness_candidate_graph` | `build_weakness_context` | `normalize_candidate_payload`, `_trace_refs` | compact sources, existing weakness refs | context bundle | set context digest | none | `weakness_candidate:{source_hash}:context` | source summary | context digest | deterministic | minimal context | `partial` | compact only |
| `weakness_candidate_graph` | `extract_weakness_candidates` | `extract_weakness_candidates`, `PolishCandidateLlmService` where enabled | context | candidate drafts | set candidate draft refs | LLM optional, candidate-only | `weakness_candidate:{context_hash}:extract` | context digest | draft summary | provider/schema retry | deterministic extraction or empty list | `low_confidence` | no formal write |
| `weakness_candidate_graph` | `suggest_weakness_merge` | `build_candidate_merge_key`, existing duplicate owner-scope tests | candidate drafts, existing weakness refs | merge suggestions | set `merge_suggestion_refs` | none | `weakness_candidate:{owner_id}:{merge_key}:merge-suggest` | draft summary | merge summary | no retry | no match -> new candidate | `partial` | duplicate merge owner-scoped |
| `weakness_candidate_graph` | `assess_weakness_severity` | `P-WEAKNESS-003` contract | candidates, evidence refs | severity refs | set severity summary | optional LLM call | `weakness_candidate:{candidate_hash}:severity` | merge summary | severity summary | provider/schema retry | low confidence severity | `low_confidence` | severity unknown |
| `weakness_candidate_graph` | `weakness_candidate_quality_gate` | `safe_candidate_dict`, forbidden key/value validators | candidates | accepted candidates | set validation status | none | `weakness_candidate:{candidate_hash}:gate` | severity summary | validation summary | one repair pass | reject unsafe candidate | `validation_failed` | raw payload sanitizer |
| `weakness_candidate_graph` | `persist_weakness_candidates` | `PolishCandidateRepository.upsert_from_feedback_payload` equivalent; PR8 candidate repository tool | accepted candidates | candidate refs | set candidate refs | upsert candidates only | `weakness_candidates:{owner_id}:{candidate_hash}` | validation summary | persisted refs | DB retry | empty list | `partial` | target_formal_ref null |
| `asset_candidate_graph` | `load_asset_sources` | `CandidateExtractionInput`, asset source refs | owner/source refs | compact sources | set source refs | read-only | `asset_candidate:{owner_id}:{source_hash}:load` | none | source summary | no retry | source unavailable | `source_unavailable` | owner/source |
| `asset_candidate_graph` | `build_asset_context` | `normalize_candidate_payload` | compact sources, existing asset refs | context | set context digest | none | `asset_candidate:{source_hash}:context` | source summary | context digest | deterministic | minimal context | `partial` | no raw source |
| `asset_candidate_graph` | `extract_asset_candidates` | `extract_asset_candidates`, `safe_candidate_dict` | context | asset/oral/polished candidate drafts | set draft refs | LLM optional | `asset_candidate:{context_hash}:extract` | context | draft summary | provider/schema retry | deterministic empty list | `low_confidence` | no formal Asset |
| `asset_candidate_graph` | `suggest_asset_version_update` | `P-ASSET-003`, merge key helpers | drafts, existing assets | version suggestions | set version suggestion refs | none | `asset_candidate:{owner_id}:{merge_key}:version` | draft summary | version summary | no retry | new asset candidate | `partial` | merge/version policy |
| `asset_candidate_graph` | `asset_quality_gate` | `P-ASSET-002`, forbidden payload validators | drafts/suggestions | accepted candidates | set validation status | none | `asset_candidate:{candidate_hash}:gate` | version summary | validation summary | one repair pass | reject unsafe candidate | `validation_failed` | user fact insufficient |
| `asset_candidate_graph` | `persist_asset_candidates` | candidate repository tool | accepted candidates | candidate refs | set candidate refs | upsert candidates only | `asset_candidates:{owner_id}:{candidate_hash}` | validation | persisted refs | DB retry | empty list | `partial` | target_formal_ref null |
| `training_suggestion_graph` | `load_training_sources` | training source refs from candidates/formal objects | confirmed weakness refs, asset refs, score trends | compact training context refs | set source refs | read-only | `training_suggestion:{owner_id}:{source_hash}:load` | none | source summary | no retry | no confirmed weakness -> blocked/low confidence | `low_confidence` | confirmed weakness required |
| `training_suggestion_graph` | `build_training_context` | `TRAINING_CONTRACTS.md` context rules | source refs | context bundle | set context digest | none | `training_suggestion:{source_hash}:context` | source summary | context digest | deterministic | minimal context | `partial` | compact only |
| `training_suggestion_graph` | `generate_training_suggestions` | `extract_training_suggestion_candidates`, `P-TRAINING-001` | context | suggestion candidates | set candidate refs | optional LLM call | `training_suggestion:{context_hash}:generate` | context | suggestion digest | provider/schema retry | deterministic suggestions | `low_confidence` | no TrainingTask |
| `training_suggestion_graph` | `rank_training_priorities` | `P-TRAINING-002` | suggestions, score trends | priority ranking | set priority refs | none or LLM if authorized | `training_suggestion:{candidate_hash}:rank` | suggestion summary | ranking summary | provider/schema retry | deterministic ranking | `partial` | priority ranking |
| `training_suggestion_graph` | `training_suggestion_quality_gate` | forbidden payload and contract validation | suggestions/ranking | accepted suggestions | set validation status | none | `training_suggestion:{candidate_hash}:gate` | ranking | validation summary | one repair pass | reject unsafe | `validation_failed` | no formal write |
| `training_suggestion_graph` | `persist_training_suggestions` | candidate/suggestion repository tool | accepted suggestions | candidate refs | set candidate refs | write recommendation candidates only | `training_suggestions:{owner_id}:{candidate_hash}` | validation | persisted refs | DB retry | empty list | `partial` | no auto TrainingTask |
| `candidate_confirmation_interrupt_graph` | `prepare_confirmation_interrupt` | runtime interrupt plan; API `ConfirmCandidateRequest` semantics | candidate ref, actor | interrupt payload | set interrupt ref | write runtime interrupt | `candidate_interrupt:{owner_id}:{candidate_id}:{version_ref}` | none | interrupt ref and redacted summary | resume idempotent | fail closed if candidate inaccessible | `not_found_or_inaccessible` | drawer payload |
| `candidate_confirmation_interrupt_graph` | `sanitize_candidate_for_drawer` | `safe_candidate_dict`, API response sanitizer | candidate | drawer schema | set redacted drawer summary | none | `candidate_drawer:{candidate_id}:{version_ref}` | candidate ref | drawer digest | deterministic | omit unsafe fields | `validation_failed` | no raw prompt/provider |
| `candidate_confirmation_interrupt_graph` | `interrupt_wait_user_action` | LangGraph interrupt/resume | drawer schema | user action | set waiting state | runtime wait only | `candidate_interrupt:{interrupt_id}:wait` | drawer digest | action ref | resume idempotent | timeout/cancel | `timed_out` / `cancelled` | pause/resume |
| `candidate_confirmation_interrupt_graph` | `resume_with_user_action` | API confirmation/correction request | action payload | normalized action | set `confirmation_action`, edited payload ref | none | `candidate_interrupt:{interrupt_id}:resume:{action_hash}` | wait state | action summary | no retry | invalid action -> drawer error | `validation_failed` | stale action |
| `candidate_confirmation_interrupt_graph` | `validate_confirmation_owner_and_version` | candidate repository owner/version checks | candidate ref, version ref, actor | valid action scope | set validation status | none | `candidate_confirm:{owner_id}:{candidate_id}:{version_ref}:validate` | action summary | validation summary | no retry | fail closed | `not_found_or_inaccessible` / `validation_failed` | owner isolation, repeat confirm |
| `candidate_confirmation_interrupt_graph` | `validate_edited_candidate` | candidate schema validators | edited payload | corrected candidate | set corrected payload ref | none | `candidate_confirm:{candidate_id}:{edited_hash}:edit-validate` | owner/version valid | corrected summary | one repair pass only for safe display fields | validation error to drawer | `validation_failed` | edit low confidence |
| `candidate_confirmation_interrupt_graph` | `call_core_formal_write_command` | `PolishCandidateRepository.confirm_candidate`, formal write helpers tested in `test_polish_candidates.py` | action, candidate, target formal ref | formal write result | set formal result ref | Core command writes Weakness/Asset/AssetVersion/TrainingRecommendation only after confirmation | `formal_write:{owner_id}:{candidate_id}:{action}:{version_ref}` | validation summary | formal result ref | transaction retry only | rollback on failure | `generation_failed` / `validation_failed` | confirm creates formal refs, rollback |
| `candidate_confirmation_interrupt_graph` | `write_user_confirmation_ref` | API `UserConfirmationRef` semantics | action, before/after summary | confirmation ref | set confirmation ref | write user confirmation | `user_confirmation:{owner_id}:{candidate_id}:{action}:{version_ref}` | formal result or no-write action | confirmation ref | DB retry | for skip/reject write no formal ref | `partial` | skip/reject no formal |
| `candidate_confirmation_interrupt_graph` | `write_audit_event` | `SECURITY_PRIVACY.md` audit event boundary | action, result, confirmation ref | audit ref | set audit ref | write sanitized audit event | `audit:candidate:{owner_id}:{candidate_id}:{action}:{version_ref}` | confirmation ref | audit ref | DB retry | fail closed for confirm; for skip/reject mark audit partial only if policy allows | `partial` / `validation_failed` | audit required |
| `candidate_confirmation_interrupt_graph` | `rollback_on_failed_formal_write` | confirm rollback test | failed formal write | rollback result | set rollback ref | transaction rollback / status restore | `rollback:{owner_id}:{candidate_id}:{version_ref}` | failed write summary | rollback summary | no retry beyond transaction | restore candidate status and null formal ref | `generation_failed` | rollback status candidate |
| `candidate_confirmation_interrupt_graph` | `publish_confirmation_result` | API response schema | confirmation/audit/formal refs | result response | terminal status | none | `candidate_result:{owner_id}:{candidate_id}:{action}:{version_ref}` | final refs | terminal summary | idempotent | sanitized error response | terminal API enum | no raw payload |
| all | `complete_ai_task` | AI task protocol | graph state | task result | terminal status | write task status | `ai_task:{ai_task_id}:complete` | persistence refs | terminal summary | idempotent | sanitized failure | terminal API enum | task status |

## 8. Formal write handoff

LLM graph nodes may create candidate/suggestion records only. `call_core_formal_write_command` is the only node allowed to invoke formal write behavior, and it must call a Core Business command/repository method that:

- verifies owner, actor, candidate status and `base_candidate_version_ref`;
- rejects stale, repeated or cross-owner confirmation;
- writes `UserConfirmationRef` and audit event;
- creates or updates formal `Weakness`, `Asset`, `AssetVersion` or `TrainingRecommendation` only after `confirm`, validated `edit` or validated `merge`;
- never creates `TrainingTask`; training tasks require explicit user action/API after recommendation confirmation;
- rolls back candidate status and `target_formal_ref` if formal write fails.

## 9. Audit event mapping

| Action | Audit event fields | Formal write |
|---|---|---|
| `confirm` | actor, candidate ref, action, before summary, created formal ref, source refs, trace refs, result | yes, via Core command |
| `edit` | actor, candidate ref, action, edited payload ref, validation summary, created/updated formal ref, result | yes, after validation |
| `merge` | actor, candidate ref, target formal/candidate ref, merge summary, result | yes, when target is formal update; no, when merging candidates only |
| `reject` | actor, candidate ref, reason category, result | no |
| `skip` | actor, candidate ref, reason category, result | no |
| `request_more_evidence` | actor, candidate ref, requested evidence summary, result | no |

Audit events store summaries and refs only. They do not store raw source text, LLM prompt, completion, provider payload, copied content body, hidden scoring rules or secrets.

## 10. Duplicate / merge suggestion policy

- `merge_key` is normalized from owner-scoped candidate type, title/summary/evidence dimensions and source category.
- Same `candidate_id` may exist for different owners; owner id is always part of repository lookup.
- Duplicate candidate within one owner becomes `merge_suggested` or points to `merge_target_candidate_id`; it must not auto-confirm.
- Low confidence duplicate evidence yields `manual_check_required`.
- Merge into formal object requires `target_formal_ref` and user action; graph suggestion alone cannot update formal object.
- Merge into candidate only changes candidate status/metadata; no formal write.

## 11. Rejection / skip behavior

| User action | Candidate status | Formal write | Audit | Retry / resume behavior |
|---|---|---|---|---|
| `reject` | `rejected` | no | yes | terminal; same version cannot confirm later without new candidate/correction |
| `skip` | `skipped` or existing implementation-compatible `dismissed` | no | yes | terminal for this interrupt; future regenerated candidate may appear with new version |
| `request_more_evidence` | `needs_confirmation` / `low_confidence` | no | yes | creates follow-up action or low confidence marker |
| `merge` candidate-only | `merged` | no | yes | terminal for source candidate |
| `archive` legacy action | `archived` | no | yes if API supports audit | terminal |

## 12. 旧代码迁移矩阵

| Existing Symbol | Target Node/Tool/Validator | keep/wrap/split/deprecate/delete | PR | Tests |
|---|---|---|---|---|
| `CandidateType`, `CandidateStatus`, `PolishCandidate`, `CandidateExtractionInput` | candidate schema and extraction nodes | keep | PR8 | schema fields, owner scoped candidates |
| `normalize_candidate_payload`, `safe_candidate_dict` | quality gates and drawer sanitizer | keep | PR8 | raw payload sanitizer |
| `extract_weakness_candidates` | `extract_weakness_candidates` node | wrap | PR8 | weakness candidate refs |
| `extract_asset_candidates` | `extract_asset_candidates` node | wrap | PR8 | asset/oral/polished candidate refs |
| `extract_training_suggestion_candidates` | `generate_training_suggestions` node | wrap | PR8 | training suggestion candidate refs |
| `build_candidate_merge_key` | merge suggestion nodes | keep | PR8 | duplicate merge key owner scoped |
| `PolishCandidateLlmService.enhance_with_llm_or_fallback` | candidate enhancement sub-node/tool | wrap | PR8 | fake provider accepted, forbidden output fallback |
| `PolishCandidateRepository.upsert_from_feedback_payload` | `persist_*_candidates` | wrap | PR8 | no formal write during upsert |
| `PolishCandidateRepository.confirm_candidate` | `call_core_formal_write_command` | wrap behind interrupt | PR8 | confirm formal refs, owner isolation, repeated confirm |
| `dismiss_candidate`, `merge_candidate`, `archive_candidate` | rejection/skip/merge actions | keep/wrap | PR8 | dismiss/merge/archive no formal write |
| Formal write helpers inside candidate repository | Core formal write command | wrap, keep transactional semantics | PR8 | rollback on failure |
| Candidate LLM raw provider fields | none | delete/forbid | PR8 | forbidden provider payload not persisted |

## 13. 与 active docs 的关系

本文落实 active docs 中 candidate / suggestion / formal object、user confirmation、audit、copy/privacy 和 trace 边界。LangGraph 只生成候选、建议、interrupt state 和 trace；正式对象由 Core Business command/API 承接。

## 14. 非目标

- 不实现 confirmation drawer UI。
- 不新增 API。
- 不写正式对象实现。
- 不自动创建训练任务。
- 不实现复杂合并算法。
- 不实现 rollback 工具。
- 不让 checkpoint 成为 business truth source。

## 15. 后续 PR 使用方式

PR8 或等价候选闭环 PR 使用本文先实现 candidate-only runtime，再接 confirmation interrupt/resume 与 Core formal write command。late graph result 不得绕过 confirmation。主 Agent 需要汇总确认 candidate status 名称是否沿用当前 `dismissed/archived` 还是扩展为 API 文档中的 `rejected/skipped`，实现时必须提供 backward-compatible 映射。

## 16. Definition of Done

- 四个 graph skeleton 已覆盖。
- candidate schema、confirmation interrupt schema、formal write handoff、audit event mapping、duplicate/merge suggestion policy、rejection/skip behavior 已冻结。
- candidate 不能静默升级 formal object。
- formal object 必须来自用户确认或显式 API。
- raw LLM payload 禁止进入 checkpoint、日志、API response。
