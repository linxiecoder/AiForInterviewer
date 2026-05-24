---
title: PROMPT_ASSET_SPEC
type: design
status: draft-f5-prompt-asset
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-002
permalink: ai-for-interviewer/docs/02-design/prompt-asset-spec
---

# PROMPT_ASSET_SPEC

## 1. 文档目的与边界

本文承接 `AIFI-PROMPT-002`，定义 AiForInterviewer 的 Production Prompt Asset 设计、Prompt Asset registry、字段模型、版本策略、与 runtime prompt builder / LLM trace 的关系。

本文只做文档设计，不修改 `apps/**`、`tests/**`、依赖、migration 或 CI。本文不是 Prompt Contract registry，也不是完整代码实现。`PROMPT_SPEC.md` 仍是 `P-*` Prompt Contract canonical registry；本文只把 contract 落到可版本化、可评审、可回滚、可评估的 Prompt Asset 设计。

## 2. 为什么 `PROMPT_SPEC.md` 不够

`PROMPT_SPEC.md` 已冻结 AI task contract、输入、输出 schema、validation、trace / evidence 和 failure policy，但它有意不保存完整生产提示词文案，也不选择 provider、模型参数或 prompt release 机制。因此仅依赖 `PROMPT_SPEC.md` 和 runtime compact prompt builder 会留下以下缺口：

| 缺口 | 风险 | 本文补齐方式 |
|---|---|---|
| Prompt 文案隐藏在 Python builder | review 只能看代码 diff，无法按业务 contract 做 prompt release | 引入 Production Prompt Asset registry |
| `prompt_version` 与 contract / schema 映射分散 | PR5-PR8 迁移 graph 时可能混用旧 schema 或旧验证器 | 每个 asset 显式声明 `contract_ids`、`task_type`、`schema_id`、builder 和 validator |
| fake transport 承载业务期望 | fake 通过不代表 prompt 质量稳定 | 将业务期望迁入 golden / negative / regression fixtures |
| 缺少 model comparison policy | provider 200 容易被误写成 prompt 成功 | 只比较结构化质量、证据、边界、成本、延迟和 fallback，不以 provider 200 作为成功 |
| redaction / rollback 不统一 | raw prompt、completion、provider payload 或隐藏评分规则可能进入日志、trace、copy content | 每个 asset 必须声明 redaction boundary 和 rollback target |

## 3. 核心区分

| 概念 | 定义 | Owner | 不能替代什么 |
|---|---|---|---|
| Prompt Contract | `PROMPT_SPEC.md` / `prompt-contracts/*.md` 中登记的 `P-*` contract，描述 goal、input、output schema、validation、trace、evidence 和 failure policy | `PROMPT_SPEC.md` | 不等于完整生产 Prompt 文案，不定义 provider / model |
| Runtime Prompt Bundle | 运行时代码构造并传入 `LlmTransportRequest` 的 compact 输入包，含 `task_type`、`prompt_version`、`schema_id`、`contract_ids`、evidence bundle 和 redaction boundary | 对应 application builder | 不等于可审计生产 Prompt Asset，不保存 raw provider payload |
| Production Prompt Asset | 可版本化、可评审、可灰度、可回滚的生产 Prompt 模板 / 文案资产，绑定 contract、schema、builder、validator 和 evaluation fixtures | 本文 registry | 不替代 Prompt Contract，不绕过 runtime validation |
| Prompt Skill / capability prompt | 面向能力、SkillGap、question pattern 或 score dimension 的任务片段或规则块 | `SKILL_MODEL_SPEC.md` + 本文 asset 字段 | 不等于 Skill Model，不得生成未授权 `Skill*` formal object |
| Prompt Evaluation Fixture | 针对 asset 的输入、期望结构、validator 期望、失败语义、redaction 断言和 model comparison baseline | `PROMPT_EVALUATION_SPEC.md` | 不等于 fake provider 本身，不保存真实简历全文或 provider payload |
| Golden Fixture | 已人工接受的代表性成功样本，证明 prompt 能输出可验证结构和证据绑定 | `PROMPT_EVALUATION_SPEC.md` | 不覆盖所有负例，不代表真实 provider 永远可用 |
| Counterexample | 明确应拒绝、fallback、low confidence 或 manual review 的负例 | `PROMPT_EVALUATION_SPEC.md` | 不得被 prompt repair 伪装成成功 |
| Prompt Regression Suite | 每个 asset 的 golden、regression、negative、redaction 和 fallback fixture 集合 | `PROMPT_EVALUATION_SPEC.md` | 不替代业务 API / repository / frontend 测试 |
| Model Comparison Policy | 在显式 gate 下比较模型结构化质量、证据绑定、成本、延迟、fallback 和边界遵守情况 | `PROMPT_EVALUATION_SPEC.md` | 不以真实 provider 200 或主观文本流畅度作为通过标准 |

