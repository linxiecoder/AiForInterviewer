---
title: APPLICATION_FLOW_SPEC
type: design
status: draft-f4-application-flow
owner: 后端架构 / API / AI 架构
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/application-flow-spec
---

# APPLICATION_FLOW_SPEC

## 1. 文档状态与治理边界

- 本文件是 application service / use-case orchestration spec，不是代码实现、任务队列设计、Prompt 文案或物理数据库 schema。
- 本文件承接人工审计中“API 只有字段设计，缺少实现编排、跨模型查询、打磨模式每次回答后的数据组装、LLM 调用时机、调用次数、Prompt 结构和持久化流程”的整改。
- `API_SPEC.md` 仍是 endpoint contract canonical；`PROMPT_SPEC.md` 仍是 P-* contract canonical registry；`DATA_MODEL.md` / `PERSISTENCE_MODEL.md` 承接持久化对象；本文件只描述应用服务如何把这些事实串起来。
- `PRESSURE_MODE_SPEC.md` 是 Pressure Mode lifecycle、turn loop、pace、end condition、report / review handoff、graph boundary 和 PR2 hold 的 mode-level spec；本文只承接流程矩阵引用，不替代该文档。
- 本文件不要求 F5 使用真实 LLM；F7 可以使用 deterministic fake transport 验证 orchestration。
- 本文件不得暴露 system prompt 原文、provider payload、completion 原文、token、cookie、secret、隐藏评分规则、无 owner 校验正文或 source unavailable 正文。

## 2. 通用编排原则

1. 前端只调用 API，不直接读库，不直接调用 LLM。
2. Application service 先校验 session / actor / owner，再读取领域模型和版本 / 快照，再创建或复用 `AiTask`。
3. AI 生成类流程对外默认异步；即使 F5 内部快速完成，也必须返回 `ai_task_id` 和可查询状态。
4. 一次 LLM call 可以覆盖多个 P-* contract，但输出必须保留每个 `contract_id`、`validation_result_ref`、`evidence_refs`、`trace_refs` 和 persistence target。
5. 用户输入保存和 AI 生成拆开。保存 `Answer`、真实面试输入、用户确认、复制事件等同步完成，不隐式触发不可见 LLM 调用。
6. Low confidence、source unavailable、validation failed、partial result 必须进入 API status、持久化对象和 F7 fixture，不得被普通 success 吞掉。

### 2.1 AI Runtime PR3 / PR4 编排边界

本节补齐 PR3 / PR4 Runtime Contracts 的 application flow。它只定义 facade / port / runtime API skeleton，不实现 concrete LangGraph、business graph、frontend 或 real provider default-on。

| 编排点 | PR3 / PR4 contract | 禁止事项 |
|---|---|---|
| Core -> Runtime 入口 | Core UseCase 只通过 `AiOrchestrationFacade` 调用 `AgentGraphRunner` port；输入为 owner-scoped refs、contract ids、idempotency key 和 sanitized command envelope | Core 不 import LangGraph、AgentState、checkpoint schema、provider SDK 或 runtime DB model |
| PR3 contract scope | 定义 facade、runner port、registry、runtime flags resolver、side-effect guard、trace bridge、handoff DTO、interrupt service、status/timeline DTO | 不执行 concrete LangGraph，不写 business graph，不调用 Core formal write repository |
| PR4 fake runtime scope | concrete adapter 可以在 default-off feature flag 下 start / resume / replay / timeline fake graph，验证 checkpoint refs、serializer、timeline 和 interrupt contract | 不迁移 Polish / JobMatch / Pressure / Report business graph，不默认调用 real provider |
| Interrupt lifecycle | create -> get detail -> validate resume payload -> resume / reject / expire；所有动作 owner-scoped、base-version checked、idempotent，并写 audit summary | drawer payload 不暴露 AgentState、checkpoint payload、Prompt、completion 或 provider payload |
| Handoff | handoff 只携带 refs、sanitized summaries、validation result、candidate refs、confirmation refs 和 `side_effect_key` | PR3 / PR4 只定义 contract / stub，不实现 `write_question_result`、`write_feedback_result`、`write_report_result`、`write_review_result`、`write_candidate_result` 或 `finalize_after_confirmation` 的真实 formal write path |
| Formal write | formal write 是 PR5+ 或对应业务迁移 PR 的 Core command 责任，必须通过 owner、version、confirmation、validation 和 side-effect guard | PR4 LangGraph adapter 不允许绕过 handoff 直接写 Core Business tables |
| Replay / cancel | replay 默认 read-only；cancel / timeout / expired interrupt 必须阻断 late formal write，并返回 sanitized status | 不从 checkpoint payload 或 raw LLM payload 恢复业务事实 |

