---
title: SEMANTICS_GLOSSARY
type: design
status: draft-f4-semantics-glossary
owner: 技术架构 / API / AI 架构
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/semantics-glossary
---

# SEMANTICS_GLOSSARY

## 1. 文档状态与治理边界

- 本文件是 F4 跨文档语义词汇表，承接人工审计中“低置信度等术语是否真实存在、是否定义清楚、是否存在系统虚假生成或语义漂移”的整改。
- 本文件统一低置信度、validation status、source availability、candidate / suggestion / formal object、用户确认和关键失败状态的语义。
- 本文件不定义 API endpoint、物理数据库、Prompt 文案、模型 provider 或 UI 文案最终稿；API 字段、持久化字段和 Prompt contract 细则仍由对应 active design docs 承接。

## 2. Low Confidence

`Low Confidence` 不是模型虚构名词，也不是普通成功态的装饰字段。它是业务风险状态，表示当前结果受输入、证据、来源、上下文、校验或模型稳定性影响，不能按高置信结论展示、复制、落正式对象或驱动确定性通过倾向。

### 2.1 触发条件

低置信度至少由以下条件触发：

| 触发条件 | 说明 |
|---|---|
| `input_insufficient` | 输入不足，例如回答过短、岗位或简历缺关键材料 |
| `evidence_missing` | 关键结论缺少 `EvidenceRef` |
| `evidence_conflict` | 证据互相冲突或与输出解释冲突 |
| `source_unavailable` | 来源不可访问、删除、禁用、归档、无权限或缺少生成快照 |
| `validation_weak_pass` | 结构化通过但业务语义弱通过 |
| `output_incomplete` | 模型输出缺少关键字段或段落 |
| `context_truncation_risky` | 上下文裁剪影响结论可靠性 |
| `score_explanation_mismatch` | 分数和解释、证据或维度分不一致 |
| `model_result_unstable` | 重试或候选输出间差异过大，不能稳定解释 |

### 2.2 影响

| 影响面 | 规则 |
|---|---|
| API status | 必须通过 `status=low_confidence`、`partial`、`validation_failed`、`manual_review_required` 或 envelope 中的 `low_confidence_flags[]` 表达；不得只返回普通 `success` |
| UI warning | F6 必须展示风险提示、受影响范围和可操作 `next_actions`；不得把低置信结果当正常完成态 |
| next_actions | 允许 `manual_review`、`correct_low_confidence`、`retry_generation`、`provide_more_input`、`choose_available_source`、`skip` |
| 是否可复制 | 可复制内容必须携带低置信提示和脱敏边界；不得包含 source unavailable 正文、隐藏评分规则、Prompt 或 provider payload |
| 是否可落正式对象 | 默认不得直接落正式 `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation` 或正式报告评分；必须经 validation、用户确认或人工校对 |
| 是否必须人工校对 | `confidence_level=insufficient` 或 `validation_status=manual_review_required` 时必须人工校对或用户补充材料 |
| 是否允许进入 report / review / training suggestion | 可以作为风险标记或候选输入进入，但必须保留 `LowConfidenceFlag`、`EvidenceRef`、`TraceRef` 和用户可见提示 |

Low confidence 不阻断保存用户原始输入，例如 `Answer`、`RealInterviewInput`、用户校对内容或复制事件审计；它阻断的是把不可靠输出伪装成高置信正式结论。

## 3. Canonical enum

### 3.1 `confidence_level`

| 值 | 语义 | 允许行为 |
|---|---|---|
| `high` | 输入、证据、校验和解释充分 | 可展示正式结果，仍需免责声明 |
| `medium` | 主要证据充分但存在轻微不确定 | 可展示正式结果，需提示局限 |
| `low` | 证据不足、冲突、弱通过或上下文风险明显 | 只能带风险展示、候选或待确认，不得给确定性倾向 |
| `insufficient` | 缺少关键输入、来源或校验失败 | 不得落正式结论；需要补充、重试或人工校对 |

### 3.2 `validation_status`

