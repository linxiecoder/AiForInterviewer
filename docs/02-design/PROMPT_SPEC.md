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
- 本文件维护 AI 子任务 contract canonical registry、统一模板、公共规则和子文档索引，不是完整提示词文案库。
- 本文件不是代码实现、API spec、数据模型、模型供应商配置或向量数据库设计。
- 本文件不定义 API endpoint、request / response schema、物理数据库 schema、embedding 模型、向量数据库或联网搜索服务。
- 本轮按 `AR-F4-FULL-001` 处置 Prompt 侧 F4 阻断项：contract 输入、输出 schema、failure state、confidence、evidence、trace、validation、candidate / suggestion / confirmation 边界已冻结；不标记 `AIFI-ARCH-002` 或 `AIFI-PROMPT-001` 完成。
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
| `docs/02-design/SCORING_SPEC.md` | score type、rubric dimensions、默认权重、公式、低置信度和正式 `ScoreResult` 规则 |
| `docs/02-design/SEMANTICS_GLOSSARY.md` | Low Confidence、`confidence_level`、`validation_status`、`source_availability` 和 candidate / suggestion / formal object 统一语义 |
| `docs/02-design/APPLICATION_FLOW_SPEC.md` | P-* contract 到 application service、AiTask、LLM call plan、Prompt 输入结构和 persistence handoff 的运行编排 |
| `docs/02-design/PROMPT_ASSET_SPEC.md` | Production Prompt Asset registry、asset 字段、runtime bundle、builder、validator、fixture 和 trace 映射 |
| `docs/02-design/PROMPT_EVALUATION_SPEC.md` | Golden / regression / negative fixtures、quality metrics、fake / real provider gate、human review、CI gate 和 rollback policy |
| `docs/02-design/PRESSURE_MODE_SPEC.md` | Pressure Mode lifecycle、turn loop、pace/end/report handoff、runtime graph boundary 和 `P-PRESSURE-*` mode-level sequencing |
| `docs/03-implementation/BACKLOG.md` | `AIFI-PROMPT-001` 范围，以及与 `AIFI-ARCH-002`、`AIFI-DATA-001`、`AIFI-SEC-001` 的依赖 |

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
| Production Prompt Asset | `PROMPT_ASSET_SPEC.md` 登记的可版本化、可评审、可灰度、可回滚 Prompt 模板 / 文案资产 |
| Runtime Prompt Bundle | 运行时代码构造并传入 `LlmTransportRequest` 的 compact prompt 输入包，必须映射到 Production Prompt Asset |
| Prompt Evaluation Fixture | `PROMPT_EVALUATION_SPEC.md` 定义的 golden、regression、negative、redaction 或 model comparison fixture |

### 3.1 Contract ID 命名空间治理（Contract ID Namespace Governance）

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

#### 3.1.7 规范登记表（Canonical Registry）

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
| `open_questions` | 否 | 仅记录不阻断 M4 的 deferred_non_blocking 事项、UX 文案润色或实现细节；不得记录新的 F4 阻断项 |

## 5. 上下文装配（Context Assembly）总策略

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
- 打磨模式的主题选择来自 API 受控选项：`PolishTopicRef`、`PolishSubtopicRef` 和可选 `custom_topic_text`。主题 / 次主题只用于上下文装配、题目生成和后续 trace，不是正式业务对象，也不得替代 `ResumeVersion`、`JobVersion` 或 `JobResumeBinding`。
- `custom_topic_text` 必须按用户输入处理：进入 prompt 前需要长度限制、敏感信息裁剪、prompt injection 防护和指令中和；模型不得把其中的“忽略规则”“泄露系统提示”等文本当作系统指令。

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

### 6.1 来源可用性（Source Availability）状态矩阵

来源可用性状态统一使用 snake_case 枚举，供 Retrieval Planning、Context Assembly、Evidence Binding、Output Validation 和 Low Confidence Classification 复用。

| 状态 | 新生成是否可读取正文 | 历史引用处理 | 规则 |
|---|---|---|---|
| `source_available` | 可以，在通过 owner / scope 校验后读取最小必要片段 | 保留来源、版本、快照和摘要 | 可进入新生成上下文，但仍需最小化裁剪 |
| `source_unavailable` | 不可以 | 保留 ref、snapshot 或 summary status | 不得重新读取不可用正文；结果应进入低置信度或人工校对路径 |
| `source_deleted` | 不可以 | 保留历史 ref / snapshot / summary status | 不得把已删除正文放入新生成；历史结论不自动失效 |
| `source_disabled` | 不可以 | 保留历史 ref / snapshot / summary status | 禁用来源默认排除，只记录状态和必要风险标记 |
| `source_archived` | 默认不可以 | 历史引用可保留 ref / snapshot / summary status | archived 来源默认不进入新生成；除非后续业务设计明确恢复或选择历史引用场景 |
| `public_material_unpublished` | 不可以 | 不作为新生成证据 | 未发布公共材料不得进入业务生成或 RAG evidence |

