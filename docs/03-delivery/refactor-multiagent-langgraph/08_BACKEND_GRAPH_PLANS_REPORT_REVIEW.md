---
title: 报告与复盘 LangGraph 实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-graph-plans-report-review
---

# 报告与复盘 LangGraph 实施计划

## 1. 文档目的

本文规划 `pressure_interview_graph`、`report_generation_graph`、`mock_review_generation_graph`、`real_review_generation_graph` 的 implementation-ready graph spec，覆盖报告、复盘、真实输入确认、parallel section worker、partial report policy、score consistency、third-party redaction 和 copy boundary。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PRESSURE_MODE_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md`

## 3. 当前状态

Pressure、Report、Review prompt contracts 已作为 Draft 设计存在。AIFI-BE-004 已由 `PRESSURE_MODE_SPEC.md` 接受 Pressure mode-level spec；Pressure code 仍是 placeholder，`pressure_interview_graph` 仍不得进入 PR2。请求的代码 recon 清单中没有 report/review repository 或 use case symbol，因此本文冻结 graph contract、state、worker/reducer、persistence target 和 failure policy；PR8 或独立受权 Pressure PR 实现前必须由主 Agent 授权读取或创建对应 repository/tool 文件。

## 4. Graph 总览

| Graph | 目标 | State 字段 | Edge / conditional edge | Persistence targets | Trace policy | Tests |
|---|---|---|---|---|---|---|
| `pressure_interview_graph` | 编排压力面开场、题目、追问、节奏、结束检查和报告输入包；必须先引用 `PRESSURE_MODE_SPEC.md` | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `session_id`, `turn_refs`, `question_refs`, `answer_refs`, `score_ref`, `report_input_ref`, `trace_refs`, `evidence_refs`, `error_state` | answer missing -> interrupt; continue -> next turn; end -> assemble report input | questions, score_results, report input package, trace/evidence | turn refs and validation summaries only | pause/resume, follow-up, end check, report input is not report body |
| `report_generation_graph` | 生成报告、section、score explanation 和 copyable content | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `report_type`, `session_ref`, `report_input_package_ref`, `section_plan`, `section_worker_results`, `report_ref`, `score_ref`, `copy_content_ref`, `trace_refs`, `evidence_refs`, `error_state` | worker failed -> partial; missing score -> low confidence; copy path deterministic if needed | reports, report_sections, copyable content, trace/evidence, low confidence | orchestrator + worker sanitized traces; no raw worker prompt | fanout/fanin, partial, no export, no exact probability |
| `mock_review_generation_graph` | 基于系统内模拟面试生成复盘 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `session_ref`, `report_ref`, `turn_refs`, `score_refs`, `review_ref`, `candidate_refs`, `trace_refs`, `evidence_refs`, `error_state` | missing report -> blocked; low confidence inherited; candidates -> confirmation | interview_reviews, review_items, candidate refs, trace/evidence | source refs only | no rescore, candidate-only, source unavailable |
| `real_review_generation_graph` | 基于用户确认的真实面试输入生成复盘 | `owner_id`, `actor_id`, `ai_task_id`, `agent_run_id`, `real_input_ref`, `user_confirmation_ref`, `job_ref`, `resume_ref`, `review_ref`, `candidate_refs`, `third_party_redaction_summary`, `trace_refs`, `evidence_refs`, `error_state` | unconfirmed -> interrupt; incomplete -> low confidence; third-party sensitive -> redacted | real interview input, real review, review items, trace/evidence | redacted source summary only | confirmed input, no outcome prediction, privacy redaction |

## 5. `report_generation_graph` worker state、Send 和 reducer

### 5.1 Orchestrator state

| Field | Meaning | Rule |
|---|---|---|
| `report_input_package_ref` | `P-PRESSURE-009` 或等价报告输入包引用 | Required; missing -> `source_unavailable` |
| `section_plan[]` | section worker plan | Contains section id, contract ids, source refs, score refs, validation rule refs |
| `section_worker_results[]` | reducer input | Worker returns sanitized section output only |
| `partial_report_policy` | `fail_closed` / `partial_allowed` | Default `partial_allowed` for optional sections; required summary/score missing -> `low_confidence` |
| `score_consistency_summary` | score gate output | Must prove report score aligns with `SCORING_SPEC.md` and source `ScoreResult` |
| `copy_boundary_metadata` | copy content policy | `clipboard_only`, no export, no hidden scoring rule |

### 5.2 Worker state

| Field | Required | Description |
|---|---|---|
| `section_id` | 是 | Stable section id: `summary`, `score`, `risk`, `weakness`, `training`, `copy_content` |
| `contract_ids` | 是 | `P-REPORT-001` to `P-REPORT-004` subset |
| `source_refs` | 是 | Report input package, turn refs, evidence refs, score refs |
| `score_refs` | 否 | Required for score/risk sections |
| `validation_rule_refs` | 是 | Prompt contract and scoring validation refs |
| `section_draft` | 否 | Sanitized section draft; no raw prompt/provider payload |
| `score_explanation_summary` | 否 | Compact score explanation only |
| `risk_pass_tendency_wording` | 否 | No exact probability |
| `copy_boundary_metadata` | 否 | Redaction/copyability flags |
| `worker_status` | 是 | `succeeded`, `partial`, `low_confidence`, `validation_failed`, `generation_failed` |

### 5.3 Send / parallel worker usage

PR8 implementation should use LangGraph `Send` or equivalent fanout only from `dispatch_report_section_workers` after `section_plan` is validated. Each worker receives a section-local state subset; workers do not share raw prompt, raw completion, provider payload or checkpoint payload. Reducer merges by `section_id`, rejects duplicate section ids, preserves required-section failure, and records optional-section partial status.

### 5.4 Reducer policy

| Reducer rule | Output |
|---|---|
| Required `summary` worker fails | report `generation_failed`; no report persistence |
| Required `score` worker missing score refs | report `low_confidence`; persist only if score disclaimer and source status are present |
| Optional `weakness` / `training` worker fails | report `partial`; candidate refs omitted or marked low confidence |
| Any worker returns exact probability or hidden scoring rule | reducer rejects section, sets `validation_failed` |
| Any worker returns raw prompt/completion/provider payload | reducer rejects section and records security validation failure |
| Copy content worker fails | report can persist; `copy_content_available=false` |

## 6. Node contract 表

| Graph | Node | Existing Symbol Mapping | Inputs | Outputs | State Patch | Side Effects | Idempotency Key | Checkpoint Before | Checkpoint After | Retry | Fallback | Failure Status | Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `pressure_interview_graph` | `load_pressure_context` | PR8 pressure use case/repository to locate | owner/session/job/resume refs | compact context | set context refs | read-only | `pressure:{owner_id}:{session_id}:load` | none | source refs | no retry | source unavailable | `source_unavailable` | owner/source |
| `pressure_interview_graph` | `generate_opening` | `P-PRESSURE-*` contract | context | opening message | set turn draft | LLM call via transport | `pressure:{session_id}:opening:{context_digest}` | context digest | opening summary | provider retry | deterministic safe opening | `generation_failed` | no raw payload |
| `pressure_interview_graph` | `generate_question` | pressure question contract | context, turn refs | question candidate | set question candidate | LLM call | `pressure:{session_id}:question:{turn_index}` | turn summary | candidate digest | provider/schema retry | low confidence question | `partial` | question refs |
| `pressure_interview_graph` | `wait_for_answer_interrupt` | runtime interrupt plan | question ref | interrupt ref | set waiting state | write interrupt record | `interrupt:{agent_run_id}:{question_ref}` | question ref | interrupt ref | resume idempotent | timeout/cancel status | `timed_out` / `cancelled` | pause/resume |
| `pressure_interview_graph` | `analyze_answer_quality` | answer quality contract | answer ref | quality refs | set quality refs | optional score write only after gate | `pressure:{session_id}:{answer_ref}:quality` | answer ref | quality summary | provider retry | low confidence quality | `low_confidence` | answer quality |
| `pressure_interview_graph` | `select_follow_up_strategy` | `P-PRESSURE-*` strategy contract | quality refs, pace state | strategy | set strategy | none | `pressure:{session_id}:{turn}:strategy` | quality summary | strategy summary | no retry | deterministic strategy | `partial` | follow-up |
| `pressure_interview_graph` | `generate_follow_up_question` | follow-up contract | strategy | follow-up question | set question candidate | LLM call | `pressure:{session_id}:{turn}:follow-up` | strategy | candidate | provider retry | deterministic follow-up | `generation_failed` | follow-up |
| `pressure_interview_graph` | `control_pace` | pace control contract | turn refs | pace state | set pace | none | `pressure:{session_id}:{turn}:pace` | turn refs | pace summary | no retry | deterministic pace | `partial` | pace |
| `pressure_interview_graph` | `check_end_condition` | end condition contract | turn refs, pace | continue/end | set route | none | `pressure:{session_id}:{turn}:end-check` | pace | route summary | no retry | max turn fallback | `partial` | end condition |
| `pressure_interview_graph` | `assemble_report_input_package` | `P-PRESSURE-009` | session/turn/score refs | report input package ref | set `report_input_ref` | persist package | `report_input:{owner_id}:{session_id}:{turn_hash}` | end route | package ref | DB retry | package partial | `partial` | package is not report body |
| `report_generation_graph` | `load_report_sources` | PR8 report repository/tool to locate | owner, report request | source refs | set report input refs | read-only | `report:{owner_id}:{report_request_id}:load` | none | source refs | no retry | source unavailable | `source_unavailable` | source status |
| `report_generation_graph` | `validate_report_scope` | `REPORT_CONTRACTS.md`, `API_SPEC.md` requested sections | requested sections | section scope | set section scope | none | `report:{request_id}:scope:{sections_hash}` | source refs | scope summary | no retry | remove unauthorized optional section | `validation_failed` | no export path |
| `report_generation_graph` | `build_report_input_package` | `P-REPORT-001` upstream package requirement | source refs | package ref/digest | set package refs | optional package persistence | `report:{session_ref}:input:{source_digest}` | scope summary | package summary | deterministic | partial package | `partial` | no raw answer dump |
| `report_generation_graph` | `plan_report_sections` | report contract registry | package, requested sections | section plan | set `section_plan` | none | `report:{package_ref}:plan:{sections_hash}` | package summary | section plan | no retry | required minimal plan | `validation_failed` | section plan |
| `report_generation_graph` | `dispatch_report_section_workers` | LangGraph `Send` / equivalent | section plan | worker tasks | set worker refs | runtime fanout only | `report:{package_ref}:dispatch:{plan_hash}` | plan | worker refs | worker-level retry | mark worker failed | `partial` | fanout/fanin |
| `report_generation_graph` | `write_report_section` | `P-REPORT-001/002/003/004` section worker | worker state | section draft | set local worker result | LLM call via transport | `report_section:{package_ref}:{section_id}:{source_hash}` | worker input refs | section result digest | provider/schema retry | section low confidence | per-worker status | worker no raw payload |
| `report_generation_graph` | `section_quality_gate` | report validation and scoring rules | section draft | accepted/rejected section | set worker status | none | `report_section:{section_id}:{draft_digest}:gate` | section digest | validation summary | one repair pass | reject optional section | `validation_failed` | no exact probability |
| `report_generation_graph` | `synthesize_report` | reducer | worker results | report draft | set report draft digest | none | `report:{package_ref}:synthesize:{worker_hash}` | worker summaries | report draft summary | no retry | partial report policy | `partial` / `generation_failed` | reducer policy |
| `report_generation_graph` | `score_report_consistency_gate` | `SCORING_SPEC.md`, `ScoreResult` refs | report draft, score refs | consistency result | set score consistency | none | `report:{package_ref}:score-gate:{score_hash}` | report draft | score validation summary | no retry | low confidence disclaimer | `low_confidence` / `validation_failed` | score consistency |
| `report_generation_graph` | `persist_report` | PR8 report repository/tool | report draft | report/report_section refs | set `report_ref` | write report and sections | `report:{owner_id}:{package_ref}:{report_digest}` | score gate | persisted refs | DB retry | fail closed if required sections absent | `generation_failed` | persistence target |
| `report_generation_graph` | `prepare_copy_boundary` | `API_SPEC.md` copy content boundary | persisted report | copy content ref | set `copy_content_ref` | write copyable content metadata; no file export | `copy_content:{owner_id}:{report_ref}:{copy_hash}` | report ref | copy metadata | DB retry | `copy_content_available=false` | `partial` | no export/download/file |
| `mock_review_generation_graph` | `load_mock_review_sources` | PR8 review repository/tool | session/report refs | source timeline refs | set source refs | read-only | `mock_review:{owner_id}:{session_ref}:load` | none | source refs | no retry | source unavailable | `source_unavailable` | source scope |
| `mock_review_generation_graph` | `build_turn_performance_timeline` | report/pressure refs | turn refs, score refs | performance timeline | set timeline refs | none | `mock_review:{session_ref}:timeline:{turn_hash}` | source refs | timeline summary | deterministic | partial timeline | `partial` | no rescore |
| `mock_review_generation_graph` | `diagnose_session_performance` | `REVIEW_CONTRACTS.md` | timeline | review draft | set review draft | LLM call | `mock_review:{session_ref}:diagnose:{timeline_hash}` | timeline | review digest | provider/schema retry | low confidence review | `low_confidence` | no outcome prediction |
| `mock_review_generation_graph` | `extract_review_weakness_candidates` | `WEAKNESS_CONTRACTS.md` handoff | review draft | weakness candidate refs | set candidate refs | candidate-only write | `mock_review:{review_digest}:weakness-candidates` | review digest | candidate summary | provider/schema retry | empty candidates | `partial` | no formal weakness |
| `mock_review_generation_graph` | `extract_review_asset_candidates` | `ASSET_CONTRACTS.md` handoff | review draft | asset candidate refs | set candidate refs | candidate-only write | `mock_review:{review_digest}:asset-candidates` | review digest | candidate summary | provider/schema retry | empty candidates | `partial` | no formal asset |
| `mock_review_generation_graph` | `generate_training_suggestions` | `TRAINING_CONTRACTS.md` handoff | review/candidate refs | training suggestion refs | set suggestion refs | suggestion-only write | `mock_review:{review_digest}:training-suggestions` | candidate summary | suggestion summary | provider/schema retry | empty suggestions | `partial` | no training task |
| `mock_review_generation_graph` | `review_quality_gate` | `REVIEW_CONTRACTS.md` validation | review draft | validation result | set validation status | none | `mock_review:{review_digest}:quality` | draft | validation summary | one repair pass | low confidence | `validation_failed` | no rescore |
| `mock_review_generation_graph` | `persist_mock_review` | PR8 review repository/tool | validated review | review ref | set `review_ref` | write review/review_items | `mock_review:{owner_id}:{session_ref}:{review_digest}` | validation | review ref | DB retry | fail closed if invalid | `generation_failed` | persistence target |
| `real_review_generation_graph` | `load_real_interview_input` | real input repository/tool by PR8 | real input ref | source summary | set real input refs | read-only | `real_review:{owner_id}:{real_input_ref}:load` | none | source summary | no retry | source unavailable | `source_unavailable` | owner |
| `real_review_generation_graph` | `validate_real_input_completeness` | `REVIEW_CONTRACTS.md`, `SECURITY_PRIVACY.md` | source summary | completeness result | set validation status | none | `real_review:{real_input_ref}:validate` | source summary | validation summary | no retry | request more evidence / low confidence | `low_confidence` / `validation_failed` | confirmed input |
| `real_review_generation_graph` | `redact_third_party_sensitive_fields` | `SECURITY_PRIVACY.md` privacy boundary, `API_SPEC.md` third-party redaction summary | real input summary | redacted evidence, redaction summary | set `third_party_redaction_summary` | write audit event summary only | `real_review:{real_input_ref}:redact:{source_digest}` | source summary | redaction summary | deterministic | fail closed on unredactable sensitive field | `validation_failed` | third-party redaction |
| `real_review_generation_graph` | `build_real_review_evidence` | review evidence binding | redacted source refs | evidence bundle refs | set evidence refs | none | `real_review:{real_input_ref}:evidence:{redacted_digest}` | redaction summary | evidence summary | deterministic | low confidence bundle | `low_confidence` | no raw real input |
| `real_review_generation_graph` | `generate_real_review` | `REVIEW_CONTRACTS.md` real review contract | evidence bundle | review draft | set review digest | LLM call | `real_review:{real_input_ref}:llm:{evidence_hash}` | evidence summary | draft digest | provider/schema retry | low confidence review | `generation_failed` / `low_confidence` | no outcome prediction |
| `real_review_generation_graph` | `real_review_quality_gate` | review validation | review draft | validation result | set validation status | none | `real_review:{draft_digest}:quality` | draft | validation summary | one repair pass | low confidence | `validation_failed` | privacy and no exact probability |
| `real_review_generation_graph` | `persist_real_review` | PR8 review repository/tool | validated review | review ref | set `review_ref` | write real review/items | `real_review:{owner_id}:{real_input_ref}:{review_digest}` | validation | review ref | DB retry | fail closed if invalid | `generation_failed` | persistence target |
| all | `complete_ai_task` | AI task protocol | graph state | terminal task | terminal status | write task result/status | `ai_task:{ai_task_id}:complete` | persistence refs | terminal summary | idempotent | sanitized failure | terminal API enum | no raw payload |

## 7. Report score consistency

`score_report_consistency_gate` must enforce:

- Report score uses `ScoreResult` refs or section score candidates validated against `SCORING_SPEC.md`.
- `score_value` is 0-100 product scale, not exact interview pass probability.
- `score_version`, `rubric_version`, `score_rule_version_ref`, `confidence_level`, `validation_status`, `evidence_refs` and `trace_refs` remain available in response or internal refs according to API schema.
- If required score refs are missing, report can only be `low_confidence` or `partial`; it cannot claim high-confidence readiness.
- LLM section worker cannot invent scoring formula, hidden weight, pass probability or calibration claims.

## 8. Real review privacy / third-party redaction

`real_review_generation_graph` must run `redact_third_party_sensitive_fields` before any LLM node. Inputs from real interviews may contain company names, interviewer names, other candidates, private feedback or confidential business details. The redaction node writes only a `third_party_redaction_summary`, redacted evidence refs and audit event metadata. It must not preserve third-party raw text in checkpoint, API response, LLM trace or copy content.

## 9. 旧代码迁移矩阵

| Existing Symbol | Target Node/Tool/Validator | keep/wrap/split/deprecate/delete | PR | Tests |
|---|---|---|---|---|
| Existing `ScoreResult` / AI task response semantics from active docs | report/review score and task nodes | keep | PR8 | task status, score consistency |
| Future report repository | `persist_report`, `prepare_copy_boundary` | wrap when created | PR8 | report readback, copy boundary |
| Future review repository | `persist_mock_review`, `persist_real_review` | wrap when created | PR8 | review readback, source summary |
| Future pressure session repository | `pressure_interview_graph` persistence nodes | wrap when created | PR8 | pause/resume, report input package |
| Prompt contract report/review validation | section/review quality gates | keep | PR8 | no exact probability, no raw payload |
| Candidate extraction from review/report | candidate handoff nodes | wrap/split | PR8 | candidate-only, confirmation required |
| File export behavior | none | delete/forbid | PR8 | route inventory no export/download/file |

## 10. 与 active docs 的关系

本文只细化 active Prompt contracts、`APPLICATION_FLOW_SPEC.md` 与 `PRESSURE_MODE_SPEC.md` 的运行编排，不替代 API、DATA、PERSISTENCE、SCORING、SECURITY 或 Prompt canonical 文档。Pressure mode-level lifecycle、turn、pace、API handoff、report / review handoff 和 PR2 hold 以 `PRESSURE_MODE_SPEC.md` 为准；report/review persistence target 以 `PERSISTENCE_MODEL.md` 和 `API_SPEC.md` 已登记对象为准；PR8 需要代码实现时由主 Agent 授权具体文件。

## 11. 非目标

- 不实现 report/review graph。
- 不新增 endpoint。
- 不生成 PDF/Markdown/docx 文件导出。
- 不重新定义评分公式。
- 不创建正式 Weakness / Asset / TrainingTask。
- 不让 checkpoint 成为 business truth source。

## 12. 后续 PR 使用方式

PR8 按本文实现 report/review/candidate closure；如 PR5/PR6 需要压力面或报告输入包，必须先在 `PRESSURE_MODE_SPEC.md`、active flow/API 中确认触发方式。实现前需要主 Agent 汇总确认 pressure/report/review repository 文件、runtime `Send` API 版本和 test fixture 范围。

## 13. Definition of Done

- 四个 graph skeleton 已覆盖。
- `report_generation_graph` 包含 worker state、reducer、`Send` / parallel worker usage、partial report policy、report score consistency 和 copy boundary。
- `real_review_generation_graph` 包含真实输入确认、third-party redaction、privacy audit 和 no outcome prediction。
- Report / Review 保留 candidate-only、copy boundary、no export、no exact probability、no raw payload。
