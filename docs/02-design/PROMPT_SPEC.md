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

### 3.1 Contract ID Namespace Governance

本节冻结 `P-*` 系列 AI Task Contract ID 的含义、格式、命名边界和维护规则。拆分后仍沿用本 namespace，不重新命名现有 ID；主 catalog 继续作为 canonical registry，子文档只承载详细正文。

#### 3.1.1 ID 定位

- `P-*` 是 AI Task Contract 的稳定引用 ID。
- `P-*` 用于在 Prompt / AI orchestration 规范、trace、validation、测试 fixture、后续 API 状态语义和子文档之间引用具体 AI 子任务。
- `P-*` 不等于完整 Prompt 文案。
- `P-*` 不等于一次 LLM 调用。
- `P-*` 不等于 API endpoint。
- `P-*` 不等于数据库表名。
- `P-*` 不等于 BACKLOG task id。
- `P-*` 不等于物理任务队列 id。
- `P-*` 不等于 UI route 或前端组件名。

#### 3.1.2 `P` 的含义

- `P` = `Prompt / AI Task Contract`。
- `P-*` = `Prompt Contract namespace for AI task contracts`。
- `P` 是本文件历史兼容前缀，后续继续沿用。
- 不再引入新的同级前缀；如确需迁移，必须通过单独文档治理任务显式完成。
- 拆分后仍沿用该 ID 体系。

#### 3.1.3 ID 格式

ID 格式固定为：

```text
P-<DOMAIN>-<NNN>
```

| 组成 | 说明 |
|---|---|
| `P` | Prompt / AI Task Contract 前缀 |
| `<DOMAIN>` | contract 所属能力域 |
| `<NNN>` | 三位递增编号，从 `001` 开始 |

格式规则：

- `DOMAIN` 使用大写英文。
- `NNN` 必须是三位数字。
- 不允许使用 `P-POLISH-1`、`P-Polish-001`、`POLISH-001`、`P_POLISH_001` 等变体。
- 新增 ID 必须先登记到主 catalog。
- 详细 contract 正文必须使用 catalog 中已登记的 ID。

#### 3.1.4 允许的 DOMAIN

| Domain | 范围 |
|---|---|
| `SHARED` | 跨模式公共 contract，例如上下文装配、检索规划、校验、低置信度、证据绑定、session summary |
| `JOBMATCH` | 岗位匹配分析链路 |
| `POLISH` | 打磨模式链路 |
| `PRESSURE` | 压力面模式链路 |
| `REPORT` | 面试报告链路 |
| `REVIEW` | 模拟 / 真实面试复盘链路 |
| `WEAKNESS` | 正式薄弱项体系链路 |
| `ASSET` | 正式资产体系链路 |
| `TRAINING` | 训练建议和训练闭环链路 |

DOMAIN 治理规则：

- 不得随意新增 domain。
- 新增 domain 必须通过 `PROMPT_SPEC.md` 治理补丁登记。
- domain 不是数据库 schema，也不是 bounded context 的最终实现边界。

#### 3.1.5 ID 稳定性

- ID 一旦进入 catalog，不应因标题、描述或正文细节微调而改变。
- Contract 名称可以优化，但 ID 应保持稳定。
- ID 不得复用。
- 删除 contract 时，应标记为 `Deprecated` 或等价状态，不得把编号分配给新 contract。
- 合并 contract 时，应保留原 ID 的迁移说明。
- 拆分 contract 时，新 contract 使用新 ID，旧 ID 保留迁移说明。
- 状态从 `Stub` 到 `Draft` 到后续状态变化，不改变 ID。

#### 3.1.6 ID 与执行顺序

- 编号通常反映默认 catalog 顺序或默认链路顺序。
- 编号不等于强制物理执行顺序。
- 编号不等于必须一对一对应一次 LLM 调用。
- 编号不等于必须同步执行。
- 应用编排层可以根据模式、状态、用户动作和失败处理选择跳过、重试、合并或拆分调用。
- 任何编排变体都必须保留输出所属 contract ID 和 trace。

#### 3.1.7 Canonical Registry

- `docs/02-design/PROMPT_SPEC.md` 中的 Contract Catalog 是 canonical registry。
- 拆分到子文档后，主 catalog 仍是 ID 的唯一登记源。
- 子文档可以承载详细正文，但不得自行创建未登记 ID。
- 子文档中的 contract ID 必须与主 catalog 完全一致。
- 拆分只迁移详细 contract 正文，不改变 ID、名称、目标、domain 或状态。
- 后续文档引用 contract 时应使用 `Contract ID + 名称`，例如 `P-POLISH-004 Round Score`。

