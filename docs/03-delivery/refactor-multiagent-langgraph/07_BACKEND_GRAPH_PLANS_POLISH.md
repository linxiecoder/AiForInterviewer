---
title: 打磨模式 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-polish
---

# 打磨模式 LangGraph 实施计划

## 1. 文档目的

本文规划 `polish_progress_tree_graph`、`polish_question_graph`、`polish_feedback_graph` 的 implementation-ready graph spec，确保 answer save 与 feedback generation 的 AI / 非 AI 边界清晰，并把当前 Polish 旧代码迁移到 graph facade 后方。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `docs/02-design/prompt-contracts/POLISH_CONTRACTS.md`
- 代码 recon：`PolishUseCases.create_question_task/create_answer/create_feedback_task/refresh_progress_tree_state`、`PolishQuestionLlmService`、`PolishFeedbackLlmService`、`build_deterministic_progress_node_question`、`validate_question_quality`、`validate_feedback_consistency`、`extract_feedback_candidates`、`PolishCandidateLlmService`、`SqlAlchemyPolishRepository.add_question/add_feedback/update_progress_tree/add_task`
- tests：`test_polish_api.py`、`test_polish_question_llm.py`、`test_polish_feedback_llm.py`、`test_polish_candidates.py`

## 3. 当前状态

打磨模式已有题目生成、回答保存、反馈生成、评分、失分点、候选提炼和候选确认的代码与测试。当前必须保留：

- answer save 不触发 LLM；`PolishUseCases.create_answer` 保持 Core Business 同步写入和 idempotency 语义。
- feedback 生成是独立 AI task；不能由 answer save 隐式触发。
- Core UseCase 不直接依赖 LangGraph；由 `AiOrchestrationFacade` 或等价 facade 启动 graph。
- candidate / suggestion 不自动升级 formal object。
- raw prompt、raw completion、provider payload 不进入 checkpoint、日志或 API response。

## 4. Graph 总览

| Graph | 目标 | State 字段 | Edge / conditional edge | Persistence targets | Trace policy | Tests |
|---|---|---|---|---|---|---|
| `polish_progress_tree_graph` | 生成或刷新 session progress tree | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `session_id`, `job_version_id`, `resume_version_id`, `progress_tree_ref`, `turn_refs`, `node_refs`, `priority_ref`, `validation_status`, `trace_refs`, `evidence_refs`, `error_state` | no tree -> generate initial; existing tree -> refresh; insufficient context -> low confidence | progress tree/state via `update_progress_tree`, `ai_task_results`, trace/evidence | sanitized context digest and node refs only | no fake tree, refresh keeps node refs, insufficient context |
| `polish_question_graph` | 基于 progress node 生成题目 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `session_id`, `progress_node_id`, `topic_ref`, `requested_progress_node_ref`, `completed_focus_refs`, `question_candidate`, `anti_repeat_refs`, `trace_refs`, `evidence_refs`, `error_state` | missing node -> validation failed; duplicate -> retry/low confidence; source unavailable -> partial | `questions`, `ai_task_results`, trace/evidence, low confidence flags | `P-POLISH-002`, sanitized digest, anti-repeat summary | duplicate, progress node, source unavailable, no candidate formal |
| `polish_feedback_graph` | 对已保存 answer 生成 feedback / score / candidates | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `session_id`, `question_id`, `answer_id`, `answer_round`, `feedback_candidate`, `score_candidate`, `score_ref`, `candidate_refs`, `trace_refs`, `evidence_refs`, `error_state` | answer too short -> low confidence; validation failed -> no score; candidate -> confirmation handoff | `feedback`, `score_results(polish_answer)`, loss points, candidates, trace/evidence | contract ids, answer ref, validation/fallback summary | answer save no LLM, feedback independent task, legacy compatibility |

## 5. `polish_question_graph` 方法级样板

### 5.1 Current method split