## 7. 输出 Schema（Output Schema）、校验（Validation）与失败处理（Failure Handling）

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

### 7.1 共享失败信号枚举（Shared Failure Signal Enum）

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

### 7.2 评分候选（Scoring Candidate）、通过倾向与风险提示全局规则

本节冻结 `AR-F4-FULL-003` 的 Prompt / AI contract 全局边界，适用于 `P-JOBMATCH-002`、`P-POLISH-004`、`P-PRESSURE-008`、`P-REPORT-002`、`P-REPORT-003` 以及后续消费评分的 contract。评分公式、score type、rubric dimensions、默认权重、缺失维度处理和 F7 scoring fixture 的 canonical 位置为 `SCORING_SPEC.md`；本节只定义 Prompt 输出和校验边界。

- LLM 可以输出 scoring candidate / draft，但不得直接输出最终不可校验评分。正式 `ScoreResult` 必须经过 output schema、`P-SHARED-005` Evidence Binding、`P-SHARED-003` Output Validation、`P-SHARED-004` Low Confidence Classification、版本记录和 persistence handoff。
- 所有评分输出必须包含 `score_value`、`score_scale=0_100_product_scale`、`score_type`、`score_version`、`rubric_version`、`score_rule_version_ref`、`generated_by_task_id`、`generated_at`、`validation_status`、`confidence_level`、`evidence_refs`、`trace_refs` 和 `low_confidence_flags`。
- `score_value` 是 0-100 产品展示刻度，不是精确通过概率。Prompt 输出不得包含 `pass_probability`、`offer_probability`、`admission_probability`、通过率百分比或“你有 73% 概率通过”等等价文案。
- MVP 正式评分不并行输出 `raw_score`、`normalized_score` 和 `display_score` 三套分数；如候选生成包含内部原始值，必须在 validation / trace 中消化，不进入用户可见 schema。
- Rubric / rule version 是评分来源。Job Match 默认维度为 `requirement_alignment`、`experience_evidence`、`skill_coverage`、`gap_risk`、`readiness_actions`；面试会话 / 报告默认维度为 `answer_relevance`、`technical_depth`、`communication_structure`、`evidence_specificity`、`risk_control`。权重来自 `ScoreRuleVersion` 元数据，总和为 100，不由 LLM 临时发明。
- 版本变更后，历史报告和评分继续引用生成时 `score_version`、`rubric_version` 与 `ScoreRuleVersion`；不同版本分数不可直接强比较，除非后续存在校准映射。
- MVP 校准使用固定 rule version、人工验收样例集和回归 fixture；真实招聘结果校准为 `LATER` / `SHOULD`，且不得使用未脱敏第三方隐私数据。
- 通过倾向只允许分档：`low` / `medium` / `high` / `caution` / `insufficient_evidence`，用户可见对应“偏低 / 中等 / 偏高 / 需谨慎 / 证据不足，无法判断倾向”。通过倾向不得作为自动决策依据。
- 低置信度、证据不足、source unavailable、validation failed、评分规则版本缺失、evidence binding failed 或输出与证据冲突时，不得生成确定性通过倾向；必须降级为 `insufficient_evidence`、`manual_check_required` 或 `risk_wording_low_confidence`。
- 风险提示必须包含 `risk_level`、`risk_reason`、`confidence_level`、`evidence_refs`、`score_version`、`rubric_version`、`score_rule_version_ref`、`validation_status` 和 `low_confidence_flags`。风险提示解释风险来源，改进建议只提供下一步行动入口，两者不得混同。
- 风险提示不得使用恐吓式、确定性、歧视性或不可解释表达，不得把岗位匹配缺口直接包装成稳定能力缺陷，不得引用无权限来源、source unavailable 正文或未脱敏第三方隐私。
- 用户可见评分、通过倾向和风险提示必须带可信度说明与非决策性免责声明，说明结果基于当前材料、规则版本和证据，仅用于面试准备辅助，不代表真实招聘决定。
- generation failed / low confidence / source unavailable / validation failed 时，fallback 只能返回失败、部分可用、低置信度、补充材料、manual review 或 retry；不得用未校验 completion 填充正式评分或确定倾向。

## 8. Trace / Evidence / Persistence 交接

每个 contract 必须说明生成结果引用哪些 `EvidenceRef`，以及记录哪些 `TraceRef`。

交接规则：