## 4. Prompt Asset Registry Model

Prompt Asset registry 是本文的 canonical 设计模型。PR5-PR8 开始迁移业务 graph 前，任何实际 prompt builder 或 graph node 都必须能映射到 registry 行；若新增 asset，必须更新本文和 `PROMPT_EVALUATION_SPEC.md` 的 fixture 计划。

| 字段 | 必填 | 规则 |
|---|---|---|
| `asset_id` | 是 | 稳定 ID，格式建议为 `prompt_asset.<domain>.<task>.<nnn>` |
| `prompt_version` | 是 | 语义版本或冻结字符串，必须可回滚 |
| `contract_ids` | 是 | 只引用 `PROMPT_SPEC.md` 已登记 `P-*` ID，不新增 contract |
| `graph_name` | 是 | 目标 graph 或 legacy service 名；PR2 不创建业务 graph 时可写 `legacy_runtime` |
| `node_name` | 是 | graph node 或 runtime builder 逻辑节点 |
| `task_type` | 是 | 传入 `LlmTransportRequest.task_type` 的值，未实现时写目标值 |
| `schema_id` | 是 | runtime 输出 schema 或目标 schema |
| system boundary | 是 | 固定系统约束、不能暴露内容和 provider-independent 边界 |
| role | 是 | 模型在本任务中的角色，例如 question generator、feedback reviewer、report writer |
| task goal | 是 | 单一任务目标，不得扩大为完整业务流程 |
| input blocks | 是 | 可进入 prompt 的 compact blocks，不得默认塞入全文历史 |
| evidence block format | 是 | 输入 evidence 的结构、allowed refs 和 copy rule |
| output schema | 是 | 结构化输出根字段和关键字段 |
| forbidden output | 是 | raw prompt、completion、provider payload、hidden rubric、精确通过概率等 |
| few-shot examples | 条件必填 | 只允许 safe summary，不保存真实完整简历 / JD |
| counterexamples | 是 | 应 fallback / low confidence / validation failed 的负例 |
| hallucination guards | 是 | 禁止编造事实、组件、技术栈、分数或证据 |
| scoring expression policy | 是 | 只输出允许展示的 score / risk / tendency，不暴露隐藏公式 |
| candidate/formal boundary | 是 | 只能输出 candidate / draft / suggestion / validation / trace，正式对象需用户确认或业务动作 |
| redaction boundary | 是 | 明确 raw-off、displayable summary、copy content 和 trace 可见性 |

## 5. Asset Registry

