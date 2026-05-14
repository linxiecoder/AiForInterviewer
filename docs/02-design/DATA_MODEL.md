---
title: DATA_MODEL
type: design
status: draft-f4-data-model
owner: 技术架构
source_task: AIFI-DATA-001
permalink: ai-for-interviewer/docs/02-design/data-model
---

# DATA_MODEL

## 1. 文档状态与治理边界

- 本文件是 F4 技术设计下的数据模型子文档，承接 `AIFI-DATA-001`。
- 当前版本是初始化版 / 工作草案，用于统一业务对象、数据对象、状态、引用、版本和持久化边界。
- 本文件不是终版数据库 schema，不提供物理表 DDL，不替代 `TECH_DESIGN.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 本文件不关闭任何 `F4_TECH_DESIGN` UNKNOWN，不标记 `AIFI-ARCH-002` 完成。
- 本文件不新增 roadmap、plan-v2、codex-plan、临时任务文档或并行设计入口。
- 本文件不得把 `archive/` 内容作为当前执行依据；历史内容只有进入 active docs 后才能影响本数据模型。

## 2. 输入来源与非目标

### 2.1 输入来源

| 来源 | 本文使用方式 |
|---|---|
| `docs/01-product/PRD.md` | 业务对象、核心数据流、非目标、状态异常、验收标准和 PRD §10 UNKNOWN |
| `docs/02-design/UX_SPEC.md` | 已冻结的用户可见页面、绑定关系入口、内容沉淀确认、低置信度校对、状态与异常 |
| `docs/02-design/TECH_DESIGN.md` | 模块划分、系统分层、LLM 边界、状态域和子文档交接边界 |
| `docs/03-delivery/DELIVERY_PLAN.md` | F4 / M4 阶段边界和不得遗留的技术设计 UNKNOWN 类型 |
| `docs/03-delivery/BACKLOG.md` | `AIFI-DATA-001` 范围和与 `AIFI-ARCH-002`、`AIFI-PROMPT-001`、`AIFI-SEC-001` 的依赖 |

### 2.2 非目标

本文不展开以下内容：

- API endpoint、request / response schema、错误码。
- Prompt 模板、模型选择、LLM 调用参数、上下文裁剪策略。
- 具体评分公式、权重、阈值、校准算法、精确通过概率或面试结果预测。
- 密钥管理、日志脱敏细则、数据保留 / 删除细则。
- UI 布局、组件规范、Figma 设计。
- 文件导出实现。
- 外部材料解析自动生成岗位 / JD。
- 将“项目”升级为独立一级业务对象或一级数据对象。

如某项内容更适合 `API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`，本文只记录交接边界，不在数据模型中展开。

## 3. 数据模型设计原则

1. 采用逻辑数据模型表达，先冻结对象、引用、状态和生命周期，不提前绑定物理数据库实现。
2. 用户、简历、岗位、会话、报告、复盘、资产、薄弱项和训练建议都必须有明确归属，避免跨用户数据串联。
3. 历史结果引用应指向生成时使用的版本或快照，不依赖会被后续编辑覆盖的当前对象。
4. 项目经历只作为简历模块、打磨主题、复盘分析对象或资产来源，不成为顶层业务对象。
5. 反馈回流和内容沉淀必须以用户确认记录为边界，不允许系统静默覆盖资产、薄弱项或后续训练输入。
6. 评分、低置信度和解释结果应以结构化结果对象承载，但公式、阈值和校准方法不在本文冻结。
7. LLM 原始输出、结构化输出和 trace 只作为后端可追踪对象，不成为前端或业务文案的直接事实源。
8. 状态枚举要能支撑前端展示、API 查询、重试、暂停恢复、历史回看和 F7 验收。

## 4. 业务对象到数据对象映射

| 业务对象 | 逻辑数据对象 | 说明 |
|---|---|---|
| 用户 / 账号 / 角色 | `UserAccount`、`RoleAssignment` | 保存账号归属、角色和最小可见性边界；完整鉴权策略交给 `SECURITY_PRIVACY.md` |
| 简历 | `Resume`、`ResumeVersion`、`ResumeModule` | 简历正文以 Markdown 为主；系统识别模块用于定位、分析和引用 |
| 项目经历模块 | `ResumeModule(type=project_experience)` | 作为简历模块存在，可被匹配分析、会话、复盘和资产引用 |
| 岗位 / JD | `Job`、`JobVersion`、`JobStatus` | 岗位来源为用户手动录入；不承接外部材料解析生成岗位 |
| 岗位-简历绑定 | `JobResumeBinding` | 保存岗位、简历、版本和绑定状态，支撑匹配分析和历史回看 |
| 岗位匹配分析 | `JobMatchAnalysis`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`MatchScore`、`EvidenceSummary` | 承载 0-100 匹配分数、解释、证据和薄弱项建议 |
| 模拟面试 | `InterviewSession` | 统一承载打磨模式和压力面模式的公共会话信息 |
| 打磨模式会话 | `PolishSessionDetail` | 承载同题多轮打磨、暂停恢复、下一步建议和内容沉淀入口 |
| 压力面模式会话 | `PressureSessionDetail` | 承载连续追问、节奏状态、中断和报告生成入口 |
| 题目 / 回答 / 点评 | `Question`、`Answer`、`Feedback` | 承载题级问答、点评、参考回答、考点解析和失分点 |
| 评分 / 失分点 / 参考回答 / 考点解析 | `ScoreResult`、`LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation` | 只保存结果与解释，不冻结评分公式 |
| 进展树 | `ProgressTree`、`ProgressNode`、`ProgressPosition` | 支撑多维进展、节点状态、当前位置和暂停恢复 |
| 面试报告 | `InterviewReport`、`ReportSection`、`CopyableContent` | 承载报告分项、可复制内容和低置信度提示 |
| 面试复盘 | `InterviewRetrospective`、`RetrospectiveItem` | 统一承载模拟面试复盘和真实面试复盘 |
| 薄弱项 | `Weakness`、`WeaknessEvidence`、`WeaknessStatusHistory` | 保存薄弱项、来源证据、状态和训练建议关联 |
| 资产 | `Asset`、`AssetVersion`、`AssetCandidate`、`AssetSource` | 保存可复用材料、候选沉淀、来源和版本引用 |
| 训练建议 | `TrainingSuggestion` | 保存建议主题、原因、优先级、来源和适用入口 |
| 反馈回流 / 用户确认 | `FeedbackLoop`、`UserConfirmation` | 保存用户确认、编辑、取消、跳过、写入成功或失败 |
| LLM 输出记录 / trace | `LlmTrace`、`LlmOutputRecord` | 保存最小可追踪信息、结构化输出状态和审计引用 |

## 5. 核心数据对象清单

### 5.1 用户、账号与角色

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `UserAccount` | 账号标识、显示名、账号状态、创建时间、更新时间 | 作为简历、岗位、会话、报告、资产和薄弱项的所有者 |
| `RoleAssignment` | 用户标识、角色、作用范围、状态 | 支撑求职者 / 面试准备用户、管理员 / 内容维护者和项目维护者的最小角色边界 |

本文不定义完整登录、权限矩阵、组织隔离和数据可见性策略；这些内容交给 `SECURITY_PRIVACY.md`。

### 5.2 简历、版本与模块

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Resume` | 所有者、简历名称、目标方向、当前版本、资料状态、创建 / 更新时间 | 简历是岗位匹配、模拟面试和复盘的基础输入，不承载资产库材料、复盘结论、打磨记录或薄弱项 |
| `ResumeVersion` | 简历标识、版本号或版本序列、Markdown 正文、摘要、来源、创建时间、创建原因 | 匹配分析、会话、报告和复盘应引用版本，而不是只引用可变的 `Resume` |
| `ResumeModule` | 简历版本、模块类型、标题、正文片段、位置范围、识别状态、证据摘要 | `project_experience` 是模块类型之一，不升级为顶层数据对象 |