`PolishUseCases.create_question_task` 当前完成 session 校验、progress tree readiness、requested node 解析、LLM/fallback 题目生成、metadata 合并、`PolishQuestion` 创建、`SqlAlchemyPolishRepository.add_question` 和 `add_task`。PR6 graph 化时拆分如下：

| Current block | Target node | Strategy |
|---|---|---|
| `get_session` + status validation | `load_polish_session_context` / `validate_question_request` | keep business validation, wrap in graph node |
| progress tree status / plan validation | `validate_progress_tree_ready` | split from question generation |
| `_combined_completed_focus_refs` / `_progress_context_with_completed_focus_refs` | `build_progress_context` | keep deterministic helper |
| follow-up branch `_build_follow_up_question_draft` | `build_follow_up_question_candidate` | keep Core deterministic branch; no provider |
| `PolishQuestionLlmService.generate_with_llm_or_fallback` | `generate_question_candidate` | wrap |
| `build_deterministic_progress_node_question` | deterministic fallback tool | keep |
| `validate_question_quality` | `question_quality_gate` | keep as validator |
| `PolishQuestion(...)` + `add_question` | `persist_question` | wrap repository write |
| `PolishTaskStatus(...)` + `add_task` | `complete_ai_task` | wrap task status write |

### 5.2 Node contract 表

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `polish_question_graph` | `load_polish_session_context` | `PolishUseCases.get_session`, `_build_session_detail` | `owner_id`, `session_id` | session, detail refs, progress context refs | set `job_version_id`, `resume_version_id`, progress refs | read-only | `polish_question:{owner_id}:{session_id}:load` | none | sanitized context refs | no graph retry | source unavailable -> partial/low confidence | `not_found_or_inaccessible`, `source_unavailable` | owner and session status |
| `polish_question_graph` | `validate_question_request` | `_validate_question_generation_request`, `_question_generation_mode`, `_question_generation_requested_ref` | command, session detail | request metadata, requested ref | set `requested_progress_node_ref`, generation mode | none | `polish_question:{session_id}:{request_digest}:validate` | context refs | request validation summary | no retry | fail closed | `validation_failed` | invalid topic/node/mode |
| `polish_question_graph` | `validate_progress_tree_ready` | progress tree checks in `create_question_task`; `_has_valid_progress_tree_plan` | detail progress status/plan | ready flag | set `validation_status` | none | `polish_question:{session_id}:tree-ready:{plan_digest}` | request summary | ready/failed summary | no retry | call `polish_progress_tree_graph` only if PR6 facade authorizes refresh; otherwise fail closed | `validation_failed` / `low_confidence` | insufficient context, refresh failed accepted |
| `polish_question_graph` | `build_progress_context` | `_combined_completed_focus_refs`, `_progress_context_with_completed_focus_refs` | detail context, completed refs | compact context | set `completed_focus_refs`, `anti_repeat_refs` | none | `polish_question:{session_id}:{progress_node_ref}:context:{completed_focus_hash}` | ready summary | context digest | deterministic | use original context with low confidence only when completed refs malformed but optional | `validation_failed` | completed focus, anti-repeat |
| `polish_question_graph` | `refresh_progress_tree_if_needed` | `PolishUseCases.refresh_progress_tree_state`, `PolishProgressTreeLlmService.generate_initial/refresh_state` | context, plan, state | refreshed plan/state refs | update progress refs | `update_progress_tree` only through repository | `polish_tree:{owner_id}:{session_id}:{context_digest}` | context digest | refreshed tree refs | graph-level retry only for provider/runtime failure | existing valid tree remains authoritative if refresh fails | `partial` / `low_confidence` | refresh does not drop node refs |
| `polish_question_graph` | `select_progress_node` | `resolve_progress_node`, `build_progress_node_question_context` | plan/state/requested ref | resolved progress node | set `progress_node_id` | none | `polish_question:{session_id}:{requested_ref}:select-node` | plan/state refs | resolved node ref | no retry | fallback priority only if requested ref absent | `validation_failed` | requested node, current priority |
| `polish_question_graph` | `generate_question_candidate` | `PolishQuestionLlmService.generate_with_llm_or_fallback`; `build_deterministic_progress_node_question` | session, compact context, plan/state, requested ref | `PolishQuestionDraft` candidate | set `question_candidate`, LLM metadata summary | LLM call only through transport wrapper | `polish_question:{session_id}:{progress_node_id}:{context_digest}:llm` | node/context digest | candidate digest and metadata summary | provider/schema/semantic retry budget from LLM service | deterministic builder; feature/real-provider disabled fallback | `generation_failed`, `low_confidence` | feature disabled, real-provider gate, fake accepted |
| `polish_question_graph` | `question_quality_gate` | `validate_question_quality`, `repair_question_text`, `fallback_question_text` | candidate, pattern, evidence refs, recent questions | quality result, optional repaired candidate | set quality score, blocking/warnings | none | `polish_question:{session_id}:{candidate_digest}:quality` | candidate digest | quality summary | one repair pass if safe | deterministic fallback question with low confidence | `validation_failed` / `low_confidence` | duplicate, answer leak, unsupported entity |
| `polish_question_graph` | `persist_question` | `SqlAlchemyPolishRepository.add_question`, `_metadata_for_new_question` | accepted candidate, metadata, owner/session | question ref | set `question_ref` | write `questions` | `question:{owner_id}:{session_id}:{progress_node_id}:{candidate_digest}` | quality summary | persisted question ref | DB retry only | none; fail closed before task success | `generation_failed` | API readback, no raw payload metadata |
| `polish_question_graph` | `complete_ai_task` | `PolishTaskStatus`, `SqlAlchemyPolishRepository.add_task` | state and question ref | task result | terminal status | write task status | `ai_task:{ai_task_id}:complete` | question ref | terminal sanitized summary | idempotent complete | sanitized failure result | terminal API status enum | task contract shape |