最小 runtime flow：

1. Core UseCase 校验业务 owner/source/version 后调用 `AiOrchestrationFacade`。
2. Facade 解析 runtime / graph flags，默认 false；仅 facade、registry 或 runner entry 可读 flag。
3. Facade 创建或复用 `AiTask` / `AgentRun`，经 `AgentGraphRunner` port start / resume。
4. Runner / adapter 只能写 `AgentRun`、`AgentNodeRun`、`AgentInterrupt`、`AgentCheckpointRef`、`LlmCall` 和 sanitized timeline refs。
5. 需要业务落库时，runner 返回 handoff request；PR3 / PR4 只校验 handoff contract，不执行真实 formal write。
6. API mapper 只返回 sanitized run status、timeline、interrupt detail 或 task refs。

### 2.2 Interview Coach Composition Layer 编排边界

本节迁入原 standalone G-003 / G-004 / Composition 规格中已确认的 composition runtime 规则；原规格文件删除后，本节与 `TECH_DESIGN.md` §14.3 共同承接 G-003 / G-004 / Composition Layer 的编排边界。

| mode | G-004 Understanding | G-003 Evaluation | response packaging | 编排禁止项 |
|---|---|---|---|---|
| `interview` | always runs | conditionally runs | 在 envelope 层合并 transcript understanding 与可选 feedback | 不把 G-004 signals 改写成评分、反馈或 coaching |
| `training` | runs | runs | 返回 balanced output；保留各层字段隔离 | 不自动创建 TrainingTask，不把训练建议写成正式对象 |
| `analysis` | only | no | 只返回 understanding output | 不隐式触发 G-003，不从 G-004 推导 feedback |

Composition Layer 的 merge 只能是 envelope-level packaging。它可以决定调用顺序、失败隔离、字段落位和可见状态，但不得解释、覆盖、降级、升级、normalize 或 synthesize 任一 layer 的业务语义。G-003 feedback task 继续属于 evaluation / feedback 路径；G-004 transcript analysis 继续属于 understanding-only 路径。

## 3. Prompt 输入结构模板

本节定义结构，不写生产完整 Prompt 文案。

| 结构字段 | 说明 |
|---|---|
| `system_boundary` | 固定边界摘要，只描述安全、权限、禁止项和输出要求，不泄露 system prompt 原文 |
| `mode_rules` | 当前模式规则，例如 job match / polish / pressure / report / review / asset / weakness / training |
| `task_goal` | 本次 AI task 的业务目标和 contract id 列表 |
| `input_refs` | `ResumeVersion`、`JobVersion`、`InterviewSession`、`Question`、`Answer`、`ScoreResult` 等 typed refs |
| `source_availability` | 每个来源的 canonical `source_*` 状态 |
| `evidence_bundle` | 经过 owner 校验和脱敏的 evidence summary，不包含不可用来源正文 |
| `current_question` | 当前题目摘要或引用 |
| `current_answer` | 当前回答摘要或受控正文，仅限本任务必要片段 |
| `recent_turns_summary` | 最近若干轮摘要和 refs |
| `session_summary` | `SessionSummary` snapshot 和 risk flags |
| `forbidden_repeat_refs` | 禁止重复题目、重复追问或重复建议的 refs |
| `output_schema` | 当前 contract 的结构化输出 schema |
| `validation_rules` | schema validation、业务语义校验、评分禁词、candidate 边界 |
| `low_confidence_rules` | 触发条件、分类、用户可见状态和降级动作 |
| `excluded_outputs` | 禁止输出字段、确定性预测、文件导出、正式对象静默写入 |