- P-* contract 不是一次 LLM call，也不是 endpoint。运行编排、哪些 contract 合并为一次 LLM call、哪些按用户点击 on-demand 生成、以及每个流程读取 / 写入哪些模型，以 `APPLICATION_FLOW_SPEC.md` 为 canonical。
- 不得把原始 Prompt、provider payload、completion 原文默认暴露给前端。
- 持久化目标应区分正式业务结果、候选结果、trace、validation result、low confidence flag 和 audit event。
- 用户确认前，只能写入候选、待确认或 validation / trace 状态，不得写入正式资产、薄弱项或训练建议。
- 用户对低置信 candidate / suggestion 的校对内容必须先形成 `CandidateCorrection` / `UserCorrectionRef`，经过 owner 校验、结构化校验、敏感信息处理和 validation 后，才能作为后续 confirmation 或 task input；不得直接反向污染 Prompt source、覆盖原始候选或创建正式对象。
- Prompt contract 可以输出 `suggested_deposit_targets[]` 或下一步动作建议，但不得静默决定正式沉淀目标。允许建议的目标类型只限 `asset`、`weakness`、`training_suggestion`、`polish_input`、`pressure_input`、`next_interview_input`、`review_note`、`none` / `skip`；正式 `DepositTarget`、`target_ref` 和 `created_formal_ref` 由 API / DATA 的用户确认链路承接。
- Prompt contract、LLM recommendation、graph candidate、fallback result 或 provider transport success 不得输出、覆盖或暗示 Polish `execution_target`。Polish question / feedback execution target 只能由 backend authority 产生，并在 `ExecutionSnapshot` 中冻结；LLM 只消费 snapshot 中允许的 refs 和 output schema。
- `decision_ref` 如进入 Prompt trace 或 validation metadata，只能作为 trace association，不得被 Prompt、provider 或 model output 解释为幂等键、恢复键、授权 token 或可执行命令。
- `EvidenceRef` 应能回溯到题目、回答、点评、评分解释、RAG 检索证据、用户确认、面试官反馈或生成时版本 / 快照。
- `TraceRef` 应能回溯到检索、Context Assembly、LLM request、LLM response、Output Schema 校验、Validation、Low Confidence classification、Failure Handling 和 audit event。
- Persistence 语义只定义业务交接和状态；物理表、ORM、DDL、索引和 migration 由后续实现承接。

## 9. Contract 目录总览

本阶段只建立 contract catalog，不填充完整 Prompt 文案。

### 9.1 共享 Contract（Shared Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-SHARED-001` | Context Assembly | 统一上下文装配 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-002` | Retrieval Planning | 决定检索来源与裁剪策略 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-003` | Output Validation | 结构化与业务语义校验 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-004` | Low Confidence Classification | 低置信度分类 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-005` | Evidence Binding | 证据引用绑定 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |
| `P-SHARED-006` | Session Summary Update | 会话摘要更新 | Draft | `prompt-contracts/SHARED_CONTRACTS.md` |

### 9.2 岗位匹配 Contract（Job Match Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-JOBMATCH-001` | Match Analysis | 生成岗位匹配分析 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |
| `P-JOBMATCH-002` | Match Score | 生成 0-100 匹配分与解释 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |
| `P-JOBMATCH-003` | Match / Mismatch / Improvement Points | 生成匹配点、不匹配点、加强点 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |
| `P-JOBMATCH-004` | Weakness Candidate from Job Match | 从岗位匹配分析提炼薄弱项候选 | Draft | `prompt-contracts/JOB_MATCH_CONTRACTS.md` |

### 9.3 打磨模式 Contract（Polish Mode Contracts）

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

#### 9.3.1 打磨进展树运行时 LLM task_type 登记

以下 task_type 是 `P-POLISH-001` 打磨主题规划链路下的运行时拆分，不新增新的 contract ID；`polish_progress_quality_first_menu` 是 canonical Progress Tree generator，也是唯一 active initial Progress Tree 生成链路。

| task_type | prompt version | schema id | 输入上下文 | 输出 | 失败状态 |
|---|---|---|---|---|---|
| `polish_progress_quality_first_menu` | `polish_progress_quality_first_menu_prompt_v1` | `polish_progress_quality_first_menu_v1` | 完整简历 Markdown、完整 JD payload、match context、topic / subtopic、quality rules | canonical quality-first initial `ProgressTreePlan`、initial `ProgressTreeState`、`deferred_candidates` metadata；LLM `status` 只能输出 `success` 或 `partial` | `insufficient_context`、`failed` |
| `polish_progress_tree_state` | `polish_progress_tree_state_prompt_v1` | `llm_progress_tree_state_v1` | existing plan、existing state、`selected_evidence_chunks`、`dropped_context_summary`、`match_context_summary`、`turns_summary` | refreshed `ProgressTreeState`，状态更新引用 evidence / question / answer / score / missing point | `refresh_failed` |

治理约束：provider adapter 只负责通用 JSON transport 和错误处理；进展树业务 prompt、schema id 和 prompt version 由 Polish prompt builder / contract 管理。不得保留替代 initial generator path 或生成侧兼容分支。岗位名、公司名、简历名、binding label 只作为 `context_metadata` 或展示信息，不能替代完整简历、完整 JD 和 match context。状态刷新不得重建 plan nodes，不得删除已有 `node_ref`，`current_priority` 必须引用现有 plan 中的节点。LLM 输出中的 `metadata`、`generated_at`、`model_name`、`session_id`、`job_id`、`resume_id` 不进入可信业务 metadata。