### 5.3 Method-level pseudo-flow

```python
def run_polish_question_graph(command):
    state = load_polish_session_context(command)
    state = validate_question_request(state)
    state = validate_progress_tree_ready(state)
    state = build_progress_context(state)
    state = refresh_progress_tree_if_needed(state)
    state = select_progress_node(state)
    state = generate_question_candidate(state)  # wraps PolishQuestionLlmService + deterministic builder
    state = question_quality_gate(state)        # wraps validate_question_quality
    state = persist_question(state)             # wraps SqlAlchemyPolishRepository.add_question
    return complete_ai_task(state)
```

`question_candidate` 不是 formal object；它只有通过 `persist_question` 写入 `questions` 后才成为业务题目。checkpoint 只保存 candidate digest、quality summary、refs 和 failure summary。

## 6. `polish_progress_tree_graph` 节点级 contract

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `polish_progress_tree_graph` | `load_polish_session_context` | `_build_session_detail`, `_resolve_job_version`, `_resolve_resume_version` | owner/session | detail refs, compact progress context | set source refs | read-only | `polish_tree:{owner_id}:{session_id}:load` | none | context refs | no retry | source unavailable -> insufficient | `not_found_or_inaccessible` / `source_unavailable` | owner scoped |
| `polish_progress_tree_graph` | `build_progress_context` | `_progress_artifacts_with_theme`, `_session_theme_strategy` | detail progress context | themed compact context | set context digest | none | `polish_tree:{session_id}:context:{source_digest}` | source refs | digest | deterministic | low confidence if sparse | `low_confidence` | compact only |
| `polish_progress_tree_graph` | `generate_progress_tree_plan` | `PolishProgressTreeLlmService.generate_initial`, `PolishProgressTreeV2Pipeline.generate_initial` | context | plan/state artifacts | set plan/state candidates | LLM call if feature path enabled | `polish_tree:{session_id}:{context_digest}:plan` | context digest | candidate plan digest | provider/schema retry budget | deterministic/failed artifacts from progress tree helpers | `generation_failed` / `low_confidence` | no fake tree |
| `polish_progress_tree_graph` | `progress_tree_quality_gate` | `_normalize_plan`, `_normalize_state`, `_state_matches_plan`, quality-first validation helpers | plan/state artifacts | validated artifacts | set `validation_status`, flags | none | `polish_tree:{session_id}:{plan_digest}:gate` | candidate digest | validation summary | one normalize/repair pass | failed/insufficient artifacts | `validation_failed` / `low_confidence` | node refs stable |
| `polish_progress_tree_graph` | `persist_progress_tree_state` | `SqlAlchemyPolishRepository.update_progress_tree` | validated artifacts | persisted session progress refs | set `progress_tree_ref`, priority refs | write progress tree/state | `polish_tree:{owner_id}:{session_id}:{plan_digest}:persist` | validation summary | persisted refs | DB retry only | keep previous tree if refresh failed and previous tree valid | `partial` | refresh keeps existing refs |
| `polish_progress_tree_graph` | `complete_ai_task` | task status protocol | graph state | task result | terminal status | task write | `ai_task:{ai_task_id}:complete` | persistence refs | terminal summary | idempotent | sanitized failure | terminal API status enum | task status |