禁止进入 Prompt / trace / API response：

- system prompt 原文。
- provider payload。
- completion 原文。
- token / cookie / secret。
- 无 owner 校验正文。
- `source_unavailable` / `source_deleted` / `source_disabled` 正文。
- 精确通过概率、offer 概率、录取概率、通过率百分比。
- 隐藏评分规则、完整内部权重表、校准样例正文。

## 4. 核心流程矩阵

| 流程 | 触发 API | 同步 / 异步 | 读取模型 | 写入模型 | AiTask | P-* contract / LLM calls | Prompt 输入结构 | Validation / Low confidence | Persistence handoff | API response | F7 fixture |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. 创建岗位匹配分析 | `POST /api/v1/job-match-analyses` | async | `JobResumeBinding`、`ResumeVersion`、`JobVersion`、latest `ScoreRuleVersion`、可选 `AssetVersion` / `Weakness` / RAG evidence | `AiTask`、`AiTaskResult`、`JobMatchAnalysis`、`ScoreResult(job_match)`、`ScoreEvidenceLink`、`LowConfidenceFlag`、candidate refs | 是，`task_type=job_match_analysis` | 默认 1 call 合并 `P-JOBMATCH-001/002/003`；`P-JOBMATCH-004` 可同 call 输出 weakness candidate refs，也可后置独立 task | job/resume summaries、binding、score rule ref、evidence bundle、output schema、low confidence rules | 缺岗位/简历版本、evidence missing、source unavailable、分数解释冲突 -> low confidence 或 validation failed | `score_results`、`score_evidence_links`、`ai_task_results`、candidate refs | 202 accepted，返回 `ai_task_id`；结果读取返回 `JobMatchAnalysis` / `ScoreResult` | `flow.job_match.create.async_contracts`、`flow.job_match.no_exact_probability` |
| 2. 获取岗位匹配分析 | `GET /api/v1/job-match-analyses/{analysis_id}` | sync | `JobMatchAnalysis`、`ScoreResult`、`EvidenceRef`、`TraceRef`、`LowConfidenceFlag` | `ApiRequestTrace`、必要 audit | 否 | 无新 LLM call | N/A | source unavailable 只展示状态，不重新读取正文 | read model assembly | 200 success / partial / low_confidence | `flow.job_match.get.low_confidence_visible` |
| 3. 创建打磨会话 | `POST /api/v1/polish-sessions` | sync | `ResumeJobBinding`、`ResumeVersion`、`JobVersion`、`PolishTopicRef` / `PolishSubtopicRef` | `InterviewSession`、`PolishSessionDetail`、`SessionSummary` initial snapshot、audit | 否 | 无 LLM call；题目生成另走流程 4 | N/A | binding stale / source unavailable 阻断或要求重新选择 | `interview_sessions` + `polish_session_details` | 201 success，返回 session refs | `flow.polish_session.create.no_llm` |
| 4. 创建打磨题目 | `POST /api/v1/polish-sessions/{session_id}/questions` | async | `InterviewSession`、`PolishSessionDetail`、`ResumeVersion`、`JobVersion`、`SessionSummary`、topic/subtopic、recent turns、可选 JobMatch / Asset / Weakness / RAG | `AiTask`、`Question`、`TraceRef`、`LowConfidenceFlag` | 是，`task_type=question_generation` | 默认 1 call：`P-POLISH-002` + shared contracts；必要时先 deterministic topic rules，再 LLM | 使用模板字段，重点包含 topic/subtopic、forbidden_repeat_refs、output_schema | 重复题、source unavailable、上下文裁剪高风险 -> low confidence / retry | question result + trace | 202 accepted；result 后产生 `Question` | `flow.polish_question.no_repeat_refs` |
| 5. 用户每次提交打磨回答 | `POST /api/v1/polish-sessions/{session_id}/answers` | sync | `InterviewSession`、`Question`、`base_question_version_ref` | `Answer`、`ApiRequestTrace`、`AuditEvent`、可选 session activity marker | 否 | 不调用 LLM | N/A | 只做字段、owner、版本和长度校验；low confidence 不阻断保存原始输入 | `answers` | 201 success，返回 `AnswerResponse` | `flow.polish_answer.save_no_llm` |
| 6. 每次回答后的打磨反馈生成 | `POST /api/v1/polish-sessions/{session_id}/feedback` | async | `InterviewSession`、`PolishSessionDetail`、当前 `Question`、当前 `Answer`、`ResumeVersion`、`JobVersion`、`SessionSummary`、最近若干轮 turn refs、可选 `JobMatchAnalysis`、可选 `AssetVersion`、可选 `Weakness`、可选 RAG evidence | `AiTask`、`Feedback`、`ScoreResult(polish_answer)`、`LossPoint`、candidate refs、`LowConfidenceFlag`、`SessionSummary` update | 是，`task_type=feedback_generation` | MVP 默认 1 call 合并 `P-POLISH-003`、`P-POLISH-004`、`P-POLISH-005`、`P-POLISH-009`；`P-POLISH-006/007/008` 默认按用户点击 on-demand 独立 task；`P-POLISH-010/011` 默认只生成 candidate refs 或入口建议 | 模板字段全部适用；必须包含 current_question、current_answer、recent_turns_summary、session_summary、forbidden_repeat_refs、score rule ref | 输出必须分别保留每个 contract_id、validation_result_ref、evidence_refs、trace_refs；answer too short、evidence missing、score mismatch -> low confidence | feedback、score、loss point、candidate refs、summary snapshot、trace | 202 accepted；result 返回 feedback / score / candidates / next_actions | `flow.polish_feedback.merged_call_contract_ids`、`flow.polish_feedback.on_demand_reference_answer`、`flow.polish_feedback.candidate_not_formal` |
| 7. 打磨模式报告生成 | `POST /api/v1/reports` with `report_type=polish_summary` | async | `InterviewSession`、`PolishSessionDetail`、questions、answers、feedback、`ScoreResult(polish_answer)`、loss points、session summary、evidence refs | `InterviewReport`、`ReportSection`、`ScoreResult(polish_report)`、copy content metadata、trace | 是，`task_type=report_generation` | 默认 1 call 生成 report sections + `polish_report` candidate；copy content 可 deterministic assembly 或 `P-REPORT-004` | 输入一组 turn refs，不得只输入最近一轮分；包含 excluded outputs | 缺 turn refs / feedback refs / evidence refs 时不得正式报告总分；不能输出精确通过概率 | reports、sections、score_results、score links | 202 accepted；GET report 返回 partial / low_confidence | `flow.polish_report.not_single_turn_score` |
| 8. 压力面问题生成和追问 | `POST /api/v1/pressure-sessions/{session_id}/questions` / feedback endpoint | async | `InterviewSession`、`PressureSessionDetail`、previous turns、pace state、Job/Resume versions、SessionSummary、forbidden_repeat_refs；mode-level rules 见 `PRESSURE_MODE_SPEC.md` | `AiTask`、`Question`、`Feedback` / follow-up decision、trace | 是 | 首题可 1 call `P-PRESSURE-001/002`；追问默认 1 call 合并 `P-PRESSURE-003/004/005`；节奏 `P-PRESSURE-006` 可 deterministic 或同 call | pressure mode rules、recent turns、pace, coverage, output_schema | 不足题量、coverage 不清、source unavailable -> low confidence or continue recommended | questions、feedback、summary | 202 accepted；result 返回 question / follow-up | `flow.pressure.followup.no_same_question_loop` |
| 9. 模拟面试报告生成 | `POST /api/v1/reports` with `report_type=pressure_full` | async | Pressure session、turns、`P-PRESSURE-008` session score、`P-PRESSURE-009` report input package、Job/Resume versions、evidence；report handoff 见 `PRESSURE_MODE_SPEC.md` | `InterviewReport`、`ReportSection`、`ScoreResult(pressure_session/report_section)`、copy content metadata | 是 | 默认 1 call `P-REPORT-001/002/003`；`P-REPORT-004` 可 deterministic copy assembly | report input package、score refs、risk signals、source availability | session score missing -> partial / low confidence；no exact probability | report + sections + score refs | 202 accepted；GET report | `flow.report.pressure_full.score_refs_required` |
| 10. 模拟面试复盘生成 | `POST /api/v1/reviews/mock` | async | `InterviewSession` 或 report、questions、answers、feedback、score results、report sections、evidence refs | `InterviewReview`、review items、weakness / asset / training candidate refs、trace | 是 | 默认 1 call `P-REVIEW-001/004`；候选提炼可同 call 输出 candidate refs 或后续 Weakness / Asset / Training task | review source summary、turn refs、score refs、candidate boundary | low confidence / source unavailable 必须进入 review status，不写 formal object | reviews、candidate refs、trace | 202 accepted；GET review | `flow.review.mock.candidate_only` |
| 11. 真实面试复盘生成 | `POST /api/v1/reviews/real-inputs` 保存输入；`POST /api/v1/reviews/real` 生成复盘 | sync 保存输入；async 生成 | `RealInterviewInput`、用户确认摘要、可选 Job/Resume versions、evidence completeness flags | `RealInterviewInput`、`InterviewReview`、review items、low confidence flags、candidate refs | 保存输入不创建 AiTask；生成复盘创建 AiTask | 输入结构化可用 `P-REVIEW-002`；复盘生成默认 1 call `P-REVIEW-003/004` | 不放第三方 / 公司 / 面试官敏感原文；使用确认摘要、trust flags、source availability | 输入不完整或可信度低 -> low confidence；不得预测真实结果 | real input, review, trace, audit | 201 input / 202 review task | `flow.review.real.confirmed_input_only` |
| 12. 资产候选生成和确认 | `POST /api/v1/assets/candidates`；`POST /api/v1/assets/candidates/{candidate_id}/confirmations` | async candidate；sync confirmation | source refs、answers、feedback、reference answer、existing assets、candidate version | `AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`；确认后写 `Asset` / `AssetVersion` | candidate 生成创建 AiTask；confirmation 不调用 LLM | 默认 1 call `P-ASSET-001`；quality/version suggestion 可同 call 或后续 `P-ASSET-002/003` | source summaries、duplicate candidates、output schema | duplicate / insufficient user fact -> merge suggestion / low confidence | candidate tables; confirmation creates formal object only after user action | 202 candidate；201/200 confirmation | `flow.asset.confirmation_required` |
| 13. 薄弱项候选生成和确认 | `POST /api/v1/weaknesses/candidates`；confirmation endpoint | async candidate；sync confirmation | feedback、score results、loss points、review items、existing weaknesses、evidence refs | `WeaknessCandidate`、merge suggestions、confirmation 后写 `Weakness` | candidate 生成创建 AiTask | 默认 1 call `P-WEAKNESS-001/002/003`；status update `P-WEAKNESS-004` 后续 | score/loss/review evidence、existing weakness refs | 单次轻微失误不得自动 formal；evidence missing -> low confidence | candidate + references; confirmation -> formal | 202 candidate；200 confirmation | `flow.weakness.no_silent_formal_write` |
| 14. 训练建议生成和确认 | `POST /api/v1/training-suggestions`；confirmation endpoint | async suggestion；sync confirmation | confirmed weaknesses、assets、score trends、review items、training history | `TrainingRecommendation` candidate、ranking hint、confirmation 后 formal recommendation；显式用户动作才创建 training task | suggestion 生成创建 AiTask | 默认 1 call `P-TRAINING-001/002`；结果复盘 `P-TRAINING-003` 独立 | weakness/asset refs、priority constraints、output schema | low confidence / missing weakness evidence -> candidate only | training recommendation candidate + confirmation | 202 suggestion；200 confirmation | `flow.training.confirm_before_task` |

