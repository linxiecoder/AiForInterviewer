---
title: 简历分析与岗位匹配 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-resume-jobmatch
---

# 简历分析与岗位匹配 LangGraph 实施计划

## 1. 文档目的

本文规划 `resume_analysis_graph` 与 `job_match_graph` 的 implementation-ready graph spec，覆盖目标、state、node、edge、conditional edge、checkpoint、retry/fallback、persistence、LLM trace、旧代码迁移和测试计划。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md`
- 代码 recon：`apps/api/app/infrastructure/llm/job_match.py`、`apps/api/app/application/llm/types.py`、`apps/api/app/application/llm/ports.py`、`tests/api/test_job_match_api.py`

## 3. 当前状态

`job_match_graph` 有 `P-JOBMATCH-*` contract、`job_match` score 依据、现有 `LlmJobMatchAnalyzer` 和 API/analyzer tests。`resume_analysis_graph` 当前没有独立 active `P-RESUME-*` contract，因此本文件将它冻结为 deterministic source-bundle / snapshot graph；PR5 若要把它升级为独立 LLM graph，必须先在 active docs 或 PR5 设计中明确 contract ID、输入、输出和 validator。

## 4. Graph 总览

| Graph | 目标 | State 字段 | Edge / conditional edge | Persistence targets | Trace policy | Tests |
|---|---|---|---|---|---|---|
| `resume_analysis_graph` | 分析 `ResumeVersion` Markdown，生成结构化 source bundle / snapshot，为 Job Match / Polish / Report 提供授权摘要 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `resume_id`, `resume_version_id`, `resume_markdown_ref`, `resume_markdown_digest`, `section_refs`, `signal_refs`, `quality_flags`, `source_availability`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` | `START -> load -> parse -> chunk -> extract -> gate -> persist -> complete`; source unavailable -> `source_unavailable`; parse failed -> `validation_failed`; insufficient signal -> `low_confidence` | `ai_tasks`, `ai_task_results`, `trace_refs`, `evidence_refs`, resume analysis snapshot by PR5 | Only sanitized refs, digests and validation summary; no raw Markdown in checkpoint/API/log | owner, empty markdown, source unavailable, low confidence, checkpoint non-truth, no raw payload |
| `job_match_graph` | 基于岗位/简历绑定生成岗位匹配分析、`job_match` 评分和 candidate handoff | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `binding_id`, `job_version_id`, `resume_version_id`, `score_rule_version_id`, `source_bundle_ref`, `source_bundle_digest`, `analysis_ref`, `score_result_ref`, `candidate_refs`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` | `START -> load -> bundle -> analyze -> normalize -> score_gate -> persist_analysis -> persist_score -> complete`; missing source -> `partial`; provider unavailable -> `generation_failed`; validation failed -> no formal score; candidate -> confirmation | `job_match_analyses`, `score_results`, `candidate_refs`, `ai_task_results`, `trace_refs`, `evidence_refs` | Capture `P-JOBMATCH-*`, sanitized bundle digest, validation errors, usage/failure summary; no provider payload | normal, owner mismatch, 0/100 score, source unavailable, validation failed, provider unavailable, no exact probability, candidate not formal |

## 5. `job_match_graph` 方法级样板

### 5.1 State contract

| Field | Required | Source | Write rule |
|---|---|---|---|
| `owner_id`, `actor_id` | 是 | API actor / Core UseCase | Every node verifies owner scope before reading or writing |
| `ai_task_id`, `agent_run_id` | 是 | AI Runtime | Used for runtime status and trace, not business identity |
| `binding_id` | 是 | `JobResumeBinding` / API command | Idempotency scope includes binding and requested score rule |
| `job_version_id`, `resume_version_id` | 是 | `load_binding_versions` | Must be frozen before source bundle build |
| `score_rule_version_id` | 是 | `SCORING_SPEC.md` / PR5 scorer | Missing value blocks formal `ScoreResult` write |
| `source_bundle_ref`, `source_bundle_digest` | 是 | `build_job_match_source_bundle` | Digest only in checkpoint; business source refs in repository |
| `analysis_ref`, `score_result_ref` | 否 | persistence nodes | Set only after repository commit |
| `candidate_refs` | 否 | candidate extraction/handoff | Candidate-only; no formal write |
| `validation_status`, `error_state` | 是 | validators / failure handlers | Drives API status |

### 5.2 Node contract 表

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `job_match_graph` | `load_binding_versions` | existing job/resume/binding repository path used by `test_job_match_api.py` seed fixtures | `owner_id`, `binding_id` | frozen `job_version_id`, `resume_version_id`, source availability | set version ids and `source_availability` | read-only | `job_match:{owner_id}:{binding_id}:load` | none | sanitized version refs | no retry except transient DB read retry in repository layer | source unavailable path | `not_found_or_inaccessible` or `source_unavailable` | owner scoped get, binding missing |
| `job_match_graph` | `build_job_match_source_bundle` | current `JobMatchSourceBundle` assembly path consumed by `LlmJobMatchAnalyzer.analyze` | frozen versions, owner refs | `source_bundle_ref`, digest, compact evidence bundle | set source bundle refs/digest | optional snapshot write only if PR5 repository exists | `job_match:{binding_id}:{job_version_id}:{resume_version_id}:bundle` | versions loaded | digest and evidence refs | deterministic rebuild is safe | if resume analysis unavailable, build compact bundle from current versions and mark `partial` | `source_unavailable` or `partial` | source digest persisted, no raw Markdown/JD in checkpoint |
| `job_match_graph` | `run_job_match_analyzer` | `LlmJobMatchAnalyzer.analyze`; `LlmTransportRequest(contract_ids=JOB_MATCH_CONTRACT_IDS, task_type="job_match_analysis", input_refs, evidence_bundle)` | source bundle, contract ids | analyzer output payload, prompt/model summary | set transient `analysis_candidate_ref`, LLM trace ref | LLM call via transport wrapper only | `job_match:{binding_id}:{source_bundle_digest}:llm:{contract_hash}` | source bundle digest | sanitized LLM call summary | provider timeout/unavailable follows runtime retry budget; schema errors go to normalize/repair | provider unavailable -> deterministic unavailable status, no completed analysis | `generation_failed` | provider unavailable maps domain error; no provider payload |
| `job_match_graph` | `normalize_job_match_payload` | `_normalize_job_match_payload`, `_normalize_dimension_scores`, gap coverage helpers | analyzer output, source bundle | normalized analysis payload | set `validation_status=normalized` and validation warnings | none | `job_match:{binding_id}:{source_bundle_digest}:normalize` | LLM summary | normalized digest and warnings | repair once for loose shape | if unrecoverable, stop before persistence | `validation_failed` | loose payload normalized; invalid payload not saved |
| `job_match_graph` | `job_match_score_gate` | current validation in `JobMatchAnalyzerOutput` consumers; `SCORING_SPEC.md` score rules | normalized payload, `score_rule_version_id` | score candidate, dimension scores, allowed flag | set `score_result_ref` only after persist node; before that store candidate digest | none | `job_match:{binding_id}:{source_bundle_digest}:score:{score_rule_version_id}` | normalized digest | score validation summary | no LLM retry; deterministic validation only | score rule missing -> analysis may persist as low confidence, no formal score | `validation_failed` for invalid score; `low_confidence` for missing optional sources | 0/100 score, no exact probability, missing score rule |
| `job_match_graph` | `persist_job_match_analysis` | existing job match analysis repository write path covered by `test_create_analysis_persists_completed_result_payload_and_source_digest` | normalized payload, source refs, score summary | `analysis_ref` | set `analysis_ref` | write `job_match_analyses`, `ai_task_result` | `job_match:{owner_id}:{binding_id}:{source_bundle_digest}:analysis` | validation summary | persisted `analysis_ref` | DB retry only if repository supports transaction retry | none; fail closed before score write | `generation_failed` or `validation_failed` | completed payload/source digest stored; invalid result not completed |
| `job_match_graph` | `persist_score_result` | PR5 ScoreResult repository handoff; active `ScoreResult(job_match)` from `SCORING_SPEC.md` | score candidate, `analysis_ref`, score rule version | `score_result_ref` | set `score_result_ref` | write `score_results` only when `allowed_as_formal_score=true` | `score_result:{owner_id}:job_match:{analysis_ref}:{score_rule_version_id}` | `analysis_ref` | persisted score ref | DB retry only | if score invalid, skip formal score and mark task `partial` | `partial` or `validation_failed` | score response fields, validation failed no formal score |
| `job_match_graph` | `complete_ai_task` | existing `AiTaskStatus` / API async task semantics | graph state | final task status, sanitized timeline refs | set terminal `status` | write task result/status | `ai_task:{ai_task_id}:complete` | persistence refs | terminal state summary | idempotent complete only | terminal failure result with sanitized error | `succeeded`, `partial`, `low_confidence`, `validation_failed`, `source_unavailable`, `generation_failed` | async task status, no raw payload |

### 5.3 Method-level pseudo-flow

```python
def run_job_match_graph(command):
    state = start_state(command)
    state = load_binding_versions(state)
    state = build_job_match_source_bundle(state)
    llm_output = run_job_match_analyzer(state)  # wraps LlmJobMatchAnalyzer.analyze
    normalized = normalize_job_match_payload(llm_output, state.source_bundle_ref)
    score_candidate = job_match_score_gate(normalized, state.score_rule_version_id)
    state = persist_job_match_analysis(state, normalized)
    if score_candidate.allowed_as_formal_score:
        state = persist_score_result(state, score_candidate)
    return complete_ai_task(state)