| 值 | 语义 | 允许行为 |
|---|---|---|
| `valid` | schema 与业务语义均通过 | 可进入正式结果 |
| `valid_with_warnings` | 可用但有非阻断警告 | 可进入正式结果或候选结果，但必须带 warning / low confidence |
| `invalid` | schema 或业务语义不通过 | 不得写 formal object，不得展示正式评分 |
| `manual_review_required` | 需要人工校对或用户补充 | 不得自动确认，允许保存候选和校对入口 |

现有文档中 `passed` 可映射为 `valid`；`failed` 可映射为 `invalid`；`validation_partial` 可映射为 `valid_with_warnings` 或 `manual_review_required`，由业务上下文决定。

### 3.3 `source_availability`

| canonical 值 | 语义 | 新生成是否可读正文 |
|---|---|---|
| `source_available` | 通过 owner / scope 校验且可读取最小必要片段 | 可以 |
| `source_archived` | 来源已归档，历史引用保留 ref / snapshot / summary status | 默认不可以 |
| `source_deleted` | 来源已删除，历史引用只保留状态和生成时引用 | 不可以 |
| `source_disabled` | 来源因风险或维护禁用 | 不可以 |
| `source_unavailable` | 不可访问、无权限、缺快照或读取失败 | 不可以 |

跨文档出现的聚合值映射如下：

| 旧 / 聚合值 | canonical 解释 | 使用边界 |
|---|---|---|
| `available` | 聚合后全部 `source_available` | 只可作为 UI / Prompt 输出聚合状态，不替代底层枚举 |
| `partial` | 部分来源 `source_available`，部分为 archived / deleted / disabled / unavailable | 必须保留每个来源的 canonical 状态 |
| `unavailable` | 聚合后无可用来源 | 对底层来源使用 `source_unavailable` 或具体 deleted / disabled / archived |
| `mixed` | 多种状态混合 | 只作为摘要，不可用于持久化底层来源 |

F5 / F7 必须以 `source_*` canonical 值为持久化和 API contract 的稳定断言；`available / partial / unavailable / mixed` 只允许作为聚合展示或 Prompt 输出摘要。

## 4. Candidate / suggestion / formal object

| 术语 | 语义 | 写入边界 |
|---|---|---|
| `candidate` / `CandidateRef` | AI 或用户动作产生的待确认候选 | 可保存为候选；用户确认前不得成为 formal object |
| `suggestion` / `SuggestionRef` | 合并、严重度、优先级、版本更新、沉淀目标等建议 | 可保存为建议或 hint；不得自动执行正式业务动作 |
| `UserConfirmationRef` | 用户确认、编辑、跳过、拒绝、合并、校对或沉淀目标选择记录 | formal write 前必须绑定，且记录 actor、target、action、before / after、trace 和 audit |
| `formal object` | 正式 `Weakness`、`Asset`、`AssetVersion`、确认后的 `TrainingRecommendation`、`TrainingTask` 等 | 必须经用户确认、编辑、合并或显式业务动作创建或更新 |

AI output 允许进入 `AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`LlmValidationResult`、`LowConfidenceFlag`、`TraceRef` 和 `EvidenceRef`；不得静默进入 formal object。

## 5. 失败状态不被 success 吞掉

以下状态不能被普通 `success` 吞掉：

| 状态 | API 表达 | Prompt / DATA 表达 | F7 要求 |
|---|---|---|---|
| `low_confidence` | `status=low_confidence` 或 success envelope 中显式 `low_confidence_flags[]` | `LowConfidenceFlag` + `TraceRef` | UI 可见，不得展示为高置信完成 |
| `source_unavailable` | 409 / 422 或历史结果读取中的 `source_availability=source_unavailable` | `SourceRef` / `EvidenceRef` 保留状态，不读正文 | 新生成被阻断或降级 |
| `validation_failed` | 422 或 task result `status=validation_failed` | `LlmValidationResult`、failure record | 不写正式评分、报告评分或 formal object |
| `manual_review_required` | `next_actions` 包含 manual review / correct / retry | `LowConfidenceFlag` / `UserCorrectionRef` | 需要人工校对或用户补充 |
| `partial` | `status=partial` 且列出可用和不可用部分 | partial result + omitted refs | 不得隐藏缺失字段 |

## 6. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-17 | 初始化跨文档语义词汇表 | 统一 Low Confidence、validation status、source availability、candidate / suggestion / formal object 和失败状态展示边界 |