## 5. 打磨回答与反馈的强制拆分

`POST /api/v1/polish-sessions/{session_id}/answers` 只保存 `Answer`，同步完成，不直接调用 LLM。它只做：

- session / question owner 校验。
- `base_question_version_ref` stale 检查。
- answer length / empty 校验。
- `Answer` 写入、`ApiRequestTrace` 和 `AuditEvent`。

`POST /api/v1/polish-sessions/{session_id}/feedback` 创建异步 feedback task。该 task 至少读取：

- `InterviewSession`
- `PolishSessionDetail`
- 当前 `Question`
- 当前 `Answer`
- `ResumeVersion`
- `JobVersion`
- `SessionSummary`
- 最近若干轮 turn refs
- 可选 `JobMatchAnalysis`
- 可选 `AssetVersion`
- 可选 `Weakness`
- 可选 RAG evidence

MVP 默认建议把 `P-POLISH-003 Answer Diagnosis`、`P-POLISH-004 Round Score`、`P-POLISH-005 Loss Point Analysis`、`P-POLISH-009 Next Round Suggestion` 合并为一次 LLM call，前提是输出 schema 保留每个 `contract_id`、`validation_result_ref`、`evidence_refs` 和 `trace_refs`。

`P-POLISH-006 Reference Answer`、`P-POLISH-007 Knowledge Point Explanation`、`P-POLISH-008 Technical Principle Expansion` 默认按用户点击 on-demand 创建独立任务，避免每次回答后过度调用。

