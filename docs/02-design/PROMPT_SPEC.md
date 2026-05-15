---
title: PROMPT_SPEC
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
permalink: ai-for-interviewer/docs/02-design/prompt-spec
---

# PROMPT_SPEC

## 1. 文档状态与治理边界

- 本文件是 F4 技术设计下的 Prompt / AI 子任务 contract 子文档，承接 `AIFI-PROMPT-001`。
- 本文件当前只初始化 AI 子任务 contract 骨架、目录和统一模板，不是完整提示词文案库。
- 本文件不是代码实现、API spec、数据模型、模型供应商配置或向量数据库设计。
- 本文件不定义 API endpoint、request / response schema、物理数据库 schema、embedding 模型、向量数据库或联网搜索服务。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN，不标记 `AIFI-ARCH-002` 完成，也不把 `AIFI-PROMPT-001` 标记为 DONE。
- 本文件不得把 `archive/**` 作为当前执行依据；历史内容只有迁入 active docs 后才能影响本规范。
- 打磨模式、压力面模式、岗位匹配分析、报告、复盘、薄弱项、资产和训练建议必须由后端应用编排层串联，不能退化为单次 LLM 调用或一个大 Prompt。

## 2. 输入来源与非目标

### 2.1 输入来源

| 来源 | 本文使用方式 |
|---|---|
| `docs/01-product/PRD.md` | MVP 业务对象、核心数据流、状态异常、验收标准、非目标和 PRD §10 UNKNOWN |
| `docs/02-design/TECH_DESIGN.md` | AI 编排总览、LLM 边界、Context Assembly、Retrieval / RAG、trace / evidence 和子文档交接边界 |
| `docs/02-design/DATA_MODEL.md` | `EvidenceRef`、`TraceRef`、`VersionRef`、`SnapshotRef`、`RAGContextAssembly`、`LlmValidationResult` 等逻辑对象和状态承载 |
| `docs/02-design/SECURITY_PRIVACY.md` | Prompt 输入最小化、owner 校验、隐私裁剪、RAG 来源治理、日志限制和 LLM / RAG failure 安全表达 |
| `docs/03-delivery/BACKLOG.md` | `AIFI-PROMPT-001` 范围，以及与 `AIFI-ARCH-002`、`AIFI-DATA-001`、`AIFI-SEC-001` 的依赖 |

### 2.2 非目标

本文不做以下事项：

- 不写完整 Prompt 文案全集。
- 不放入可直接调用生产模型的长提示词。
- 不选择具体 LLM provider。
- 不冻结模型参数。
- 不选择向量数据库。
- 不选择 embedding 模型。
- 不实现联网搜索服务。
- 不实现后端代码。
- 不定义 API endpoint。
- 不定义物理数据库 schema。
- 不承诺精确通过概率或准确预测真实面试结果。
- 不绕过用户确认写入正式资产、薄弱项或训练建议。
- 不把 Prompt 当成完整业务能力。

## 3. 核心术语

| 术语 | 定义 |
|---|---|
| AI Task Contract | 单个 AI 子任务的输入、检索、上下文、模型调用、输出、校验、失败处理和持久化交接约束 |
| Prompt Contract | AI Task Contract 中与模型输入输出直接相关的部分 |
| Context Assembly | 把简历、岗位、会话、资产、薄弱项、RAG evidence、历史摘要等组装成模型上下文的过程 |
| Retrieval Policy | 决定是否检索、检索哪些来源、如何过滤、排序、裁剪和引用证据的规则 |
| Session Memory | 会话过程中的短期上下文、历史摘要、已问问题、已暴露薄弱项和禁止重复项 |
| Output Schema | 模型输出进入业务校验前必须满足的结构化协议 |
| Validation | 对模型输出进行结构化校验和业务语义校验 |
| Low Confidence | 资料不足、证据冲突、模型输出不完整或校验弱通过时的显式状态 |
| EvidenceRef | 支撑评分、建议、弱项、资产候选和报告结论的证据引用 |
| TraceRef | 支撑模型调用、检索、上下文装配、输出校验和失败记录的过程引用 |
| Failure Signal | 跨 Shared Contract 传递的标准化失败信号，统一使用 snake_case 命名 |

## 4. AI Task Contract 标准模板

后续每个 AI 子任务 contract 必须使用统一字段。字段是 contract 结构，不是 Prompt 文案。

| 字段 | 必填 | 说明 |
|---|---|---|
| `contract_id` | 是 | 稳定编号，例如 `P-QUESTION-001` |
| `name` | 是 | 子任务名称 |
| `mode` | 是 | `job_match` / `polish` / `pressure` / `report` / `review` / `weakness` / `asset` / `training` / `shared` |
| `trigger` | 是 | 由哪个用户动作、系统状态或编排步骤触发 |
| `goal` | 是 | 该子任务要产生的业务结果 |
| `required_inputs` | 是 | 必需输入对象和版本引用 |
| `optional_inputs` | 否 | 可选增强输入 |
| `retrieval_sources` | 否 | 可使用的检索来源 |
| `context_assembly` | 是 | 上下文分层、裁剪和排序规则 |
| `excluded_inputs` | 是 | 禁止进入模型的内容 |
| `output_schema` | 是 | 结构化输出要求 |
| `validation_rules` | 是 | 结构化校验和业务语义校验 |
| `low_confidence_rules` | 是 | 低置信度触发条件 |
| `evidence_refs` | 是 | 输出必须绑定的证据引用 |
| `trace_refs` | 是 | 必须记录的过程引用 |
| `persistence_targets` | 是 | 输出可写入或候选写入的业务对象 |
| `user_confirmation_required` | 是 | 是否需要用户确认后才能回流 |
| `retry_policy` | 否 | 可重试条件 |
| `fallback_policy` | 否 | 降级或人工校对路径 |
| `api_state_mapping` | 是 | 对 API 状态语义的要求；本文只定义语义，不定义 endpoint 或 schema |
| `security_notes` | 是 | owner 校验、隐私裁剪、日志限制 |
| `test_strategy` | 是 | 确定性替身和最小验证要求 |
| `open_questions` | 否 | 仍待后续业务 contract、API 或实现阶段关闭的问题；不得在 shared contract 中提前关闭 `F4_TECH_DESIGN` UNKNOWN |

## 5. Context Assembly 总策略

一场模拟面试内容不能整体塞进一个 Prompt。后端应用编排层必须按 contract、模式、轮次和输出目标组装最小必要上下文。

上下文装配至少分层：

1. 固定系统规则。
2. 模式规则。
3. 当前岗位版本摘要。
4. 当前简历版本摘要。
5. 当前题目。
6. 当前用户回答。
7. 最近若干轮问答。
8. session summary。
9. 已问问题列表。
10. 禁止重复追问列表。
11. 资产库命中。
12. 薄弱项命中。
13. 历史报告 / 复盘摘要命中。
14. RAG evidence。
15. 输出 schema 和 validation 要求。

Context Assembly 规则：

- 每个 contract 必须说明自己需要哪些上下文层。
- 不得默认塞入全部简历、全部岗位、全部历史会话和全部资产。
- 上下文超长时必须有裁剪策略。
- 裁剪不得破坏 owner 校验、证据引用和历史结果可追踪性。
- 被删除、禁用、归档、不可访问或缺少版本快照的来源不得进入新生成上下文；历史结果只能通过来源可用性状态表达 `source_unavailable` 等标准枚举。
- 组装过程应能通过 `RAGContextAssembly`、`LlmRequestTrace` 或同等 `TraceRef` 回溯输入来源、裁剪原因、检索状态和低置信度状态。

## 6. Retrieval / RAG / 资产检索策略

检索不是所有 AI 子任务的默认前置步骤。每个 contract 必须声明是否检索、检索哪些来源、如何过滤、排序、裁剪和引用证据。

| 来源 | 是否默认启用 | 适用场景 | 进入上下文前要求 |
|---|---|---|---|
| 简历版本 / 摘要 | 是 | 岗位匹配、出题、评分、报告、复盘 | 引用 `ResumeVersion` 或 `SnapshotRef` |
| 岗位版本 / 摘要 | 是 | 岗位匹配、出题、评分、压力面 | 引用 `JobVersion` 或 `SnapshotRef` |
| 资产库 | 条件启用 | 打磨、压力面、复盘、训练建议 | owner 校验、资产状态校验、版本引用 |
| 薄弱项 | 条件启用 | 题目推荐、追问、训练建议、报告 | 状态过滤、来源证据引用 |
| 历史报告 / 复盘 | 条件启用 | 后续模拟面试、训练建议、弱项更新 | 版本 / 快照引用、低置信度继承 |
| 知识库 / RAG | 条件启用 | 考点解析、技术原理扩展、参考回答、证据增强 | owner / scope 校验、chunk 版本、evidence 引用 |
| 公共参考材料 | 条件启用 | 基础评分口径、通用考点、公共知识 | 维护者发布状态、来源版本 |
| 互联网检索 | 非默认，需显式启用 | 仅在后续产品或技术设计明确需要时使用 | 来源可信度、时间戳、引用、隐私约束、失败降级 |

Retrieval Policy 边界：

- 不把互联网检索写成 MVP 默认强依赖。
- 不选择具体搜索服务。
- 不选择具体向量数据库。
- 不选择具体 embedding 模型。
- 私有来源必须按 owner / scope 过滤；公共来源必须有维护者、发布状态和版本。
- RAG evidence 进入业务结果时必须绑定 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef` 和 `TraceRef`。
- 检索为空、证据不足、证据冲突或 `source_unavailable` 时，结果必须进入 Low Confidence、部分可用、证据不足、证据冲突或生成失败状态，不能伪装成高置信结果。

### 6.1 Source Availability 状态矩阵

来源可用性状态统一使用 snake_case 枚举，供 Retrieval Planning、Context Assembly、Evidence Binding、Output Validation 和 Low Confidence Classification 复用。

| 状态 | 新生成是否可读取正文 | 历史引用处理 | 规则 |
|---|---|---|---|
| `source_available` | 可以，在通过 owner / scope 校验后读取最小必要片段 | 保留来源、版本、快照和摘要 | 可进入新生成上下文，但仍需最小化裁剪 |
| `source_unavailable` | 不可以 | 保留 ref、snapshot 或 summary status | 不得重新读取不可用正文；结果应进入低置信度或人工校对路径 |
| `source_deleted` | 不可以 | 保留历史 ref / snapshot / summary status | 不得把已删除正文放入新生成；历史结论不自动失效 |
| `source_disabled` | 不可以 | 保留历史 ref / snapshot / summary status | 禁用来源默认排除，只记录状态和必要风险标记 |
| `source_archived` | 默认不可以 | 历史引用可保留 ref / snapshot / summary status | archived 来源默认不进入新生成；除非后续业务设计明确恢复或选择历史引用场景 |
| `public_material_unpublished` | 不可以 | 不作为新生成证据 | 未发布公共材料不得进入业务生成或 RAG evidence |

## 7. Output Schema、Validation 与 Failure Handling

所有 LLM 输出进入报告、复盘、薄弱项、资产候选或训练建议前，必须先经过 Output Schema 结构化校验。结构化校验通过后，还必须进行业务语义校验。

输出状态必须能表达：

- 成功。
- 部分可用。
- 低置信度。
- 校验失败。
- 生成失败。
- 证据不足。
- 证据冲突。
- `source_unavailable`。

Validation 与失败处理规则：

- 失败不得伪装为正常高置信结果。
- 可用部分可以保留，但必须标记风险、来源和证据范围。
- 需要用户确认的回流结果不得静默写入正式资产、薄弱项或训练建议。
- 结构化校验失败时，不得进入正常业务事实；只能进入 validation result、failure record、候选修复或人工校对路径。
- 业务语义校验应检查模式边界、来源可用性、证据一致性、0-100 展示范围、不可承诺精确通过概率、用户确认要求和安全隐私边界。
- retry / fallback 不能扩大数据范围，不能把原始 Prompt、completion 或 provider payload 写入日志。

### 7.1 Shared Failure Signal Enum

Shared contracts 统一使用以下 failure signal 语义，业务 contracts 不应重复定义同一批 failure signals；除非存在业务特有扩展，否则应直接消费本枚举。枚举命名统一使用 snake_case，不混用空格写法。

| failure signal | 语义 |
|---|---|
| `required_input_missing` | 必需输入缺失或当前任务无法形成最小输入 |
| `retrieval_not_required` | 当前 contract 不需要检索 |
| `retrieval_empty` | 检索已执行但无可用命中 |
| `owner_mismatch` | 输入、来源或证据未通过 owner / scope 校验 |
| `source_unavailable` | 来源不可访问或当前不可读取正文 |
| `source_deleted` | 来源已删除 |
| `source_disabled` | 来源已禁用 |
| `source_archived` | 来源已归档，默认不参与新生成 |
| `public_material_unpublished` | 公共材料未发布 |
| `context_too_large` | 上下文超出预算且不能直接进入模型 |
| `context_truncated_with_risk` | 上下文已裁剪且裁剪影响结论可靠性 |
| `evidence_missing` | 关键结论缺少证据绑定 |
| `evidence_conflict` | 证据之间存在冲突 |
| `schema_invalid` | 输出结构不符合 output schema |
| `semantic_invalid` | 输出违反业务语义或安全边界 |
| `score_out_of_range` | 分数不在 0-100 展示范围内 |
| `output_incomplete` | 模型输出缺少关键字段或关键段落 |
| `validation_partial` | 结构化通过但业务语义弱通过或部分可用 |
| `manual_check_required` | 需要人工校对或用户补充确认 |
| `generation_failed` | 生成失败或结果不可用 |
| `summary_generation_failed` | 会话摘要生成或压缩失败 |
| `snapshot_missing` | 生成时版本或快照缺失 |

`P-SHARED-003` Output Validation 产出 normalized failure signals；`P-SHARED-004` Low Confidence Classification 消费 failure signals，负责分类、用户可见表达和 recommended action。业务 contract 可以添加业务特有 failure signal，但不得重命名或重复定义上述共享枚举。

## 8. Trace / Evidence / Persistence 交接

每个 contract 必须说明生成结果引用哪些 `EvidenceRef`，以及记录哪些 `TraceRef`。

交接规则：

- 不得把原始 Prompt、provider payload、completion 原文默认暴露给前端。
- 持久化目标应区分正式业务结果、候选结果、trace、validation result、low confidence flag 和 audit event。
- 用户确认前，只能写入候选、待确认或 validation / trace 状态，不得写入正式资产、薄弱项或训练建议。
- `EvidenceRef` 应能回溯到题目、回答、点评、评分解释、RAG 检索证据、用户确认、面试官反馈或生成时版本 / 快照。
- `TraceRef` 应能回溯到检索、Context Assembly、LLM request、LLM response、Output Schema 校验、Validation、Low Confidence classification、Failure Handling 和 audit event。
- Persistence 语义只定义业务交接和状态；物理表、ORM、DDL、索引和 migration 由后续实现承接。

## 9. Contract 目录总览

本阶段只建立 contract catalog，不填充完整 Prompt 文案。

### 9.1 Shared Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-SHARED-001` | Context Assembly | 统一上下文装配 | Draft |
| `P-SHARED-002` | Retrieval Planning | 决定检索来源与裁剪策略 | Draft |
| `P-SHARED-003` | Output Validation | 结构化与业务语义校验 | Draft |
| `P-SHARED-004` | Low Confidence Classification | 低置信度分类 | Draft |
| `P-SHARED-005` | Evidence Binding | 证据引用绑定 | Draft |
| `P-SHARED-006` | Session Summary Update | 会话摘要更新 | Draft |

