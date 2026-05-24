---
title: Job Match Agent Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/job-match-agent-package
---

# Job Match Agent Package

## 1. Package 目标

本 package 只冻结 Job Match / ResumeAnalysis 在 LangGraph migration 中的降级实施边界。PR2-PR5 不得实施完整 `resume_analysis_graph` 或 `job_match_graph`；这几个 PR 只允许 descriptor、DTO、trace-compatible wrapper 和 graph placeholder。完整 graph 只能在 PR6 且确认 Job Match / ResumeAnalysis 仍需要 graph migration 后实施。

PR5 的 first migration target 是 Polish，不是 Job Match。Job Match legacy direct analyzer path 至少保留到 PR7 frontend ready，且在 graph parity 被证明前不得删除或静默替换。

## 2. Graph scope

| Graph | Target | Contract source | PR / allowed status |
|---|---|---|---:|
| `resume_analysis_graph` | deterministic resume source bundle / snapshot | active data / persistence docs; no independent `P-RESUME-*` contract yet | PR6 only if still needed；PR2-PR5 placeholder only |
| `job_match_graph` | job/resume binding analysis, `job_match` score, candidate refs | `P-JOBMATCH-*`, `SCORING_SPEC.md`, `API_SPEC.md` | PR6 only if still needed；PR2-PR5 trace-compatible wrapper / placeholder only |

## 3. PR2-PR5 allowed artifacts

| Artifact | Allowed content | Forbidden before PR6 |
|---|---|---|
| Descriptor | graph name, capability name, source refs, contract ids, owner-scope requirements, no raw payload policy | executable graph, LangGraph import, node side effects |
| DTO | request/response refs, validation flags, trace refs, score/candidate refs | provider payload, raw resume/JD body, checkpoint payload |
| Trace-compatible wrapper | wrapping `LlmJobMatchAnalyzer.analyze` with future `PersistedLlmTransport` semantics without response shape drift | graph runner, checkpointer, facade replacement, direct path removal |
| Placeholder | file/package placeholder only after explicit scope lock; no runtime execution | full `job_match_graph`, full `resume_analysis_graph`, graph node implementation |

## 4. Deferred PR6 state fields

| Graph | Required state fields |
|---|---|
| `resume_analysis_graph` | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `resume_id`, `resume_version_id`, `resume_markdown_ref`, `resume_markdown_digest`, `section_refs`, `signal_refs`, `quality_flags`, `source_availability`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` |
| `job_match_graph` | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `binding_id`, `job_version_id`, `resume_version_id`, `score_rule_version_id`, `source_bundle_ref`, `source_bundle_digest`, `analysis_ref`, `score_result_ref`, `candidate_refs`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` |

这些字段是 PR6-if-needed 的 DTO / AgentState sketch，不授权 PR2-PR5 创建 graph state implementation。