简历版本创建触发、版本保留策略和历史引用细节仍为 UNKNOWN，见 §12。

### 5.3 岗位 / JD、版本与状态

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Job` | 所有者、岗位名称、公司、部门、投递状态、当前版本、资料状态、创建 / 更新时间 | 岗位仅来自用户手动录入，不保存外部材料解析来源 |
| `JobVersion` | 岗位标识、版本号或版本序列、岗位职责、岗位要求、其他、创建时间、创建原因 | 匹配分析和历史报告应引用生成时的岗位版本 |
| `JobStatus` | 岗位标识、状态类型、状态值、状态更新时间 | 区分资料状态与投递状态；用户可见枚举以 UX / API 后续契约为准，不重开 F2 UX UNKNOWN |
| `JobResumeBinding` | 岗位、岗位版本、简历、简历版本、绑定状态、绑定 / 解绑时间、是否当前有效 | 支撑岗位详情绑定简历模块、匹配分析生成和历史记录回看 |

岗位版本策略仍为 UNKNOWN，见 §12。

### 5.4 岗位匹配分析

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `JobMatchAnalysis` | 岗位版本、简历版本、绑定关系、分析状态、生成时间、低置信度标记、解释摘要 | 一次分析结果引用固定版本，不能随简历或岗位编辑自动变形 |
| `MatchScore` | 分数类型、0-100 分值、分项或总分、解释、生成来源 | 保存展示刻度和解释，不保存公式，因为公式仍属 `F4_TECH_DESIGN` UNKNOWN |
| `MatchPoint` | 分析标识、标题、说明、证据引用、排序 | 表达匹配点 |
| `MismatchPoint` | 分析标识、标题、说明、证据引用、影响范围、排序 | 表达不匹配点 |
| `ImprovementPoint` | 分析标识、标题、建议动作、关联薄弱项、证据引用 | 表达加强点 |
| `EvidenceSummary` | 来源对象类型、来源版本、片段摘要、置信度提示、可展示性 | 关联解释、证据和低置信度提示 |

匹配分析可以提炼薄弱项，但薄弱项写入应通过 `Weakness` / `FeedbackLoop` 记录，不能隐式覆盖既有薄弱项。

### 5.5 模拟面试会话、题目、回答与反馈

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `InterviewSession` | 所有者、会话名称、模式、岗位版本、简历版本、状态、启动来源、创建 / 更新时间 | 统一承载打磨模式和压力面模式；模式值至少区分 `polish` 与 `pressure` |
| `PolishSessionDetail` | 会话、当前题目、当前节点、同题轮次、暂停恢复快照引用、下一步建议 | 支撑同题多轮回答、暂停恢复和内容沉淀 |
| `PressureSessionDetail` | 会话、当前题目、追问链、节奏状态、中断状态、报告生成状态 | 支撑连续追问、中断和结束后报告 |
| `Question` | 会话、进展节点、题目正文、题目类型、来源上下文、生成状态、生成时间 | 可来源于岗位、简历、薄弱项、资产或进展树节点 |
| `Answer` | 题目、用户、回答正文、回答轮次、提交时间、保存状态 | 支撑打磨模式同题多轮回答和压力面连续问答 |
| `Feedback` | 回答、点评摘要、下一步建议、生成状态、低置信度标记 | 聚合评分、失分点、参考回答和考点解析 |
| `ScoreResult` | 关联对象、分数类型、0-100 分值、分项名称、解释、生成来源 | 可关联匹配分析、回答反馈、报告或复盘 |
| `LossPoint` | 关联反馈或报告、失分说明、证据、建议动作 | 可转化为薄弱项候选 |
| `ReferenceAnswer` | 关联题目或反馈、参考回答正文、适用场景、与失分点对应关系 | 仅保存结果，不定义 Prompt 模板 |
| `KnowledgePointExplanation` | 关联题目或反馈、考点、解析、技术原理扩展 | 支撑打磨反馈和报告展示 |

打磨模式暂停恢复需要保存的字段和引用仍为 UNKNOWN，见 §12。

### 5.6 进展树

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `ProgressTree` | 会话、整体进度、生成来源、状态、更新时间 | 打磨模式和压力面模式都应具备进展树 |
| `ProgressNode` | 进展树、父节点、节点类型、标题、状态、排序、完成度、来源证据 | 节点可表达技术点、项目经历、能力项、自我介绍、软技能、行为面、薄弱项、题目或训练主题 |
| `ProgressPosition` | 会话、当前节点、当前题目、当前位置更新时间、恢复状态 | 支撑当前位置展示和暂停恢复 |

进展树数据结构、节点状态全集和更新触发仍为 UNKNOWN，见 §12。

### 5.7 面试报告、复盘与可复制内容

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `InterviewReport` | 会话、报告状态、总体评分、低置信度标记、生成时间、可复制内容引用 | 来源于打磨阶段性完成或压力面结束 |
| `ReportSection` | 报告、分项类型、标题、正文、分项评分、排序 | 承载表现总结、主要失分点、具体建议、参考回答、考点解析、技术原理扩展、薄弱项和训练方向 |
| `CopyableContent` | 报告、可复制范围、内容片段、生成状态 | 只支撑页面复制，不生成文件 |
| `InterviewRetrospective` | 复盘类型、关联会话或真实面试输入、岗位版本、简历版本、状态、低置信度标记 | 统一承载模拟面试复盘和真实面试复盘 |
| `RetrospectiveItem` | 复盘、题目摘要、回答摘要、表现、失分点、建议、证据 | 支撑题级复盘、薄弱项提炼和训练建议 |

复盘材料切分规则、报告与复盘合并展示规则属于 F4 跨文档设计；本文只保留数据承载位置，不关闭 UNKNOWN。

### 5.8 薄弱项、资产、训练建议与回流

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Weakness` | 所有者、主题、严重程度、当前状态、关联岗位、关联简历、更新时间 | 来源于匹配分析、报告、复盘或打磨反馈 |
| `WeaknessEvidence` | 薄弱项、来源对象、来源版本、证据摘要、置信度提示 | 支撑来源可见和历史追溯 |
| `WeaknessStatusHistory` | 薄弱项、前后状态、变更原因、触发来源、变更时间 | 支撑生命周期审计 |
| `Asset` | 所有者、资产标题、资产类型、当前版本、状态、可用场景、更新时间 | 资产库独立于简历 |
| `AssetVersion` | 资产、版本号或版本序列、正文、摘要、质量提示、创建原因、来源 | 历史会话和报告引用资产版本 |
| `AssetCandidate` | 来源对象、候选内容、目标资产、候选状态、用户编辑内容 | 内容沉淀确认前的候选态 |
| `AssetSource` | 资产或候选、来源类型、来源版本、证据摘要 | 保存来源与回流关联 |
| `TrainingSuggestion` | 建议主题、原因、优先级、适用入口、来源证据、状态 | 可指向打磨模式、压力面模式、资产补充或后续复盘 |
| `FeedbackLoop` | 来源对象、目标集合、总体状态、创建时间、完成时间 | 表达内容沉淀确认流程 |
| `UserConfirmation` | 回流记录、目标对象、确认动作、编辑后内容、目标级状态、失败原因 | 保存确认、编辑、取消、跳过、写入中、写入成功和写入失败 |