### 9.2 Job Match Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-JOBMATCH-001` | Match Analysis | 生成岗位匹配分析 | Draft |
| `P-JOBMATCH-002` | Match Score | 生成 0-100 匹配分与解释 | Draft |
| `P-JOBMATCH-003` | Match / Mismatch / Improvement Points | 生成匹配点、不匹配点、加强点 | Draft |
| `P-JOBMATCH-004` | Weakness Candidate from Job Match | 从岗位匹配分析提炼薄弱项候选 | Draft |

### 9.3 Polish Mode Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-POLISH-001` | Topic Planning | 规划打磨主题 | Draft |
| `P-POLISH-002` | Question Generation | 生成或选择打磨题目 | Draft |
| `P-POLISH-003` | Answer Diagnosis | 诊断用户回答 | Draft |
| `P-POLISH-004` | Round Score | 生成每轮 0-100 得分 | Draft |
| `P-POLISH-005` | Loss Point Analysis | 生成失分点与原因 | Stub |
| `P-POLISH-006` | Reference Answer | 生成参考回答 | Stub |
| `P-POLISH-007` | Knowledge Point Explanation | 生成考点解析 | Stub |
| `P-POLISH-008` | Technical Principle Expansion | 生成技术原理扩展 | Stub |
| `P-POLISH-009` | Next Round Suggestion | 生成下一轮改进建议 | Stub |
| `P-POLISH-010` | Asset Candidate | 生成资产候选 | Stub |
| `P-POLISH-011` | Weakness Candidate | 生成薄弱项候选 | Stub |

### 9.4 Pressure Mode Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-PRESSURE-001` | Opening Strategy | 生成压力面开场策略 | Stub |
| `P-PRESSURE-002` | First Question Generation | 生成首题 | Stub |
| `P-PRESSURE-003` | Answer Quality Assessment | 判断回答质量 | Stub |
| `P-PRESSURE-004` | Follow-up Strategy | 选择追问策略 | Stub |
| `P-PRESSURE-005` | Follow-up Question Generation | 生成连续追问 | Stub |
| `P-PRESSURE-006` | Pace Control | 控制节奏与压力强度 | Stub |
| `P-PRESSURE-007` | End Condition Check | 判断是否结束整场 | Stub |
| `P-PRESSURE-008` | Session Score | 生成整场评分 | Stub |
| `P-PRESSURE-009` | Report Input Assembly | 组装报告输入 | Stub |

### 9.5 Report Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-REPORT-001` | Interview Report Generation | 生成面试报告 | Stub |
| `P-REPORT-002` | Section Score Explanation | 生成分项评分解释 | Stub |
| `P-REPORT-003` | Risk and Pass Tendency Wording | 生成风险提示和通过倾向表达 | Stub |
| `P-REPORT-004` | Copyable Content Assembly | 生成可复制内容结构 | Stub |

### 9.6 Review Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-REVIEW-001` | Mock Interview Review | 生成模拟面试复盘 | Stub |
| `P-REVIEW-002` | Real Interview Input Structuring | 结构化真实面试输入 | Stub |
| `P-REVIEW-003` | Real Interview Review | 生成真实面试复盘 | Stub |
| `P-REVIEW-004` | Review Item Extraction | 提炼题级复盘项 | Stub |

### 9.7 Weakness Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-WEAKNESS-001` | Weakness Extraction | 提炼薄弱项候选 | Stub |
| `P-WEAKNESS-002` | Weakness Merge Suggestion | 生成薄弱项合并建议 | Stub |
| `P-WEAKNESS-003` | Weakness Severity Assessment | 判断薄弱项严重度 | Stub |
| `P-WEAKNESS-004` | Weakness Status Update Suggestion | 生成状态更新建议 | Stub |

### 9.8 Asset Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-ASSET-001` | Asset Candidate Extraction | 提炼资产候选 | Stub |
| `P-ASSET-002` | Asset Quality Hint | 生成资产质量提示 | Stub |
| `P-ASSET-003` | Asset Version Suggestion | 生成资产版本更新建议 | Stub |