| asset_id | Contract | Runtime task_type | Prompt Version | Code Builder | Validator | Evaluation Fixture Set | Gap |
|---|---|---|---|---|---|---|---|
| `prompt_asset.polish.question.001` | `P-POLISH-002` + shared validation | `polish_question_generation` | `polish_question_generation_prompt_v1` | `build_polish_question_generation_prompt_bundle` | `validate_llm_question_output`; `adapt_llm_output_to_question_draft`; `validate_question_quality` | `eval.polish.question.v1` | implementation-ready for prompt migration |
| `prompt_asset.polish.feedback.001` | `P-POLISH-003/004/005/009` | `polish_answer_feedback_generation` | `polish_answer_feedback_prompt_v1` | `build_polish_feedback_prompt_bundle` | `validate_feedback_llm_output`; `adapt_llm_output_to_structured_payload`; `validate_feedback_consistency` | `eval.polish.feedback.v1` | implementation-ready for prompt migration |
| `prompt_asset.polish.progress.001` | `P-POLISH-001` + shared validation | `polish_progress_quality_first_menu`; `polish_progress_global_understanding`; `polish_progress_tree_draft_plan`; `polish_progress_tree_critic_refiner`; `polish_progress_tree_evidence_grounding` | `polish_progress_*_prompt_v1/v2` | `build_progress_quality_first_menu_prompt`; `build_progress_global_understanding_prompt`; `build_progress_tree_draft_plan_prompt`; `build_progress_tree_critic_refiner_prompt`; `build_progress_tree_grounding_prompt` | progress tree normalization / quality gates | `eval.polish.progress.v1` | needs implementation fixture expansion before PR6 |
| `prompt_asset.pressure.opening.001` | `P-PRESSURE-001` | target `pressure_opening_strategy` | target `pressure_opening_strategy_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.opening.v1` | blocked until AIFI-BE-004 mode-level spec |
| `prompt_asset.pressure.first_question.001` | `P-PRESSURE-002` | target `pressure_first_question_generation` | target `pressure_first_question_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.first_question.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.answer_quality.001` | `P-PRESSURE-003` | target `pressure_answer_quality_assessment` | target `pressure_answer_quality_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.answer_quality.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.follow_up_strategy.001` | `P-PRESSURE-004` | target `pressure_follow_up_strategy` | target `pressure_follow_up_strategy_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.follow_up_strategy.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.follow_up_question.001` | `P-PRESSURE-005` | target `pressure_follow_up_question_generation` | target `pressure_follow_up_question_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.follow_up_question.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.pace.001` | `P-PRESSURE-006` | target `pressure_pace_control` | target `pressure_pace_control_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.pace.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.end_condition.001` | `P-PRESSURE-007` | target `pressure_end_condition_check` | target `pressure_end_condition_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.end_condition.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.session_score.001` | `P-PRESSURE-008` | target `pressure_session_score` | target `pressure_session_score_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.session_score.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.pressure.report_input.001` | `P-PRESSURE-009` | target `pressure_report_input_assembly` | target `pressure_report_input_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | `eval.pressure.report_input.v1` | blocked until AIFI-BE-004 |
| `prompt_asset.report.main.001` | `P-REPORT-001` | target `report_generation` | target `report_generation_prompt_v1` | Target Report prompt builder | Target Report validator | `eval.report.main.v1` | target for PR8 |
| `prompt_asset.report.score_explanation.001` | `P-REPORT-002` | target `report_section_score_explanation` | target `report_score_explanation_prompt_v1` | Target Report prompt builder | Target Report validator | `eval.report.score_explanation.v1` | target for PR8 |
| `prompt_asset.report.risk_wording.001` | `P-REPORT-003` | target `report_risk_pass_tendency_wording` | target `report_risk_wording_prompt_v1` | Target Report prompt builder | Target Report validator | `eval.report.risk_wording.v1` | target for PR8 |
| `prompt_asset.report.copyable.001` | `P-REPORT-004` | target `report_copyable_content_assembly` | target `report_copyable_prompt_v1` | Target Report prompt builder | Target Report validator | `eval.report.copyable.v1` | target for PR8 |
| `prompt_asset.review.mock.001` | `P-REVIEW-001` | target `mock_interview_review` | target `mock_review_prompt_v1` | Target Review prompt builder | Target Review validator | `eval.review.mock.v1` | target for PR8 |
| `prompt_asset.review.real_input.001` | `P-REVIEW-002` | target `real_interview_input_structuring` | target `real_input_structuring_prompt_v1` | Target Review prompt builder | Target Review validator | `eval.review.real_input.v1` | target for PR8 |
| `prompt_asset.review.real_review.001` | `P-REVIEW-003` | target `real_interview_review` | target `real_review_prompt_v1` | Target Review prompt builder | Target Review validator | `eval.review.real_review.v1` | target for PR8 |
| `prompt_asset.review.item_extraction.001` | `P-REVIEW-004` | target `review_item_extraction` | target `review_item_extraction_prompt_v1` | Target Review prompt builder | Target Review validator | `eval.review.item_extraction.v1` | target for PR8 |
| `prompt_asset.jobmatch.analysis.001` | `P-JOBMATCH-001` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | `_normalize_job_match_payload`; scoring / evidence normalization | `eval.jobmatch.analysis.v1` | legacy parity needed before PR5 |
| `prompt_asset.jobmatch.score.001` | `P-JOBMATCH-002` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | scoring normalization | `eval.jobmatch.score.v1` | legacy parity needed before PR5 |
| `prompt_asset.jobmatch.points.001` | `P-JOBMATCH-003` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | points / evidence normalization | `eval.jobmatch.points.v1` | legacy parity needed before PR5 |
| `prompt_asset.jobmatch.weakness.001` | `P-JOBMATCH-004` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | weakness candidate boundary checks | `eval.jobmatch.weakness.v1` | legacy parity needed before PR5 |

## 6. Required Mapping Table

| Contract | Runtime task_type | Prompt Version | Code Builder | Validator | Tests | Gap |
|---|---|---|---|---|---|---|
| `P-POLISH-002` | `polish_question_generation` | `polish_question_generation_prompt_v1` | `build_polish_question_generation_prompt_bundle` | `validate_llm_question_output`; `adapt_llm_output_to_question_draft`; `validate_question_quality` | `tests/api/test_polish_question_llm.py` covers schema, semantic, evidence refs, repeated question, redaction and fallback | closed for design; implementation already has runtime builder |
| `P-POLISH-003` | `polish_answer_feedback_generation` | `polish_answer_feedback_prompt_v1` | `build_polish_feedback_prompt_bundle` | `validate_feedback_llm_output`; `adapt_llm_output_to_structured_payload`; `validate_feedback_consistency` | `tests/api/test_polish_feedback_llm.py` covers valid / invalid feedback and consistency | closed for design |
| `P-POLISH-004` | `polish_answer_feedback_generation` | `polish_answer_feedback_prompt_v1` | `build_polish_feedback_prompt_bundle` | `validate_feedback_llm_output`; score repair; `validate_feedback_consistency` | feedback tests cover score dimension mismatch, low confidence and raw payload omission | closed for design |
| `P-POLISH-005` | `polish_answer_feedback_generation` | `polish_answer_feedback_prompt_v1` | `build_polish_feedback_prompt_bundle` | `validate_feedback_llm_output`; loss point consistency | feedback tests cover loss point delta and invalid retry fallback | closed for design |
| `P-POLISH-009` | `polish_answer_feedback_generation` | `polish_answer_feedback_prompt_v1` | `build_polish_feedback_prompt_bundle` | `validate_feedback_llm_output`; retry / next focus consistency | feedback tests cover retry delta, previous loss refs and same-question boundary | closed for design |
| `P-PRESSURE-001` | target `pressure_opening_strategy` | target `pressure_opening_strategy_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: opening strategy success / insufficient input | blocked by AIFI-BE-004 implementation spec, not by Prompt Asset design |
| `P-PRESSURE-002` | target `pressure_first_question_generation` | target `pressure_first_question_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: first question, anti-repeat, source unavailable | blocked by AIFI-BE-004 |
| `P-PRESSURE-003` | target `pressure_answer_quality_assessment` | target `pressure_answer_quality_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: answer quality, low confidence, clarification needed | blocked by AIFI-BE-004 |
| `P-PRESSURE-004` | target `pressure_follow_up_strategy` | target `pressure_follow_up_strategy_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: strategy, no unsupported pressure escalation | blocked by AIFI-BE-004 |
| `P-PRESSURE-005` | target `pressure_follow_up_question_generation` | target `pressure_follow_up_question_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: follow-up, no same-question loop | blocked by AIFI-BE-004 |
| `P-PRESSURE-006` | target `pressure_pace_control` | target `pressure_pace_control_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: pace, pause / resume, low confidence | blocked by AIFI-BE-004 |
| `P-PRESSURE-007` | target `pressure_end_condition_check` | target `pressure_end_condition_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: continue / end / pause decision | blocked by AIFI-BE-004 |
| `P-PRESSURE-008` | target `pressure_session_score` | target `pressure_session_score_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: score refs, no exact probability, risk evidence | blocked by AIFI-BE-004 |
| `P-PRESSURE-009` | target `pressure_report_input_assembly` | target `pressure_report_input_prompt_v1` | Target Pressure prompt builder | Target Pressure validator | target fixture: report input is not report body | blocked by AIFI-BE-004 |
| `P-REPORT-001` | target `report_generation` | target `report_generation_prompt_v1` | Target Report prompt builder | Target Report validator | target fixture: report body, low confidence, source unavailable | target PR8 |
| `P-REPORT-002` | target `report_section_score_explanation` | target `report_score_explanation_prompt_v1` | Target Report prompt builder | Target Report validator | target fixture: section score refs and explanation consistency | target PR8 |
| `P-REPORT-003` | target `report_risk_pass_tendency_wording` | target `report_risk_wording_prompt_v1` | Target Report prompt builder | Target Report validator | target fixture: no exact probability, disclaimer and evidence binding | target PR8 |
| `P-REPORT-004` | target `report_copyable_content_assembly` | target `report_copyable_prompt_v1` | Target Report prompt builder | Target Report validator | target fixture: copy boundary and redaction | target PR8 |
| `P-REVIEW-001` | target `mock_interview_review` | target `mock_review_prompt_v1` | Target Review prompt builder | Target Review validator | target fixture: mock review, candidate refs, no formal write | target PR8 |
| `P-REVIEW-002` | target `real_interview_input_structuring` | target `real_input_structuring_prompt_v1` | Target Review prompt builder | Target Review validator | target fixture: third-party privacy and confirmation required | target PR8 |
| `P-REVIEW-003` | target `real_interview_review` | target `real_review_prompt_v1` | Target Review prompt builder | Target Review validator | target fixture: source trust flags and low confidence | target PR8 |
| `P-REVIEW-004` | target `review_item_extraction` | target `review_item_extraction_prompt_v1` | Target Review prompt builder | Target Review validator | target fixture: review item extraction and candidate-only | target PR8 |
| `P-JOBMATCH-001` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | `_normalize_job_match_payload` | target parity fixture: analysis summary and evidence refs | target PR5 |
| `P-JOBMATCH-002` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | scoring normalization | target parity fixture: score range, confidence, no exact probability | target PR5 |
| `P-JOBMATCH-003` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | points / evidence normalization | target parity fixture: match / mismatch / improvement points | target PR5 |
| `P-JOBMATCH-004` | `job_match_analysis` | `JOB_MATCH_PROMPT_VERSION` | `LlmJobMatchAnalyzer.analyze` | weakness candidate boundary checks | target parity fixture: candidate, confirmation required, no formal write | target PR5 |

## 7. Prompt Asset Field Contract

每个 Production Prompt Asset 必须在 registry 或后续实现 manifest 中保存以下字段族：

| Field Group | Required Fields | Rule |
|---|---|---|
| identity | `asset_id`, `prompt_version`, `status`, `owner`, `source_task` | `asset_id` 稳定；`prompt_version` 可回滚；`status` 只能表达设计 / accepted / deprecated |
| contract binding | `contract_ids`, `schema_id`, `task_type`, `graph_name`, `node_name` | contract 必须存在于 `PROMPT_SPEC.md`；schema 与 validator 一一对应 |
| system boundary | system boundary, role, task goal, forbidden output | 不暴露 provider payload、secret、token、system prompt、hidden rubric |
| input blocks | input blocks, evidence block format, context budget note, omitted refs policy | 只允许 compact summary / refs / displayable excerpts |
| output | output schema, validation mode, low confidence mode, fallback mode | 输出必须能进入 deterministic validator |
| examples | few-shot examples, counterexamples, hallucination guards | 示例必须脱敏，不保存真实全文 |
| scoring | scoring expression policy, score type, rubric / rule version | 不输出精确通过概率，不暴露隐藏公式 |
| persistence | candidate/formal boundary, redaction boundary, trace refs, rollback target | 正式对象写入需用户确认或显式业务动作 |

## 8. Polish Prompt Asset Plan

Polish 现有 runtime builder 已具备 compact prompt bundle 和校验闭环；AIFI-PROMPT-002 的设计结论是：Polish prompt migration 不再只依赖 builder，而是按本文 asset registry 和 `PROMPT_EVALUATION_SPEC.md` fixture set 管理。

| Asset | 输入块 | Evidence 格式 | 输出 / 禁止输出 | Release Gate |
|---|---|---|---|---|
| `prompt_asset.polish.question.001` | selected topic、progress node、question pattern、scenario constraint、compact evidence、recent questions、schema | `input_evidence_refs` 必须精确复制 allowed chunk id；不得用 source ref / object ref 替代 | 输出单题 draft；不得输出参考答案、raw prompt、provider payload、编造组件 | `eval.polish.question.v1` 全部通过 |
| `prompt_asset.polish.feedback.001` | current question、answer、question metadata、expected dimensions、scoring summary、previous answer / feedback compact summaries | evidence refs 使用 answer / question / score / loss refs；retry 只引用真实 previous loss point | 输出 feedback payload candidate；不得写正式 ScoreResult / Weakness / Asset | `eval.polish.feedback.v1` 全部通过 |
| `prompt_asset.polish.progress.001` | resume / JD / match summary、selected evidence chunks、turn summaries、schema | evidence chunk ids 稳定且可追踪 | 输出 progress tree plan / grounded plan；不得把 evidence 原句直接当 display title | `eval.polish.progress.v1` 通过后进入 PR6 |

## 9. Pressure Prompt Asset Plan

Pressure contracts 已为 Draft，但 Pressure mode-level runtime spec 仍由 `AIFI-BE-004` 承接。本文冻结 Prompt Asset 设计，使后续 Pressure graph 不再从空白 builder 开始。

| Stage | Contracts | Asset Boundary | Required Counterexamples |
|---|---|---|---|
| opening | `P-PRESSURE-001` | 只生成开场策略，不生成首题正文 | input insufficient; unsupported pressure tone |
| first question | `P-PRESSURE-002` | 基于 opening strategy 生成首题 | duplicate risk; source unavailable |
| answer quality | `P-PRESSURE-003` | 判断当前回答质量，不生成追问 | answer too short; clarification needed |
| follow-up strategy | `P-PRESSURE-004` | 选择追问策略，不生成题目 | low confidence; unsupported escalation |
| follow-up question | `P-PRESSURE-005` | 生成连续追问 | same-question loop; evidence missing |
| pace | `P-PRESSURE-006` | 控制节奏和压力强度可见语义 | over-pressure; pause signal ignored |
| end condition | `P-PRESSURE-007` | 判断继续、暂停或结束 | premature end; missing coverage |
| session score | `P-PRESSURE-008` | 生成整场评分 candidate | exact probability; score without evidence |
| report input | `P-PRESSURE-009` | 组装报告输入包，不生成报告正文 | report body generated; candidate formal write |

## 10. Report / Review Prompt Asset Plan

Report / Review Prompt Asset 在 PR8 或后续授权实现前必须满足：

| Area | Contracts | Boundary |
|---|---|---|
| Report | `P-REPORT-001` 至 `P-REPORT-004` | 生成报告正文、分项解释、风险措辞和可复制内容；不得生成文件导出，不暴露隐藏评分规则，不输出精确通过概率 |
| Review | `P-REVIEW-001` 至 `P-REVIEW-004` | 生成模拟 / 真实复盘和 review items；真实面试输入需可信度标记和用户确认；不得直接写正式 Weakness / Asset / TrainingRecommendation |
| Candidate handoff | Report / Review outputs | 只能输出 candidate refs、suggested deposit targets、validation result 和 trace；正式写入由确认流承接 |

## 11. Prompt Versioning And Deprecation

1. `prompt_version` 只允许前进，不允许复用旧版本语义。
2. schema 破坏性变化必须同步更新 `schema_id` 或 schema version，并更新 evaluation fixture set。
3. 每个新版本必须声明 `rollback_target_prompt_version`。
4. deprecated asset 至少保留：弃用原因、最后兼容 contract、替代 asset、回滚风险。
5. runtime builder 允许继续承载 legacy path，但必须在 metadata 中暴露当前 `prompt_version` 和 `contract_ids`。

## 12. Relationship With Runtime Prompt Builders

Runtime prompt builder 是 Production Prompt Asset 的执行承载，不是 asset 的唯一来源。后续实现必须满足：

- builder 返回的 `task_type`、`prompt_version`、`schema_id`、`contract_ids` 必须与本文 registry 一致。
- builder 可以动态装配 compact evidence，但不得改变 contract goal、output schema、forbidden output 或 redaction boundary。
- builder 不得保存 raw prompt、raw completion 或 provider payload 到普通日志、checkpoint、API response 或 copy content。
- fake provider 只能作为 deterministic transport；业务期望必须由 `PROMPT_EVALUATION_SPEC.md` fixtures 表达。
- 任何 graph migration 先保持 legacy API / fallback / validator parity，再替换 runtime 调度层。

## 13. Relationship With LLM Trace

LLM trace 只保存安全摘要、refs、状态和 validator 结果。每次 LLM call 至少应关联：

| Trace Field | Rule |
|---|---|
| `asset_id` | 指向本文 registry |
| `prompt_version` | 指向实际运行版本 |
| `contract_ids` | 与 `LlmTransportRequest.contract_ids` 一致 |
| `task_type` | 与 runtime bundle 一致 |
| `schema_id` | 与 validator 期望一致 |
| `input_refs` | 只保存 refs，不保存全文 |
| `evidence_refs` | 只保存 allowed evidence refs 或 displayable summary |
| `validation_status` | 区分 schema / semantic / evidence / consistency / low confidence |
| `fallback_reason` | provider、schema、semantic、evidence、redaction 或 consistency 的归因 |
| raw payload | 默认禁止；如未来 debug gate 允许，也不能进入普通日志、checkpoint 或 API response |

## 14. AIFI-PROMPT-002 Readiness Verdict

`AIFI-PROMPT-002` 的 Prompt Asset 设计在本文和 `PROMPT_EVALUATION_SPEC.md` 同时登记后，达到 implementation-ready 的文档标准：Production Prompt Asset、Runtime Prompt Bundle、Prompt Contract、Evaluation Fixture、Golden Fixture、Counterexample、Prompt Regression Suite、Model Comparison Policy、redaction / rollback 和 LLM trace 关系均已冻结。

该结论只关闭 Prompt Asset / Evaluation 设计 blocker，不授权 PR2 code implementation，不允许修改 `apps/**`、`tests/**`、依赖、migration 或 CI。PR2 是否可启动仍以 `BACKLOG.md` 中其他 blocker、PR2 preflight 和主 Agent 重新授权为准。

## 15. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-24 | 新增 Prompt Asset registry 与 mapping table | 关闭 AIFI-PROMPT-002 的 Prompt Asset 设计缺口；PR2 仍需其他 blocker 关闭或 accepted risk |