资产版本、合并、质量判断、薄弱项合并和自动消减规则仍为 UNKNOWN，见 §12。

### 5.9 LLM 输出记录与 trace

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `LlmTrace` | 调用场景、关联业务对象、请求时间、状态、错误摘要、调用方 | 保存最小可追踪链路；密钥和脱敏规则交给 `SECURITY_PRIVACY.md` |
| `LlmOutputRecord` | trace、原始输出引用、结构化输出、校验状态、低置信度标记、可用片段 | 原始输出和结构化输出保存边界仍需 F4 进一步确定 |

前端不得直接消费 LLM 原始输出；业务对象只引用通过校验的结构化结果或人工确认后的结果。

## 6. 对象关系与引用规则

1. 所有用户业务数据必须通过 `UserAccount` 或后续安全文档定义的所有权边界归属。
2. `JobMatchAnalysis`、`InterviewSession`、`InterviewReport`、`InterviewRetrospective`、`WeaknessEvidence` 和 `AssetSource` 应引用生成时的 `ResumeVersion`、`JobVersion` 或具体来源对象版本。
3. `JobResumeBinding` 保存绑定关系本身；解除绑定不得破坏历史报告、复盘、匹配分析或会话的可回看性。
4. `ResumeModule(type=project_experience)` 可以被题目、反馈、复盘、资产和证据引用，但不作为一级数据对象独立管理。
5. `InterviewSession` 是题目、回答、反馈、进展树和报告的聚合根；打磨模式和压力面模式只在模式详情上分化。
6. `InterviewReport` 可以进入 `InterviewRetrospective`、`Weakness`、`TrainingSuggestion` 和 `FeedbackLoop`，但不自动写入资产或薄弱项。
7. `FeedbackLoop` 与 `UserConfirmation` 是回流写入边界；系统建议必须先成为候选或确认记录，再进入资产、薄弱项、训练建议或后续模拟面试输入。
8. `LlmTrace` 与 `LlmOutputRecord` 只提供追踪、校验和审计引用，不替代业务结果对象。