### 9.9 Training Contracts

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-TRAINING-001` | Training Recommendation | 生成训练建议 | Stub |
| `P-TRAINING-002` | Training Priority Ranking | 训练建议排序 | Stub |
| `P-TRAINING-003` | Training Result Review | 训练结果复盘 | Stub |

## 10. Shared Contract 细则

本节只填充可被后续业务 contract 引用的公共规则，不写完整生产 Prompt 文案，不选择 provider、向量数据库、embedding 模型或互联网检索服务。

### 10.0 Shared Contract 推荐调用顺序

后续业务 AI Task 可按任务需要裁剪步骤，但 Shared Contract 的默认推荐顺序如下，用于避免 Evidence / Validation / Low Confidence 之间的输入依赖循环：

1. `P-SHARED-002` Retrieval Planning。
2. `P-SHARED-005` Evidence Binding 的 Input Evidence Selection 子步骤，输出 `selected_input_evidence_refs`。
3. `P-SHARED-001` Context Assembly。
4. 业务 AI Task / LLM generation。
5. `P-SHARED-005` Evidence Binding 的 Output Evidence Binding 子步骤，输出 `bound_output_evidence_refs`、`missing_evidence` 和 `conflicting_evidence`。
6. `P-SHARED-003` Output Validation。
7. `P-SHARED-004` Low Confidence Classification。
8. `P-SHARED-006` Session Summary Update。
9. Persistence / candidate write / user confirmation flow。

其中 Input Evidence Selection 发生在 Retrieval Planning / Context Assembly 之前或过程中，用于选择允许进入上下文的证据；Output Evidence Binding 发生在模型输出或业务结果生成之后，用于把评分、建议、弱项、资产候选和报告结论绑定到证据。`P-SHARED-003` 只校验上游已经声明或绑定的证据引用，不创建 evidence binding；`P-SHARED-004` 只消费 validation、retrieval、context 和 evidence binding 的 failure signal，不重复执行 validation。

### 10.1 `P-SHARED-001` Context Assembly

- Contract ID: `P-SHARED-001`
- Name: Context Assembly
- Mode: `shared`
- Trigger: 任一 AI 子任务在调用模型、生成结构化结果或进入业务校验前，需要组装当前任务上下文时触发。
- Goal: 形成最小必要、可追踪、已完成 owner / scope 校验的 `context_bundle`，供后续 contract 使用。
- Required Inputs:
  - 当前用户 / owner / role scope。
  - 当前 `contract_id`、业务模式和任务目标。
  - 当前任务必需的业务对象 `VersionRef` / `SnapshotRef`，按业务模式条件包含适用的 `ResumeVersion`、`JobVersion`、会话或题答引用。
  - 当前会话状态、当前题目、当前回答、最近若干轮问答和已问问题列表；初始轮次可只包含当前会话、题目或任务目标。
  - `session_summary` 为条件必需：已有可用摘要时必须传入；初始轮次可使用 `session_summary.status = empty_initial`；无可用摘要时可使用 `session_summary.status = not_available`。
  - `retrieval_plan` 为条件必需：当前 task 需要检索时必须传入；不需要检索时使用 `retrieval_plan.status = retrieval_not_required`。
  - `retrieval_results` 为条件必需：已执行检索时必须传入；无命中时使用 `retrieval_results.status = retrieval_empty`；来源不可用时使用 `retrieval_results.status = source_unavailable` 且只保留 ref / status。
  - 输出 schema 和 validation requirement。
  - 当前上下文预算或大小约束的语义状态。
- Optional Inputs:
  - 资产命中、薄弱项命中、历史报告 / 复盘命中、RAG evidence、用户确认记录和禁止重复追问列表。
  - 长历史压缩摘要、暂停恢复快照摘要、低置信度或失败状态继承信息。
- Retrieval Sources: 不适用为主动检索；本 contract 只消费 `P-SHARED-002` 产出的 `retrieval_plan` 和 `retrieval_results`。
- Context Assembly:
  - 上下文层级按固定系统规则、模式规则、当前任务目标、简历版本摘要、岗位版本摘要、当前题目、当前回答、最近轮次、session summary、已问问题、禁止重复追问、资产命中、薄弱项命中、历史报告 / 复盘命中、RAG evidence、输出 schema、validation rules 组织。
  - 不默认塞入全部简历、全部岗位、全部历史会话或全部资产；只选择当前 contract 必需片段和摘要。
  - 上下文超长时，优先保留当前轮、当前题目、当前回答、显式证据、版本引用、输出 schema 和 validation rules。
  - 长历史优先压缩为 `session_summary`；被裁剪内容必须通过 `omitted_refs`、裁剪原因或 trace 表达。
  - 前端传入内容只能作为用户输入材料，不能作为已验证 prompt 或系统规则。
  - system rules、business refs、RAG evidence、用户回答和外部材料必须分区处理；前端传入内容默认不可信，不得直接作为 system instruction。
- Excluded Inputs:
  - 无 owner / scope 校验的数据、无关用户数据和不需要的完整原文。
  - `source_unavailable`、`source_deleted`、`source_disabled`、已归档且未显式选择的来源正文。
  - 原始密钥、token、cookie、provider payload、日志正文、错误堆栈、原始 embedding 向量。
  - 前端直接传入的未校验 prompt、要求覆盖系统规则的用户内容或 RAG 指令。
- Output Schema:
  - `context_bundle`
  - `context_sections`
  - `section_id`
  - `section_type`
  - `trust_level`
  - `source_type`
  - `owner_scope`
  - `displayability`
  - `included_layers`
  - `included_refs`
  - `omitted_refs`
  - `budget_by_layer`
  - `truncation_reason`
  - `token_or_size_budget_status`
  - `risk_flags`
  - `trace_ref`
  - `section_type` 至少包含 `system_rules`、`mode_rules`、`task_goal`、`business_snapshot`、`user_answer`、`recent_turns`、`session_summary`、`asset_evidence`、`weakness_evidence`、`rag_evidence`、`historical_report_evidence`、`output_schema`、`validation_rules`。
  - `trust_level` 至少包含 `system_trusted`、`owner_verified`、`retrieved_verified`、`user_supplied`、`untrusted_external`、`unavailable_ref_only`。
  - `displayability` 至少包含 `frontend_displayable_summary`、`backend_only`、`ref_only`、`not_displayable`。
- Validation Rules:
  - `included_refs` 必须全部通过 owner / scope、来源状态和版本引用校验。
  - 必需输入、输出 schema 和 validation requirement 缺失时不得进入正常模型调用。
  - `omitted_refs` 必须说明裁剪原因，不得静默丢弃关键证据。
  - `context_bundle` 不得包含禁止输入、provider payload 或无关用户数据。
  - 无 owner 校验的数据不得进入任何 `context_sections`；`source_unavailable` 内容只能保留 ref / status，不得重新读取正文。
- Low Confidence Rules:
  - `context_too_large`、`required_input_missing`、`evidence_missing`、`source_unavailable` 或 `context_truncated_with_risk` 时标记低置信度并输出 failure signal。
  - 裁剪影响当前结论可靠性时，必须输出 `context_truncated_with_risk` 风险并传递给后续 validation。
- Evidence Requirements: 当前上下文中的关键业务来源必须保留 `SourceRef`、`EvidenceRef`、`VersionRef` / `SnapshotRef`；若仅使用摘要，应保留摘要来源引用。
- Trace Requirements: 必须记录 Context Assembly trace，包括 contract、输入来源、裁剪原因、omitted refs、risk flags、预算状态和低置信度状态。
- Persistence Targets: `RAGContextAssembly`、`LlmRequestTrace` 或同等 trace / validation 记录；不直接写入正式业务结果。
- User Confirmation Requirement: 不适用；上下文装配本身不需要用户确认，但其输出不能绕过后续业务 contract 的用户确认要求。
- Retry / Fallback:
  - `owner_mismatch`、`required_input_missing`、validation requirement missing 时停止并返回失败分类。
  - 初始轮次使用 `session_summary.status = empty_initial`，不因缺少历史摘要阻断上下文装配。
  - 无检索任务使用 `retrieval_plan.status = retrieval_not_required`，不生成伪造检索结果。
  - 检索为空使用 `retrieval_results.status = retrieval_empty`，可降级为核心业务输入 + 低置信度。
  - 摘要生成失败时保留原始问答和上一版可用摘要，并输出 `summary_generation_failed` failure signal。
  - `source_unavailable` 或 `evidence_missing` 时可降级为低置信度、部分可用或要求用户补充材料。
  - `context_too_large` 时先裁剪长历史和非关键命中，再生成 `omitted_refs`；仍超限则停止或转人工校对。
- API State Mapping: 只定义状态语义，包括 `context_ready`、`context_partial`、`context_too_large`、`source_unavailable`、`owner_mismatch`、`required_input_missing` 和 `validation_requirement_missing`；不定义 endpoint 或 schema。
- Security Notes: 所有输入进入上下文前必须完成 owner / scope 校验和最小必要裁剪；不得保存或返回原始 Prompt、provider payload、密钥、token、cookie 和无关正文。
- Test Strategy: 使用确定性 fixture 验证上下文层级、裁剪顺序、禁止输入过滤、`owner_mismatch`、`source_unavailable`、omitted refs、trace_ref 和预算状态。
- Open Questions: 具体 token / size 预算数值、最近轮次数量和暂停恢复快照最小字段仍继承 `F4_TECH_DESIGN` UNKNOWN，不在本 contract 关闭。

### 10.2 `P-SHARED-002` Retrieval Planning

- Contract ID: `P-SHARED-002`
- Name: Retrieval Planning
- Mode: `shared`
- Trigger: 任一 AI 子任务在需要判断是否检索、选择检索来源、过滤证据或裁剪命中结果时触发。
- Goal: 生成可执行的 `retrieval_plan`，明确检索来源、过滤条件、排序、裁剪、证据选择和失败表达。
- Sub-stages:
  1. `retrieval_need_decision`：判断当前 task 是否需要检索；不需要时输出 `retrieval_not_required`。
  2. `source_filter_planning`：按 owner / scope、source availability、公共材料发布状态和用户确认状态规划来源过滤。
  3. `query_planning`：生成结构化查询、关键词检索或人工维护材料查询的语义计划。
  4. `result_normalization`：把结构化引用、数据库过滤、关键词检索、RAG 命中或人工维护材料统一成候选 evidence refs。
  5. `candidate_ranking`：按任务相关性、最近性、用户确认状态、来源可信度和可用性排序。
  6. `selected_input_evidence_refs`：将候选证据交给 `P-SHARED-005` Input Evidence Selection 子步骤选择，并记录允许进入 Context Assembly 的 refs。
- Required Inputs:
  - 当前用户 / owner / role scope、当前 `contract_id`、业务模式和任务目标。
  - 当前 `ResumeVersion` / `ResumeModule`、`JobVersion`、会话、题目、回答或报告 / 复盘引用。
  - 当前 source availability、公共材料发布状态、用户确认状态和已知低置信度 / 失败状态。
  - 当前 contract 对 evidence、schema、validation 和上下文预算的要求。
- Optional Inputs:
  - 资产、资产版本、薄弱项、薄弱项证据、历史报告、模拟复盘、真实复盘、知识库文档、公共参考材料和显式用户选择的来源。
  - 后续明确启用时的互联网检索开关、查询边界和来源可信度要求。
- Retrieval Sources:
  - `ResumeVersion` / `ResumeModule`
  - `JobVersion`
  - `Asset` / `AssetVersion`
  - `Weakness` / `WeaknessEvidence`
  - `InterviewReport`
  - `MockInterviewReview`
  - `RealInterviewReview`
  - `KnowledgeBase` / `KnowledgeDocument` / `KnowledgeChunk`
  - 公共参考材料
  - 互联网检索，非 MVP 默认强依赖，仅在后续设计明确启用时使用
- Context Assembly:
  - 检索计划自身只使用来源元数据、摘要、版本引用、状态和任务目标，不读取未校验正文。
  - 简历和岗位版本是核心输入，不等同于 RAG；资产、薄弱项、历史报告、复盘和知识库是条件检索。
  - 结果进入 `P-SHARED-001` 前必须去重、排序、裁剪并生成 evidence refs。
- Excluded Inputs:
  - owner 不一致的私有来源、`source_deleted` / `source_disabled` / `source_unavailable` 正文、未发布公共材料、未启用的互联网结果。
  - 无来源、无版本、无维护者边界或无法形成 evidence ref 的材料。
  - provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - `retrieval_plan`
  - `retrieval_need_decision`
  - `source_filters`
  - `retrieval_queries`
  - `retrieval_results`
  - `candidate_evidence_refs`
  - `selected_input_evidence_refs`
  - `excluded_evidence`
  - `citation_or_evidence_refs`
  - `trace_ref`
  - `risk_flags`
- Validation Rules:
  - 私有来源必须 owner / scope 一致；公共材料必须发布、可用并有维护者边界。
  - 排序至少考虑当前任务相关性、当前题目相关性、当前岗位相关性、当前薄弱项相关性、最近性、用户确认状态、证据完整度、来源可信度和 source availability。
  - 证据过长时必须先生成摘要和裁剪原因，不得把整份原文默认送入上下文。
  - `evidence_conflict` 必须显式进入 `excluded_evidence`、`risk_flags` 或 selected evidence 的冲突标记。
- Low Confidence Rules:
  - 检索为空、检索结果 owner 不一致、`source_disabled` / `source_deleted` / `source_archived`、`evidence_conflict`、evidence too long、`public_material_unpublished` 或 internet retrieval unavailable 时进入低置信度或部分可用。
  - 互联网检索不可用不得阻断 MVP 默认流程，除非后续业务 contract 明确把它设为必需。
- MVP Execution Notes:
  - MVP 不默认要求向量库、embedding 或 vector index。
  - MVP 可优先使用结构化引用、数据库过滤、关键词检索和人工维护的知识材料。
  - RAG / embedding / vector index 是后续实现选择，不在本阶段冻结。
  - 互联网检索不是 MVP 默认依赖，只能在后续产品、安全和来源治理设计明确启用时使用。
- Evidence Requirements: `candidate_evidence_refs` 和 `selected_input_evidence_refs` 必须能生成 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef` 和 `TraceRef`；被排除证据应保留排除原因。
- Trace Requirements: 必须记录查询意图、source filters、排序维度、裁剪原因、selected / excluded evidence、检索为空或冲突状态。
- Persistence Targets: `RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`Citation` / `EvidenceRef`、`RAGContextAssembly` 和检索 trace；不直接写入报告、复盘、资产或薄弱项。
- User Confirmation Requirement: 不适用；检索计划不需要用户确认，但使用未确认资产、候选资产或候选薄弱项时必须保留候选状态并交给业务 contract 决定。
- Retry / Fallback:
  - 检索为空时可降级为仅核心输入、低置信度或要求补充材料。
  - `owner_mismatch`、`source_disabled` / `source_deleted` / `source_unavailable` 时必须排除来源并记录风险。
  - evidence too long 时裁剪为可展示摘要和 refs；冲突证据保留冲突标记，不静默择一。
- API State Mapping: 只定义状态语义，包括 `retrieval_not_required`、`retrieval_ready`、`retrieval_empty`、`retrieval_partial`、`evidence_conflict`、`source_unavailable`、`public_material_unpublished` 和 `internet_retrieval_unavailable`；不定义 endpoint 或 schema。
- Security Notes: 检索必须在服务端按 owner / public scope 过滤；公共材料未发布不得进入业务生成；互联网检索默认关闭，启用前需补来源治理和隐私边界。
- Test Strategy: 使用确定性检索 fixture 覆盖 owner 隔离、公共材料发布状态、`source_deleted` / `source_disabled` / `source_archived`、空结果、冲突证据、过长证据裁剪和互联网检索不可用。
- Open Questions: 具体检索数量、排序权重、公共材料发布流程、互联网检索启用条件和具体索引实现仍为后续设计问题，不在本 contract 关闭。

### 10.3 `P-SHARED-003` Output Validation

- Contract ID: `P-SHARED-003`
- Name: Output Validation
- Mode: `shared`
- Trigger: 任一 AI 输出准备进入业务对象、候选对象、前端展示或持久化前触发。
- Goal: 对候选输出进行结构化校验和业务语义校验，产出可保存、可修复、需重试或需人工校对的状态。
- Required Inputs:
  - 候选结构化输出、当前 contract 的 output schema、validation requirement 和业务模式。
  - 当前 owner / scope、来源状态、`bound_output_evidence_refs`、`missing_evidence`、`conflicting_evidence`、trace refs、低置信度标记和用户确认要求。
  - 评分、建议、资产候选、薄弱项候选、报告或复盘等目标对象的状态语义。
- Optional Inputs:
  - 原始模型输出引用、repair candidate、人工校对备注、上游 retrieval / context assembly 风险和历史 validation result。
- Retrieval Sources: 不适用为主动检索；仅校验候选输出中声明的 evidence refs、`bound_output_evidence_refs` 和 trace refs 是否存在、合法、可追踪。
- Context Assembly:
  - 只读取候选输出、schema、validation requirement、来源引用和必要业务对象摘要。
  - 不重新组装生产 Prompt，不读取无关原文，不扩大上游上下文范围。
  - 不负责创建 evidence binding；证据绑定创建或补全由 `P-SHARED-005` 完成。
- Excluded Inputs:
  - 原始 Prompt、provider payload、未脱敏 completion 原文、无权限来源、`source_unavailable` 正文和前端未校验 prompt。
  - 与当前 validation 无关的完整简历、完整岗位、完整会话历史和无关用户数据。
- Output Schema:
  - `validation_result`
  - `schema_valid`
  - `semantic_valid`
  - `validated_output`
  - `rejected_fields`
  - `repairable_fields`
  - `normalized_failure_signals`
  - `risk_flags`
  - `trace_ref`
- Validation Rules:
  - 结构化校验必须检查必填字段、字段类型、枚举值、0-100 分值范围、evidence refs、trace refs、confidence / low confidence 字段、next action 和 user confirmation requirement。
  - 业务语义校验必须检查不承诺精确通过概率、不把低置信度伪装成正常结论、不把候选资产写成正式资产、不把候选薄弱项写成正式薄弱项、不绕过用户确认。
  - 业务语义校验还必须检查不引用无权限来源、不引用 `source_unavailable` 正文、不把打磨模式当压力面、不把压力面当同题无限打磨、不生成与岗位 / 简历证据明显冲突的结论。
  - 校验失败字段必须进入 `rejected_fields` 或 `repairable_fields`，不得静默进入 `validated_output`。
  - Validation 失败必须归一化为 §7.1 的 failure signal，例如 `schema_invalid`、`semantic_invalid`、`score_out_of_range`、`evidence_missing`、`evidence_conflict`、`validation_partial`、`output_incomplete` 或 `manual_check_required`。
- Low Confidence Rules:
  - `validation_partial`、`output_incomplete`、score explanation weak、`evidence_conflict`、`source_unavailable` 或 `context_truncated_with_risk` 时标记低置信度。
  - 低置信度不能被 `schema_valid=true` 覆盖；结构化通过但语义弱通过时必须保留风险。
- Evidence Requirements: 输出中每个关键结论引用的 evidence refs 必须存在、可访问、来源状态可解释；证据不足时必须显式消费 `missing_evidence`，证据冲突时必须显式消费 `conflicting_evidence`。本 contract 不创建新 evidence binding。
- Trace Requirements: 必须记录 validation trace，包含 schema 校验、语义校验、低置信度、rejected / repairable fields、retry / fallback 建议和上游 trace_ref。
- Persistence Targets: `LlmValidationResult`、validation trace、failure record、候选业务对象或通过校验的业务结果；正式资产、薄弱项或训练建议仍需业务 contract 和用户确认。
- User Confirmation Requirement: 校验不替代用户确认；凡进入正式资产、正式薄弱项、训练建议确认或用户可见关键回流的结果，必须保留确认要求。
- Retry / Fallback:
  - `validation failed` 时不得保存为正常业务事实，可进入 repair、retry、manual review 或 generation failed。
  - `partial usable` 可保存可用片段和风险标记，不能扩大数据范围或隐去失败字段。
  - retry / fallback 不得把原始 Prompt、completion 或 provider payload 写入日志。
- API State Mapping: 只定义状态语义，包括 `validation_passed`、`validation_failed`、`validation_partial`、`repair_required`、`manual_review_required`、`retry_allowed`、`fallback_allowed` 和 `generation_failed`；不定义 endpoint 或 schema。
- Security Notes: 校验层必须阻断无权限来源、`source_unavailable` 正文、未确认候选写正式对象和敏感字段外泄；日志只记录错误分类、trace id 和状态。
- Test Strategy: 使用确定性输出 fixture 覆盖缺字段、类型错误、非法枚举、分数越界、缺 evidence / trace、低置信度伪装、模式边界错误、用户确认绕过和 `source_unavailable`。
- Open Questions: 各业务 contract 的详细 output schema、评分校准阈值和 repair 策略细节仍待后续填充；本 contract 只冻结共享校验边界。

### 10.4 `P-SHARED-004` Low Confidence Classification

- Contract ID: `P-SHARED-004`
- Name: Low Confidence Classification
- Mode: `shared`
- Trigger: 输入不足、检索失败、证据冲突、上下文裁剪、模型输出不完整或 validation 弱通过时触发。
- Goal: 生成一致的低置信度分类、影响范围、用户可见提示和推荐动作，避免把风险结果伪装成正常高置信结论。
- Required Inputs:
  - 当前 contract、业务模式、任务目标、`validation_result`、`missing_evidence`、`conflicting_evidence`、`context_risk_flags`、`retrieval_status` 和 `failure_signals`。
  - required inputs 完整性、answer 完整性、resume / job evidence 完整性、source availability 和 `evidence_conflict` 状态。
  - 模型输出完整性、评分解释质量、真实面试输入完整度和 material context truncation 状态。
- Optional Inputs:
  - 人工校对备注、用户补充材料请求、历史低置信度继承状态和失败恢复记录。
- Retrieval Sources: 不适用为主动检索；只消费上游 retrieval、context assembly、validation 和 evidence binding 的状态。
- Context Assembly:
  - 只需要风险来源、受影响字段、证据摘要和 trace；不读取无关正文。
  - 若风险来源本身被裁剪或不可读，应保留 source availability 状态和 omitted refs。
  - 不重复执行 Output Validation，不重新判断 schema / semantic 是否通过；只消费 validation failure signals 并生成低置信度分类、用户可见提示和 recommended action。
- Excluded Inputs:
  - 无权限来源正文、`source_unavailable` 正文、原始 Prompt、provider payload、密钥、token、cookie 和无关用户数据。
  - 不能用未校验证据补足低置信度解释。
- Output Schema:
  - `low_confidence_flag`
  - `confidence_level`
  - `failure_signals`
  - `reasons`
  - `affected_sections`
  - `user_visible_message`
  - `recommended_action`
  - `trace_ref`
- Validation Rules:
  - 触发条件至少覆盖 `required_input_missing`、insufficient answer、insufficient resume evidence、insufficient job evidence、`retrieval_empty`、`evidence_conflict`、`source_unavailable`、`validation_partial`、`output_incomplete`、score explanation weak、real interview input incomplete 和 `context_truncated_with_risk`。
  - 低置信度类型只能使用 `insufficient_input`、`insufficient_evidence`、`evidence_conflict`、`source_unavailable`、`validation_partial`、`model_output_incomplete`、`context_truncated`、`manual_check_required` 或后续明确扩展值。
  - 用户可见表达必须说明影响范围，不得使用确定性结论包装低置信度结果。
  - `failure_signals` 是分类输入，不是二次 validation 结果；分类不得把 `schema_invalid`、`semantic_invalid` 或 `evidence_missing` 改写成高置信状态。
- Low Confidence Rules:
  - 低置信度分类失败时，默认进入保守风险提示和 `manual_check_required`。
  - 低置信度不得阻断保存原始用户输入。
  - 低置信度结果不得静默进入正式资产或薄弱项；只能进入候选、待确认、部分可用或人工校对路径。
- Evidence Requirements: 每个 reason 应关联 evidence ref、source ref、validation trace 或 omitted ref；证据不足本身也必须有 trace_ref。
- Trace Requirements: 必须记录触发条件、低置信度类型、受影响区块、推荐动作、用户可见提示和上游 trace。
- Persistence Targets: `LowConfidenceFlag`、validation result、业务对象风险标记、failure record、audit event 或候选对象风险字段；不直接创建正式业务结论。
- User Confirmation Requirement: 标记低置信度不需要用户确认；但用户接受、修正、跳过或继续使用低置信度结果时，业务 contract 应记录确认或操作引用。
- Retry / Fallback:
  - 推荐动作可以是重新生成、补充材料、人工校对、跳过或仅保存原始输入。
  - 分类失败时使用保守提示；重试不得扩大输入范围或读取不可用来源正文。
- API State Mapping: 只定义状态语义，包括 `low_confidence`、`partial_usable`、`manual_check_required`、`insufficient_input`、`source_unavailable` 和 `evidence_conflict`；不定义 endpoint 或 schema。
- Security Notes: 用户可见提示只展示必要摘要和风险范围，不暴露原始敏感正文、无权限证据或 provider payload。
- Test Strategy: 使用 fixture 覆盖每类触发条件、低置信度类型映射、用户可见提示、保存原始输入不被阻断、候选对象不静默转正式对象。
- Open Questions: `confidence_level` 的具体分级阈值和各业务页面的用户提示文案由后续业务 contract / UX 收敛，本 contract 不关闭。

### 10.5 `P-SHARED-005` Evidence Binding

- Contract ID: `P-SHARED-005`
- Name: Evidence Binding
- Mode: `shared`
- Trigger: 输入证据准备进入 Context Assembly 前，或评分、建议、薄弱项、资产候选、报告、复盘结论准备进入展示、校验或持久化前触发。
- Goal: 分别完成 Input Evidence Selection 与 Output Evidence Binding，确保进入上下文的证据和生成后结论的证据引用都可追踪、可展示范围明确、状态可解释。
- Required Inputs:
  - Input Evidence Selection：来自简历、岗位、资产、薄弱项、历史报告、复盘、知识库 chunk、公共材料或用户显式选择来源的候选 evidence set。
  - Output Evidence Binding：候选结论、评分、建议、资产候选、薄弱项候选、报告段落或复盘项。
  - 可用 evidence set、source availability、owner / scope、生成时 `VersionRef` / `SnapshotRef` 和上游 trace_ref。
  - 当前业务模式、用户确认状态和输出校验要求。
- Optional Inputs:
  - RAG 检索证据、历史报告 / 复盘摘要、真实面试补充材料、评分解释、用户确认记录和 displayable evidence summary。
- Retrieval Sources:
  - 简历版本 / 模块、岗位版本、当前题目、当前回答、历史问答、点评、评分解释、RAG 检索证据。
  - 资产版本、薄弱项证据、模拟面试报告、模拟面试复盘、真实面试输入和用户确认记录。
- Context Assembly:
  - Input Evidence Selection 发生在 Retrieval Planning / Context Assembly 之前或过程中，只选择允许进入上下文的证据，不生成 `context_bundle`。
  - Output Evidence Binding 发生在模型输出或业务结果生成之后，只消费候选输出和证据集合，为 `P-SHARED-003` 与业务 contract 提供 evidence 绑定结果。
  - 历史结果必须引用生成时版本或快照，不引用当前最新对象替代历史来源。
- Excluded Inputs:
  - owner 不一致、`source_deleted` / `source_disabled` / `source_unavailable` 正文、无 evidence ref 能力的材料。
  - 原始敏感正文默认展示、provider payload、原始 Prompt、密钥、token、cookie 和无关用户数据。
- Output Schema:
  - `evidence_binding_result`
  - `selected_input_evidence_refs`
  - `bound_output_evidence_refs`
  - `missing_evidence`
  - `conflicting_evidence`
  - `displayable_evidence_summary`
  - `failure_signals`
  - `trace_ref`
- Validation Rules:
  - Input Evidence Selection 必须排除 `owner_mismatch`、`source_unavailable`、`source_deleted`、`source_disabled`、`source_archived` 默认不可用正文、`public_material_unpublished` 和不可形成 evidence ref 的材料。
  - Output Evidence Binding 中每个关键结论至少应绑定一个 evidence ref，除非明确标记证据不足或不适用。
  - 评分必须绑定评分依据或评分解释；薄弱项必须绑定来源证据；资产候选必须绑定来源内容。
  - 参考回答和技术解释如使用知识库，应绑定 RAG evidence。
  - 证据冲突、缺失或不可展示必须显式进入输出，不得静默删除。
  - Evidence Binding 失败时必须输出可被 Validation 和 Low Confidence 消费的 failure signals，例如 `evidence_missing`、`evidence_conflict`、`source_unavailable`、`owner_mismatch`、`snapshot_missing` 或 `manual_check_required`。
- Low Confidence Rules:
  - `evidence_missing`、`evidence_conflict`、`source_unavailable`、`snapshot_missing` 或 evidence not displayable 时触发低置信度或 manual check。
  - 证据不足的关键结论不得升级为高置信正式结论。
- Evidence Requirements:
  - `selected_input_evidence_refs` 只表示允许进入 Context Assembly 的证据，不等于生成后结论已经完成 evidence binding。
  - `bound_output_evidence_refs` 表示业务输出或候选输出已经绑定的证据，供 `P-SHARED-003` 校验。
  - evidence summary 可以展示给前端，但原始敏感正文不默认展示。
  - 无权限证据不得进入业务结果。
  - `source_deleted` / `source_disabled` / `source_unavailable` 时，应保留历史引用状态，但不得重新读取不可用正文。
- Trace Requirements: 必须记录候选结论、绑定证据、缺失证据、冲突证据、displayable summary 生成来源和 source availability。
- Persistence Targets: `EvidenceRef`、`Citation`、`ScoreEvidenceLink`、`SourceRef`、`VersionRef` / `SnapshotRef`、`TraceRef`、业务对象 evidence 字段或候选对象 evidence 字段。
- User Confirmation Requirement: 证据绑定本身不需要用户确认；资产候选入库、薄弱项正式化、训练建议采纳或用户修正证据时仍需业务 contract 记录确认。
- Retry / Fallback:
  - `evidence_missing` 时可回退为证据不足、要求补充材料或转人工校对。
  - `evidence_conflict` 时保留冲突双方摘要和 refs，不静默择一。
  - owner mismatch 或 evidence not displayable 时排除证据并记录风险。
- API State Mapping: 只定义状态语义，包括 `evidence_bound`、`missing_evidence`、`evidence_conflict`、`source_unavailable`、`evidence_not_displayable` 和 `snapshot_missing`；不定义 endpoint 或 schema。
- Security Notes: 前端只接收可展示证据摘要和必要引用；日志、trace 和错误不记录原始敏感正文、Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖评分证据、薄弱项证据、资产候选来源、RAG evidence、历史版本引用、`source_unavailable`、`owner_mismatch`、不可展示证据和冲突证据。
- Open Questions: 证据摘要展示粒度、snapshot 缺失时的恢复策略和各业务 contract 的关键结论清单仍由后续设计收敛。

### 10.6 `P-SHARED-006` Session Summary Update

- Contract ID: `P-SHARED-006`
- Name: Session Summary Update
- Mode: `shared`
- Trigger: 每轮用户回答后、每轮点评后、追问生成后、主题切换时、暂停前、恢复后、报告生成前、复盘生成前或会话结束时触发。
- Goal: 更新可回溯到 `covered_turn_refs` 的 `SessionSummary`，减少后续 Context Assembly 对完整历史的依赖，同时不替代原始问答和 evidence refs。
- Required Inputs:
  - 当前用户 / owner / role scope、会话 id、当前模式、会话状态和当前 `ResumeVersion` / `JobVersion`。
  - 当前题目、回答、点评、评分、追问、当前进展树位置、`covered_turn_refs` 和上一版 summary。
  - 已问问题、禁止重复追问列表、已暴露薄弱项、资产候选、低置信度和失败状态。
- Optional Inputs:
  - 已生成参考回答要点、重要失分点、下一步建议、暂停恢复快照、报告 / 复盘生成前输入摘要和用户确认记录。
- Retrieval Sources: 不适用为主动检索；仅消费当前会话内题答、点评、评分、追问、报告前输入和复盘前输入。
- Context Assembly:
  - 摘要内容应覆盖当前模式、当前岗位 / 简历版本、已问问题、用户回答要点、已暴露薄弱项、已确认资产候选、参考回答要点、重要失分点、禁止重复追问列表、当前进展树位置、下一步建议、低置信度和失败状态。
  - 压力面摘要应保留连续追问链路和节奏状态；打磨模式摘要应保留同题多轮改进过程。
  - 摘要服务后续 Context Assembly，但不得替代 evidence refs、`covered_turn_refs` 或原始问答记录。
- MVP Execution Policy:
  - MVP 默认优先使用 deterministic delta summary，而不是每轮强制 LLM summary。
  - 每轮更新只写入轻量结构化摘要字段，例如 asked question refs、answer key points、exposed weakness candidate refs、asset candidate refs、open threads、closed threads、forbidden repeat refs 和 risk flags。
  - LLM compression summary 不是每轮强制步骤；只作为历史过长、报告生成前、复盘生成前、暂停前或会话结束时的可选后处理。
  - 长耗时 summary 可异步或降级；summary 失败不得阻断保存原始问答。
  - summary 失败时必须产生 `summary_generation_failed` failure signal，并保留上一版可用 summary 或 `summary_status = summary_failed`。
- Excluded Inputs:
  - 与当前会话无关的历史会话全文、无 owner 校验数据、`source_unavailable` 正文、provider payload、原始 Prompt、密钥、token、cookie 和无关用户数据。
  - 未通过业务校验的候选资产或候选薄弱项不得写成已确认事实。
- Output Schema:
  - `SessionSummary`
  - `session_summary.status`
  - `summary_version`
  - `covered_turn_refs`
  - `source_session_snapshot_ref`
  - `asked_question_refs`
  - `answer_key_points`
  - `open_threads`
  - `closed_threads`
  - `forbidden_repeat_refs`
  - `weakness_candidate_refs`
  - `asset_candidate_refs`
  - `risk_flags`
  - `low_confidence_flags`
  - `trace_ref`
- Validation Rules:
  - 摘要不能覆盖原始问答记录，不能成为唯一事实源，必须能回溯到 `covered_turn_refs`。
  - `covered_turn_refs` 必须存在且与 summary_version 连续；open / closed threads、forbidden repeat refs 和进展树位置必须一致。
  - 摘要中出现低置信度内容时必须保留风险标记。
  - 候选资产、候选薄弱项和训练建议不得因摘要更新而静默转正式对象。
- Low Confidence Rules:
  - `summary_generation_failed`、covered turn refs missing、context conflict、low confidence inherited、resume failed 或 pause snapshot unavailable 时标记低置信度或失败。
  - 摘要低置信度不得阻断原始用户输入保存，但应影响后续上下文使用和用户提示。
- Evidence Requirements: 摘要条目应引用 `covered_turn_refs`、题目、回答、点评、评分、用户确认或上游 evidence refs；摘要本身不替代 EvidenceRef。
- Trace Requirements: 必须记录 summary_version、`covered_turn_refs`、变更原因、风险继承、暂停 / 恢复状态和上游 trace。
- Persistence Targets: `SessionSummary`、summary version、session trace、risk flags、forbidden repeat refs、weakness candidate refs、asset candidate refs 和必要 audit event；不覆盖原始题答、点评或评分记录。
- User Confirmation Requirement: 常规摘要更新不需要用户确认；若用户编辑、确认或拒绝摘要中的资产候选、薄弱项或下一步建议，应由业务 contract 记录 `UserConfirmationRef`。
- Retry / Fallback:
  - `summary_generation_failed` 时保留上一版 summary 和失败状态，不阻断原始问答保存。
  - covered turn refs missing 或 pause snapshot unavailable 时停止使用该摘要作为高置信上下文，并要求恢复或人工校对。
  - context conflict 时保留冲突标记，不静默覆盖旧摘要。
- API State Mapping: 只定义状态语义，包括 `summary_updated`、`summary_partial`、`summary_failed`、`covered_turn_refs_missing`、`pause_snapshot_unavailable`、`resume_failed` 和 `low_confidence_inherited`；不定义 endpoint 或 schema。
- Security Notes: 摘要仍属于 owner 私有会话数据；前端展示只返回可展示摘要和风险状态，不暴露 Prompt、provider payload、原始敏感正文或无关会话内容。
- Test Strategy: 使用多轮会话 fixture 覆盖回答后、点评后、追问后、主题切换、暂停、恢复、报告前、复盘前和结束时更新；验证 `covered_turn_refs`、禁止重复追问、低置信度继承和候选不转正式对象。
- Open Questions: summary 最小字段、压缩策略、暂停恢复快照字段和同题多轮结束阈值仍继承 `F4_TECH_DESIGN` UNKNOWN，不在本 contract 关闭。

## 11. Job Match Contract 细则

本节填充岗位匹配分析链路的 AI 子任务 contract。四个 contract 只定义输入、检索依赖、上下文装配、输出结构、校验、低置信度、证据、trace、持久化交接和安全边界；不写完整生产 Prompt 文案，不冻结评分公式、权重、阈值、校准方法、模型供应商、模型参数、向量数据库、embedding 模型、API endpoint 或物理数据库 schema。

### 11.0 Job Match Output Schema 公共字段

四个 Job Match contract 的 Output Schema 都必须包含以下公共字段；各 contract 可在此基础上增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `displayable_evidence_summary` | 否 | object[] | 可展示给前端的证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验、低置信度和持久化交接等过程引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议，允许值见本节下方 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能回流正式对象 |

`next_recommended_actions` 只表达建议动作，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值包括 `polish_entry`、`pressure_entry`、`review_later`、`confirm_weakness_candidate`、`edit_weakness_candidate`、`skip_weakness_candidate`、`merge_weakness_candidate`、`regenerate_job_match`、`provide_more_resume_evidence` 和 `provide_more_job_evidence`。其中需要用户确认的动作必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。映射语义：`polish_entry` / `pressure_entry` 只表示后续 Polish / Pressure contract 入口建议；`regenerate_job_match` 映射为重新触发 Job Match contract；`confirm_weakness_candidate`、`edit_weakness_candidate`、`skip_weakness_candidate` 和 `merge_weakness_candidate` 映射为候选薄弱项确认流；补充证据类 action 只要求用户补充材料。

### 11.1 `P-JOBMATCH-001` Match Analysis

- Contract ID: `P-JOBMATCH-001`
- Name: Match Analysis
- Mode: `job_match`
- Trigger:
  - 用户在岗位与简历存在、已通过 owner / scope 校验且可访问时发起岗位匹配分析。
  - 用户主动重新生成岗位匹配分析。
  - 后续模拟面试前需要刷新匹配分析输入时，由应用编排层触发。
- Goal: 基于 `JobResumeBinding`、`JobVersion`、`ResumeVersion` 和必要 `ResumeModule` 生成可解释、可追踪、可进入后续打磨模式、压力面模式、报告、复盘、薄弱项、资产和训练建议的岗位匹配分析结构。
- Required Inputs:
  - `OwnerRef`
  - `JobResumeBinding`
  - `JobVersion`
  - `ResumeVersion`
  - 必要的 `ResumeModule`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - 用户已确认的 `AssetVersion`
  - 已存在的 `Weakness`
  - 历史 `JobMatchAnalysis`
  - 历史 `InterviewReport`
  - 历史 `MockInterviewReview`
  - 历史 `RealInterviewReview`
  - 公共参考材料
  - 知识库 / RAG evidence
- Retrieval Sources:
  - 默认使用 `ResumeVersion` 和 `JobVersion` 作为核心输入，不把它们误写成 RAG。
  - 条件检索用户已确认资产、既有薄弱项、历史报告、模拟复盘和真实复盘。
  - 知识库 / RAG 仅用于证据增强或通用岗位能力解释，不作为默认必需输入。
  - 互联网检索不是 MVP 默认强依赖，不在本 contract 默认启用。
- Context Assembly:
  - 必须消费 `P-SHARED-001` 产出的 `context_bundle`，并继承其 owner 校验、来源可用性、裁剪和 trace 规则。
  - 上下文至少包含岗位摘要、简历摘要、关键简历模块、绑定关系、当前分析目标、必要证据和输出 schema。
  - 不得默认塞入全部历史会话、全部资产、全部复盘或无关知识库材料。
  - 上下文过长时，优先保留岗位要求、简历中与岗位强相关模块、证据引用和输出 schema；被裁剪内容必须进入 omitted refs 或风险标记。
- Excluded Inputs:
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 未经用户确认的资产候选、薄弱项候选或训练建议作为已确认事实。
  - 无关历史会话全文、无关用户数据、原始 Prompt、原始 completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果、无法形成 `EvidenceRef` 的材料和要求覆盖系统规则的用户 / RAG 指令。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - 本 contract 是 orchestration / result aggregate，只汇总子 contract 结果和引用，不直接生成或写入正式 `Weakness`。
  - `analysis_id_candidate`
  - `binding_ref`
  - `analysis_summary`
  - `match_score_ref`
  - `match_points_ref`
  - `mismatch_points_ref`
  - `improvement_points_ref`
  - `weakness_candidate_refs`：只能引用 `P-JOBMATCH-004` 的候选结果；如果 `P-JOBMATCH-004` 未触发，可以为空数组。
  - `aggregate_result_refs`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 检查 `JobVersion`、`ResumeVersion` 和 `JobResumeBinding` 的 owner 一致。
  - 检查输出引用生成时版本或快照，不得隐式绑定到当前最新对象。
  - 检查所有关键结论绑定 `EvidenceRef` 或明确标记证据不足。
  - 检查不能承诺精确通过概率，不能输出确定的真实面试结果预测。
  - 检查不能把匹配分析直接写成最终面试结果预测。
  - 检查不能把候选薄弱项静默写入正式薄弱项。
- Low Confidence Rules:
  - 简历过短。
  - 岗位职责或岗位要求缺失。
  - 绑定关系不可用。
  - 关键简历模块缺失。
  - 证据冲突。
  - 检索结果为空但本 contract 需要增强输入。
  - 上下文被高风险裁剪。
  - 输出无法解释主要分数或主要结论。
  - 低置信度分类必须交给 `P-SHARED-004` 消费 validation、retrieval、context 和 evidence failure signals，不在本 contract 重复定义公共分类枚举。
- Evidence Requirements: 分析摘要、主要匹配 / 不匹配 / 加强结论、匹配分引用和薄弱项候选引用必须绑定 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef`；证据不足时必须输出 `evidence_missing` 或等价低置信度标记。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `JobMatchAnalysis` aggregate / result envelope。
  - `match_score_ref`、`match_points_ref`、`mismatch_points_ref`、`improvement_points_ref` 和 `weakness_candidate_refs` 等子结果引用。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
  - 不直接持久化薄弱项候选详情，不创建正式 `Weakness`；候选详情由 `P-JOBMATCH-004` 负责。