进展树上下文使用 RAG-lite / deterministic evidence chunking，不等于完整向量 RAG。当前不引入 embedding provider、不调用真实 embedding、不引入向量数据库，也不持久化 chunk 索引；后续可以在不改变 `P-POLISH-001` contract ID 的前提下升级为可持久化 evidence chunks、向量检索或 UI evidence drill-down。进入 prompt 的 chunk 必须有稳定 `chunk_id`，推荐格式包括 `job_requirement_001`、`job_responsibility_001`、`resume_project_001`、`resume_skill_001`、`match_gap_001`、`match_focus_001`、`turn_feedback_001`。`source_type` 至少覆盖 `job_responsibility`、`job_requirement`、`job_other_note`、`resume_summary`、`resume_skill`、`resume_project`、`resume_work_experience`、`resume_education`、`match_gap`、`match_focus`、`match_suggested_question`、`turn_question`、`turn_answer`、`turn_feedback`、`asset_summary` 和 `weakness`。

### 9.4 压力面模式 Contract（Pressure Mode Contracts）

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

`PRESSURE_MODE_SPEC.md` 是 `P-PRESSURE-*` 的 mode-level lifecycle、runtime handoff 和 graph boundary 入口；它不新增 contract ID，不替代 `PRESSURE_CONTRACTS.md` 或 `PROMPT_ASSET_SPEC.md`，也不授权 PR2 创建 Pressure graph。

### 9.5 报告 Contract（Report Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-REPORT-001` | Interview Report Generation | 生成面试报告 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |
| `P-REPORT-002` | Section Score Explanation | 生成分项评分解释 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |
| `P-REPORT-003` | Risk and Pass Tendency Wording | 生成风险提示和通过倾向表达 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |
| `P-REPORT-004` | Copyable Content Assembly | 生成可复制内容结构 | Draft | `prompt-contracts/REPORT_CONTRACTS.md` |

### 9.6 复盘 Contract（Review Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-REVIEW-001` | Mock Interview Review | 生成模拟面试复盘 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |
| `P-REVIEW-002` | Real Interview Input Structuring | 结构化真实面试输入 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |
| `P-REVIEW-003` | Real Interview Review | 生成真实面试复盘 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |
| `P-REVIEW-004` | Review Item Extraction | 提炼题级复盘项 | Draft | `prompt-contracts/REVIEW_CONTRACTS.md` |

### 9.7 薄弱项 Contract（Weakness Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-WEAKNESS-001` | Weakness Extraction | 提炼薄弱项候选 | Draft | `prompt-contracts/WEAKNESS_CONTRACTS.md` |
| `P-WEAKNESS-002` | Weakness Merge Suggestion | 生成薄弱项合并建议 | Draft | `prompt-contracts/WEAKNESS_CONTRACTS.md` |
| `P-WEAKNESS-003` | Weakness Severity Assessment | 判断薄弱项严重度 | Draft | `prompt-contracts/WEAKNESS_CONTRACTS.md` |
| `P-WEAKNESS-004` | Weakness Status Update Suggestion | 生成状态更新建议 | Draft | `prompt-contracts/WEAKNESS_CONTRACTS.md` |

### 9.8 资产 Contract（Asset Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-ASSET-001` | Asset Candidate Extraction | 提炼资产候选 | Draft | `prompt-contracts/ASSET_CONTRACTS.md` |
| `P-ASSET-002` | Asset Quality Hint | 生成资产质量提示 | Draft | `prompt-contracts/ASSET_CONTRACTS.md` |
| `P-ASSET-003` | Asset Version Suggestion | 生成资产版本更新建议 | Draft | `prompt-contracts/ASSET_CONTRACTS.md` |

### 9.9 训练 Contract（Training Contracts）

| Contract ID | 名称 | 目标 | 状态 | 子文档 |
|---|---|---|---|---|
| `P-TRAINING-001` | Training Recommendation | 生成训练建议 | Draft | `prompt-contracts/TRAINING_CONTRACTS.md` |
| `P-TRAINING-002` | Training Priority Ranking | 训练建议排序 | Draft | `prompt-contracts/TRAINING_CONTRACTS.md` |
| `P-TRAINING-003` | Training Result Review | 训练结果复盘 | Draft | `prompt-contracts/TRAINING_CONTRACTS.md` |

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
| `prompt-contracts/WEAKNESS_CONTRACTS.md` | `P-WEAKNESS-*` | Draft | Weakness 001-004 细则 |
| `prompt-contracts/ASSET_CONTRACTS.md` | `P-ASSET-*` | Draft | Asset 001-003 细则 |
| `prompt-contracts/TRAINING_CONTRACTS.md` | `P-TRAINING-*` | Draft | Training 001-003 细则 |

## 11. 单个 Contract Stub 模板

后续填充 contract 时复制以下结构。模板只写字段结构，不写具体 Prompt 文案。