## 7. 状态枚举与状态流

本节给出逻辑状态域，具体 API 返回值、错误码和前端文案由 `API_SPEC.md` 承接。

| 对象域 | 建议状态域 | 基本状态流 |
|---|---|---|
| 简历资料状态 | `draft`、`available`、`needs_supplement`、`archived`、`deleted` | 草稿 -> 可用；可用 -> 需补充；可用 / 需补充 -> 废弃或删除候选 |
| 简历模块识别状态 | `pending`、`recognized`、`failed`、`partial` | 待识别 -> 已识别 / 失败 / 部分可用 |
| 岗位资料状态 | `draft`、`available`、`needs_binding`、`needs_supplement`、`archived` | 草稿 -> 可用；可用 -> 待绑定 / 需补充；可用 -> 废弃 |
| 岗位投递状态 | `user_defined` 或后续枚举 | F2 已冻结用户可见投递状态入口；具体落库枚举由 API 契约固化 |
| 绑定关系状态 | `active`、`unbinding`、`unbound`、`failed` | 绑定中 -> 已绑定；解绑中 -> 已解除；失败后保留原关系 |
| 生成任务状态 | `not_generated`、`generating`、`generated`、`failed`、`low_confidence`、`partial` | 未生成 -> 生成中 -> 已生成 / 失败 / 低置信度 / 部分可用 |
| 会话状态 | `not_started`、`in_progress`、`paused`、`completed`、`interrupted`、`failed` | 未开始 -> 进行中 -> 暂停 / 完成 / 中断 / 失败 |
| 题目状态 | `draft`、`generated`、`answered`、`skipped`、`failed` | 草稿或生成中 -> 已生成 -> 已回答 / 跳过 |
| 回答状态 | `draft`、`submitted`、`saved`、`invalid` | 草稿 -> 已提交 -> 已保存；异常时标记无效 |
| 反馈状态 | `generating`、`available`、`failed`、`low_confidence`、`partial` | 生成中 -> 可用 / 失败 / 低置信度 / 部分可用 |
| 进展节点状态 | `not_started`、`in_progress`、`completed`、`suggested`、`paused`、`blocked` | 未开始 -> 进行中 -> 已完成；可被建议、暂停或阻塞 |
| 报告状态 | `not_generated`、`generating`、`available`、`failed`、`low_confidence` | 未生成 -> 生成中 -> 可查看 / 失败 / 低置信度 |
| 复盘状态 | `not_generated`、`generating`、`needs_user_review`、`available`、`failed`、`low_confidence` | 未生成 -> 生成中 -> 待校对 / 可用 / 失败 |
| 薄弱项状态 | `candidate`、`active`、`low_priority`、`ignored`、`resolved_candidate`、`resolved`、`reopened` | 候选 -> 活跃；活跃 -> 低优先级 / 忽略 / 解决候选 / 已解决；可再次暴露 |
| 资产状态 | `candidate`、`confirmed`、`archived`、`superseded`、`disabled`、`failed` | 候选 -> 已确认；已确认 -> 已归档 / 被替代 / 禁用 |
| 内容沉淀目标状态 | `not_confirmed`、`confirmed`、`cancelled`、`skipped`、`writing`、`written`、`failed`、`disabled` | 未确认 -> 已确认 / 取消 / 跳过；已确认 -> 写入中 -> 写入成功 / 失败 |
| LLM 输出状态 | `validated`、`validation_failed`、`low_confidence`、`partial`、`unusable` | 输出后经校验进入可用、失败、低置信度、部分可用或不可用 |