- User Confirmation Requirement:
  - 匹配分析结果可以作为分析结果保存。
  - 薄弱项候选、资产候选或训练建议不得绕过用户确认直接写入正式对象。
  - 如果产品后续定义自动创建候选薄弱项，也必须保留待确认状态和证据引用。
- Retry / Fallback:
  - owner mismatch、绑定关系不可用或必需版本缺失时停止正常生成，返回失败或补充材料路径。
  - 证据不足、检索为空或上下文高风险裁剪时可保存低置信度 / 部分可用结果，或要求用户补充岗位、简历或模块信息。
  - 重试不得扩大输入范围、启用默认互联网检索或记录原始 Prompt / completion。
- API State Mapping: 只定义状态语义，包括 `not_generated`、`generating`、`generated`、`failed`、`low_confidence`、`partial`、`insufficient_input`、`owner_mismatch` 和 `source_unavailable`；不定义 endpoint 或 request / response schema。
- Security Notes: 所有输入必须通过 owner / scope 校验和最小必要裁剪；前端只可见结构化分析、风险状态、可展示证据摘要和必要 trace id，不暴露原始 Prompt、completion、provider payload 或无权限来源正文。
- Test Strategy: 使用确定性 fixture 覆盖正常匹配分析、owner mismatch、岗位缺失、简历过短、绑定关系不可用、证据冲突、检索为空、上下文高风险裁剪、候选薄弱项不转正式对象和不可承诺精确通过概率。
- Open Questions: 评分公式、分项权重、阈值、校准方法、通过倾向展示边界、薄弱项合并规则、上下文预算数值和 API 具体状态字段仍为后续设计问题，不在本 contract 关闭。