## 7. `polish_feedback_graph` 节点级 contract

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `polish_feedback_graph` | `load_answer_context` | `PolishUseCases.create_feedback_task` load session/answer/question/list previous answers/feedbacks | owner, session, answer | answer context refs, previous feedback summary | set `question_id`, `answer_round`, compact previous refs | read-only | `polish_feedback:{owner_id}:{session_id}:{answer_id}:load` | none | answer context refs | no retry | answer missing fail closed | `not_found_or_inaccessible` | answer/session/question owner |
| `polish_feedback_graph` | `validate_feedback_request` | answer/session checks in use case; `_validate_answer_text` is answer-save only | answer context | request valid | set validation status | none | `polish_feedback:{answer_id}:validate` | context refs | validation summary | no retry | short answer -> low confidence feedback allowed only if active API permits | `validation_failed` / `low_confidence` | answer too short |
| `polish_feedback_graph` | `build_feedback_input` | `_build_feedback_input`, `_compact_previous_feedback_summary` | session, question, answer, previous feedbacks | compact feedback input | set feedback input digest | none | `polish_feedback:{answer_id}:{answer_round}:input` | validation summary | input digest | deterministic | previous feedback absent -> first answer mode | `partial` | compact input only |
| `polish_feedback_graph` | `build_deterministic_feedback_seed` | `_build_deterministic_structured_feedback_payload` | feedback input, generated ids | deterministic payload | set seed digest | none | `polish_feedback:{answer_id}:{feedback_id}:seed` | input digest | seed digest | deterministic | safe minimum payload | `low_confidence` | deterministic payload fields |
| `polish_feedback_graph` | `generate_feedback_candidate` | `PolishFeedbackLlmService.generate_with_llm_or_fallback` | feedback input, deterministic seed | feedback candidate payload | set candidate digest and metadata summary | LLM call via transport wrapper | `polish_feedback:{answer_id}:{input_digest}:llm` | seed digest | candidate digest | provider/schema/consistency retry budget in service | deterministic seed; feature/real-provider disabled fallback | `generation_failed` / `low_confidence` | fake accepted, fallback reasons |
| `polish_feedback_graph` | `feedback_schema_gate` | `validate_feedback_llm_output`, `adapt_llm_output_to_structured_payload` | candidate payload | schema-valid payload | set schema validation status | none | `polish_feedback:{feedback_id}:schema:{candidate_digest}` | candidate digest | schema summary | one repair pass if service supports it | deterministic seed | `validation_failed` | schema invalid fallback |
| `polish_feedback_graph` | `feedback_consistency_gate` | `validate_feedback_consistency`, `compute_score_result_from_dimensions` | schema-valid payload | normalized payload and score candidate | set normalized digest, score candidate | none | `polish_feedback:{feedback_id}:consistency:{payload_digest}` | schema summary | consistency summary | one repair pass | safe structured fallback | `validation_failed` / `low_confidence` | score repair, retry delta invalid, no leaks |
| `polish_feedback_graph` | `extract_weakness_asset_candidates` | `extract_feedback_candidates`, `CandidateExtractionInput`, `safe_candidate_dict` | normalized payload, question metadata | candidate refs/payloads | set candidate refs | none | `polish_feedback:{feedback_id}:extract-candidates:{payload_digest}` | consistency summary | candidate summary | deterministic | no structured material -> empty candidate lists | `partial` | candidate refs, no formal write |
| `polish_feedback_graph` | `enhance_candidates_with_llm_if_enabled` | `PolishCandidateLlmService.enhance_with_llm_or_fallback` | candidate payload | enhanced candidate payload | update candidate metadata summary | LLM call only if feature and real-provider gates allow | `polish_feedback:{feedback_id}:candidate-llm:{candidate_digest}` | candidate summary | enhancement summary | provider/schema retry budget | fallback with candidate-only payload | `partial` / `low_confidence` | fake provider accepted, forbidden provider payload fallback |
| `polish_feedback_graph` | `persist_feedback` | `SqlAlchemyPolishRepository.add_feedback`; `_serialize_feedback_payload` | normalized/enhanced payload | feedback ref | set `feedback_ref` | write `feedback` | `feedback:{owner_id}:{answer_id}:{feedback_id}` | final payload summary | persisted feedback ref | DB retry only | fail closed before task success | `generation_failed` | API response sanitizer, legacy compatibility |
| `polish_feedback_graph` | `persist_score` | `ScoreType.POLISH_ANSWER`, score payload from feedback; PR6 ScoreResult repository handoff | score candidate, feedback ref | score ref | set `score_ref` | write `score_results(polish_answer)` when repository exists | `score_result:{owner_id}:polish_answer:{feedback_id}:{score_version}` | feedback ref | score ref or skipped reason | DB retry only | if invalid, skip formal score and mark task partial | `partial` / `validation_failed` | score consistency, allowed_as_formal_score |
| `polish_feedback_graph` | `persist_candidates` | `PolishCandidateRepository.upsert_from_feedback_payload` | candidate payload | persisted candidate refs | set `candidate_refs` | upsert candidates only | `polish_candidates:{owner_id}:{feedback_id}:{candidate_digest}` | candidate summary | candidate refs | DB retry only | empty candidate list | `partial` | owner-scoped merge keys, no formal write |
| `polish_feedback_graph` | `update_progress_state` | `_progress_tree_state_with_completed_question`, `update_progress_tree` | feedback ref, answer/question refs | updated progress state | set progress update refs | update progress tree state | `polish_progress:{owner_id}:{session_id}:{answer_id}:feedback` | feedback ref | progress update summary | DB retry only | no-op if progress tree unavailable, mark partial | `partial` | state update logic |
| `polish_feedback_graph` | `complete_ai_task` | `PolishTaskStatus`, `SqlAlchemyPolishRepository.add_task` | state refs | task result | terminal status | write task status | `ai_task:{ai_task_id}:complete` | persistence refs | terminal summary | idempotent | sanitized failure | terminal API status enum | feedback independent task |