## 8. 版本策略与历史引用

### 8.1 当前可冻结原则

- 简历、岗位和资产都需要版本对象，避免历史分析结果引用被当前编辑覆盖。
- 匹配分析、会话、报告、复盘、薄弱项证据和资产来源都应保存生成时引用的版本。
- 版本引用应保留到足以支持历史报告和复盘回看。
- 用户编辑当前简历或岗位，不应隐式重算历史匹配分析、报告或复盘。
- 内容沉淀写入资产时，默认先形成 `AssetCandidate` 或 `FeedbackLoop` 记录，再由用户确认产生或更新 `AssetVersion`。

### 8.2 仍未冻结的版本决策

- 简历版本创建触发、命名、保留和回滚策略仍为 UNKNOWN。
- 岗位版本创建触发、投递状态是否进入版本正文仍为 UNKNOWN。
- 项目经历表达打磨结果是否形成独立表达版本、如何回指简历模块仍为 UNKNOWN。
- 资产版本、合并、替代、质量判断和回滚策略仍为 UNKNOWN。

## 9. 回流、资产、薄弱项生命周期

### 9.1 回流生命周期

1. 系统从报告、复盘、薄弱项或打磨反馈中生成可沉淀内容。
2. 可沉淀内容进入 `AssetCandidate`、`Weakness` 候选或 `TrainingSuggestion` 候选。
3. 系统创建 `FeedbackLoop`，并为每个目标创建 `UserConfirmation`。
4. 用户确认、编辑、取消、跳过或重试。
5. 只有目标级状态为已确认且写入成功时，才更新资产、薄弱项、训练建议或后续模拟面试输入。
6. 写入失败必须保留来源、候选内容、失败原因和重试状态。

