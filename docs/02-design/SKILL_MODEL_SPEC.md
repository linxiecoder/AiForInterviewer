---
title: SKILL_MODEL_SPEC
type: design
status: draft-f5-skill-model-spec
owner: 技术架构 / AI 架构
source_task: AIFI-ARCH-007
permalink: ai-for-interviewer/docs/02-design/skill-model-spec
---

# SKILL_MODEL_SPEC

## 1. 文档目的与治理边界

本文件是 AIFI-ARCH-007 的 active design doc，冻结 AiForInterviewer MVP 的统一 Skill / Capability Model。它为简历分析、岗位匹配、进展树、出题、反馈评分、报告、复盘、薄弱项、资产、训练建议和后续 LangGraph 业务节点提供同一套能力语义、证据引用、低置信度和确认边界。

本文件只定义逻辑模型、引用关系、AI graph 读写边界、API 可见性和测试策略；不定义 ORM、DDL、migration、endpoint 实现、前端页面或生产 Prompt 文案。任何实现仍必须遵守 `BACKLOG.md`、`DELIVERY_PLAN.md`、`DATA_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md` 和 PR scope。

## 2. 输入来源与当前结论

| 来源 | 读取结论 |
|---|---|
| `SCORING_SPEC.md` / `models/scoring.py` | `ScoreDimension` 只属于 `ScoreRuleVersion`，保存评分维度、权重和解释，不表达长期能力 taxonomy、等级、证据累积或训练路径。 |
| `PROMPT_SPEC.md` / `POLISH_CONTRACTS.md` / `progress_tree_v2.py` | `ProgressTree` 是会话内 topic / node / status / current position 规划，节点可引用 evidence chunks，但不是跨模式能力本体。 |
| `DATA_MODEL.md` / `models/weakness.py` | `Weakness` / `WeaknessCandidate` 表达已确认或待确认的问题、风险和缺口，不能覆盖正向能力、已掌握能力或成长趋势。 |
| `DATA_MODEL.md` / `models/asset.py` | `Asset` / `AssetVersion` 是可复用表达素材和来源版本，可作为能力证据或训练材料，但不是 Skill。 |
| `DATA_MODEL.md` / `models/training.py` | `TrainingRecommendation` / `TrainingTask` 是训练建议和显式训练动作，作用于能力缺口，但不能替代能力分类体系。 |
| `job_match.py` / `JOB_MATCH_CONTRACTS.md` | Job Match 已有 `skill_coverage` 等评分维度和岗位缺口输出，但缺少 stable skill id、target level、assessment / gap / progress 引用。 |

结论：必须建立独立 Skill / Capability taxonomy。现有对象只能引用或消费 Skill Model，不能被临时升级为 Skill Model。

## 3. Non-goals