```markdown
### <Contract ID> <名称（Name）>

- Contract ID：
- 名称（Name）：
- 模式（Mode）：
- 触发条件（Trigger）：
- 目标（Goal）：
- 必需输入（Required Inputs）：
- 可选输入（Optional Inputs）：
- 检索来源（Retrieval Sources）：
- 上下文装配（Context Assembly）：
- 排除输入（Excluded Inputs）：
- 输出 Schema（Output Schema）：
- 校验规则（Validation Rules）：
- 低置信度规则（Low Confidence Rules）：
- 证据要求（Evidence Requirements）：
- Trace 要求（Trace Requirements）：
- 持久化目标（Persistence Targets）：
- 用户确认要求（User Confirmation Requirement）：
- 重试 / 兜底（Retry / Fallback）：
- API 状态映射（API State Mapping）：
- 安全说明（Security Notes）：
- 测试策略（Test Strategy）：
- 开放问题（Open Questions）：
```

## 12. 当前 Draft 覆盖状态与后续收口路径

当前已将 Shared、Job Match、Polish、Pressure、Report、Review、Weakness、Asset、Training 全部 contract domain 填充为 Draft。主 catalog 中已登记的 48 个 `P-*` contract 均为 Draft，详细正文由 `prompt-contracts/*.md` 承载；后续不应继续重复填充这些 contract，也不应新增未登记的 Prompt contract ID。

下一步应从 contract 填充转入以下收口路径：

1. 以 `APPLICATION_FLOW_SPEC.md` 对齐 P-* contract 的运行编排、LLM call plan 和 persistence handoff。
2. 以 `SCORING_SPEC.md` / `SEMANTICS_GLOSSARY.md` 对齐评分、低置信度和状态枚举。
3. 以 `SKILL_MODEL_SPEC.md` 对齐跨 Job Match、Polish、Pressure、Report、Review、Weakness、Asset、Training 的 Skill taxonomy、SkillEvidence、SkillAssessment、SkillGap 和 SkillProgress 引用；不得新增未登记 `P-*` contract ID。
4. 以 `PROMPT_ASSET_SPEC.md` / `PROMPT_EVALUATION_SPEC.md` 对齐 Production Prompt Asset、Runtime Prompt Bundle、Prompt Evaluation Fixture、Golden Fixture、Counterexample、Prompt Regression Suite 和 Model Comparison Policy。
5. 以 `API_SPEC.md` / `DATA_MODEL.md` / `PERSISTENCE_MODEL.md` 做跨文档回归门禁。
6. `AIFI-PROMPT-001` 关闭前置检查。

`AIFI-PROMPT-001` 当前仍不自动 DONE；跨文档证据已在本轮转入 `AR-F4-FULL-001` 处置表，后续进入 verification，而不是继续保留阻断式 Prompt UNKNOWN。

## 13. F4 Prompt 待决策项处置表

以下条目保留原待决策主题作为审计追踪，但不再表示 M4 阻断。评分、通过倾向、风险提示、API handoff、低置信度、source unavailable、validation failed、candidate / formal object 和 copy boundary 已由当前 active docs 冻结；剩余复杂算法或 provider 选择统一为 deferred_non_blocking。