### 11.2 `P-JOBMATCH-002` Match Score

- Contract ID: `P-JOBMATCH-002`
- Name: Match Score
- Mode: `job_match`
- Trigger:
  - `P-JOBMATCH-001` 需要生成或刷新匹配分。
  - 用户重新生成匹配分析。
  - 后续报告或训练建议需要读取已有匹配分时，不重新生成，只引用已保存结果。
- Goal: 定义岗位匹配 0-100 分与解释的输出 contract；不冻结评分公式、权重、阈值或校准方法，只冻结评分输出必须具备的结构、解释、证据和风险表达。
- Required Inputs:
  - `JobVersion`
  - `ResumeVersion`
  - `JobResumeBinding`
  - `EvidenceRef`
  - `ScoreRuleVersion` 或评分规则占位引用
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `MatchPoint`
  - `MismatchPoint`
  - `ImprovementPoint`
  - 历史匹配分析
  - 公共评分口径
  - 用户已确认资产
  - 薄弱项证据
- Retrieval Sources:
  - 默认使用 `JobVersion`、`ResumeVersion`、`JobResumeBinding` 和已选择 evidence refs。
  - 条件读取 match / mismatch / improvement points、历史匹配分析、公共评分口径、用户已确认资产和薄弱项证据。
  - 条件读取必须经过 `P-SHARED-002`；如果没有条件检索结果，不阻断基础评分。
  - 基础评分仍可仅基于 `JobVersion`、`ResumeVersion`、`JobResumeBinding` 和已选 evidence 运行，并把检索为空或未使用增强证据传递给低置信度分类。
  - 知识库 / RAG 只作为证据增强或公共评分口径来源，不替代核心岗位与简历输入。
  - 互联网检索不作为默认评分输入。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的上下文分区、裁剪和 trace 规则。
  - 上下文至少包含岗位要求摘要、简历证据摘要、绑定关系、评分目标、评分规则版本或 UNKNOWN 占位、正负证据和输出 schema。
  - 上下文过长时，优先保留评分所需证据、岗位关键要求、简历对应片段、评分规则引用和 validation 要求。
- Excluded Inputs:
  - 具体未冻结评分公式、权重、阈值或校准方法的虚构内容。
  - 与评分无关的完整历史会话、全部资产、全部复盘、原始 Prompt、completion、provider payload、密钥、token 和日志正文。
  - source unavailable 正文、无 evidence ref 的材料和无 owner 校验数据。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - `score_result_ref`
  - `match_score_view_ref`
  - `score_value`
  - `score_scale`
  - `score_type`
  - `score_explanation`
  - `positive_evidence_refs`
  - `negative_evidence_refs`
  - `uncertainty_reasons`
  - `score_rule_version_ref`
- Validation Rules:
  - `score_value` 必须在 0-100 范围内。
  - `score_scale` 必须表明是产品展示刻度。
  - 不得输出精确通过概率。
  - 不得输出“必过”“必挂”等确定预测。
  - 分数解释必须引用 evidence refs。
  - 低分和高分都必须有解释。
  - 缺少足够证据时必须触发 low confidence。
  - 如果评分规则版本尚未冻结，应显式保留 UNKNOWN，不得虚构公式。
- Low Confidence Rules:
  - 评分证据不足。
  - 分数与解释不一致。
  - 岗位要求缺失。
  - 简历证据缺失。
  - 评分规则版本缺失或未冻结。
  - 上下文裁剪影响评分依据。
  - 模型输出只有分数没有解释。
  - 解释无法绑定证据。
- Evidence Requirements: `score_explanation`、正向证据、负向证据和不确定性原因必须绑定 `EvidenceRef` 或明确标记证据不足；评分规则版本或 UNKNOWN 占位必须可追踪到 `ScoreRuleVersion` / `TraceRef`。
- Trace Requirements: 必须记录评分生成、评分规则引用、证据绑定、validation、low confidence 和重试 / 降级路径的 `TraceRef`。
- `canonical` score 关系:
  - `ScoreResult` 是统一评分承载对象，保存 score value、score type、explanation、rule version、evidence refs、validation result 和 trace refs。
  - `MatchScore` 是岗位匹配场景下的视图、引用或领域包装，用于从 `JobMatchAnalysis` 指向对应 `ScoreResult`。
  - 不允许 `ScoreResult` 与 `MatchScore` 分别保存两份不一致的分数、解释或证据。
  - 历史回看、校准和报告复用应引用 canonical score。
  - 如果后续 `DATA_MODEL.md` 需要同步命名，应另开数据模型修正任务；本任务不修改 `DATA_MODEL.md`。
- Persistence Targets:
  - `ScoreResult` canonical score。
  - `MatchScore` view / reference wrapper。
  - `ScoreExplanation`
  - `ScoreEvidenceLink`
  - `LowConfidenceFlag`
  - `LlmValidationResult`
  - `TraceRef`
- User Confirmation Requirement: 匹配分作为分析结果保存不要求用户逐项确认；若后续根据分数生成正式薄弱项、资产或训练建议，仍必须经过对应 contract 或用户确认。
- Retry / Fallback:
  - 分数越界、缺少解释或缺 evidence refs 时进入 repair / retry / validation failed。
  - 证据不足或评分规则版本 UNKNOWN 时可保存低置信度分数或仅保存分析摘要，不得伪造公式。
  - 后续消费已有匹配分时只引用保存结果，不因报告或训练建议读取而自动重算。
- API State Mapping: 只定义状态语义，包括 `score_available`、`score_low_confidence`、`score_partial`、`score_validation_failed`、`score_rule_unknown`、`score_out_of_range` 和 `evidence_missing`；不定义 endpoint 或 schema。
- Security Notes: 评分上下文只能包含当前 owner 的必要岗位、简历、证据和已授权公共材料；日志不得记录原始 Prompt、completion、provider payload 或隐私正文。
- Test Strategy: 使用确定性输出 fixture 覆盖 0、100、中间分、分数越界、只有分数无解释、解释无证据、评分规则 UNKNOWN、证据不足、高分 / 低分均有解释和不得输出精确通过概率。
- Open Questions:
  - 评分公式。
  - 分项权重。
  - 阈值。
  - 校准方法。
  - 评分等级映射。
  - 通过倾向展示边界。

### 11.3 `P-JOBMATCH-003` Match / Mismatch / Improvement Points

- Contract ID: `P-JOBMATCH-003`
- Name: Match / Mismatch / Improvement Points
- Mode: `job_match`
- Trigger:
  - `P-JOBMATCH-001` 生成岗位匹配分析时触发。
  - `P-JOBMATCH-002` 评分后需要解释分数构成时触发。
  - 用户重新生成匹配分析时触发。
- Goal: 生成匹配点、不匹配点和加强点，作为匹配分析、后续模拟面试输入、复盘、薄弱项候选和训练建议的结构化上游。
- Required Inputs:
  - `JobVersion`
  - `ResumeVersion`
  - `ResumeModule`
  - `JobResumeBinding`
  - `EvidenceRef`
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - 历史匹配分析。
  - 已确认资产。
  - 已有薄弱项。
  - 历史报告或复盘摘要。
  - 公共参考材料或知识库 evidence。
- Retrieval Sources:
  - 默认使用 `JobVersion`、`ResumeVersion`、`ResumeModule`、`JobResumeBinding` 和 selected evidence refs。
  - 条件检索历史匹配分析、已确认资产、已有薄弱项、历史报告、复盘摘要、公共参考材料或知识库 evidence。
  - 简历和岗位版本是核心输入，不作为 RAG；RAG 仅作为证据增强。
  - 互联网检索不默认启用。
- Context Assembly:
  - 必须继承 `P-SHARED-001`，并使用 `P-SHARED-002` 的检索计划和 `P-SHARED-005` 的 input evidence selection 结果。
  - 上下文至少包含岗位要求、相关简历模块、证据摘要、当前分类目标和输出 schema。
  - 不得默认塞入全部简历、全部岗位、全部资产或全部历史复盘。
  - 上下文过长时，优先保留岗位要求、相关简历模块、可绑定证据、分类规则和输出 schema。
- Excluded Inputs:
  - 无 evidence ref 的泛化判断、owner 不一致来源、source unavailable 正文、未确认候选对象作为事实。
  - 完整无关历史、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - `match_points`
  - `mismatch_points`
  - `improvement_points`
  - `point_ordering`
  - `max_points_hint`
  - 每个 point 的 `point_id_candidate`
  - 每个 point 的 `point_type`
  - 每个 point 的 `title`
  - 每个 point 的 `description`
  - 每个 point 的 `impact`
  - 每个 point 的 `priority`
  - 每个 point 的 `confidence`
  - 每个 point 的 `related_resume_modules`
  - 每个 point 的 `related_job_requirements`
  - 每个 point 的 `evidence_refs`
  - 每个 point 的 `source_refs`
  - 每个 point 的 `suggested_next_action`
  - `point_type` 只能是 `match` / `mismatch` / `improvement`。
  - `impact` 和 `priority` 建议使用 `high` / `medium` / `low` 或等价枚举。
  - `max_points_hint` 是 MVP 展示和成本控制提示，不冻结最终算法；默认建议每类 point 不超过 3-5 条，除非后续产品设计另行明确。