- 不把 `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` 或 `TrainingTask` 改名为 Skill。
- 不新增 `P-*` Prompt contract ID；现有 contract 只通过输入 / 输出字段引用 Skill Model。
- 不设计 Skill ORM、物理表、migration、repository、API endpoint 或前端组件。
- 不让 AI 输出绕过候选 / 建议 / 用户确认边界，直接创建正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation` 或 `TrainingTask`。
- 不把岗位缺口直接包装成用户稳定能力缺陷。
- 不承诺真实招聘结果校准、精确通过概率、自动能力评级或全自动训练闭环。

## 4. Core concepts

| 概念 | 定义 | 最小字段 / 语义 |
|---|---|---|
| `SkillTaxonomyVersion` | 一套可版本化能力分类。 | `taxonomy_version_id`、`version`、`scope`、`status`、`effective_from`、`owner`、`migration_policy`。 |
| `SkillArea` | 顶层能力域。 | `skill_area_id`、`taxonomy_version_id`、`area_key`、`name`、`description`、`display_order`。 |
| `Skill` | 稳定能力项，是跨模式共享的最小能力语义单元。 | `skill_id`、`skill_area_id`、`skill_key`、`name`、`observable_behaviors[]`、`related_job_signals[]`、`status`。 |
| `SkillLevel` | 能力等级 rubric。 | `skill_level_id`、`skill_id`、`level_key`、`behavior_rubric`、`evidence_threshold`、`confidence_requirement`。 |
| `SkillEvidence` | 指向具体输入或结果的能力证据。 | `skill_evidence_id`、`skill_id`、`evidence_ref`、`source_type`、`source_version_ref`、`summary`、`confidence_level`、`validation_status`、`owner_ref`、`trace_refs[]`。 |
| `SkillAssessment` | 对某个 Skill 的当前评估。 | `skill_assessment_id`、`skill_id`、`target_ref`、`level_ref`、`score_hint`、`confidence_level`、`evidence_refs[]`、`validation_status`、`generated_by_task_id`、`candidate_status`。 |
| `SkillGap` | 目标能力与当前评估之间的缺口。 | `skill_gap_id`、`skill_id`、`target_level_ref`、`current_level_ref`、`gap_reason`、`evidence_refs[]`、`source_ref`、`candidate_status`、`confirmation_ref`。 |
| `SkillProgress` | 能力随时间变化的趋势。 | `skill_progress_id`、`skill_id`、`target_ref`、`assessment_refs[]`、`training_result_refs[]`、`trend`、`last_updated_at`。 |
| `SkillToQuestionPattern` | Skill 到题型 / 追问策略的映射。 | `skill_id`、`question_pattern_id`、`difficulty`、`mode_applicability`、`non_equivalence_note`。 |
| `SkillToScoreDimension` | Skill 到评分维度的映射。 | `skill_id`、`score_type`、`score_dimension_key`、`weight_policy`、`non_equivalence_note`。 |
| `SkillToTrainingAction` | Skill / Gap 到训练建议形态的映射。 | `skill_id`、`gap_pattern`、`training_action_shape`、`asset_ref_policy`、`entry_mode`。 |

## 5. 逻辑数据模型

| 分组 | 逻辑对象 | 关系 |
|---|---|---|
| Taxonomy | `SkillTaxonomyVersion`、`SkillArea`、`Skill`、`SkillLevel` | taxonomy version 拥有 area / skill / level；发布后不得原地改写语义。 |
| Evidence | `SkillEvidence` | 只保存 refs、summary、confidence、validation 和 trace，不保存 raw prompt、raw completion 或 provider payload。 |
| Assessment | `SkillAssessment` | 可以由 Job Match、Polish feedback、Report、Review 或 Training result 生成 candidate；正式采用需满足证据与校验规则。 |
| Gap | `SkillGap` | 可由岗位要求、评分低分、薄弱项候选或复盘项生成；候选到正式必须保留确认或风险接受记录。 |
| Progress | `SkillProgress` | 汇总多个 `SkillAssessment`、`TrainingResult` 和人工校正记录；不得覆盖历史 assessment。 |
| Mapping | `SkillToQuestionPattern`、`SkillToScoreDimension`、`SkillToTrainingAction` | 显式表达 Skill 与题目、评分、训练之间的非等价映射。 |

逻辑引用规则：

1. 所有 Skill 相关对象必须携带 `owner_ref` 或可推导 owner scope。
2. 所有 AI 生成的 `SkillEvidence`、`SkillAssessment`、`SkillGap` 必须带 `generated_by_task_id` 或 `trace_refs[]`。
3. 所有可见结论必须带 `confidence_level`、`validation_status` 和 `evidence_refs[]`；证据不足时只能输出 `low_confidence`、`manual_review_required` 或 candidate。
4. taxonomy 变更必须生成新 `SkillTaxonomyVersion`；历史 assessment / gap 继续引用生成时版本。

## 6. 与 ScoreDimension 的关系

`ScoreDimension` 不是 Skill。它属于某个 `ScoreRuleVersion`，用于解释某类评分结果的维度、权重和分值来源。Skill 是跨评分类型、跨模式、跨时间的能力语义。

| Score area | 现有 `ScoreDimension` 示例 | Skill Model 使用方式 |
|---|---|---|
| `job_match` | `requirement_alignment`、`experience_evidence`、`skill_coverage`、`gap_risk`、`readiness_actions` | 通过 `SkillToScoreDimension` 映射岗位目标 skill、证据强度和 gap，不把维度当 skill id。 |
| `polish_answer` | `technical_depth`、`communication_structure`、`evidence_specificity`、`risk_control` | 反馈评分可生成 `SkillEvidence` / `SkillAssessment` candidate，但正式能力判断必须可追溯到 evidence refs。 |
| `pressure_session` | `answer_quality`、`follow_up_resilience`、`breadth_coverage` | 压力面可读取 target `SkillGap` 安排追问，但 session score 不等于 SkillProgress。 |
| `report_section` | `evidence_binding`、`score_explanation_quality`、`actionability` | 报告分项可聚合 skill refs，用于解释和训练建议输入，不暴露隐藏评分规则。 |

## 7. 与 ProgressTree 的关系

`ProgressTree` 是打磨模式或压力面模式中的会话规划结构。它可以消费 `SkillToQuestionPattern`、`SkillGap` 和 `SkillEvidence` 来选择题目、排序节点和标注低置信度，但 `ProgressNode` 不是 Skill。

映射规则：

- `ProgressNode.skill_target_refs[]` 可以引用目标 Skill 或 SkillGap。
- `ProgressNode.evidence_chunk_ids[]` 继续引用 RAG-lite / deterministic chunks；这些 chunks 可以转为 `SkillEvidence` candidate。
- 进展树刷新不得删除已有 `node_ref`，也不得因节点完成直接更新正式 `SkillProgress`。
- 暂停 / 恢复只保存 progress position 和安全摘要，不把 checkpoint 或 tree state 当能力事实源。

## 8. 与 Weakness / Asset / Training 的关系

| 对象 | 与 Skill Model 的关系 | 禁止替代 |
|---|---|---|
| `Weakness` | 可引用一个或多个 `SkillGap`；表示用户已确认或规则确认的薄弱项。 | `Weakness` 不是 Skill；岗位缺口或单次失误不得直接变成正式 Weakness。 |
| `WeaknessCandidate` | 可由 `SkillGap` candidate、低分维度、复盘项或反馈失分点生成。 | 候选不得绕过确认写正式 Weakness。 |
| `Asset` / `AssetVersion` | 可作为 `SkillEvidence` 来源或 `SkillToTrainingAction` 的训练材料。 | Asset 是内容，不是能力本体。 |
| `AssetCandidate` | 可与 SkillEvidence 互相引用，表达某段回答或项目表达可支撑某项 Skill。 | 不得自动归档为正式 Asset / AssetVersion。 |
| `TrainingRecommendation` | 针对一个或多个 `SkillGap` 生成训练建议。 | 训练建议不是 Skill，也不是训练任务。 |
| `TrainingTask` | 用户显式开始的训练动作，可回写 `SkillProgress` candidate。 | AI suggestion 不得自动创建 TrainingTask。 |

## 9. 与 JobMatch dimensions 的关系

岗位匹配链路负责把岗位要求转换为目标能力和能力缺口：

1. `JobVersion` / `ResumeVersion` / `JobResumeBinding` 生成 source evidence。
2. `P-JOBMATCH-001` 输出匹配点、不匹配点、加强点和面试重点。
3. `P-JOBMATCH-002` 输出 0-100 `ScoreResult(job_match)`，维度继续由 `SCORING_SPEC.md` 管理。
4. `P-JOBMATCH-004` 可以生成 `SkillGap` / `WeaknessCandidate` candidate refs，但不得把岗位缺口直接包装成正式能力缺陷。
5. 后续 Polish / Pressure / Training 读取 target `SkillGap`，不得重新发明临时 skill key。

## 10. 与 Prompt Contracts 的关系

本文件不新增 Prompt contract ID。现有 contracts 通过以下字段族引用 Skill Model：

| Contract domain | Skill 输入 | Skill 输出 |
|---|---|---|
| Job Match | `target_skill_refs[]`、`skill_taxonomy_version_ref` | `skill_gap_candidate_refs[]`、`skill_evidence_refs[]` |
| Polish | `skill_target_refs[]`、`skill_gap_refs[]`、`skill_evidence_refs[]` | feedback 产生 `skill_assessment_candidate_refs[]`、`skill_gap_candidate_refs[]` |
| Pressure | `skill_gap_refs[]`、`pressure_focus_skill_refs[]` | pressure answer quality 产生 candidate refs；mode-level spec 未完成前不得实现 pressure graph。 |
| Report | `skill_assessment_refs[]`、`score_refs[]` | 报告 section 可聚合 `skill_summary_refs[]`，不暴露隐藏评分规则。 |
| Review | report / turn / score / skill refs | 复盘生成 SkillGap、Weakness、Asset、Training candidate refs。 |
| Weakness | `skill_gap_candidate_refs[]`、`skill_evidence_refs[]` | Weakness candidate / merge / severity / status suggestion 均保留候选边界。 |
| Asset | `skill_evidence_refs[]`、`skill_gap_refs[]` | asset candidate 可支撑 SkillEvidence 或训练材料。 |
| Training | `skill_gap_refs[]`、`skill_progress_refs[]` | training recommendation / result review 只产生建议或 progress candidate。 |

所有 contract 仍必须复用 Shared failure signals、Output Validation、Evidence Binding、Low Confidence、Trace / Persistence 规则。

## 11. 与 LangGraph nodes 的关系

| Graph / Node | 读取 Skill | 写入 Skill | 边界 |
|---|---|---|---|
| Job Match graph | taxonomy version、target skill refs、job requirement evidence | `SkillEvidence` candidate、`SkillGap` candidate | 保留 legacy analyzer fallback；不输出精确通过概率。 |
| Polish progress tree node | `SkillToQuestionPattern`、`SkillGap`、selected evidence chunks | node-level `skill_target_refs`、`SkillEvidence` candidate | ProgressTree 不是 Skill source of truth。 |
| Polish question node | `SkillGap`、topic/subtopic、forbidden repeat refs | question refs and trace only | 出题不直接写 assessment / gap formal object。 |
| Polish feedback node | current question / answer、score rule、Skill refs | `SkillAssessment` candidate、`SkillEvidence` candidate、possible `SkillGap` candidate | answer save no LLM；feedback candidate-only。 |
| Pressure graph | `SkillGap`、pressure focus、pace rules | answer quality candidate refs | AIFI-BE-004 未关闭前保持 hold。 |
| Report graph | score refs、confirmed evidence、assessment refs | report skill summary refs | 不暴露 hidden scoring rules。 |
| Review graph | report / turn / score / skill refs | `SkillGap`、Weakness / Asset / Training candidate refs | 仍需用户确认。 |
| Weakness / Asset / Training graph | candidate refs、SkillGap、SkillEvidence | suggestion refs、progress candidate | 不直接 formalize。 |

Graph state 只能保存 refs、安全摘要、validation flags 和 low confidence flags；不得保存 raw prompt、raw completion、provider payload 或把 checkpoint 当业务事实源。

## 12. Evidence / trace / low confidence rules

- `SkillEvidence` 必须引用 `EvidenceRef`、`SourceRef`、`VersionRef` 或 `SnapshotRef`；不能只保存不可追溯文案。
- `SkillAssessment` 和 `SkillGap` 至少需要一个可见 evidence ref；证据不足时 `validation_status=manual_review_required` 或 `invalid`。
- 多来源冲突时必须记录 `conflicting_evidence` low confidence flag，不能选择性覆盖旧结论。
- `source_unavailable` 时不得读取来源正文，不得生成高置信 assessment。
- 单次轻微失误、岗位缺口、低质量回答或 provider fallback 只能生成 low-confidence candidate。
- 人工校正必须生成 `UserCorrectionRef` 或 `UserConfirmationRef`，不得原地改写历史 evidence。
- 所有 trace 只保存必要结构化引用、模型名、prompt version、validation summary 和 redacted usage，不保存 raw payload。

## 13. API visibility

MVP API 可以在现有 response 中暴露 Skill 相关摘要字段，但不在本文件定义新 endpoint。

| API 可见字段族 | 规则 |
|---|---|
| `skill_refs[]` | 只包含 stable skill id、taxonomy version、display name 和 area，不包含隐藏 rubric。 |
| `skill_gap_candidate_refs[]` | 用于 job match、feedback、review、training suggestion 的候选引用。 |
| `skill_assessment_summary[]` | 只展示用户可见摘要、confidence、evidence refs 和低置信提示。 |
| `skill_progress_summary[]` | 仅在有 confirmed evidence 或训练结果时展示；不得伪造趋势。 |
| `next_actions[]` | 可以指向训练、打磨或压力面入口，但不得自动启动 TrainingTask。 |

API 不得返回 raw prompt、completion、provider payload、完整内部权重表、隐藏评分规则或无权限来源正文。

## 14. 测试策略

F7 / graph migration 至少覆盖以下 fixture：

| Fixture | 断言 |
|---|---|
| `skill.taxonomy.version_stable_refs` | taxonomy 发布后历史 assessment / gap 继续引用生成时版本。 |
| `skill.score_dimension.non_equivalence` | `ScoreDimension` 只能通过 mapping 引用 Skill，不能被当成 skill id。 |
| `skill.progress_tree.non_equivalence` | `ProgressNode` 可引用 skill refs，但节点完成不自动更新正式 SkillProgress。 |
| `skill.weakness.candidate_confirmation_required` | `SkillGap` / `WeaknessCandidate` 不绕过用户确认写正式 Weakness。 |
| `skill.asset.evidence_not_skill` | Asset 可作为 SkillEvidence 来源，但 Asset 不是 Skill。 |
| `skill.training.confirm_before_task` | TrainingRecommendation candidate 不自动创建 TrainingTask。 |
| `skill.low_confidence.conflicting_evidence` | 多来源冲突时输出 low confidence / manual review，不覆盖历史结论。 |
| `skill.source_unavailable.no_formal_assessment` | source unavailable 不生成高置信正式 SkillAssessment。 |
| `skill.manual_correction.audit_ref` | 人工校正生成 correction / confirmation ref，不改写历史 evidence。 |
| `skill.raw_payload.redaction` | Skill trace 不保存 raw prompt、completion、provider payload 或 system prompt。 |

## 15. Migration and rollout sequence

1. AIFI-ARCH-007 先冻结本文件、`DOCS_INDEX.md` 登记和轻量 cross-reference。
2. AIFI-BE-005 的 PR2 preflight 必须确认 PR2 不创建任何 `Skill*` formal object，也不把现有对象临时升级为 Skill。
3. PR5 = Polish first migration target：读取 SkillGap / SkillToQuestionPattern，反馈只写 assessment / gap candidate refs。
4. PR6 = Graph Configuration Backend：只登记 graph descriptor / config registry metadata，不实现 Skill 相关业务 graph。
5. PR7 = AI Runtime graph configuration console：只展示 sanitized Skill / prompt / eval / model policy refs，不展示 raw runtime internals。
6. PR8 = JobMatch / ResumeAnalysis deferred / conditional graph migration：只有在 dedicated scope lock 下才可引用已冻结 mapping、输出 `SkillGap` candidate refs、保留 legacy fallback parity。
7. Pressure graph 只有在 AIFI-BE-004 关闭后才能读取 pressure focus skill refs。
8. PR8 Report / Review / Candidate closure 聚合 SkillAssessment / SkillGap，并通过确认流进入 Weakness / Asset / Training。
9. F7 fixtures 覆盖 low confidence、conflicting evidence、manual correction 和 training result update。

## 16. Definition of Done

- `SKILL_MODEL_SPEC.md` 已作为 active design doc 登记到 `DOCS_INDEX.md`。
- 本文件明确说明 `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` / `TrainingTask` 均不能替代 Skill Model。
- 核心概念、逻辑模型、Score / Progress / Weakness / Asset / Training / JobMatch / Prompt / LangGraph 关系已冻结。
- evidence、trace、low confidence、API visibility、testing strategy 和 rollout sequence 可直接指导后续实现。
- `BACKLOG.md` 中 AIFI-ARCH-007 状态已更新为 `ACCEPTED` 或等价关闭状态。
- PR2 code implementation 仍需等待其余 blocker 关闭或 accepted risk 登记；AIFI-ARCH-007 关闭不自动授权 PR2。

## 17. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-24 | 初始化 Skill / Capability Model 设计 | 关闭 AIFI-ARCH-007 的设计缺口；冻结 Skill taxonomy、现有对象非替代关系、AI graph 读写边界、证据 / 低置信度规则和后续 rollout gate |
