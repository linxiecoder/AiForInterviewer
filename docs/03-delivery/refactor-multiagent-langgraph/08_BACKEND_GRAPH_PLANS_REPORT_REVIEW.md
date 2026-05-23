---
title: 报告与复盘 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-report-review
---

# 报告与复盘 LangGraph 实施计划

## 1. 文档目的

本文规划 `pressure_interview_graph`、`report_generation_graph`、`mock_review_generation_graph`、`real_review_generation_graph` 的 skeleton，覆盖报告、复盘、真实输入确认和 copy boundary。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md`

## 3. 当前状态

Pressure、Report、Review prompt contracts 已作为 Draft 设计存在。PR1 只规划 graph skeleton，不实现 report generation、review generation 或 UI。

## 4. 目标输出

- 四个 graph skeleton。
- `report_generation_graph` 的 orchestrator-worker / parallel section worker 设计占位。
- mock review 与 real review 分流。

## 5. 必须覆盖范围

### 5.1 Graph skeleton 表

| Graph | 目标 | State 字段占位 | Node 清单 | Edge / conditional edge | Checkpoint | Retry / fallback | Persistence targets | LLM trace capture | 测试计划 |
|---|---|---|---|---|---|---|---|---|---|
| `pressure_interview_graph` | 编排压力面开场、题目、追问、节奏、结束检查和报告输入包 | `session_id`, `turn_refs`, `question_refs`, `answer_refs`, `score_ref`, `report_input_ref`, `trace_refs` | `load_pressure_context`, `generate_opening`, `generate_question`, `wait_for_answer_interrupt`, `analyze_answer_quality`, `select_follow_up_strategy`, `generate_follow_up_question`, `control_pace`, `check_end_condition`, `assemble_report_input_package`, `complete_ai_task` | answer missing -> interrupt; continue -> next turn; end -> assemble report input | 每个用户等待点和每个 contract 后 | provider retry；score rule missing 不写正式分；no exact probability | questions, score_results, report input package, trace/evidence | contract ids、turn refs、validation | pause/resume、追问、end check、report input 非报告正文 |
| `report_generation_graph` | 生成报告和 copyable content | `report_type`, `session_ref`, `report_input_package_ref`, `section_worker_results`, `report_ref`, `copy_content_ref`, `trace_refs` | `load_report_sources`, `validate_report_scope`, `build_report_input_package`, `plan_report_sections`, `dispatch_report_section_workers`, `write_report_section`, `section_quality_gate`, `synthesize_report`, `score_report_consistency_gate`, `persist_report`, `prepare_copy_boundary`, `complete_ai_task` | worker failed -> partial; missing score -> low confidence; copy path deterministic if needed | orchestrator plan 后、每个 worker 后、fanin 后、persist 后 | worker-level retry；partial report；不生成文件导出 | reports, report_sections, copyable content, trace/evidence, low confidence | orchestrator + worker sanitized traces | fanout/fanin、partial、no export、no exact probability |
| `mock_review_generation_graph` | 基于系统内模拟面试生成复盘 | `session_ref`, `report_ref`, `turn_refs`, `score_refs`, `review_ref`, `candidate_refs`, `trace_refs` | `load_mock_review_sources`, `build_turn_performance_timeline`, `diagnose_session_performance`, `extract_review_weakness_candidates`, `extract_review_asset_candidates`, `generate_training_suggestions`, `review_quality_gate`, `persist_mock_review`, `complete_ai_task` | missing report -> blocked; low confidence inherited; candidates -> confirmation | context 后、review 后、candidate extraction 后、persist 后 | schema invalid retry；不得重新评分 | interview_reviews, review_items, candidate refs, trace/evidence | review contract ids、source refs | no rescore、candidate-only、source unavailable |
| `real_review_generation_graph` | 基于用户确认的真实面试输入生成复盘 | `real_input_ref`, `user_confirmation_ref`, `job_ref`, `resume_ref`, `review_ref`, `candidate_refs`, `trace_refs` | `load_real_interview_input`, `validate_real_input_completeness`, `redact_third_party_sensitive_fields`, `build_real_review_evidence`, `generate_real_review`, `real_review_quality_gate`, `persist_real_review`, `complete_ai_task` | unconfirmed -> interrupt; incomplete -> low confidence; third-party sensitive -> redacted | structuring 后、confirmation 前后、review 后、persist 后 | 短输入请求补充；不得互联网检索或虚构面试官意图 | real interview input, real review, review items, trace/evidence | third-party redacted summary | confirmed input、no outcome prediction、privacy redaction |

### 5.2 Orchestrator-worker 占位

`report_generation_graph` 的 section worker 不共享 raw prompt，不共享 checkpoint payload。orchestrator 只分配 section plan、source refs、score refs 和 validation rule；worker 返回 section draft、score explanation summary、risk/pass tendency wording 和 copy boundary metadata。

## 6. 与 active docs 的关系

本文只细化 active Prompt contracts 与 `APPLICATION_FLOW_SPEC.md` 的运行编排，不替代 API、DATA、SCORING、SECURITY 或 Prompt canonical 文档。

## 7. 非目标

- 不实现 report/review graph。
- 不新增 endpoint。
- 不生成 PDF/Markdown/docx 文件导出。
- 不重新定义评分公式。
- 不创建正式 Weakness / Asset / TrainingTask。

## 8. 后续 PR 使用方式

PR8 按本文实现 report/review/candidate closure；如 PR5/PR6 需要压力面或报告输入包，必须先在 active flow/API 中确认触发方式。

## 9. Definition of Done

- 四个 graph skeleton 已覆盖。
- `report_generation_graph` 包含 orchestrator-worker / parallel section worker。
- Report / Review 保留 candidate-only、copy boundary、no export、no exact probability、no raw payload。