- Point 分类规则:
  - `MatchPoint` 表示简历证据与岗位要求有正向对应。
  - `MismatchPoint` 表示岗位要求中缺少简历证据、证据弱或表达不充分。
  - `ImprovementPoint` 表示可以通过打磨、资产补充、训练或复盘改进的准备方向。
  - 不得把同一证据同时无解释地归入匹配点和不匹配点。
  - 无证据内容不得伪装成匹配点。
- Validation Rules:
  - 每个 point 必须绑定 evidence refs，除非显式标记证据不足。
  - 每个 point 必须关联岗位要求或简历模块。
  - `MismatchPoint` 不得直接等同于失败结论。
  - `ImprovementPoint` 不得直接写入正式训练建议，后续仍需训练建议 contract 或用户确认。
  - 点位数量不得无边界扩张；`max_points_hint` 默认用于 MVP 展示和成本控制，不能被解释为最终评分算法或硬性产品上限。
  - 输出不得绕过 `P-SHARED-005` Evidence Binding。
- Low Confidence Rules:
  - point 缺少证据。
  - 简历模块识别不完整。
  - 岗位要求过短或模糊。
  - 同一证据存在冲突解释。
  - 生成结果无法区分 match / mismatch / improvement。
  - 输出过泛、无法绑定具体岗位或简历片段。
- Evidence Requirements: 每个 point 必须绑定 `EvidenceRef`、相关 `ResumeModule` 或岗位要求引用；证据不足时必须显式输出 `evidence_missing`、`low_confidence_flags` 和受影响 point。
- Trace Requirements: 必须记录分类输入、证据绑定、冲突证据、上下文裁剪、validation 和 low confidence 的 `TraceRef`。
- Persistence Targets:
  - `MatchPoint`
  - `MismatchPoint`
  - `ImprovementPoint`
  - `EvidenceSummary`
  - `ScoreEvidenceLink`
  - `LowConfidenceFlag`
  - `TraceRef`
- User Confirmation Requirement: 保存 points 作为匹配分析结果不要求用户逐项确认；由 points 派生正式薄弱项、资产或训练建议时必须进入对应候选 / 确认链路。
- Retry / Fallback:
  - 无法区分分类、字段缺失或 evidence binding 失败时进入 repair / retry / validation failed。
  - 证据不足时可保留候选 point 和低置信度，不得伪装成高置信匹配点。
  - 上下文过长时先裁剪无关历史和低相关证据，再保留 omitted refs。
- API State Mapping: 只定义状态语义，包括 `points_available`、`points_partial`、`points_low_confidence`、`points_validation_failed`、`evidence_missing` 和 `classification_ambiguous`；不定义 endpoint 或 schema。
- Security Notes: 输出只展示可展示证据摘要和必要引用；不得暴露无权限来源、source unavailable 正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖三类 point、同一证据冲突分类、无证据匹配点、岗位要求模糊、简历模块缺失、数量无边界扩张、improvement 不转正式训练建议和 mismatch 不等同失败结论。
- Open Questions: 最终点位排序策略、产品化硬上限、训练建议映射和点位合并规则仍待后续业务 contract / API / UX 收敛，不在本 contract 关闭。

### 11.4 `P-JOBMATCH-004` Weakness Candidate from Job Match

- Contract ID: `P-JOBMATCH-004`
- Name: Weakness Candidate from Job Match
- Mode: `job_match`
- Trigger:
  - `P-JOBMATCH-001` 完成后触发。
  - `P-JOBMATCH-003` 生成 mismatch / improvement points 后触发。
  - 用户选择从岗位匹配分析生成薄弱项候选时触发。
- Goal: 从岗位匹配分析、mismatch / improvement points、低分解释或证据不足中提炼薄弱项候选；本 contract 只生成候选，不直接写入正式 `Weakness`，后续进入正式薄弱项生命周期必须经过用户确认流。
- Required Inputs:
  - `JobMatchAnalysis`
  - `MismatchPoint`
  - `ImprovementPoint`
  - `MatchScore` / `score_result_ref` 条件输入；不可用时允许 `score_dependency_status = score_unavailable`
  - `EvidenceRef`
  - `JobVersion`
  - `ResumeVersion`
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果，或 `retrieval_plan.status = retrieval_not_required`
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - 既有 `Weakness`
  - 历史薄弱项状态
  - 历史训练建议
  - 历史报告和复盘
  - 用户已确认资产
  - session summary
- Retrieval Sources:
  - 默认使用当前 `JobMatchAnalysis`、`MismatchPoint`、`ImprovementPoint`、可用的 `MatchScore` / `score_result_ref` 和 evidence refs。
  - 如果只消费 `P-JOBMATCH-001` / `P-JOBMATCH-003` 上游结果且不读取既有 `Weakness`、历史训练建议、历史报告、复盘或 session summary，可使用 `retrieval_not_required`。
  - 如果读取既有 `Weakness`、历史训练建议、历史报告、复盘或 session summary，必须经过 `P-SHARED-002`，并保留 owner / source / evidence 过滤边界与 trace。
  - 条件检索既有 `Weakness`、历史薄弱项状态、历史训练建议、历史报告 / 复盘、用户已确认资产和 session summary。
  - 条件检索必须沿用 `P-SHARED-002` 的来源过滤、排序、裁剪和 source availability 规则。
  - 知识库 / RAG 只作为证据解释补充，不替代岗位匹配分析来源。
  - 互联网检索不默认启用。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、分区、裁剪、omitted refs 和 trace 规则。
  - 使用当前匹配分析结果、mismatch / improvement points、低分解释、证据不足原因，以及经 `P-SHARED-002` 选入的既有薄弱项摘要。
  - 使用 `retrieval_not_required` 时不得读取既有 `Weakness`、历史训练建议、历史报告、复盘或 session summary 的正文或摘要。
  - 不读取无关历史会话全文，不把全部训练建议或全部资产塞入上下文。
  - 上下文过长时，优先保留来源 points、分数解释、证据 refs、既有薄弱项候选合并线索和输出 schema。
- Excluded Inputs:
  - 无来源证据的能力缺陷判断。
  - 未通过 owner 校验的历史弱项、训练建议、报告、复盘或资产。
  - source unavailable 正文、未确认候选对象作为正式事实、原始 Prompt、completion、provider payload、密钥、token、cookie 和日志正文。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - `weakness_candidates`
  - `merge_suggestions`
  - `score_dependency_status`
  - 每个候选的 `candidate_id`
  - 每个候选的 `candidate_status`
  - 每个候选的 `title`
  - 每个候选的 `description`
  - 每个候选的 `source_type`
  - 每个候选的 `source_refs`
  - 每个候选的 `evidence_refs`
  - 每个候选的 `severity_hint`
  - 每个候选的 `suggested_training_direction`
  - 每个候选的 `related_job_requirements`
  - 每个候选的 `related_resume_modules`
  - 每个候选的 `merge_candidate_refs`
  - 每个候选的 `user_confirmation_required`
  - `candidate_status` 建议使用 `weakness_detected` 或等价候选态，不得静默写入正式 `Weakness`。
  - `score_dependency_status` 至少区分 `score_available` / `score_unavailable`；当 score unavailable 时必须触发 low confidence flag。
- Candidate 规则:
  - 薄弱项候选必须来源于 mismatch point、improvement point、低分解释或证据不足。
  - 薄弱项候选必须绑定来源证据。
  - 输出是候选态，不是正式 `Weakness`；用户确认后才可进入正式薄弱项生命周期。
  - 薄弱项候选不得静默覆盖既有薄弱项。
  - 如可能与既有薄弱项重复，应输出 merge suggestion，而不是直接合并或覆盖。
  - 用户可确认、编辑、跳过或合并；确认动作必须形成 `UserConfirmationRef` 或等价记录。
  - `MatchScore` / `score_result_ref` 不可用时，允许以 `score_unavailable` 和低置信度方式基于 mismatch / improvement points 生成候选。
  - `severity_hint` 只是提示，不冻结薄弱项严重度算法。
  - `suggested_training_direction` 只是训练方向，不等同于正式训练任务。
- Validation Rules:
  - 缺少来源证据时不得生成正式候选，只能标记证据不足。
  - 候选必须关联岗位要求或简历模块。
  - 候选必须保留来源类型和来源引用。
  - 不得把岗位不匹配直接包装为用户能力缺陷。
  - 不得生成无法训练、无法行动或过泛的薄弱项。
  - 不得绕过用户确认写入正式 `Weakness`。
- Low Confidence Rules:
  - mismatch / improvement points 本身低置信度。
  - 来源证据不足。
  - 既有薄弱项冲突。
  - `score_unavailable` 但仍基于 mismatch / improvement points 生成候选。
  - 薄弱项粒度过粗或过细。
  - 训练方向无法从证据推出。
  - 用户简历信息不足以判断真实能力。
- Evidence Requirements: 每个候选必须绑定来源 point、低分解释或证据不足记录的 `EvidenceRef`；无法绑定时不得生成高置信候选，更不得写入正式 `Weakness`，只能输出证据不足和 `manual_check_required`。
- Trace Requirements: 必须记录来源匹配分析、来源 point、分数解释、证据绑定、重复候选判断、validation、low confidence、用户确认状态和回流失败的 `TraceRef`。
- Persistence Targets:
  - `Weakness` candidate result，状态为 `weakness_detected` 或等价候选态。
  - `WeaknessEvidence` candidate evidence。
  - `merge_suggestions`，只表达合并建议，不自动覆盖既有 `Weakness`。
  - `UserConfirmationRef` 或等价确认记录。
  - `FeedbackLoop` candidate / confirmation flow。
  - `LowConfidenceFlag`
  - `LlmValidationResult`
  - `TraceRef`
  - `AuditEvent`
  - 正式 `Weakness` 只能在用户确认后由后续确认流写入；候选结果、正式对象、用户确认记录、trace、validation result 和 audit event 不得混写。
- User Confirmation Requirement:
  - 默认需要用户确认后才能成为正式薄弱项。
  - 用户可以确认、编辑、跳过或合并。
  - 用户确认动作必须进入 `UserConfirmationRef` 或等价记录。
  - 回流失败不得影响原始岗位匹配分析结果。
- Retry / Fallback:
  - 来源证据不足、重复关系冲突或粒度不可用时输出低置信度候选、merge suggestion 或 manual check。
  - validation failed 时不得写入正式 `Weakness`，只能保留候选、失败记录或用户校对路径。
  - 回流失败只影响候选确认流程，不得覆盖原始 `JobMatchAnalysis`、points 或 score。
- API State Mapping: 只定义状态语义，包括 `candidate_generated`、`candidate_low_confidence`、`candidate_partial`、`candidate_validation_failed`、`confirmation_required`、`merge_suggested`、`feedback_loop_failed` 和 `formal_weakness_not_written`；不定义 endpoint 或 schema。
- Security Notes: 候选生成只使用当前 owner 的匹配分析、points、分数解释和授权历史摘要；不得把无权限历史弱项或 source unavailable 正文纳入 Prompt；日志不记录原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖从 mismatch、improvement、低分解释和证据不足生成候选、候选缺证据、既有薄弱项冲突、merge suggestion、不把岗位不匹配包装成能力缺陷、粒度过粗 / 过细、用户确认 required 和回流失败不影响原始分析。
- Open Questions: 薄弱项严重度算法、合并规则、自动消减规则、训练任务生成规则、正式 `Weakness` 状态流和用户确认 API 字段仍待后续 Weakness / Training / API contract 收敛，不在本 contract 关闭。

### 11.5 Job Match Contract 关系

- `P-JOBMATCH-001` 是岗位匹配分析总控 contract。
- `P-JOBMATCH-002` 负责 0-100 匹配分和解释。
- `P-JOBMATCH-003` 负责匹配点、不匹配点和加强点。
- `P-JOBMATCH-004` 负责从分析结果中生成薄弱项候选。
- 4 个 contract 都必须引用 Shared Contracts，且默认按 `P-SHARED-002`、`P-SHARED-005` Input Evidence Selection、`P-SHARED-001`、业务生成、`P-SHARED-005` Output Evidence Binding、`P-SHARED-003`、`P-SHARED-004` 和持久化 / 用户确认链路交接。
- 4 个 contract 的结果都不得承诺精确通过概率或确定预测真实面试结果。
- `P-JOBMATCH-004` 的输出不得绕过用户确认写入正式薄弱项。

## 12. Polish Contract 细则

本节填充打磨模式主链路前半段的 AI 子任务 contract。Polish 第一组只定义主题规划、题目生成或选择、回答诊断和每轮 0-100 得分的输入输出、检索依赖、上下文装配、校验、低置信度、证据、trace、持久化交接和安全边界；不写完整生产 Prompt 文案，不冻结题目推荐算法、评分公式、权重、阈值、校准方法、模型供应商、模型参数、RAG 实现、API endpoint 或物理数据库 schema。

### 12.0 Polish 第一组公共字段与边界

#### 模式边界

- Polish 是打磨模式，不是压力面模式；允许用户围绕同一题多轮改进。
- Polish 第一组可以给出诊断、评分、改进方向和后续建议，但不生成最终面试报告。
- Polish 第一组不生成正式薄弱项、正式资产或正式训练计划。
- Polish 第一组不负责连续压力追问、整场压力评分或压力面节奏控制。
- 同题打磨结束建议阈值仍为 UNKNOWN，本阶段不得关闭。
- 四个 contract 都必须引用 Shared Contracts，默认按 `P-SHARED-002`、`P-SHARED-005` Input Evidence Selection、`P-SHARED-001`、业务生成、`P-SHARED-005` Output Evidence Binding、`P-SHARED-003`、`P-SHARED-004`、`P-SHARED-006` 和持久化 / 用户确认链路交接。

#### 上游输入边界

Polish 第一组可以条件消费 `JobMatchAnalysis`、`ScoreResult` canonical score、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`Weakness` candidate refs、`JobVersion`、`ResumeVersion`、`ResumeModule`、`AssetVersion`、`Weakness`、`SessionSummary`、最近若干轮 Polish turns、当前题目、当前用户回答、RAG evidence 和公共参考材料。

这些输入不得默认全部进入上下文：不得默认塞入全部简历、全部岗位、全部历史会话、全部资产或全部知识库材料。`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG；Job Match 结果是结构化上游，不是 RAG。

#### 检索边界

- 默认基础流程只要求岗位、简历、当前打磨会话和必要 session summary。
- 资产库、薄弱项、历史 Polish turns、Job Match 结果、历史报告 / 复盘摘要和知识库都是条件检索来源。
- RAG / 知识库可用于考点、技术原理或参考依据增强，但不是 Polish 第一组 MVP 的硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002`，并沿用 owner / source availability / evidence / trace 过滤规则。
- 无 RAG、无资产、无历史报告、无历史复盘时不得阻断基础 Polish 流程；需要时应输出低置信度或资料不足状态。