#### 3.1.8 ID 与状态

- `Stub` 表示已登记但尚未填充正文。
- `Draft` 表示 contract 细则已经填充，但仍属于 F4 draft。
- `Deprecated` 可用于后续废弃 contract。
- `DONE` 不是 contract catalog 状态，`DONE` 只能用于 BACKLOG / delivery task，不应用于 contract 状态。
- 把某个 contract 标为 `Draft` 不代表实现完成。
- 把全部 contract 标为 `Draft` 也不代表 `AIFI-PROMPT-001` 自动 DONE。

#### 3.1.9 跨文档引用

- 引用时使用 `Contract ID + 名称`。
- 首次引用建议写完整，例如 `P-PRESSURE-003 Answer Quality Assessment`。
- 后续可简称 ID。
- 不得只写中文名称而省略 ID。
- 不得只写 ID 而不在附近提供名称或上下文。
- trace、validation、fixture、API state mapping 后续应优先使用 ID 作为稳定引用键。

#### 3.1.10 拆分维护规则

- 拆分或维护子文档时，必须先确保本 namespace 已冻结，并以主 catalog 为准。
- 拆分只迁移详细 contract 正文，不改变 ID。
- 拆分后主文件继续保留 canonical registry 和 governance。
- 子文档不得改变 ID 含义、domain 或状态。
- 如果拆分中发现 ID 冲突，应停止拆分并先修 registry。

## 4. AI Task Contract 标准模板

后续每个 AI 子任务 contract 必须使用统一字段。字段是 contract 结构，不是 Prompt 文案。

| 字段 | 必填 | 说明 |
|---|---|---|
| `contract_id` | 是 | 稳定编号，例如 `P-POLISH-004`；新 ID 必须符合 `P-<DOMAIN>-<NNN>` |
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

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-SHARED-001` | Context Assembly | 统一上下文装配 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-002` | Retrieval Planning | 决定检索来源与裁剪策略 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-003` | Output Validation | 结构化与业务语义校验 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-004` | Low Confidence Classification | 低置信度分类 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-005` | Evidence Binding | 证据引用绑定 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-006` | Session Summary Update | 会话摘要更新 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |

### 9.2 Job Match Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-JOBMATCH-001` | Match Analysis | 生成岗位匹配分析 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |
| `P-JOBMATCH-002` | Match Score | 生成 0-100 匹配分与解释 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |
| `P-JOBMATCH-003` | Match / Mismatch / Improvement Points | 生成匹配点、不匹配点、加强点 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |
| `P-JOBMATCH-004` | Weakness Candidate from Job Match | 从岗位匹配分析提炼薄弱项候选 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |

### 9.3 Polish Mode Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-POLISH-001` | Topic Planning | 规划打磨主题 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-002` | Question Generation | 生成或选择打磨题目 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-003` | Answer Diagnosis | 诊断用户回答 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-004` | Round Score | 生成每轮 0-100 得分 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-005` | Loss Point Analysis | 生成失分点与原因 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-006` | Reference Answer | 生成参考回答 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-007` | Knowledge Point Explanation | 生成考点解析 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-008` | Technical Principle Expansion | 生成技术原理扩展 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-009` | Next Round Suggestion | 生成下一轮改进建议 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-010` | Asset Candidate | 生成资产候选 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |
| `P-POLISH-011` | Weakness Candidate | 生成薄弱项候选 | Draft | `prompt-contracts/POLISH_CONTRACTS.md` |

### 9.4 Pressure Mode Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-PRESSURE-001` | Opening Strategy | 生成压力面开场策略 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-002` | First Question Generation | 生成首题 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-003` | Answer Quality Assessment | 判断回答质量 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-004` | Follow-up Strategy | 选择追问策略 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-005` | Follow-up Question Generation | 生成连续追问 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-006` | Pace Control | 控制节奏与压力强度 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-007` | End Condition Check | 判断是否结束整场 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-008` | Session Score | 生成整场评分 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |
| `P-PRESSURE-009` | Report Input Assembly | 组装报告输入 | Draft | `prompt-contracts/PRESSURE_CONTRACTS.md` |

### 9.5 Report Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-REPORT-001` | Interview Report Generation | 生成面试报告 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |
| `P-REPORT-002` | Section Score Explanation | 生成分项评分解释 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |
| `P-REPORT-003` | Risk and Pass Tendency Wording | 生成风险提示和通过倾向表达 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |
| `P-REPORT-004` | Copyable Content Assembly | 生成可复制内容结构 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |

### 9.6 Review Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-REVIEW-001` | Mock Interview Review | 生成模拟面试复盘 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |
| `P-REVIEW-002` | Real Interview Input Structuring | 结构化真实面试输入 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |
| `P-REVIEW-003` | Real Interview Review | 生成真实面试复盘 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |
| `P-REVIEW-004` | Review Item Extraction | 提炼题级复盘项 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |

### 9.7 Weakness Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-WEAKNESS-001` | Weakness Extraction | 提炼薄弱项候选 | Stub | `prompt-contracts/WEAKNESS_CONTRACTS.md` |
| `P-WEAKNESS-002` | Weakness Merge Suggestion | 生成薄弱项合并建议 | Stub | `prompt-contracts/WEAKNESS_CONTRACTS.md` |
| `P-WEAKNESS-003` | Weakness Severity Assessment | 判断薄弱项严重度 | Stub | `prompt-contracts/WEAKNESS_CONTRACTS.md` |
| `P-WEAKNESS-004` | Weakness Status Update Suggestion | 生成状态更新建议 | Stub | `prompt-contracts/WEAKNESS_CONTRACTS.md` |

### 9.8 Asset Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-ASSET-001` | Asset Candidate Extraction | 提炼资产候选 | Stub | `prompt-contracts/ASSET_CONTRACTS.md` |
| `P-ASSET-002` | Asset Quality Hint | 生成资产质量提示 | Stub | `prompt-contracts/ASSET_CONTRACTS.md` |
| `P-ASSET-003` | Asset Version Suggestion | 生成资产版本更新建议 | Stub | `prompt-contracts/ASSET_CONTRACTS.md` |