### 9.2 资产生命周期

- `candidate`：系统建议沉淀，但用户尚未确认。
- `confirmed`：用户确认后进入资产库，可作为后续模拟面试增强输入。
- `superseded`：被新版本或合并结果替代。
- `archived`：用户不再使用，但历史引用可回看。
- `disabled`：因来源不可用、质量不足或安全边界不可用。

资产合并、质量判断、重复检测和版本替代规则仍为 UNKNOWN。

### 9.3 薄弱项生命周期

- `candidate`：系统从匹配分析、报告、复盘或反馈中识别出的候选。
- `active`：用户或系统确认后进入薄弱项列表，可用于训练和出题。
- `low_priority`：仍存在但优先级降低。
- `ignored`：用户明确忽略。
- `resolved_candidate`：系统建议已改善，但尚未最终关闭。
- `resolved`：确认已解决。
- `reopened`：后续证据再次暴露。

薄弱项合并、状态流转、生命周期和是否自动消减仍为 UNKNOWN。

## 10. 评分、低置信度与可解释结果的数据承载边界

- `ScoreResult` 只保存 0-100 展示分值、分数类型、关联对象、分项名称和解释摘要。
- 本文不定义评分公式、权重、阈值、校准方法或通过概率。
- 低置信度应作为结果对象的状态或标记保存，并关联触发原因、影响范围和可校对入口。
- `EvidenceSummary` 保存可展示证据摘要，原始输入片段、隐私字段和日志脱敏边界交给 `SECURITY_PRIVACY.md`。
- 匹配分析、面试报告、复盘和反馈卡片可以引用证据摘要、评分结果和低置信度标记。
- 用户校对低置信度结果时，应产生 `UserConfirmation` 或后续 API 定义的校对记录，不能只覆盖原始结果。
- LLM 原始输出和结构化输出保存边界仍为 UNKNOWN；前端只接收通过校验的可展示结果或低置信度 / 部分可用状态。

## 11. 持久化边界与逻辑 schema 草案

### 11.1 持久化边界

- 前端不保存业务真相，不直接读取数据库，不直接调用 LLM。
- 后端持久化层负责保存用户数据、版本、会话、报告、复盘、资产、薄弱项、训练建议、回流确认和最小 trace。
- `SECURITY_PRIVACY.md` 负责定义隐私字段、日志脱敏、密钥、权限、保留和删除策略。
- `API_SPEC.md` 负责定义具体资源路径、请求响应结构、错误语义和异步任务查询。
- `PROMPT_SPEC.md` 负责定义 Prompt 输入输出、模型调用、结构化校验和低置信度判定。

### 11.2 逻辑 schema 草案

以下是逻辑对象分组，不是物理表 DDL。

| 分组 | 逻辑对象 |
|---|---|
| 身份与归属 | `UserAccount`、`RoleAssignment` |
| 简历 | `Resume`、`ResumeVersion`、`ResumeModule` |
| 岗位 | `Job`、`JobVersion`、`JobStatus`、`JobResumeBinding` |
| 匹配分析 | `JobMatchAnalysis`、`MatchScore`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`EvidenceSummary` |
| 模拟面试 | `InterviewSession`、`PolishSessionDetail`、`PressureSessionDetail`、`Question`、`Answer`、`Feedback` |
| 评分与解释 | `ScoreResult`、`LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation` |
| 进展 | `ProgressTree`、`ProgressNode`、`ProgressPosition` |
| 报告 | `InterviewReport`、`ReportSection`、`CopyableContent` |
| 复盘 | `InterviewRetrospective`、`RetrospectiveItem` |
| 薄弱项 | `Weakness`、`WeaknessEvidence`、`WeaknessStatusHistory` |
| 资产 | `Asset`、`AssetVersion`、`AssetCandidate`、`AssetSource` |
| 训练与回流 | `TrainingSuggestion`、`FeedbackLoop`、`UserConfirmation` |
| LLM 追踪 | `LlmTrace`、`LlmOutputRecord` |