## 5. Deferred `job_match_graph` node sketch

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_binding_versions` | owner, binding id | frozen job/resume versions, source availability | read only | `job_match:{owner_id}:{binding_id}:load` | `not_found_or_inaccessible` / `source_unavailable` | owner scoped binding read |
| `build_job_match_source_bundle` | frozen versions | bundle ref, digest, evidence refs | optional snapshot write if PR6 authorizes it | `job_match:{binding_id}:{job_version_id}:{resume_version_id}:bundle` | `source_unavailable` / `partial` | no raw Markdown/JD in checkpoint |
| `run_job_match_analyzer` | bundle, `P-JOBMATCH-*` contract ids | analyzer candidate, model summary | LLM via persisted transport only | `job_match:{binding_id}:{source_bundle_digest}:llm:{contract_hash}` | `generation_failed` | provider failure sanitized |
| `normalize_job_match_payload` | analyzer output | normalized payload, validation warnings | none | `job_match:{binding_id}:{source_bundle_digest}:normalize` | `validation_failed` | loose payload normalized, invalid blocked |
| `job_match_score_gate` | normalized payload, score rule version | score candidate and validation | none | `job_match:{binding_id}:{source_bundle_digest}:score:{score_rule_version_id}` | `validation_failed` / `low_confidence` | 0-100 bounds, no exact probability |
| `persist_job_match_analysis` | normalized payload, source refs | `analysis_ref` | write job match analysis and AI task result | `job_match:{owner_id}:{binding_id}:{source_bundle_digest}:analysis` | `generation_failed` / `validation_failed` | completed result payload/source digest |
| `persist_score_result` | score candidate, analysis ref | `score_result_ref` | write `ScoreResult(job_match)` only when valid | `score_result:{owner_id}:job_match:{analysis_ref}:{score_rule_version_id}` | `partial` / `validation_failed` | invalid score writes no formal score |
| `complete_ai_task` | graph state | terminal task status | write task result/status | `ai_task:{ai_task_id}:complete` | terminal status | no raw payload in task response |

本节是 PR6 决策仍需要完整 graph 时的 sketch。PR2-PR5 不得把这些节点落成 executable graph。

## 6. Deferred `resume_analysis_graph` node sketch

| Node | Inputs | Outputs | Side effects | Idempotency key | Failure status | Tests |
|---|---|---|---|---|---|---|
| `load_resume_version` | owner, resume version | markdown ref and version metadata | read only | `resume_analysis:{owner_id}:{resume_version_id}:load` | `not_found_or_inaccessible` / `source_unavailable` | deleted/cross-owner source |
| `parse_resume_markdown` | markdown ref, parser config | section candidates | none | `resume_analysis:{resume_version_id}:{digest}:parse` | `validation_failed` | empty/malformed markdown |
| `chunk_resume_sections` | section candidates | chunk refs and digests | optional snapshot if authorized | `resume_analysis:{resume_version_id}:{digest}:chunk` | `low_confidence` | no raw text in checkpoint |
| `extract_resume_signals` | chunk refs | signal refs and quality flags | none | `resume_analysis:{resume_version_id}:{digest}:signals` | `low_confidence` | sparse signal extraction |
| `resume_signal_quality_gate` | signal refs and section refs | validation result | none | `resume_analysis:{resume_version_id}:{digest}:gate` | `validation_failed` / `low_confidence` | confidence flags |
| `persist_resume_analysis_snapshot` | validated snapshot | snapshot ref | write snapshot only if PR6 authorizes table | `resume_analysis:{owner_id}:{resume_version_id}:{digest}:snapshot` | `partial` | repository truth, checkpoint non-truth |
| `complete_ai_task` | graph state | terminal status | write task result/status | `ai_task:{ai_task_id}:complete` | terminal status | redacted status |

本节是 PR6 决策仍需要完整 graph 时的 sketch。PR2-PR5 不得把这些节点落成 executable graph。

## 7. Prompt and input rules

| Item | Rule |
|---|---|
| `job_match_graph` contract ids | Must match active `P-JOBMATCH-*` registry before implementation |
| LLM input package | Use compact source refs, chunk refs, digest, dimension hints and safe summaries |
| Forbidden LLM input | Full resume Markdown, full JD, raw prompt, raw completion, provider payload |
| Score | Must use 0-100 product scale and score rule version; no exact pass probability |
| Candidate refs | Weakness / asset / training candidates remain candidate-only until confirmation |

## 8. Migration mapping

| Existing symbol | Target node | Strategy | PR |
|---|---|---|---:|
| `LlmJobMatchAnalyzer.analyze` | trace-compatible direct wrapper first; `run_job_match_analyzer` only if PR6 graph is still needed | wrap, no response shape drift | PR6 |
| `LlmTransportRequest` | LLM input package DTO | keep | PR6 |
| `_source_input_refs`, `_evidence_bundle` | source bundle descriptor / DTO | keep / wrap | PR6 |
| `_normalize_job_match_payload` | normalize DTO or node sketch | keep / split only if graph approved | PR6 |
| `_normalize_dimension_scores` | score gate DTO or node sketch | split only if graph approved | PR6 |
| existing job match repository write path | persist analysis | keep / wrap | PR6 |
| direct use case analyzer invocation | legacy direct path | keep until at least PR7 frontend ready；deprecate only after parity | PR6 / PR7+ |

## 9. PR6-if-needed tests

| Test file | Assertions |
|---|---|
| `tests/api/test_job_match_graph.py` | source bundle owner scope, result refs, no direct formal Weakness write |
| `tests/api/test_job_match_graph.py` | low confidence visible, no exact probability field |
| `tests/api/test_job_match_api.py` | existing API owner / validation behavior preserved |
| `tests/api/test_sensitive_payload_redaction.py` | no raw prompt/completion/provider/JD/resume body leaks |

## 10. Non-goals

- 不做 PR2 implementation。
- PR2-PR5 不创建 executable Job Match / ResumeAnalysis graph。
- PR5 不迁移 Job Match；PR5 只属于 Polish first migration target。
- 不在 PR7 frontend ready 前删除 Job Match direct path。
- 不在 active API contract 外自行发明 endpoint。
- No formal Weakness / Asset / TrainingRecommendation write.
- No checkpoint business read model.
- 本 package 不做 real provider smoke。