#### Polish 第一组 Output Schema 公共字段

四个 Polish 第一组 contract 的 Output Schema 都必须包含以下公共字段；各 contract 可增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `polish_session_ref` | 是 | ref | 打磨会话引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `job_match_refs` | 否 | ref[] | 被消费的岗位匹配结果引用 |
| `turn_refs` | 否 | ref[] | 被消费的打磨轮次引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的 `EvidenceRef` |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 `TraceRef` |
| `session_summary_update_ref` | 否 | ref | `P-SHARED-006` 产出的摘要更新引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议，允许值见本节下方 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能回流正式对象 |

`next_recommended_actions` 只表达建议动作，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值至少包括 `answer_again`、`generate_reference_answer`、`explain_knowledge_point`、`expand_technical_principle`、`continue_same_question`、`switch_topic`、`generate_next_question`、`mark_weakness_candidate`、`mark_asset_candidate`、`enter_pressure_mode`、`generate_review_later`、`provide_more_answer_detail`、`provide_more_resume_evidence` 和 `skip_current_question`。其中需要用户确认的动作必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

#### 输出和持久化边界

Polish 第一组输出可以保存为题目规划候选、打磨题目、回答诊断、每轮得分、validation result、low confidence flag、evidence refs、trace refs 和 session summary update 输入。

Polish 第一组不得直接写入正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation`、最终面试报告或压力面整场评分。如需要产生弱项、资产、失分点、参考答案、知识点解析、技术原理扩展或训练方向，只能输出候选引用、后续 contract 入口建议或用户确认入口。

### 12.1 `P-POLISH-001` Topic Planning

- Contract ID: `P-POLISH-001`
- Name: Topic Planning
- Mode: `polish`
- Trigger:
  - 用户进入打磨模式。
  - 用户选择岗位、简历或 Job Match 结果后开始打磨。
  - 用户完成一轮打磨后请求下一主题。
  - `SessionSummary` 显示当前主题已完成、需要切换或存在未完成主题。
  - 用户手动选择关注方向。
- Goal: 规划当前或下一组打磨主题，决定本轮应围绕哪些岗位要求、简历模块、匹配缺口、薄弱项候选或用户目标展开；不生成正式训练计划，不关闭同题打磨结束建议阈值 UNKNOWN。
- Required Inputs:
  - `OwnerRef`
  - `polish_session_ref`
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `JobMatchAnalysis`
  - `ScoreResult` canonical score
  - `MatchPoint`
  - `MismatchPoint`
  - `ImprovementPoint`
  - 已确认 `AssetVersion`
  - 既有 `Weakness`
  - `Weakness` candidate refs
  - 最近若干轮 Polish turns
  - 历史报告 / 复盘摘要
  - 公共参考材料
  - 知识库 / RAG evidence
- Retrieval Sources:
  - 默认使用 `JobVersion`、`ResumeVersion` 和当前 `SessionSummary`。
  - 条件检索 Job Match 结果、资产、薄弱项、历史打磨轮次、报告、复盘和知识库。
  - Job Match 结果是结构化上游，不是 RAG；`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
  - 知识库 / RAG 只作为考点或背景依据增强，不作为基础主题规划的硬依赖。
  - 互联网检索不默认启用。
  - 无 Job Match 结果时可以基于岗位与简历直接规划主题，但必须标记输入较弱、`job_match_refs` 为空或触发低置信度。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的 owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含岗位摘要、简历摘要、当前打磨目标、session summary、已问主题、禁止重复主题、Job Match 相关 refs 和输出 schema。
  - 不得默认塞入全部历史会话、全部资产、全部复盘或全部知识库材料。
  - 上下文过长时优先保留当前目标、未完成主题、mismatch / improvement points、用户显式选择方向、禁止重复列表和输出 schema。
- Excluded Inputs:
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 未经用户确认的资产候选、薄弱项候选或训练建议作为已确认事实。
  - 全量无关历史会话、全量资产库、无关知识库材料、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果和无法形成 `EvidenceRef` 的材料。
- Output Schema:
  - 公共字段：必须完整包含 §12.0 的 Polish 第一组公共字段。
  - `topic_plan_id_candidate`
  - `topic_candidates`
  - 每个 topic 的 `topic_id_candidate`
  - 每个 topic 的 `title`
  - 每个 topic 的 `focus_area`
  - 每个 topic 的 `source_type`
  - 每个 topic 的 `source_refs`
  - 每个 topic 的 `evidence_refs`
  - 每个 topic 的 `priority`
  - 每个 topic 的 `difficulty_hint`
  - 每个 topic 的 `reason`
  - 每个 topic 的 `related_job_requirements`
  - 每个 topic 的 `related_resume_modules`
  - 每个 topic 的 `related_match_or_mismatch_refs`
  - `selected_topic_ref`
  - `forbidden_repeat_topics`
  - `topic_ordering`
  - `max_topics_hint`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个 topic 必须绑定岗位要求、简历模块或 Job Match evidence。
  - 主题不得完全脱离岗位与简历。
  - 主题不得重复最近已完成主题，除非明确是同题继续打磨或用户手动选择重复。
  - `difficulty_hint` 只能是建议，不冻结题目难度算法。
  - `max_topics_hint` 是展示和成本控制提示，不冻结最终算法。
  - 不得把 topic candidate 直接写成正式训练计划、正式薄弱项或正式资产。
- Low Confidence Rules:
  - 无 Job Match 结果。
  - 岗位要求过短或模糊。
  - 简历模块不足。
  - session summary 缺失。
  - evidence 不足。
  - 已问主题无法确认。
  - 用户目标过泛。
  - 上下文高风险裁剪。
  - 低置信度分类必须交给 `P-SHARED-004` 消费 validation、retrieval、context 和 evidence failure signals，不在本 contract 重复定义公共分类枚举。
- Evidence Requirements: 每个 topic 的来源、优先级原因、岗位要求、简历模块和 Job Match 引用必须绑定 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef`；证据不足时必须输出 `evidence_missing` 或等价低置信度标记。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、主题生成或选择、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PolishSession` topic plan candidate 或等价会话内结果。
  - `PolishTopic` candidate 或等价逻辑对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 用户可以接受、切换、跳过或手动选择 topic。
  - topic plan 不直接创建正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
  - 如果后续根据 topic 派生弱项或资产，必须进入对应候选 / 确认链路。
- Retry / Fallback:
  - 必需版本缺失、owner mismatch 或 session 不可访问时停止正常生成，返回失败或补充材料路径。
  - Job Match 不存在、历史主题不可确认或 RAG 为空时可保存低置信度主题候选，不阻断基础打磨。
  - 重试不得扩大输入范围、默认启用互联网检索或记录原始 Prompt / completion。
- API State Mapping: 只定义状态语义，包括 `topic_plan_available`、`topic_plan_partial`、`topic_plan_low_confidence`、`topic_plan_validation_failed`、`insufficient_input`、`anti_repeat_unknown` 和 `source_unavailable`；不定义 endpoint 或 request / response schema。
- Security Notes: 所有输入必须通过 owner / scope 校验和最小必要裁剪；前端只可见结构化主题候选、状态、可展示证据摘要和必要 trace id，不暴露原始 Prompt、completion、provider payload 或无权限来源正文。
- Test Strategy: 使用确定性 fixture 覆盖有 Job Match、无 Job Match、岗位模糊、简历模块不足、session summary 缺失、重复主题、用户手动选择方向、RAG 为空、上下文高风险裁剪和不得写入正式训练计划。
- Open Questions: 主题排序算法、主题数量上限、同题打磨结束建议阈值、进展树推荐算法和 topic 与后续训练计划的映射仍待后续 contract / API / UX 收敛，不在本 contract 关闭。

### 12.2 `P-POLISH-002` Question Generation

- Contract ID: `P-POLISH-002`
- Name: Question Generation
- Mode: `polish`
- Trigger:
  - `P-POLISH-001` 选定 topic 后。
  - 用户请求生成题目。
  - 用户跳过当前题目并请求新题。
  - 用户要求继续同一主题但换题。
  - `SessionSummary` 显示需要补充某类题目。
- Goal: 基于选定主题、岗位、简历、Job Match 结果、session summary 和必要证据生成或选择打磨题目；不生成完整参考答案，不冻结题目推荐算法。
- Required Inputs:
  - `OwnerRef`
  - `polish_session_ref`
  - `selected_topic_ref` 或等价 topic context
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `JobMatchAnalysis`
  - `MismatchPoint`
  - `ImprovementPoint`
  - `MatchPoint`
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 最近若干轮 Polish turns
  - 已问问题列表
  - 禁止重复问题列表
  - 公共参考材料
  - 知识库 / RAG evidence
- Retrieval Sources:
  - 默认使用 selected topic、`JobVersion`、`ResumeVersion` 和 `SessionSummary`。
  - 条件检索 Job Match points、资产、薄弱项、历史题目和知识库。
  - 知识库 / RAG 可用于考点覆盖或题目素材增强，不是必需输入。
  - 互联网检索不默认启用。
  - 无 RAG 时仍必须可以生成基础题目；如技术原理题缺少知识证据，应传递低置信度或资料不足状态。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 selected topic、岗位要求、简历相关模块、已问问题、禁止重复列表、当前打磨目标和输出 schema。
  - 不得默认塞入全部知识库材料、全部历史会话、全部资产或全部弱项。
  - 上下文过长时优先保留 selected topic、禁止重复问题、相关岗位要求、简历模块、evidence refs 和输出 schema。
- Excluded Inputs:
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 完整参考答案、未校验知识库原文、无 evidence ref 的题目素材。
  - 无关历史问答全文、全量资产库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果、违法或隐私侵入材料。
- Output Schema:
  - 公共字段：必须完整包含 §12.0 的 Polish 第一组公共字段。
  - `question_id_candidate`
  - `topic_ref`
  - `question_text`
  - `question_type`
  - `difficulty_hint`
  - `expected_focus_points`
  - `related_job_requirements`
  - `related_resume_modules`
  - `source_refs`
  - `evidence_refs`
  - `anti_repeat_refs`
  - `answer_guidance_visibility`
  - `time_box_hint`
  - `follow_up_allowed`
  - `same_question_polish_allowed`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 题目必须与 selected topic、岗位要求或简历模块有关。
  - 题目不得重复最近已问问题；无法判断重复时必须触发低置信度。
  - 题目不得直接泄露完整参考答案。
  - `difficulty_hint` 只是建议，不冻结题目推荐算法。
  - `question_type` 必须使用稳定枚举，例如 `experience` / `project_deep_dive` / `technical_principle` / `scenario` / `behavioral` / `system_design` / `coding_discussion` 或后续等价枚举。
  - `answer_guidance_visibility` 必须区分用户答题前是否展示提示。
  - 不得生成违法、隐私侵入或与岗位无关题目。
- Low Confidence Rules:
  - selected topic 缺失。
  - 岗位或简历证据不足。
  - 禁止重复列表缺失。
  - 题目与岗位 / 简历关联弱。
  - RAG evidence 不可用但题目需要知识补充。
  - 输出题目过泛。
  - 无法判断是否重复。
  - 上下文高风险裁剪。
- Evidence Requirements: 题目、预期考察点、岗位要求、简历模块和去重依据必须绑定 `EvidenceRef` 或 `anti_repeat_refs`；缺少证据时不得伪装成高置信题目。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、题目生成或选择、去重检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PolishQuestion` candidate 或等价会话内题目对象。
  - `PolishTurn` 初始化输入。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 生成题目可以直接进入答题流程。
  - 用户可跳过、换题、继续同主题或切换主题。
  - 题目生成不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- Retry / Fallback:
  - selected topic 缺失、owner mismatch 或必需版本缺失时停止正常生成，返回失败或补充材料路径。
  - RAG 为空、历史题目不可确认或题目过泛时可重试、降级为基础题目或要求用户补充方向。
  - 重试不得默认启用互联网检索、扩大到全量历史会话或泄露完整参考答案。
- API State Mapping: 只定义状态语义，包括 `question_available`、`question_partial`、`question_low_confidence`、`question_validation_failed`、`duplicate_risk`、`topic_missing` 和 `source_unavailable`；不定义 endpoint 或 schema。
- Security Notes: 题目生成只使用当前 owner 的必要岗位、简历、topic、session summary 和已授权增强材料；日志不记录原始 Prompt、completion、provider payload 或隐私正文。
- Test Strategy: 使用 fixture 覆盖有 topic、无 topic、禁止重复列表缺失、重复题、无 RAG、技术题缺证据、过泛题、答题前提示可见性、违法 / 隐私题拒绝和题目不转正式弱项 / 资产 / 训练建议。
- Open Questions: 题目推荐算法、难度排序、题目数量控制、time box 默认值、进展树推荐策略和后续题目 API 字段仍待后续 contract / API / UX 收敛，不在本 contract 关闭。

### 12.3 `P-POLISH-003` Answer Diagnosis

- Contract ID: `P-POLISH-003`
- Name: Answer Diagnosis
- Mode: `polish`
- Trigger:
  - 用户提交当前题目的回答。
  - 用户修改回答后重新诊断。
  - 用户请求解释回答问题。
  - `P-POLISH-004` 评分前需要诊断输入。
- Goal: 诊断用户对当前题目的回答，输出结构化反馈、优点、不足、缺失信息、追问线索和后续评分输入；不静默创建正式薄弱项、资产或训练建议。
- Required Inputs:
  - `OwnerRef`
  - `polish_session_ref`
  - `PolishQuestion` 或当前题目引用
  - 用户当前回答
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - selected topic
  - Job Match points
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 最近若干轮回答
  - 题目相关知识库 / RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用当前题目、当前回答、`JobVersion`、`ResumeVersion` 和 `SessionSummary`。
  - 条件检索 Job Match points、资产、薄弱项、知识库和历史回答。
  - 如果需要判断技术准确性或补充考点，可经过 `P-SHARED-002` 使用知识库 / RAG。
  - 不得默认启用互联网检索。
  - 无知识库时仍可基于题目、岗位、简历和回答进行基础诊断；技术原理类判断应标记证据弱或低置信度。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、裁剪、omitted refs 和 trace 规则；条件检索时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前题目、用户回答、岗位相关要求、简历相关模块、selected topic、最近相关 turn 和输出 schema。
  - 对长回答必须优先保留用户原始回答、问题要求、岗位证据和诊断目标。
  - 不得默认塞入全部历史回答、全部知识库材料、全部资产或全部薄弱项。
- Excluded Inputs:
  - 用户未表达的经历、无证据的能力判断、未确认候选对象作为正式事实。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 无关历史回答全文、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果和无法形成 `EvidenceRef` 的技术断言。
- Output Schema:
  - 公共字段：必须完整包含 §12.0 的 Polish 第一组公共字段。
  - `diagnosis_id_candidate`
  - `question_ref`
  - `answer_ref`
  - `answer_summary`
  - `strengths`
  - `weaknesses`
  - `missing_points`
  - `unclear_points`
  - `off_topic_segments`
  - `technical_accuracy_notes`
  - `structure_notes`
  - `communication_notes`
  - `evidence_refs`
  - `score_input_refs`
  - `suggested_follow_up_questions`
  - `candidate_loss_points`
  - `candidate_improvement_actions`
  - `requires_user_clarification`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 诊断必须基于当前题目和当前回答。
  - 不得把用户未表达的经历虚构为事实。
  - 不得把岗位不匹配直接包装为用户能力缺陷。
  - 不得静默创建正式 `Weakness`。
  - 技术准确性判断如缺少知识证据，应触发低置信度。
  - 诊断输出必须能作为 `P-POLISH-004` 的评分输入。
  - `suggested_follow_up_questions` 只是候选，不等同于压力面连续追问。
- Low Confidence Rules:
  - 用户回答过短。
  - 用户回答明显跑题。
  - 当前题目缺失。
  - 岗位 / 简历证据不足。
  - 技术判断缺少知识证据。
  - 回答中存在自相矛盾内容。
  - 上下文裁剪影响诊断。
  - 模型无法区分事实、推测和建议。
  - 诊断输出无法绑定证据或无法作为评分输入。
- Evidence Requirements: strengths、weaknesses、missing points、technical accuracy notes、candidate loss points 和 improvement actions 必须绑定当前题目、当前回答、岗位 / 简历 evidence 或知识库 `EvidenceRef`；证据不足时必须显式标记。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Context Assembly、条件 Retrieval Planning、Input Evidence Selection、回答诊断、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PolishAnswerDiagnosis` 或等价会话内诊断对象。
  - `PolishTurn` 诊断结果。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 诊断结果可作为本轮反馈展示。
  - 派生的弱项、资产或训练方向只能作为候选或后续 contract 输入。
  - 用户可补充回答、重新诊断或继续评分。