### 9.9 Training Contracts

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-TRAINING-001` | Training Recommendation | 生成训练建议 | Stub | `prompt-contracts/TRAINING_CONTRACTS.md` |
| `P-TRAINING-002` | Training Priority Ranking | 训练建议排序 | Stub | `prompt-contracts/TRAINING_CONTRACTS.md` |
| `P-TRAINING-003` | Training Result Review | 训练结果复盘 | Stub | `prompt-contracts/TRAINING_CONTRACTS.md` |

## 10. Contract 子文档索引

本节是详细 contract 正文迁移后的子文档入口。主 `PROMPT_SPEC.md` 继续保留 Contract Catalog canonical registry；子文档只承载已登记 contract 的详细正文或 Stub 摘要，不覆盖主 catalog 的 ID、名称、目标或状态。

| 子文档 | 范围 | 状态 | 说明 |
|---|---|---|---|
| `prompt-contracts/SHARED_CONTRACTS.md` | `P-SHARED-*` | Draft | Shared contract 细则 |
| `prompt-contracts/JOB_MATCH_CONTRACTS.md` | `P-JOBMATCH-*` | Draft | Job Match contract 细则 |
| `prompt-contracts/POLISH_CONTRACTS.md` | `P-POLISH-*` | Draft | Polish 001-011 细则 |
| `prompt-contracts/PRESSURE_CONTRACTS.md` | `P-PRESSURE-*` | Draft | Pressure 001-009 细则 |
| `prompt-contracts/REPORT_CONTRACTS.md` | `P-REPORT-*` | Draft | Report 001-004 细则 |
| `prompt-contracts/REVIEW_CONTRACTS.md` | `P-REVIEW-*` | Draft | Review 001-004 细则 |
| `prompt-contracts/WEAKNESS_CONTRACTS.md` | `P-WEAKNESS-*` | Stub | 待后续授权填充 |
| `prompt-contracts/ASSET_CONTRACTS.md` | `P-ASSET-*` | Stub | 待后续授权填充 |
| `prompt-contracts/TRAINING_CONTRACTS.md` | `P-TRAINING-*` | Stub | 待后续授权填充 |

## 11. 单个 Contract Stub 模板

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

## 12. 后续填充顺序

当前已将 Shared contracts、Job match contracts、Polish `P-POLISH-001` 至 `P-POLISH-011`、Pressure `P-PRESSURE-001` 至 `P-PRESSURE-009`、Report `P-REPORT-001` 至 `P-REPORT-004` 和 Review `P-REVIEW-001` 至 `P-REVIEW-004` 填充为 Draft。Review 细则完成后，下一批不应继续重复填充 Review contracts；应先进入 Review 001-004 只读验收，或在另行授权后进入 Weakness / Asset / Training 等后续阶段。

1. Review `P-REVIEW-001` 至 `P-REVIEW-004` 只读验收。
2. Weakness / asset / training contracts。
3. Cross-contract consistency review。

## 13. UNKNOWN 与后续交接

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

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-16 | 填充 Review Contract 细则 | 将 `P-REVIEW-001` 至 `P-REVIEW-004` 从 Stub 更新为 Draft，补充模拟面试复盘、真实面试输入结构化、真实面试复盘和题级复盘项提取 contract；不填充 Weakness / Asset / Training contracts，不生成真实复盘实例，不写正式 Weakness、正式 Asset 或 TrainingRecommendation，不关闭复盘切分、真实面试输入结构化、题级复盘项合并、薄弱项合并、资产归档或训练优先级 UNKNOWN |
| 2026-05-16 | 填充 Report Contract 细则 | 将 `P-REPORT-001` 至 `P-REPORT-004` 从 Stub 更新为 Draft，补充报告生成、分项评分解释、风险提示与通过倾向、可复制内容组装 contract；不填充 Review / Weakness / Asset / Training contracts，不生成报告实例，不写正式 Weakness、正式 Asset 或 TrainingRecommendation，不关闭评分公式、分项权重、通过倾向、风险提示阈值或 RAG 实现 UNKNOWN |
| 2026-05-15 | 拆分 contract 子文档 | 主文件保留 canonical registry 和治理规则，详细正文迁移到 `prompt-contracts/*.md`；不改变 contract ID、名称、状态或语义，不填充 Stub contract，不关闭 UNKNOWN |
| 2026-05-15 | 填充 Pressure 7B Contract 细则 | 将 `P-PRESSURE-005` 至 `P-PRESSURE-009` 从 Stub 更新为 Draft，补充连续追问生成、节奏控制、结束条件判断、整场评分和报告输入组装 contract；不填充 Report / Review / Weakness / Asset / Training contracts，不生成报告正文，不写正式 Weakness、正式 Asset 或 TrainingRecommendation，不关闭压力强度、追问深度、结束条件、整场评分公式、通过倾向或 RAG 实现 UNKNOWN |
| 2026-05-15 | 填充 Pressure 第一组 Contract 细则 | 将 `P-PRESSURE-001` 至 `P-PRESSURE-004` 从 Stub 更新为 Draft，补充开场策略、首题生成、回答质量判断和追问策略 contract；不填充 `P-PRESSURE-005` 至 `P-PRESSURE-009`，不生成连续追问题目、整场评分、最终报告、正式薄弱项、正式资产或训练建议，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 填充 Polish 6B 回流候选链路 Contract 细则 | 将 `P-POLISH-009` 至 `P-POLISH-011` 从 Stub 更新为 Draft，补充下一轮建议、资产候选和薄弱项候选 contract；不填充 Pressure / Report / Review / Weakness / Asset / Training contracts，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 填充 Polish 第一组 Contract 细则 | 将 `P-POLISH-001` 至 `P-POLISH-004` 从 Stub 更新为 Draft，补充主题规划、题目生成、回答诊断和每轮 0-100 得分 contract；不填充 `P-POLISH-005` 至 `P-POLISH-011`，不生成最终报告、正式薄弱项、正式资产或训练计划，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 填充 Job Match Contract 细则 | 将 `P-JOBMATCH-001` 至 `P-JOBMATCH-004` 从 Stub 更新为 Draft，补充岗位匹配分析总控、0-100 匹配分、匹配 / 不匹配 / 加强点和薄弱项候选 contract；不填充其他业务 contract，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 修复 Shared Contracts 审计阻塞问题 | 拆分 Input Evidence Selection / Output Evidence Binding，补充推荐调用顺序、failure signal enum、source availability 矩阵、Context Assembly 条件输入和安全分区、Retrieval Planning 子阶段，以及 Session Summary MVP 执行策略；不填充业务 contract，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 填充 Shared Contract 细则 | 将 `P-SHARED-001` 至 `P-SHARED-006` 从 Stub 更新为 Draft，补充上下文装配、检索规划、输出校验、低置信度、证据绑定和会话摘要更新的公共 contract；不填充业务 contract，不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 初始化 F4 Prompt / AI 子任务 contract 草案 | 创建 AI Task Contract 标准模板、Context Assembly、Retrieval、Output Schema、Validation、Low Confidence、EvidenceRef、TraceRef、Persistence、Failure Handling 和 contract catalog；不写完整 Prompt 文案，不关闭 `F4_TECH_DESIGN` UNKNOWN |
