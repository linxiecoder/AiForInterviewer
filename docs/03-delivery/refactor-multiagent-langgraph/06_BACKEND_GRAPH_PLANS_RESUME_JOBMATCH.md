---
title: 简历分析与岗位匹配 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-resume-jobmatch
---

# 简历分析与岗位匹配 LangGraph 实施计划

## 1. 文档目的

本文规划 `resume_analysis_graph` 与 `job_match_graph` 的 graph skeleton，覆盖目标、state、node、edge、conditional edge、checkpoint、retry/fallback、persistence、LLM trace 和测试计划。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md`

## 3. 当前状态

`job_match_graph` 有 `P-JOBMATCH-*` contract 和 `job_match` score 依据。`resume_analysis_graph` 目前更多来自 LangGraph 重构输入，PR1 不新增 `P-RESUME-*` contract；是否需要独立 contract 由 PR5 前 recon 决定。

## 4. 目标输出

- `resume_analysis_graph` skeleton。
- `job_match_graph` skeleton。
- 明确 Core UseCase 不直接依赖 LangGraph。

## 5. 必须覆盖范围

| Graph | 目标 | State 字段占位 | Node 清单 | Edge / conditional edge | Checkpoint | Retry / fallback | Persistence targets | LLM trace capture | 测试计划 |
|---|---|---|---|---|---|---|---|---|---|
| `resume_analysis_graph` | 分析 `ResumeVersion` Markdown，生成结构化 source bundle / snapshot | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `resume_id`, `resume_version_id`, `resume_markdown_ref`, `section_refs`, `signal_refs`, `quality_flags`, `trace_refs`, `evidence_refs`, `error_state` | `load_resume_version`, `parse_resume_markdown`, `chunk_resume_sections`, `extract_resume_signals`, `resume_signal_quality_gate`, `persist_resume_analysis_snapshot`, `complete_ai_task` | `START -> load -> parse -> chunk -> extract -> gate -> persist -> complete`; source unavailable -> low confidence; parse failed -> validation_failed | load 后、extract 后、gate 后、persist 后；checkpoint 非事实源 | parse 失败走 validation_failed；信号不足走 low confidence；不扩大输入范围 | `ai_tasks`, `ai_task_results`, `trace_refs`, `evidence_refs`, resume analysis snapshot by PR5 | sanitized input refs、quality flags、hash、validation summary | owner、空 markdown、source unavailable、low confidence、checkpoint 非 truth source、no raw payload |
| `job_match_graph` | 基于岗位/简历绑定生成岗位匹配分析和 `job_match` 评分 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `binding_id`, `job_version_id`, `resume_version_id`, `score_rule_version_id`, `source_bundle_ref`, `analysis_ref`, `score_result_ref`, `candidate_refs`, `trace_refs`, `error_state` | `load_binding_versions`, `build_job_match_source_bundle`, `run_job_match_analyzer`, `normalize_job_match_payload`, `job_match_score_gate`, `persist_job_match_analysis`, `persist_score_result`, `complete_ai_task` | `START -> load -> bundle -> analyze -> normalize -> score_gate -> persist_analysis -> persist_score -> complete`; missing source -> partial; validation failed -> no formal score; candidate -> confirmation | source bundle 后、LLM 后、score gate 后、persistence 后 | schema invalid 可 repair/retry；score rule missing 不写 `ScoreResult`; provider failed -> generation_failed | `job_match_analyses`, `score_results`, `weakness_candidates`, `ai_task_results`, `trace_refs`, `evidence_refs` | `P-JOBMATCH-*`, sanitized bundle digest、validation errors、usage/failure | normal、owner mismatch、0/100 score、source unavailable、validation failed、no exact probability、candidate not formal |

## 6. 与 active docs 的关系

本文不替代 `APPLICATION_FLOW_SPEC.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`DATA_MODEL.md` 或 `SECURITY_PRIVACY.md`。`job_match_graph` 必须复用 active contract；`resume_analysis_graph` 在 contract 未补齐前只能作为 skeleton。

## 7. 非目标

- 不实现 graph。
- 不新增 endpoint。
- 不写 ORM / migration。
- 不创建正式 Weakness。
- 不暴露 raw prompt/completion/provider payload。

## 8. 后续 PR 使用方式

PR5 使用本文实现 Job Match Graph；若 PR5 需要独立 Resume Analysis Graph，必须先确认 `P-RESUME-*` 或等价 deterministic contract 是否进入 active docs。

## 9. Definition of Done

- 两个 graph 的目标、state、node、edge、conditional edge、checkpoint、retry/fallback、persistence、trace、tests 已列明。
- `job_match_graph` 与 `P-JOBMATCH-*`、`ScoreResult(job_match)`、candidate confirmation 边界对齐。
- checkpoint 非业务事实源、raw payload 禁止已明确。