| 主题 | 分类 | F4 处置结论 | 后续承接 |
|---|---|---|---|
| 评分、权重、阈值、通过倾向、风险提示、可信度和免责声明 | already_closed_by_recent_remediation | `PROMPT_SPEC.md` §7.2 和 scoring / report contracts 已冻结 0-100 产品刻度、rubric / rule version、分档倾向、风险字段、低置信度降级、版本追踪、免责声明和禁止精确概率边界；score type、默认维度、权重、公式、缺失维度处理和 F7 scoring fixture 以 `SCORING_SPEC.md` 为 canonical。 | `SCORING_SPEC.md`; F7 scoring / risk fixture |
| Prompt contract 输出状态、低置信度、source unavailable、validation failed | must_close_in_F4 | Shared failure signals、source availability、Output Validation、Low Confidence、Evidence Binding、Trace / Persistence 已冻结；业务 contract 必须复用 `status`、`validation_result_ref`、`low_confidence_flags`、`evidence_refs` 和 `trace_refs`。 | `P-SHARED-003` / `P-SHARED-004` / `P-SHARED-005`；API response envelope |
| candidate / suggestion / confirmation / formal object 边界 | must_close_in_F4 | AI 输出只能进入 candidate、draft、suggestion、validation result、trace 或 low confidence；正式 `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation`、`TrainingTask` 需用户确认或显式业务动作。 | `DATA_MODEL.md` §4.3；`API_SPEC.md` §7；Weakness / Asset / Training contracts |
| Skill / Capability Model 引用 | already_closed_by_aifi_arch_007 | Prompt contracts 不新增未登记 ID；Job Match、Polish、Pressure、Report、Review、Weakness、Asset、Training 只通过 `skill_refs[]`、`skill_gap_candidate_refs[]`、`skill_evidence_refs[]`、`skill_assessment_candidate_refs[]` 等字段族引用 `SKILL_MODEL_SPEC.md` 冻结的 taxonomy 和 mapping。 | `SKILL_MODEL_SPEC.md`; F7 skill fixture |
| Prompt Asset / Evaluation 设计 | already_closed_by_aifi_prompt_002 | Production Prompt Asset registry、Prompt Evaluation Fixture、Golden Fixture、Counterexample、Prompt Regression Suite、Model Comparison Policy、redaction / rollback 和 LLM trace 关系已冻结；runtime builder 必须映射到 asset registry，fake provider 不再承载业务真相。 | `PROMPT_ASSET_SPEC.md`; `PROMPT_EVALUATION_SPEC.md`; PR5-PR8 prompt migration fixture |
| Prompt 输入最小化、system prompt、provider payload、隐藏评分规则 | must_close_in_F4 | Context Assembly 和 Security 边界禁止前端、日志、trace、copy content 或 API response 暴露 system prompt、Prompt 模板、completion、provider payload、密钥、隐藏评分规则或内部校准细节。 | `SECURITY_PRIVACY.md` §9 / §17.1 / §21；`API_SPEC.md` §8 |
| 题目推荐、压力面题量 / 节奏、连续追问深度、同题结束阈值 | deferred_non_blocking | MVP contract 已冻结输入、输出、状态、证据、trace、低置信度和用户动作边界；排序、强度、题量、追问深度和结束阈值为策略优化，不阻断 M4。 | `POLISH_CONTRACTS.md` / `PRESSURE_CONTRACTS.md`; `AR-F4-FULL-005` |
| 复盘切分、题级复盘合并、跨复盘聚合 | deferred_non_blocking | Review contracts 已冻结模拟 / 真实复盘输入、可信度、完整度、ReviewItem、证据和候选回流边界；复杂合并与最终 UX 展示后置。 | `REVIEW_CONTRACTS.md`; F7 review fixture |
| 薄弱项合并、严重度、状态流转、自动消减 | deferred_non_blocking | Weakness contracts 已冻结候选、合并建议、严重度提示、状态更新建议、用户确认和不得自动改正式 Weakness 的边界；复杂算法后置。 | `WEAKNESS_CONTRACTS.md`; Training 后续优化 |
| 资产质量、资产合并、版本替代、可复用评分 | deferred_non_blocking | Asset contracts 已冻结资产候选、质量提示、版本建议、用户确认和不得自动发布 `AssetVersion` 的边界；复杂质量算法、归档策略和去重后置。 | `ASSET_CONTRACTS.md`; Asset / F7 fixture |
| 训练优先级、训练结果评估、弱项自动消减、自动训练任务 | deferred_non_blocking | Training contracts 已冻结训练建议、排序 hint、结果复盘、候选 / 建议回流和显式训练任务启动边界；算法和自动化后置。 | `TRAINING_CONTRACTS.md`; Training 后续优化 |
| 上下文预算具体数值、模型 provider、模型参数、RAG 索引、embedding、向量库 | deferred_non_blocking | Contract 已冻结 provider-independent 的上下文层级、裁剪、source availability、trace / evidence、validation 和 fallback 语义；具体数值和技术选型属于 F5 配置 / 实现，不改变业务 contract。 | F5 实现设计；Security provider review |
| retry / fallback 具体次数和退避参数 | deferred_non_blocking | Contract 与 API 已冻结 retryable / non-retryable 条件、不得扩大上下文、不得记录 raw payload 和低置信度 / manual review 降级语义；次数和退避参数后置。 | `API_SPEC.md` §5；F7 retry fixture |

本节不把 `AIFI-PROMPT-001` 标记为 DONE；只表示 Prompt 侧 `AR-F4-FULL-001` 阻断项已回写为可验证的设计结论或 deferred_non_blocking 后置项。整体 acceptance 仍保持 Pending，等待 verification。

## 14. BMAD feedback-loop Prompt 回写边界

本节登记 2026-06-23 BMAD feedback-loop active docs 回写入口。`_bmad-output/planning-artifacts/PRD.md` 是需求来源；`.omo/plans/bmad-feedback-loop-refactor-planning.md` 是工程规划来源。本文只承接 Prompt contract（提示词契约）与输出边界规划，不写完整 Prompt 文本，不授权 provider 或模型参数实现。

- 后续需要明确 feedback 输出 schema、validation failed 不伪成功、candidate / formal payload 边界、低置信和失败降级的 Prompt 侧约束。
- “基本一致”“评分趋势应上升”“大量失分点”“用户补足失分点”只能先作为 contract expectation（契约期望）和评测需求登记，不得直接写成未确认 prompt magic 或固定判定规则。
- provider payload、raw prompt、completion 原文、隐藏评分规则和内部校准样例不得进入前端、日志、API response 或 copy content。
- C-049 到 C-054 保持 Deferred / Open Question；本文不选择相似题算法、阈值、下一题算法或 retry / fallback 具体参数。

