---
title: 打磨模式 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-polish
---

# 打磨模式 LangGraph 实施计划

## 1. 文档目的

本文规划 `polish_progress_tree_graph`、`polish_question_graph`、`polish_feedback_graph` 的 skeleton，确保 answer save 与 feedback generation 的 AI / 非 AI 边界清晰。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`
- `docs/02-design/prompt-contracts/POLISH_CONTRACTS.md`

## 3. 当前状态

打磨模式已有题目生成、回答保存、反馈生成、评分、失分点、候选提炼等 active 设计。当前必须保留：answer save 不触发 LLM；feedback 生成是独立 AI task；Core UseCase 不直接依赖 LangGraph。

## 4. 目标输出

- 三个 Polish graph skeleton。
- 明确旧 `PolishQuestionLlmService` / `PolishFeedbackLlmService` 迁移策略由 PR6 补齐。

## 5. 必须覆盖范围

| Graph | 目标 | State 字段占位 | Node 清单 | Edge / conditional edge | Checkpoint | Retry / fallback | Persistence targets | LLM trace capture | 测试计划 |
|---|---|---|---|---|---|---|---|---|---|
| `polish_progress_tree_graph` | 生成或刷新 session progress tree | `session_id`, `job_version_id`, `resume_version_id`, `progress_tree_ref`, `turn_refs`, `node_refs`, `priority_ref`, `trace_refs` | `load_polish_session_context`, `build_progress_context`, `generate_progress_tree_plan`, `progress_tree_quality_gate`, `persist_progress_tree_state`, `complete_ai_task` | no tree -> plan; existing tree -> refresh; insufficient context -> low confidence | context 后、plan 后、persist 后 | schema invalid retry；context 不足不伪造节点 | progress tree/state、`ai_task_results`、trace/evidence | prompt version、chunk refs、validation | no fake tree、state refresh 不丢 node ref |
| `polish_question_graph` | 基于进展节点生成题目 | `session_id`, `progress_node_id`, `topic_ref`, `question_candidate`, `anti_repeat_refs`, `trace_refs` | `load_polish_session_context`, `validate_question_request`, `build_progress_context`, `refresh_progress_tree_if_needed`, `select_progress_node`, `generate_question_candidate`, `question_quality_gate`, `persist_question`, `complete_ai_task` | missing node -> validation_failed; duplicate -> retry/low confidence; source unavailable -> partial | context 后、candidate 后、gate 后、persist 后 | 题目过泛/重复可 retry；RAG 空降级 deterministic topic question | `questions`, `ai_task_results`, trace/evidence, low confidence | `P-POLISH-002`、sanitized digest、anti-repeat summary | duplicate、progress node、source unavailable、no candidate formal |
| `polish_feedback_graph` | 对已保存 Answer 生成 feedback / score / candidates | `question_id`, `answer_id`, `answer_round`, `feedback_candidate`, `score_ref`, `candidate_refs`, `trace_refs` | `load_answer_context`, `validate_feedback_request`, `build_feedback_input`, `build_deterministic_feedback_seed`, `generate_feedback_candidate`, `feedback_schema_gate`, `feedback_consistency_gate`, `extract_weakness_asset_candidates`, `enhance_candidates_with_llm_if_enabled`, `persist_feedback`, `update_progress_state`, `complete_ai_task` | answer too short -> low confidence; validation failed -> no score; candidate -> confirmation handoff | answer context 后、candidate 后、validation 后、persist 后 | schema invalid retry；score missing 不写 `ScoreResult`; deterministic seed 保底 | `feedback`, `score_results(polish_answer)`, loss points, candidates, trace/evidence | contract ids、answer ref、validation/fallback | answer save no LLM、feedback independent task、legacy compatibility |

## 6. 与 active docs 的关系

本文遵循 `APPLICATION_FLOW_SPEC.md` 对 question / answer / feedback 的同步异步拆分，遵循 `PROMPT_SPEC.md` 的 `P-POLISH-*` registry，遵循 `SCORING_SPEC.md` 的 `polish_answer` 评分边界，遵循 `SECURITY_PRIVACY.md` 的 LLM 输入最小化和 trace 边界。

## 7. 非目标

- 不实现 PR6 迁移。
- 不改 API。
- 不改旧 service。
- 不引入真实 provider。
- 不引入向量库。
- 不把候选写成正式对象。

## 8. 后续 PR 使用方式

PR6 按本文把旧 question/feedback LLM service 收敛到 facade + graph runner 后方，并保持现有 API 与 legacy `feedback_text` 兼容。

## 9. Definition of Done

- 三个 Polish graph 的 state、node、edge、conditional edge、checkpoint、retry/fallback、persistence、trace、tests 已覆盖。
- 明确 answer save 不触发 LLM。
- 明确 feedback 是独立 AI task。
- 明确旧服务迁移由 PR6 补齐。