## 12. UNKNOWN / 待决策项

本节只登记数据模型相关待决策项，不关闭 PRD §10 或 `TECH_DESIGN.md` 中的 `F4_TECH_DESIGN` UNKNOWN。

| 编号 | 待决策项 | 来源 | 本文当前边界 |
|---|---|---|---|
| DM-UNK-001 | 简历版本策略 | OQ-F1-002 | 已确认需要 `ResumeVersion`，未冻结创建触发、保留、回滚和历史引用细则 |
| DM-UNK-002 | 岗位版本策略 | OQ-F1-004 | 已确认需要 `JobVersion`，未冻结字段范围、投递状态是否入版本和重算规则 |
| DM-UNK-003 | 项目经历表达版本策略 | OQ-F1-013 | 已确认项目经历仍是简历模块，未冻结打磨表达版本如何引用模块 |
| DM-UNK-004 | 资产版本、合并与质量判断 | OQ-F1-018、OQ-F1-019 | 已确认 `AssetVersion`、`AssetCandidate` 和 `AssetSource`，未冻结合并、替代、去重和质量规则 |
| DM-UNK-005 | 打磨模式暂停恢复字段与引用 | OQ-F1-025 | 已列出会话、题目、回答、反馈、进展位置和下一步建议，未冻结最小恢复快照 |
| DM-UNK-006 | 进展树数据结构、节点状态和更新触发 | OQ-F1-030 | 已确认 `ProgressTree` / `ProgressNode` / `ProgressPosition`，未冻结节点全集、状态机和触发规则 |
| DM-UNK-007 | 薄弱项合并、状态流转、生命周期和自动消减 | OQ-F1-038、OQ-F1-039 | 已给出候选生命周期，不冻结合并算法、关闭条件或自动消减 |
| DM-UNK-008 | 匹配分析和报告评分结果如何存储 | OQ-F1-009、OQ-F1-011、OQ-F1-032 | 已确认 `ScoreResult` 承载 0-100 展示值和解释，不冻结公式、权重、阈值和校准 |
| DM-UNK-009 | 解释、证据和低置信度如何关联 | OQ-F1-011、OQ-F1-040 | 已确认 `EvidenceSummary` 和低置信度标记，不冻结判定规则、可信度说明和免责声明 |
| DM-UNK-010 | LLM 原始输出、结构化输出、trace 与审计记录保存边界 | TECH_DESIGN §14、§16 | 已确认最小 `LlmTrace` / `LlmOutputRecord`，未冻结原始输出保存范围、保留周期、脱敏和审计策略 |

## 13. 与 API / Prompt / Security 子文档的交接边界

| 子文档 | 本文交接内容 | 本文不展开内容 |
|---|---|---|
| `API_SPEC.md` | 逻辑对象、状态域、引用关系、生成任务状态和历史引用原则 | endpoint、request / response schema、错误码、分页过滤参数、异步任务协议 |
| `PROMPT_SPEC.md` | LLM 输出应落到哪些结构化对象、低置信度和部分可用状态应被持久化 | Prompt 模板、模型选择、模型调用参数、上下文裁剪、评分公式、权重、阈值、校准算法 |
| `SECURITY_PRIVACY.md` | 哪些对象包含用户资料、简历、岗位、回答、报告、复盘、资产和 trace | 密钥管理、权限矩阵、数据可见性、日志脱敏、保留 / 删除细则、隐私字段分级 |
| `TECH_DESIGN.md` | 本文回填数据模型子文档状态和待协同关闭的 UNKNOWN | 顶层架构重写、F4 UNKNOWN 关闭、`AIFI-ARCH-002` 完成判定 |

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-15 | 初始化 F4 数据模型工作草案 | 建立 `AIFI-DATA-001` 的对象、关系、状态、版本、回流、评分和 trace 承载边界；不关闭 `F4_TECH_DESIGN` UNKNOWN |
