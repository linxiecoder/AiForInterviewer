---
title: Job Match Agent Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/job-match-agent-package
---

# Job Match Agent Package

## 1. Package 目标

本 package 冻结 `resume_analysis_graph` 与 `job_match_graph` 的 implementation plan。PR5 才能实施本 package；PR2 不得创建 business graph。

## 2. Graph scope

| Graph | Target | Contract source | PR |
|---|---|---|---:|
| `resume_analysis_graph` | deterministic resume source bundle / snapshot | active data / persistence docs; no independent `P-RESUME-*` contract yet | PR5 only if authorized |
| `job_match_graph` | job/resume binding analysis, `job_match` score, candidate refs | `P-JOBMATCH-*`, `SCORING_SPEC.md`, `API_SPEC.md` | PR5 |

## 3. State fields

| Graph | Required state fields |
|---|---|
| `resume_analysis_graph` | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `resume_id`, `resume_version_id`, `resume_markdown_ref`, `resume_markdown_digest`, `section_refs`, `signal_refs`, `quality_flags`, `source_availability`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` |
| `job_match_graph` | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `binding_id`, `job_version_id`, `resume_version_id`, `score_rule_version_id`, `source_bundle_ref`, `source_bundle_digest`, `analysis_ref`, `score_result_ref`, `candidate_refs`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` |

## 4. `job_match_graph` node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_binding_versions` | owner, binding id | frozen job/resume versions, source availability | read only | `job_match:{owner_id}:{binding_id}:load` | `not_found_or_inaccessible` / `source_unavailable` | owner scoped binding read |
| `build_job_match_source_bundle` | frozen versions | bundle ref, digest, evidence refs | optional snapshot write if PR5 authorizes it | `job_match:{binding_id}:{job_version_id}:{resume_version_id}:bundle` | `source_unavailable` / `partial` | no raw Markdown/JD in checkpoint |
| `run_job_match_analyzer` | bundle, `P-JOBMATCH-*` contract ids | analyzer candidate, model summary | LLM via persisted transport only | `job_match:{binding_id}:{source_bundle_digest}:llm:{contract_hash}` | `generation_failed` | provider failure sanitized |
| `normalize_job_match_payload` | analyzer output | normalized payload, validation warnings | none | `job_match:{binding_id}:{source_bundle_digest}:normalize` | `validation_failed` | loose payload normalized, invalid blocked |
| `job_match_score_gate` | normalized payload, score rule version | score candidate and validation | none | `job_match:{binding_id}:{source_bundle_digest}:score:{score_rule_version_id}` | `validation_failed` / `low_confidence` | 0-100 bounds, no exact probability |
| `persist_job_match_analysis` | normalized payload, source refs | `analysis_ref` | write job match analysis and AI task result | `job_match:{owner_id}:{binding_id}:{source_bundle_digest}:analysis` | `generation_failed` / `validation_failed` | completed result payload/source digest |
| `persist_score_result` | score candidate, analysis ref | `score_result_ref` | write `ScoreResult(job_match)` only when valid | `score_result:{owner_id}:job_match:{analysis_ref}:{score_rule_version_id}` | `partial` / `validation_failed` | invalid score writes no formal score |
| `complete_ai_task` | graph state | terminal task status | write task result/status | `ai_task:{ai_task_id}:complete` | terminal status | no raw payload in task response |

## 5. `resume_analysis_graph` node plan

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_resume_version` | owner, resume version | markdown ref and version metadata | read only | `resume_analysis:{owner_id}:{resume_version_id}:load` | `not_found_or_inaccessible` / `source_unavailable` | deleted/cross-owner source |
| `parse_resume_markdown` | markdown ref, parser config | section candidates | none | `resume_analysis:{resume_version_id}:{digest}:parse` | `validation_failed` | empty/malformed markdown |
| `chunk_resume_sections` | section candidates | chunk refs and digests | optional snapshot if authorized | `resume_analysis:{resume_version_id}:{digest}:chunk` | `low_confidence` | no raw text in checkpoint |
| `extract_resume_signals` | chunk refs | signal refs and quality flags | none | `resume_analysis:{resume_version_id}:{digest}:signals` | `low_confidence` | sparse signal extraction |
| `resume_signal_quality_gate` | signal refs and section refs | validation result | none | `resume_analysis:{resume_version_id}:{digest}:gate` | `validation_failed` / `low_confidence` | confidence flags |
| `persist_resume_analysis_snapshot` | validated snapshot | snapshot ref | write snapshot only if PR5 authorizes table | `resume_analysis:{owner_id}:{resume_version_id}:{digest}:snapshot` | `partial` | repository truth, checkpoint non-truth |
| `complete_ai_task` | graph state | terminal status | write task result/status | `ai_task:{ai_task_id}:complete` | terminal status | redacted status |

## 6. Prompt and input rules

| Item | Rule |
|---|---|
| `job_match_graph` contract ids | Must match active `P-JOBMATCH-*` registry before implementation |
| LLM input package | Use compact source refs, chunk refs, digest, dimension hints and safe summaries |
| Forbidden LLM input | Full resume Markdown, full JD, raw prompt, raw completion, provider payload |
| Score | Must use 0-100 product scale and score rule version; no exact pass probability |
| Candidate refs | Weakness / asset / training candidates remain candidate-only until confirmation |

## 7. Migration mapping

| Existing symbol | Target node | Strategy | PR |
|---|---|---|---:|
| `LlmJobMatchAnalyzer.analyze` | `run_job_match_analyzer` | wrap | PR5 |
| `LlmTransportRequest` | LLM input package | keep | PR5 |
| `_source_input_refs`, `_evidence_bundle` | source bundle builder | keep / wrap | PR5 |
| `_normalize_job_match_payload` | normalize node | keep / split | PR5 |
| `_normalize_dimension_scores` | score gate | split | PR5 |
| existing job match repository write path | persist analysis | keep / wrap | PR5 |
| direct use case analyzer invocation | facade call | deprecate after parity | PR5 |

## 8. PR5 tests

| Test file | Assertions |
|---|---|
| `tests/api/test_job_match_graph.py` | source bundle owner scope, result refs, no direct formal Weakness write |
| `tests/api/test_job_match_graph.py` | low confidence visible, no exact probability field |
| `tests/api/test_job_match_api.py` | existing API owner / validation behavior preserved |
| `tests/api/test_sensitive_payload_redaction.py` | no raw prompt/completion/provider/JD/resume body leaks |

## 9. Non-goals

- 不做 PR2 implementation。
- 不在 active API contract 外自行发明 endpoint。
- No formal Weakness / Asset / TrainingRecommendation write.
- No checkpoint business read model.
- 本 package 不做 real provider smoke。