`P-POLISH-010 Asset Candidate`、`P-POLISH-011 Weakness Candidate` 默认只生成 candidate refs 或入口建议。正式对象必须走确认 API。

session summary update 可以在 feedback task 后执行；短会话可用 deterministic summarizer，长会话可用独立 AI task，但必须记录 `contract_id` 和 trace。

## 6. Output validation 与 low confidence

每个 AI flow 必须执行：

1. schema validation。
2. 业务语义校验：owner、mode、candidate boundary、no exact probability、no hidden prompt / payload。
3. evidence binding。
4. low confidence classification。
5. persistence handoff。
6. API status mapping。

`low_confidence`、`source_unavailable`、`validation_failed` 和 `partial` 结果必须返回用户可见状态和 `next_actions`，不得作为普通 `success` 隐藏。

## 7. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-24 | 增加 PR3 / PR4 AI Runtime application flow backfill | 补齐 Core UseCase -> `AiOrchestrationFacade` -> `AgentGraphRunner` port、PR3 contract scope、PR4 fake runtime、interrupt、handoff、formal write PR5+、replay/cancel/late write block；不进入代码实现 |
| 2026-05-24 | 增加 Pressure Mode mode-level spec 交叉引用 | 将 Pressure lifecycle、turn loop、pace、end condition、report / review handoff 和 PR2 hold 交给 `PRESSURE_MODE_SPEC.md`；流程矩阵只保留 application orchestration 引用，不进入 implementation |
| 2026-05-17 | 初始化 application flow handoff | 补齐 API 到应用编排、P-* contract、LLM call plan、Prompt 输入结构、持久化和 F7 fixture 的映射 |