## 15. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-06-23 | 登记 BMAD feedback-loop Prompt 回写边界 | 明确只承接 feedback 输出 schema、validation、candidate/formal 和失败降级规划；不写完整 Prompt 文本，不授权 provider 或模型参数实现 |
| 2026-06-19 | 回写 Polish execution authority Prompt 边界 | 明确 Prompt / LLM / graph / fallback / provider 只能给 recommendation / candidate / validation / trace，不能产生或覆盖 `execution_target`；`decision_ref` 在 Prompt trace 中仍是 trace-only |
| 2026-05-24 | 增加 Pressure Mode mode-level spec 交叉引用 | 将 `P-PRESSURE-*` 的 lifecycle、runtime handoff、graph boundary 和 PR2 hold 交给 `PRESSURE_MODE_SPEC.md`；不新增 contract ID，不替代 Prompt Asset / Evaluation 设计 |
| 2026-05-24 | 补充 Prompt Asset / Evaluation 交叉引用 | 明确 `PROMPT_SPEC.md` 只维护 `P-*` contract registry；Production Prompt Asset、fixture、model comparison、release / rollback 和 runtime builder 映射由 `PROMPT_ASSET_SPEC.md` / `PROMPT_EVALUATION_SPEC.md` 承接 |
| 2026-05-24 | 补充 Skill / Capability Model 交叉引用 | 明确 Prompt contracts 通过字段族引用 `SKILL_MODEL_SPEC.md`，不新增 `P-*` contract ID，不把 Prompt 输出直接 formalize 为 Weakness / Asset / Training 或 Skill 事实 |
| 2026-05-27 | 收敛 Progress Tree active initial generator | 新生成只使用 `polish_progress_quality_first_menu`；该 task_type 是 canonical Progress Tree generator；结构化输出 `status` 统一按 `success` / `partial` 解析 |
| 2026-05-19 | 为打磨进展树登记 RAG-lite evidence chunking | `polish_progress_tree_state` 使用 `selected_evidence_chunks`、`dropped_context_summary`、`match_context_summary` 和 `turns_summary`；节点 evidence 可引用稳定 `evidence_chunk_ids`；明确当前不引入 embedding、向量库或外部检索系统 |
| 2026-05-17 | 增加 scoring / semantics / application flow 交接 | 明确评分细则以 `SCORING_SPEC.md` 为 canonical，Low Confidence / validation / source availability 以 `SEMANTICS_GLOSSARY.md` 为 canonical，P-* contract 运行编排以 `APPLICATION_FLOW_SPEC.md` 为 canonical；不新增 contract ID |
| 2026-05-17 | 修复 `AR-DOCS02-SEM-001` Prompt 校对 / 沉淀目标断链 | 明确低置信校对只能形成 `CandidateCorrection` / `UserCorrectionRef` 并在确认后作为后续输入；Prompt 只能建议沉淀目标，不能静默决定正式 `DepositTarget` 或写入正式对象；不处理 `AR-DOCS02-SEM-002/003`，不进入 implementation |
| 2026-05-17 | 修复 `AR-F4-F8-006` Polish topic / subtopic Prompt 语义 | 明确 `PolishTopicRef` / `PolishSubtopicRef` / `custom_topic_text` 只作为打磨上下文装配与题目生成输入；主题 / 次主题不是正式业务对象；自定义主题文本必须经过 prompt injection 防护；不新增 contract ID，不进入实现 |
| 2026-05-16 | 修复 `AR-F4-FULL-001` Prompt 阻断项 | 将 Prompt 待决策项改为处置表；冻结 contract 状态、failure signals、low confidence、source unavailable、validation、evidence、trace、candidate / formal object 和安全边界；复杂算法、provider、模型参数、RAG 实现和 retry 参数改为 deferred_non_blocking；等待 verification |
| 2026-05-16 | 修复 `AR-F4-FULL-003` Prompt 评分全局边界 | 新增 scoring candidate、rubric / rule version、通过倾向分档、风险提示、低置信度降级、版本字段、免责声明和 MVP 校准策略；适用于评分与报告相关 contract；不写完整 Prompt 文案，不进入实现 |
| 2026-05-16 | 更新阶段性说明 / Draft 覆盖状态 | 说明所有已登记 Prompt contracts 已完成 Draft 覆盖，后续转入 API / DATA / SECURITY / TECH 对齐和回归门禁；不改 contract 状态，不标记 `AIFI-PROMPT-001` DONE |
| 2026-05-16 | 填充 Training Contract 细则 | 将 `P-TRAINING-001` 至 `P-TRAINING-003` 从 Stub 更新为 Draft，补充训练建议、训练建议排序和训练结果复盘 contract；不实现训练执行，不自动创建 TrainingTask，不自动更新正式 Weakness，不自动归档 Asset，不自动发布 AssetVersion |
| 2026-05-16 | 填充 Asset Contract 细则 | 将 `P-ASSET-001` 至 `P-ASSET-003` 从 Stub 更新为 Draft，补充资产候选提炼、资产质量提示和资产版本更新建议 contract；不填充 Training contracts，不自动创建 TrainingRecommendation，不自动归档 Asset，不自动替换、覆盖或发布 AssetVersion |
| 2026-05-16 | 填充 Weakness Contract 细则 | 将 `P-WEAKNESS-001` 至 `P-WEAKNESS-004` 从 Stub 更新为 Draft，补充薄弱项候选提炼、合并建议、严重度提示和状态更新建议 contract；不填充 Asset / Training contracts，不自动创建 TrainingRecommendation，不自动归档 Asset，不自动合并、删除或更新正式 Weakness |
| 2026-05-16 | 填充 Review Contract 细则 | 将 `P-REVIEW-001` 至 `P-REVIEW-004` 从 Stub 更新为 Draft，补充模拟面试复盘、真实面试输入结构化、真实面试复盘和题级复盘项提取 contract；不填充 Weakness / Asset / Training contracts，不生成真实复盘实例，不写正式 Weakness、正式 Asset 或 TrainingRecommendation |
| 2026-05-16 | 填充 Report Contract 细则 | 将 `P-REPORT-001` 至 `P-REPORT-004` 从 Stub 更新为 Draft，补充报告生成、分项评分解释、风险提示与通过倾向、可复制内容组装 contract；不填充 Review / Weakness / Asset / Training contracts，不生成报告实例，不写正式 Weakness、正式 Asset 或 TrainingRecommendation；隐藏评分公式实现细节、复杂分项权重调参和 RAG 实现仍不在该填充轮关闭，后续 `AR-F4-FULL-003` 已另行冻结通过倾向分档、风险提示证据绑定、低置信度降级和禁止精确概率边界 |
| 2026-05-15 | 拆分 contract 子文档 | 主文件保留 canonical registry 和治理规则，详细正文迁移到 `prompt-contracts/*.md`；不改变 contract ID、名称、状态或语义，不填充 Stub contract |
| 2026-05-15 | 填充 Pressure 7B Contract 细则 | 将 `P-PRESSURE-005` 至 `P-PRESSURE-009` 从 Stub 更新为 Draft，补充连续追问生成、节奏控制、结束条件判断、整场评分和报告输入组装 contract；不填充 Report / Review / Weakness / Asset / Training contracts，不生成报告正文，不写正式 Weakness、正式 Asset 或 TrainingRecommendation |
| 2026-05-15 | 填充 Pressure 第一组 Contract 细则 | 将 `P-PRESSURE-001` 至 `P-PRESSURE-004` 从 Stub 更新为 Draft，补充开场策略、首题生成、回答质量判断和追问策略 contract；不填充 `P-PRESSURE-005` 至 `P-PRESSURE-009`，不生成连续追问题目、整场评分、最终报告、正式薄弱项、正式资产或训练建议，不写完整 Prompt 文案 |
| 2026-05-15 | 填充 Polish 6B 回流候选链路 Contract 细则 | 将 `P-POLISH-009` 至 `P-POLISH-011` 从 Stub 更新为 Draft，补充下一轮建议、资产候选和薄弱项候选 contract；不填充 Pressure / Report / Review / Weakness / Asset / Training contracts，不写完整 Prompt 文案 |
| 2026-05-15 | 填充 Polish 第一组 Contract 细则 | 将 `P-POLISH-001` 至 `P-POLISH-004` 从 Stub 更新为 Draft，补充主题规划、题目生成、回答诊断和每轮 0-100 得分 contract；不填充 `P-POLISH-005` 至 `P-POLISH-011`，不生成最终报告、正式薄弱项、正式资产或训练计划，不写完整 Prompt 文案 |
| 2026-05-15 | 填充 Job Match Contract 细则 | 将 `P-JOBMATCH-001` 至 `P-JOBMATCH-004` 从 Stub 更新为 Draft，补充岗位匹配分析总控、0-100 匹配分、匹配 / 不匹配 / 加强点和薄弱项候选 contract；不填充其他业务 contract，不写完整 Prompt 文案 |
| 2026-05-15 | 修复 Shared Contracts 审计阻塞问题 | 拆分 Input Evidence Selection / Output Evidence Binding，补充推荐调用顺序、failure signal enum、source availability 矩阵、Context Assembly 条件输入和安全分区、Retrieval Planning 子阶段，以及 Session Summary MVP 执行策略；不填充业务 contract |
| 2026-05-15 | 填充 Shared Contract 细则 | 将 `P-SHARED-001` 至 `P-SHARED-006` 从 Stub 更新为 Draft，补充上下文装配、检索规划、输出校验、低置信度、证据绑定和会话摘要更新的公共 contract；不填充业务 contract，不写完整 Prompt 文案 |
| 2026-05-15 | 初始化 F4 Prompt / AI 子任务 contract草案 | 创建 AI Task Contract 标准模板、Context Assembly、Retrieval、Output Schema、Validation、Low Confidence、EvidenceRef、TraceRef、Persistence、Failure Handling 和 contract catalog；不写完整 Prompt 文案 |