```

`run_job_match_analyzer` 的唯一 LLM input package 形态为 `LlmTransportRequest(contract_ids=JOB_MATCH_CONTRACT_IDS, task_type="job_match_analysis", input_refs=_source_input_refs(source_bundle), evidence_bundle=_evidence_bundle(source_bundle))`。`evidence_bundle` 只能包含 compact source refs、chunk refs、digest、dimension hints 和安全摘要，不包含完整简历 Markdown、完整 JD、raw prompt、raw completion 或 provider payload。

## 6. `resume_analysis_graph` 节点级 contract

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `resume_analysis_graph` | `load_resume_version` | Resume repository path from current resume/job binding flow | `owner_id`, `resume_version_id` | markdown ref, version metadata, availability | set `resume_markdown_ref`, digest seed | read-only | `resume_analysis:{owner_id}:{resume_version_id}:load` | none | sanitized resume version ref | no graph retry | source unavailable | `not_found_or_inaccessible` / `source_unavailable` | owner scoped, deleted source |
| `resume_analysis_graph` | `parse_resume_markdown` | deterministic parser to be located/frozen by PR5 | markdown ref, allowed parser config | section candidates | set `section_refs`, parser warnings | none | `resume_analysis:{resume_version_id}:{digest}:parse` | loaded ref | section digest only | deterministic retry not needed | empty sections -> low confidence | `validation_failed` | empty markdown, malformed markdown |
| `resume_analysis_graph` | `chunk_resume_sections` | deterministic chunker by PR5 | section candidates | chunk refs and chunk digests | update `section_refs` | optional snapshot write if PR5 adds repository | `resume_analysis:{resume_version_id}:{digest}:chunk` | parse summary | chunk digest summary | no retry | coarse single chunk with low confidence if allowed by PR5 | `low_confidence` | chunk count, no raw text in checkpoint |
| `resume_analysis_graph` | `extract_resume_signals` | deterministic signal extractor by PR5; no LLM unless contract is added | chunk refs | signal refs, quality flags | set `signal_refs`, `quality_flags` | none | `resume_analysis:{resume_version_id}:{digest}:signals` | chunk summary | signal summary | no LLM retry | insufficient signals -> low confidence | `low_confidence` | signal extraction sparse |
| `resume_analysis_graph` | `resume_signal_quality_gate` | `SCORING_SPEC.md` / `SEMANTICS_GLOSSARY.md` low confidence semantics | signal refs, section refs | validation result | set `validation_status`, `source_availability` | none | `resume_analysis:{resume_version_id}:{digest}:gate` | signal summary | validation summary | no retry | block only when source unavailable or parse invalid | `validation_failed`, `low_confidence` | confidence flags |
| `resume_analysis_graph` | `persist_resume_analysis_snapshot` | PR5 repository handoff; active docs do not yet define final table | validated snapshot | snapshot ref | set snapshot ref | write snapshot/trace/evidence if PR5 authorizes table | `resume_analysis:{owner_id}:{resume_version_id}:{digest}:snapshot` | validation summary | persisted snapshot ref | DB retry only | no snapshot -> downstream builds direct source bundle and marks partial | `partial` | checkpoint non-truth, repository truth |
| `resume_analysis_graph` | `complete_ai_task` | `AiTask` status protocol | graph state | terminal status | set terminal status | write task result/status | `ai_task:{ai_task_id}:complete` | persistence refs | terminal summary | idempotent complete | sanitized failure | terminal API status enum | task status redacted |

## 7. 旧代码迁移矩阵

| Existing Symbol | Target Node/Tool/Validator | keep/wrap/split/deprecate/delete | PR | Tests |
|---|---|---|---|---|
| `LlmJobMatchAnalyzer.analyze` | `run_job_match_analyzer` | wrap | PR5 | `test_llm_analyzer_normalizes_loose_provider_payload_shapes`, provider unavailable |
| `LlmTransportRequest` | LLM tool input package | keep | PR2-PR8 | compact bundle and raw-off scan |
| `_source_input_refs`, `_evidence_bundle` | `build_job_match_source_bundle` / LLM tool adapter | keep/wrap | PR5 | prompt bundle excludes raw resume/JD |
| `_normalize_job_match_payload` | `normalize_job_match_payload` | keep/split | PR5 | loose payload, uncovered job chunks |
| `_normalize_dimension_scores` and score helpers | `job_match_score_gate` | split | PR5 | 0/100 bounds, score rule version, no exact probability |
| Existing job match repository write path | `persist_job_match_analysis` | keep/wrap | PR5 | persisted completed result/source digest |
| Future ScoreResult repository | `persist_score_result` | wrap once implemented | PR5 | validation failed no formal score |
| Existing direct use case analyzer invocation | `AiOrchestrationFacade.start_job_match_graph` | deprecate after graph parity | PR5 | API compatibility tests |
| Full raw resume/JD in runtime state | none | delete/forbid | PR5 | checkpoint/API/log raw-off scan |

## 8. 与 active docs 的关系

本文不替代 `APPLICATION_FLOW_SPEC.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`API_SPEC.md` 或 `SECURITY_PRIVACY.md`。`job_match_graph` 必须复用 active `P-JOBMATCH-*` contract；`resume_analysis_graph` 在 contract 未冻结前只能作为 deterministic source bundle graph。

## 9. 非目标

- 不实现 graph。
- 不新增 endpoint。
- 不写 ORM / migration。
- 不创建正式 Weakness、Asset 或 TrainingRecommendation。
- 不暴露 raw prompt/completion/provider payload。
- 不把 checkpoint 当成业务事实源。

## 10. 后续 PR 使用方式

PR5 使用本文实现 Job Match Graph。若 PR5 需要独立 Resume Analysis Graph，必须先确认 `P-RESUME-*` 或等价 deterministic contract 是否进入 active docs，并明确 repository target、validator symbol 和 F7 fixture。

## 11. Definition of Done

- 两个 graph 的目标、state、node、edge、conditional edge、checkpoint、retry/fallback、persistence、trace、tests 已列明。
- `job_match_graph` 与 `P-JOBMATCH-*`、`ScoreResult(job_match)`、candidate confirmation 边界对齐。
- `resume_analysis_graph` 的 contract 缺口已冻结为 PR5 文件/symbol 边界。
- checkpoint 非业务事实源、raw payload 禁止已明确。
