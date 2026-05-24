---
title: Report Review Agent Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构 / 安全隐私
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/report-review-agent-package
---

# Report Review Agent Package

## 1. Package 目标

本 package 冻结 `report_generation_graph`、`mock_review_generation_graph`、`real_review_generation_graph` 的 implementation plan。Pressure report input assembly 在 Pressure package 中定义；报告正文、复盘和复制边界在本 package 定义。

## 2. Graph scope

| Graph | Target | PR |
|---|---|---:|
| `report_generation_graph` | report sections, score explanation, copyable content metadata | PR8 |
| `mock_review_generation_graph` | review from system interview/session/report refs | PR8 |
| `real_review_generation_graph` | review from user-confirmed real interview input with privacy redaction | PR8 |

## 3. `report_generation_graph` state

| Field | Rule |
|---|---|
| `report_input_package_ref` | required; missing means `source_unavailable` |
| `section_plan[]` | section id, contract ids, source refs, score refs, validation rule refs |
| `section_worker_results[]` | sanitized worker outputs only |
| `partial_report_policy` | required sections fail closed; optional sections may produce `partial` |
| `score_consistency_summary` | proves score refs align with `SCORING_SPEC.md` |
| `copy_boundary_metadata` | clipboard-only, no export/download artifact |

## 4. Report worker / reducer rules

| Rule | Output |
|---|---|
| required `summary` worker fails | report `generation_failed`; no report persistence |
| required `score` worker missing score refs | report `low_confidence` unless score disclaimer and source status are present |
| optional `weakness` / `training` worker fails | report `partial`; candidate refs omitted or low confidence |
| worker returns exact probability or hidden scoring rule | reject section and set `validation_failed` |
| worker returns raw prompt/completion/provider payload | reject section and record security validation failure |
| copy content worker fails | report may persist with `copy_content_available=false` |

## 5. Report node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_report_sources` | owner, report request | source refs | read only | `report:{owner_id}:{report_request_id}:load` | `source_unavailable` | source status |
| `validate_report_scope` | requested sections, contract refs | section scope | none | `report:{request_id}:scope:{sections_hash}` | `validation_failed` | no export path |
| `build_report_input_package` | source refs | package ref/digest | optional package persistence | `report:{session_ref}:input:{source_digest}` | `partial` | no raw answer dump |
| `plan_report_sections` | package and requested sections | section plan | none | `report:{package_ref}:plan:{sections_hash}` | `validation_failed` | section plan |
| `dispatch_report_section_workers` | section plan | worker refs | runtime fanout only | `report:{package_ref}:dispatch:{plan_hash}` | `partial` | fanout/fanin |
| `write_report_section` | section-local state | section draft | LLM via persisted transport | `report_section:{package_ref}:{section_id}:{source_hash}` | per-worker status | worker no raw payload |
| `section_quality_gate` | section draft | accepted/rejected section | none | `report_section:{section_id}:{draft_digest}:gate` | `validation_failed` | no exact probability |
| `synthesize_report` | worker results | report draft | none | `report:{package_ref}:synthesize:{worker_hash}` | `partial` / `generation_failed` | reducer policy |
| `score_report_consistency_gate` | report draft, score refs | consistency result | none | `report:{package_ref}:score-gate:{score_hash}` | `low_confidence` / `validation_failed` | score consistency |
| `persist_report` | report draft | report refs | write report and sections | `report:{owner_id}:{package_ref}:{report_digest}` | `generation_failed` | persistence target |
| `prepare_copy_boundary` | persisted report | copy content ref | write copy metadata only | `copy_content:{owner_id}:{report_ref}:{copy_hash}` | `partial` | no export/download/file |
| `complete_ai_task` | graph state | task result | write task status | `ai_task:{ai_task_id}:complete` | terminal status | sanitized task |

## 6. Mock review node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_mock_review_sources` | session/report refs | source timeline refs | read only | `mock_review:{owner_id}:{session_ref}:load` | `source_unavailable` | source scope |
| `build_turn_performance_timeline` | turn refs, score refs | performance timeline | none | `mock_review:{session_ref}:timeline:{turn_hash}` | `partial` | no rescore |
| `diagnose_session_performance` | timeline | review draft | LLM via transport | `mock_review:{session_ref}:diagnose:{timeline_hash}` | `low_confidence` | no outcome prediction |
| `extract_review_weakness_candidates` | review draft | weakness candidate refs | candidate-only write | `mock_review:{review_digest}:weakness-candidates` | `partial` | no formal weakness |
| `extract_review_asset_candidates` | review draft | asset candidate refs | candidate-only write | `mock_review:{review_digest}:asset-candidates` | `partial` | no formal asset |
| `generate_training_suggestions` | review/candidate refs | training suggestion refs | suggestion-only write | `mock_review:{review_digest}:training-suggestions` | `partial` | no training task |
| `review_quality_gate` | review draft | validation result | none | `mock_review:{review_digest}:quality` | `validation_failed` | no rescore |
| `persist_mock_review` | validated review | review ref | write review/items | `mock_review:{owner_id}:{session_ref}:{review_digest}` | `generation_failed` | review readback |
| `complete_ai_task` | graph state | task result | write task status | `ai_task:{ai_task_id}:complete` | terminal status | sanitized task |

## 7. Real review node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_real_interview_input` | real input ref | source summary | read only | `real_review:{owner_id}:{real_input_ref}:load` | `source_unavailable` | owner scope |
| `validate_real_input_completeness` | source summary | completeness result | none | `real_review:{real_input_ref}:validate` | `low_confidence` / `validation_failed` | confirmed input |
| `redact_third_party_sensitive_fields` | real input summary | redacted evidence and summary | write audit summary | `real_review:{real_input_ref}:redact:{source_digest}` | `validation_failed` | third-party redaction |
| `build_real_review_evidence` | redacted source refs | evidence bundle refs | none | `real_review:{real_input_ref}:evidence:{redacted_digest}` | `low_confidence` | no raw real input |
| `generate_real_review` | evidence bundle | review draft | LLM via transport | `real_review:{real_input_ref}:llm:{evidence_hash}` | `generation_failed` / `low_confidence` | no outcome prediction |
| `real_review_quality_gate` | review draft | validation result | none | `real_review:{draft_digest}:quality` | `validation_failed` | privacy and no exact probability |
| `persist_real_review` | validated review | review ref | write real review/items | `real_review:{owner_id}:{real_input_ref}:{review_digest}` | `generation_failed` | review readback |
| `complete_ai_task` | graph state | task result | write task status | `ai_task:{ai_task_id}:complete` | terminal status | sanitized task |

## 8. Score and copy rules

| Concern | Rule |
|---|---|
| score | 0-100 product scale, confidence/validation visible, no pass/offer probability |
| hidden scoring | worker output cannot expose hidden formulas or weights |
| copy | copy content is clipboard-only; no file export/download artifact |
| privacy | real review runs redaction before any LLM node |
| candidate | review/report candidate refs remain candidate-only until confirmation |

## 9. Tests

| Area | Assertions |
|---|---|
| report workers | required/optional section reducer behavior, partial policy |
| report score | score refs required, no exact probability |
| copy boundary | no export/download/file artifacts |
| mock review | no rescore, candidate-only refs |
| real review | confirmed input required, third-party redaction before LLM |
| raw-off | no raw prompt/completion/provider/checkpoint payload |

## 10. Non-goals

- 不做 PR2 implementation。
- No PDF/Markdown/docx export.
- No new scoring formula.
- No formal Weakness / Asset / TrainingTask creation.
- 默认不调用 real provider。