- Retry / Fallback:
  - 当前题目或当前回答缺失、owner mismatch 或必需版本缺失时停止正常诊断，返回失败或补充材料路径。
  - 回答过短、证据不足或技术判断缺证据时可保存低置信度诊断、要求用户补充回答或跳过技术准确性判断。
  - 重试不得默认启用互联网检索、虚构用户经历或把建议写成事实。
- API State Mapping: 只定义状态语义，包括 `diagnosis_available`、`diagnosis_partial`、`diagnosis_low_confidence`、`diagnosis_validation_failed`、`answer_too_short`、`clarification_required` 和 `technical_evidence_missing`；不定义 endpoint 或 schema。
- Security Notes: 诊断只使用当前 owner 的题目、回答、岗位、简历和授权增强证据；可展示结果不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖正常回答、过短回答、跑题回答、题目缺失、岗位 / 简历证据不足、技术判断缺 RAG、回答自相矛盾、虚构经历防护、岗位不匹配不包装成能力缺陷和不静默创建正式 `Weakness`。
- Open Questions: 失分点归因细则、参考答案生成、考点解析、技术原理扩展、压力面追问策略和正式弱项候选生成仍交给后续 Polish / Pressure / Weakness contracts，不在本 contract 关闭。

### 12.4 `P-POLISH-004` Round Score

- Contract ID: `P-POLISH-004`
- Name: Round Score
- Mode: `polish`
- Trigger:
  - `P-POLISH-003` 完成回答诊断后。
  - 用户提交回答并请求评分。
  - 用户修改回答后重新评分。
  - 系统需要决定是否建议继续同题打磨。
- Goal: 基于当前题目、用户回答和诊断结果生成每轮 0-100 展示分与解释；不冻结评分公式、权重、阈值或校准方法，只冻结评分输出必须具备的结构、解释、证据、低置信度和 trace。
- Required Inputs:
  - `OwnerRef`
  - `polish_session_ref`
  - 当前题目引用
  - 用户当前回答引用
  - `P-POLISH-003` Answer Diagnosis 结果或等价诊断输入
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - `ScoreRuleVersion` 或评分规则占位引用
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - `JobMatchAnalysis`
  - `ScoreResult` canonical score from Job Match
  - selected topic
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 历史同题打磨轮次
  - 知识库 / RAG evidence
  - 公共评分口径
- Retrieval Sources:
  - 默认使用当前题目、当前回答、回答诊断、`JobVersion`、`ResumeVersion` 和 `SessionSummary`。
  - 条件读取 Job Match canonical score、历史同题轮次、公共评分口径和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或公共评分口径时仍可生成基础得分，但必须保留评分规则 UNKNOWN、资料不足或低置信度边界。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、裁剪、omitted refs 和 trace 规则；条件读取时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前题目、用户回答、诊断结果、岗位要求、简历相关模块、评分目标、评分规则版本或 UNKNOWN 占位、输出 schema。
  - 上下文过长时优先保留当前题目、当前回答、诊断结果、评分证据、输出 schema 和 validation 要求。
  - 不得默认塞入全部历史回答、全部资产、全部知识库或全部复盘。
- Excluded Inputs:
  - 具体未冻结评分公式、权重、阈值、校准方法或精确通过概率。
  - Job Match 分数作为本轮回答分的直接替代。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 无关历史回答全文、全量资产、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §12.0 的 Polish 第一组公共字段。
  - `round_score_ref`
  - `score_result_ref`
  - `score_value`
  - `score_scale`
  - `score_type`
  - `score_explanation`
  - `dimension_scores`
  - `positive_evidence_refs`
  - `negative_evidence_refs`
  - `diagnosis_refs`
  - `loss_point_candidate_refs`
  - `improvement_action_refs`
  - `score_rule_version_ref`
  - `uncertainty_reasons`
  - `same_question_continue_hint`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - `score_value` 必须在 0-100 范围内。
  - `score_scale` 必须表明是产品展示刻度。
  - 不得输出精确通过概率。
  - 不得输出“必过”“必挂”等确定性预测。
  - 不得把岗位匹配分直接当成本轮回答分。
  - 分数解释必须绑定当前题目、当前回答和诊断证据。
  - 低分和高分都必须有解释。
  - 评分规则未冻结时必须保留 UNKNOWN，不得虚构公式。
  - `same_question_continue_hint` 只是建议，不关闭同题打磨结束阈值 UNKNOWN。
- Low Confidence Rules:
  - 用户回答过短。
  - 诊断结果缺失或低置信度。
  - 当前题目缺失。
  - 评分规则版本缺失或未冻结。
  - 证据不足。
  - 分数与解释不一致。
  - 只有分数没有解释。
  - 上下文裁剪影响评分依据。
  - 技术准确性需要知识证据但 RAG 不可用。
- Evidence Requirements: `score_explanation`、正向证据、负向证据、dimension scores、诊断引用、失分点候选和改进动作必须绑定当前题目、当前回答、诊断结果和 `EvidenceRef`；评分规则版本或 UNKNOWN 占位必须可追踪到 `ScoreRuleVersion` / `TraceRef`。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Context Assembly、条件 Retrieval Planning、Input Evidence Selection、评分生成、评分规则引用、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- `canonical` score 关系:
  - `ScoreResult` 是统一评分承载对象，保存 score value、score type、explanation、rule version、evidence refs、validation result 和 trace refs。
  - `PolishRoundScore` 是打磨轮次场景下的视图、引用或领域包装，用于从 `PolishTurn` 指向对应 `ScoreResult`。
  - 不允许 `ScoreResult` 与 `PolishRoundScore` 分别保存两份不一致的分数、解释或证据。
  - Job Match canonical score 可作为上游参考，但不得直接替代本轮回答分。
  - 历史回看、校准和报告复用应引用 canonical score。
- Persistence Targets:
  - `PolishRoundScore` 或等价会话内得分对象。
  - `ScoreResult` canonical score。
  - `ScoreExplanation`
  - `ScoreEvidenceLink`
  - `PolishTurn` scoring result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 本轮得分可直接作为打磨反馈展示。
  - 由得分派生的正式 `Weakness`、`Asset` 或 `TrainingRecommendation` 必须进入后续候选 / 确认链路。
  - 用户可以重新回答、继续同题打磨、换题或进入后续解释 / 参考答案 contract。
- Retry / Fallback:
  - 分数越界、缺少解释、缺 evidence refs 或诊断引用缺失时进入 repair / retry / validation failed。
  - 评分规则 UNKNOWN、证据不足或 RAG 不可用时可保存低置信度分数、部分可用解释或要求用户补充回答。
  - 重试不得默认启用互联网检索、虚构评分公式或把 Job Match 分数当成本轮回答分。
- API State Mapping: 只定义状态语义，包括 `round_score_available`、`round_score_partial`、`round_score_low_confidence`、`round_score_validation_failed`、`score_rule_unknown`、`score_out_of_range`、`evidence_missing` 和 `same_question_continue_suggested`；不定义 endpoint 或 schema。
- Security Notes: 评分上下文只能包含当前 owner 的题目、回答、诊断、岗位、简历、证据和授权增强材料；日志不得记录原始 Prompt、completion、provider payload 或隐私正文；前端只可见结构化分数、解释、状态、可展示证据摘要和必要 trace id。
- Test Strategy: 使用 fixture 覆盖 0、100、中间分、分数越界、只有分数无解释、解释无证据、诊断缺失、评分规则 UNKNOWN、Job Match 分数不可直接复用、本轮高分 / 低分均有解释、不得输出精确通过概率和 same question continue hint 不关闭 UNKNOWN。
- Open Questions:
  - 评分公式。
  - 分项权重。
  - 阈值。
  - 校准方法。
  - 评分等级映射。
  - 同题打磨结束建议阈值。
  - 通过倾向展示边界。

### 12.5 Polish 第一组 Contract 关系

- `P-POLISH-001` 负责规划打磨主题。
- `P-POLISH-002` 基于选定主题生成或选择题目。
- `P-POLISH-003` 基于当前题目和用户回答生成诊断。
- `P-POLISH-004` 基于当前题目、用户回答和诊断生成本轮 0-100 得分。
- 四个 contract 都必须引用 Shared Contracts，并至少交接 validation、low confidence、EvidenceRef、TraceRef 和 session summary update 输入。
- `P-POLISH-001` 和 `P-POLISH-002` 可以消费 Job Match 输出作为上游参考。
- `P-POLISH-003` 和 `P-POLISH-004` 必须绑定当前题目和当前回答。
- `P-POLISH-004` 不得把 Job Match 分数直接当成本轮回答分。
- Polish 第一组不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- Polish 第一组产生的弱项、资产、失分点、参考答案、知识点解析和下一轮建议，应交给后续 Polish contracts 或对应业务 contract。
- Polish 第一组每轮结束后应为 `P-SHARED-006` Session Summary Update 提供输入。

## 13. 单个 Contract Stub 模板

后续填充 contract 时复制以下结构。模板只写字段结构，不写具体 Prompt 文案。

```markdown
### <Contract ID> <Name>

- Contract ID:
- Name:
- Mode:
- Trigger:
- Goal:
- Required Inputs:
- Optional Inputs:
- Retrieval Sources:
- Context Assembly:
- Excluded Inputs:
- Output Schema:
- Validation Rules:
- Low Confidence Rules:
- Evidence Requirements:
- Trace Requirements:
- Persistence Targets:
- User Confirmation Requirement:
- Retry / Fallback:
- API State Mapping:
- Security Notes:
- Test Strategy:
- Open Questions:
```

## 14. 后续填充顺序

当前已将 Shared contracts、Job match contracts 和 Polish 第一组 contracts 填充为 Draft。后续业务 contract 建议按以下顺序继续填充：

1. Polish mode 剩余 contracts（`P-POLISH-005` 至 `P-POLISH-011`）。
2. Pressure mode contracts。
3. Report contracts。
4. Review contracts。
5. Weakness / asset / training contracts。
6. Cross-contract consistency review。

## 15. UNKNOWN 与后续交接

以下 UNKNOWN 本阶段只承接，不关闭：

- 评分公式、权重、阈值、校准方法。
- 通过倾向 / 风险提示展示边界。
- 题目推荐算法。
- 压力面题量和节奏规则。
- 连续追问深度规则。
- 同题打磨结束建议阈值。
- 复盘切分规则。
- 薄弱项算法和合并规则。
- 资产合并和版本策略。
- 上下文预算具体数值。
- 模型选择和模型参数。
- retry / fallback 具体策略。
- RAG 索引、embedding 和向量库实现。

本阶段不关闭上述 UNKNOWN，不改变 PRD §10 的关闭台账，不把 `AIFI-PROMPT-001` 标记为 DONE。后续只有在具体 contract 完成、与 `TECH_DESIGN.md` / `DATA_MODEL.md` / `SECURITY_PRIVACY.md` / `API_SPEC.md` 一致性复核通过，并具备可验证证据后，才能进入 `AIFI-ARCH-002` 的 UNKNOWN 关闭检查。

## 16. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-15 | 填充 Polish 第一组 Contract 细则 | 将 `P-POLISH-001` 至 `P-POLISH-004` 从 Stub 更新为 Draft，补充主题规划、题目生成、回答诊断和每轮 0-100 得分 contract；不填充 `P-POLISH-005` 至 `P-POLISH-011`，不生成最终报告、正式薄弱项、正式资产或训练计划，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 填充 Job Match Contract 细则 | 将 `P-JOBMATCH-001` 至 `P-JOBMATCH-004` 从 Stub 更新为 Draft，补充岗位匹配分析总控、0-100 匹配分、匹配 / 不匹配 / 加强点和薄弱项候选 contract；不填充其他业务 contract，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 修复 Shared Contracts 审计阻塞问题 | 拆分 Input Evidence Selection / Output Evidence Binding，补充推荐调用顺序、failure signal enum、source availability 矩阵、Context Assembly 条件输入和安全分区、Retrieval Planning 子阶段，以及 Session Summary MVP 执行策略；不填充业务 contract，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 填充 Shared Contract 细则 | 将 `P-SHARED-001` 至 `P-SHARED-006` 从 Stub 更新为 Draft，补充上下文装配、检索规划、输出校验、低置信度、证据绑定和会话摘要更新的公共 contract；不填充业务 contract，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 初始化 F4 Prompt / AI 子任务 contract 草案 | 创建 AI Task Contract 标准模板、Context Assembly、Retrieval、Output Schema、Validation、Low Confidence、EvidenceRef、TraceRef、Persistence、Failure Handling 和 contract catalog；不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