## 8. Answer Save 非 AI 边界

`PolishUseCases.create_answer` 保留在 Core Business，不迁入 LangGraph。它只做 session/question owner 校验、answer text validation、idempotency key conflict detection、answer round 计算和 `add_answer` 写入。PR6 必须保留测试断言：提交 answer 不调用 `PolishFeedbackLlmService`、不启动 graph、不同 answer payload 复用 idempotency key 返回 validation error。

## 9. 旧代码迁移矩阵

| Existing Symbol | Target Node/Tool/Validator | keep/wrap/split/deprecate/delete | PR | Tests |
|---|---|---|---|---|
| `PolishUseCases.create_question_task` | `polish_question_graph` facade entry | split | PR6 | question API compatibility |
| `PolishQuestionLlmService.generate_with_llm_or_fallback` | `generate_question_candidate` | wrap | PR6 | feature disabled, real-provider gate, fake accepted |
| `build_deterministic_progress_node_question` | deterministic question fallback | keep | PR6 | deterministic progress node question |
| `validate_question_quality` | `question_quality_gate` | keep | PR6 | duplicate, answer leak, unsupported entity |
| `PolishUseCases.refresh_progress_tree_state` | `polish_progress_tree_graph` facade entry | split | PR6 | refresh keeps refs |
| `PolishUseCases.create_answer` | Core answer save | keep | PR6 | answer save no LLM, idempotency |
| `PolishUseCases.create_feedback_task` | `polish_feedback_graph` facade entry | split | PR6 | feedback API compatibility |
| `_build_feedback_input` / `_compact_previous_feedback_summary` | `build_feedback_input` | keep | PR6 | compact previous feedback only |
| `_build_deterministic_structured_feedback_payload` | `build_deterministic_feedback_seed` | keep | PR6 | deterministic fallback |
| `PolishFeedbackLlmService.generate_with_llm_or_fallback` | `generate_feedback_candidate` | wrap | PR6 | fake accepted, fallback metadata |
| `validate_feedback_consistency` | `feedback_consistency_gate` | keep | PR6 | score repair, no leak |
| `extract_feedback_candidates` | `extract_weakness_asset_candidates` | wrap | PR6/PR8 | candidate refs, no formal write |
| `PolishCandidateLlmService.enhance_with_llm_or_fallback` | `enhance_candidates_with_llm_if_enabled` | wrap | PR8 | forbidden provider payload fallback |
| `SqlAlchemyPolishRepository.add_question/add_feedback/update_progress_tree/add_task` | persistence nodes | keep/wrap | PR6 | repository write/readback |
| Raw feedback/provider fields in API response | none | delete/forbid | PR6 | response omits raw prompt/completion/provider payload |

## 10. 与 active docs 的关系

本文遵循 `APPLICATION_FLOW_SPEC.md` 对 question / answer / feedback 的同步异步拆分，遵循 `PROMPT_SPEC.md` 的 `P-POLISH-*` registry，遵循 `SCORING_SPEC.md` 的 `polish_answer` 评分边界，遵循 `SECURITY_PRIVACY.md` 的 LLM 输入最小化和 trace 边界。

## 11. 非目标

- 不实现 PR6 迁移。
- 不改 API。
- 不改旧 service。
- 不引入真实 provider。
- 不引入向量库。
- 不把候选写成正式对象。
- 不把 checkpoint 当成业务事实源。

## 12. 后续 PR 使用方式

PR6 按本文把旧 question/feedback LLM service 收敛到 facade + graph runner 后方，并保持现有 API、legacy `feedback_text`、response sanitizer 和候选确认回归测试。

## 13. Definition of Done

- 三个 Polish graph 的 state、node、edge、conditional edge、checkpoint、retry/fallback、persistence、trace、tests 已覆盖。
- `polish_question_graph` 已映射 `PolishUseCases.create_question_task`、`PolishQuestionLlmService`、`build_deterministic_progress_node_question`、`validate_question_quality`、`SqlAlchemyPolishRepository.add_question` 和 progress tree state update 逻辑。
- `polish_feedback_graph` 已覆盖 `persist_feedback`、`persist_score`、candidate extraction/enhancement contract。
- 明确 answer save 不触发 LLM。
- 明确 feedback 是独立 AI task。
