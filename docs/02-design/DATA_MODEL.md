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
- 本文件不关闭任何 `F4_TECH_DESIGN` UNKNOWN，不标记 `AIFI-ARCH-002` 完成，也不把 `AIFI-DATA-001` 标记为 DONE。
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
8. RAG / Knowledge Base 只作为 MVP 逻辑对象和外部引用边界，不在本文绑定向量数据库、embedding 模型、索引或物理实现。
9. 真实面试复盘必须显式记录用户输入来源、完整度和可信度，不能假设系统拥有完整真实面试过程。
10. 状态枚举要能支撑前端展示、API 查询、重试、暂停恢复、历史回看和 F7 验收。

## 4. 业务对象到数据对象映射

| 业务对象 | 逻辑数据对象 | 说明 |
|---|---|---|
| 用户 / 账号 / 角色 / 审计 | `UserAccount`、`OwnerRef`、`RoleAssignment`、`RoleScope`、`PermissionBoundary`、`AuditEvent` | 保存账号归属、最小角色范围、关键动作审计和可见性边界；完整鉴权策略交给 `SECURITY_PRIVACY.md` |
| 简历 | `Resume`、`ResumeVersion`、`ResumeModule` | MVP 简历正文来自 Markdown 粘贴 / 手动编辑；系统识别模块用于定位、分析和引用；不要求保存文件原文、MIME、文件名或文件大小 |
| 项目经历模块 | `ResumeModule(type=project_experience)` | 作为简历模块存在，可被匹配分析、会话、复盘和资产引用 |
| 岗位 / JD | `Job`、`JobVersion`、`JobStatus` | 岗位来源为用户手动录入；不承接外部材料解析生成岗位 |
| 岗位-简历绑定 | `JobResumeBinding` | 保存岗位、简历、版本和绑定状态，支撑匹配分析和历史回看 |
| 岗位匹配分析 | `JobMatchAnalysis`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`MatchScore`、`EvidenceSummary` | 承载 0-100 匹配分数、解释、证据和薄弱项建议 |
| 知识库 / RAG | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`KnowledgeEmbeddingRef`、`RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`Citation` / `EvidenceRef`、`RAGContextAssembly` | 只定义检索、证据和上下文组装的逻辑对象，不绑定向量库、embedding 模型或索引实现 |
| 模拟面试 | `InterviewSession` | 统一承载打磨模式和压力面模式的公共会话信息 |
| 打磨模式会话 | `PolishSessionDetail` | 承载同题多轮打磨、暂停恢复、下一步建议和内容沉淀入口 |
| 压力面模式会话 | `PressureSessionDetail` | 承载连续追问、节奏状态、中断和报告生成入口 |
| 题目 / 回答 / 点评 | `Question`、`Answer`、`Feedback` | 承载题级问答、点评、参考回答、考点解析和失分点 |
| 评分规则 / 解释 / 低置信度 | `ScoreRuleSet`、`ScoreRuleVersion`、`ScoreDimension`、`ScoreRubric`、`ScoreResult`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag` | 保存评分规则版本、维度、证据和解释链路，不冻结评分公式、权重或阈值 |
| 失分点 / 参考回答 / 考点解析 | `LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation` | 只保存结果与解释，不冻结 Prompt 模板或评分算法 |
| 进展树 | `ProgressTree`、`ProgressNode`、`ProgressPosition` | 支撑多维进展、节点状态、当前位置和暂停恢复 |
| 面试报告 | `InterviewReport`、`ReportSection`、`CopyableContent` | 承载报告分项、可复制内容和低置信度提示 |
| 面试复盘 | `InterviewRetrospective`、`MockInterviewReview`、`RealInterviewReview`、`RealInterviewInput`、`RealInterviewEvidence`、`ReviewItem`、`ReviewSourceRef` | 区分系统内模拟复盘和用户手动录入的真实面试复盘来源 |
| 薄弱项 | `Weakness`、`WeaknessEvidence`、`WeaknessStatusHistory` | 保存薄弱项、来源证据、状态和训练建议关联 |
| 资产 | `Asset`、`AssetVersion`、`AssetCandidate`、`AssetSource`、`AssetPromotionRecord` | 保存可复用材料、候选沉淀、来源、确认状态和版本引用 |
| 训练建议 / 训练过程 | `TrainingRecommendation`、`TrainingTask`、`TrainingSession`、`TrainingResult` | 保存建议主题、原因、优先级、来源、执行状态和结果 |
| 反馈回流 / 用户确认 | `FeedbackLoop`、`UserConfirmation` | 保存用户确认、编辑、取消、跳过、写入成功或失败 |
| LLM request / response / usage / validation | `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord`、`LlmValidationResult`、`LlmRetentionPolicyRef`、`LlmRedactionRef`、`LlmFailureRecord` | 保存最小可追踪信息、结构化输出状态、用量统计边界、校验和保留 / 脱敏引用 |

### 4.1 统一引用模型

统一引用模型只定义逻辑引用形态，不定义 API 字段命名规范，不定义 request / response schema，也不展开字段全集、类型、长度、DDL、外键或索引。后续 `API_SPEC.md` 可以基于这些逻辑引用对象定义接口字段，但不得改变其语义。

这些引用对象可被 `InterviewReport`、`MockInterviewReview`、`RealInterviewReview`、`ReviewItem`、`ScoreResult`、`WeaknessEvidence`、`TrainingRecommendation`、`AssetCandidate`、`AssetVersion`、`RetrievalEvidence`、`RAGContextAssembly`、`LlmRequestTrace`、`LlmResponseTrace`、`LlmValidationResult` 和 `AuditEvent` 复用。

| 引用对象 | 职责 | 适用对象 | 引用规则 | 后续交接文档 |
|---|---|---|---|---|
| `SourceRef` | 记录业务来源，例如简历、岗位、会话、报告、复盘、知识文档、用户录入或真实面试输入 | 报告、复盘、评分、资产候选、训练建议、RAG / LLM trace 和审计事件 | 按来源类型、来源对象、生成场景和可展示摘要建立逻辑引用；不得只保留当前最新对象名称 | `API_SPEC.md` 定义接口字段，`SECURITY_PRIVACY.md` 定义可见性和脱敏边界 |
| `EvidenceRef` | 记录证据来源，例如题目、回答、点评、评分解释、RAG 检索证据、用户确认或面试官反馈 | `ReviewItem`、`ScoreResult`、`WeaknessEvidence`、`TrainingRecommendation`、`AssetCandidate`、`RetrievalEvidence` | 证据引用应能回溯到证据对象、证据版本或快照、摘要和置信度 / 完整度标记 | `API_SPEC.md` 定义查询和展示字段，`SECURITY_PRIVACY.md` 定义证据片段可展示范围 |
| `VersionRef` | 记录源对象版本，例如 `ResumeVersion`、`JobVersion`、`KnowledgeDocument` version、`AssetVersion`、`ScoreRuleVersion` | 历史报告、复盘、评分、资产候选、RAG evidence、LLM trace | 指向生成时使用的版本；源对象后续编辑不得改写已生成结果 | `API_SPEC.md` 定义版本引用表达，F5 实现冻结具体持久化方式 |
| `SnapshotRef` | 记录生成时快照引用，用于历史报告、复盘、评分和资产候选的稳定回看 | `InterviewReport`、`MockInterviewReview`、`RealInterviewReview`、`ScoreResult`、`AssetCandidate`、`AuditEvent` | 当版本对象不足以稳定回看时，引用生成时的内容快照或快照摘要；不得退化为当前最新对象引用 | `API_SPEC.md` 定义快照读取语义，`SECURITY_PRIVACY.md` 定义快照保留和删除边界 |
| `TraceRef` | 记录 LLM、RAG、校验、审计等过程引用 | `ScoreResult`、`InterviewReport`、`ReviewItem`、`WeaknessEvidence`、`TrainingRecommendation`、`AssetCandidate`、`AuditEvent` | 只表达过程追踪链路，不暴露 provider-specific payload、Prompt 模板或模型调用参数 | `PROMPT_SPEC.md` 定义模型过程边界，`SECURITY_PRIVACY.md` 定义日志和保留边界 |
| `UserConfirmationRef` | 记录用户确认、拒绝、修正、回流确认或资产入库确认 | `AssetCandidate`、`AssetVersion`、`WeaknessEvidence`、`TrainingRecommendation`、`FeedbackLoop`、`AuditEvent` | 系统建议进入正式资产、薄弱项或训练输入前，应保留确认动作、确认状态和编辑结果引用 | `API_SPEC.md` 定义确认流程字段，`SECURITY_PRIVACY.md` 定义确认记录可见性 |
| `OwnerRef` | 记录对象归属、创建者和 MVP 最小 role scope | 用户业务对象、知识文档、资产、报告、复盘、trace、审计事件 | MVP 默认以个人工作台 owner 为主要边界；只表达最小可见性和维护角色范围，不设计复杂权限继承 | `API_SPEC.md` 定义资源 owner 表达，`SECURITY_PRIVACY.md` 定义鉴权和审计边界 |

历史报告、复盘、评分结果和资产候选不能只引用“当前最新简历 / 岗位 / 知识文档 / 评分规则”，必须引用生成时的 `VersionRef` 或 `SnapshotRef`。如果源对象被后续编辑、归档、禁用或删除，历史结果仍保留生成时引用，只额外展示来源当前可用性状态。

### 4.2 逻辑对象分层

本节按职责和实现重量标注逻辑对象，避免后续把所有对象都建成同等重量的持久化表。该分层是逻辑设计分层，不等同于数据库表拆分，也不要求 F5 逐一建表。

#### 4.2.1 按职责分层

| 分层 | 对象 | 说明 |
|---|---|---|
| 一级领域对象 / Domain Entity | `User` / `Account`、`Resume`、`ResumeVersion`、`Job` / `JD`、`JobVersion`、`ResumeJobBinding`、`MatchAnalysis`、`InterviewSession`、`PolishingSession`、`PressureInterviewSession`、`ProgressTree`、`InterviewReport`、`MockInterviewReview`、`RealInterviewReview`、`Weakness`、`TrainingRecommendation`、`TrainingTask` / `TrainingSession`、`Asset`、`AssetVersion`、`AssetCandidate`、`KnowledgeBase`、`KnowledgeDocument`、`LlmRequestTrace` / `LlmResponseTrace`、`AuditEvent` | 具有独立生命周期、状态或跨模块引用价值；其中 `KnowledgeBase` 只是后端逻辑检索边界，不代表产品一级模块 |
| 明细或值对象 / Value Object or Detail Object | `ResumeModule`、`ProjectExperienceModule`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`InterviewQuestion`、`InterviewAnswer`、`Feedback`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`ReviewItem`、`WeaknessEvidence`、`RetrievalEvidence`、`Citation` / `CitationRef`、`TrainingResult`、`AssetPromotionRecord` | 依附于主对象，通常不独立管理生命周期 |
| 引用对象 / Reference Object | `SourceRef`、`EvidenceRef`、`VersionRef`、`TraceRef`、`SnapshotRef`、`UserConfirmationRef`、`OwnerRef`、`RoleScope`、`PermissionBoundary` | 用于跨模块引用、证据追踪、版本追踪、归属、确认和最小权限边界 |
| 延后对象 / Deferred Object | API request / response schema、API endpoint、Prompt 输入输出 schema、Prompt 模板、LLM 调用参数、安全隐私字段细则、retention / deletion 具体策略、物理数据库表、ORM model、DDL、索引、外键、migration | 不在 `DATA_MODEL.md` 展开，交给后续 `API_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 或 F5 实现 |

#### 4.2.2 按实现重量标注

| 对象 | 标注 | 说明 |
|---|---|---|
| `Resume` | `aggregate root` | 具有独立生命周期和主要一致性边界 |
| `ResumeVersion` | `entity` / `snapshot` | 可被历史结果引用，也可作为生成时内容快照边界 |
| `Job` / `JD` | `aggregate root` | 岗位资料的主要一致性边界 |
| `JobVersion` | `entity` / `snapshot` | 支撑匹配、会话和报告的历史引用 |
| `ResumeJobBinding` | `entity` | 保存岗位与简历的绑定状态和历史关系 |
| `MatchAnalysis` | `derived view` / `entity` | 从简历版本、岗位版本和评分解释派生，也可被历史记录引用 |
| `InterviewSession` | `aggregate root` | 题目、回答、反馈、进展树和报告生成的主要一致性边界 |
| `InterviewReport` | `entity` / `snapshot-backed result` | 生成后引用生成时版本和快照，不随后续输入变化自动改写 |
| `MockInterviewReview` | `entity` / `snapshot-backed result` | 来源于系统内会话链路和生成时快照 |
| `RealInterviewReview` | `entity` / `user-input-backed result` | 来源于用户录入和补充材料，需要可信度和完整度标记 |
| `Weakness` | `entity` | 可被训练、报告、复盘和资产候选引用 |
| `TrainingRecommendation` | `derived view` / `entity` | 从薄弱项、评分、复盘和证据派生，可转入训练执行 |
| `TrainingTask` / `TrainingSession` | `entity` | 承载训练执行状态 |
| `Asset` | `aggregate root` | 资产库材料的主要一致性边界 |
| `AssetVersion` | `entity` / `snapshot` | 支撑历史会话、报告和复盘引用 |
| `AssetCandidate` | `candidate` | 候选沉淀对象，需要确认后才能变为正式资产或正式结果 |
| `KnowledgeBase` | `logical boundary` / `aggregate-like backend boundary` | 后端检索边界，不升级为产品一级模块 |
| `KnowledgeDocument` | `entity` | 可被 RAG、评分解释、报告、复盘和训练建议引用 |
| `KnowledgeChunk` | `value object` / `reference` | 依附于知识文档版本，用作检索和证据引用 |
| `RetrievalEvidence` | `reference` | 连接检索结果、知识文档、chunk、版本和命中摘要 |
| `RAGContextAssembly` | `trace` / `derived context` | 记录一次上下文组装过程和来源集合 |
| `LlmRequestTrace` | `trace` | 记录 LLM 请求过程边界 |
| `LlmResponseTrace` | `trace` | 记录 LLM 响应和结构化输出边界 |
| `LlmValidationResult` | `trace` / `validation result` | 记录结构化校验和业务语义校验结果 |
| `AuditEvent` | `trace` | 记录关键动作的审计链路 |
| `SourceRef` / `EvidenceRef` / `VersionRef` / `SnapshotRef` / `TraceRef` / `UserConfirmationRef` / `OwnerRef` | `reference` | 跨对象引用、证据、版本、归属和确认记录 |

## 5. 核心数据对象清单

### 5.1 用户、账号与角色

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `UserAccount` | 账号标识、显示名、账号状态、创建时间、更新时间 | 作为简历、岗位、会话、报告、资产和薄弱项的所有者 |
| `OwnerRef` | 所有者类型、所有者标识、创建者、创建时间 | MVP 默认以用户个人工作台为主要 ownership 边界；用户、简历、岗位、会话、报告、复盘、薄弱项、资产和知识库文档都应有 owner 或创建者引用 |
| `RoleAssignment` | 用户标识、角色、作用范围、状态 | 支撑 `owner`、`user`、`admin-like maintenance` 的最小角色边界 |
| `RoleScope` | 角色、作用对象类型、作用对象标识、有效状态 | 只保留 MVP 需要的个人工作台和维护角色范围，不展开组织、团队、部门空间或资源继承 |
| `PermissionBoundary` | 资源类型、资源标识、owner 引用、允许动作摘要、限制原因 | 表达数据模型层面的最小可见性和操作边界；具体鉴权 API 由 `API_SPEC.md` 承接 |
| `AuditActor` | actor 类型、actor 标识、角色快照、来源 | 记录用户、系统任务或维护动作的执行主体 |
| `AuditTarget` | target 类型、target 标识、target 版本、owner 引用 | 记录被操作对象，支持版本化对象的历史追踪 |
| `AuditEvent` | actor、action、target、timestamp、source、result、risk flag | 只记录关键动作的最小审计字段；日志保留、脱敏和安全细节交给 `SECURITY_PRIVACY.md` |

本文不定义完整登录、权限矩阵、复杂 ACL、企业级多租户、组织隔离和资源继承策略；这些内容交给后续 `API_SPEC.md` / `SECURITY_PRIVACY.md`。

### 5.2 简历、版本与模块

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Resume` | 所有者、简历名称、目标方向、当前版本、资料状态、创建 / 更新时间 | 简历是岗位匹配、模拟面试和复盘的基础输入，不承载资产库材料、复盘结论、打磨记录或薄弱项 |
| `ResumeVersion` | 简历标识、版本号或版本序列、Markdown 正文、摘要、来源（`markdown_paste` / `manual_input`）、创建时间、创建原因 | 匹配分析、会话、报告和复盘应引用版本，而不是只引用可变的 `Resume` |
| `ResumeModule` | 简历版本、模块类型、标题、正文片段、位置范围、识别状态、证据摘要 | `project_experience` 是模块类型之一，不升级为顶层数据对象 |

MVP 不要求保存 `original_file`、`parsed_file`、MIME、文件名或文件大小；`file_upload` / PDF 类来源如未来需要，只能作为 Deferred enum 扩展，不能成为 MVP required path。简历版本创建触发、版本保留策略和历史引用细节仍为 UNKNOWN，见 §12。

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
| `LossPoint` | 关联反馈或报告、失分说明、证据、建议动作 | 可转化为薄弱项候选 |
| `ReferenceAnswer` | 关联题目或反馈、参考回答正文、适用场景、与失分点对应关系 | 仅保存结果，不定义 Prompt 模板 |
| `KnowledgePointExplanation` | 关联题目或反馈、考点、解析、技术原理扩展 | 支撑打磨反馈和报告展示 |

#### 5.5.1 评分规则版本与解释链路

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `ScoreRuleSet` | 规则集标识、适用场景、状态、当前版本、创建 / 更新时间 | 归集匹配分析、回答点评、报告和复盘可引用的评分规则族 |
| `ScoreRuleVersion` | 规则集、版本号、适用阶段、启用状态、创建原因、生效时间 | `ScoreResult` 必须引用生成时使用的评分规则版本 |
| `ScoreDimension` | 规则版本、维度名称、维度说明、适用对象、排序 | 表达评分维度，不定义权重或阈值 |
| `ScoreRubric` | 规则版本、维度、等级或区间说明、解释模板引用 | 保存评分解释需要的 rubric 边界，不冻结具体评分公式 |
| `ScoreResult` | 关联对象、`ScoreRuleVersion`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`VersionRef`、`SnapshotRef`、`TraceRef`、分数类型、0-100 展示值、状态 | 可关联匹配分析、回答反馈、报告、复盘或训练结果；必须能追溯评分规则版本、输入来源版本或快照、证据链、解释链路和相关 LLM validation 结果 |
| `ScoreExplanation` | 评分结果、解释摘要、命中维度、低置信度标记、冲突或不完整标记 | 面试报告、题目点评、弱项识别和训练建议应引用解释对象而不是复制散落文案 |
| `ScoreEvidenceLink` | 评分结果、证据对象、证据版本、片段摘要、证据作用 | 连接题答、报告、复盘、RAG 证据或用户确认记录 |
| `LowConfidenceFlag` | 关联对象、触发原因、影响范围、建议校对入口、状态 | 低置信度、冲突、不完整和失败都应作为状态或风险标记进入数据模型 |

本文只冻结评分规则版本、维度、证据和解释的承载边界，不定义具体评分公式、权重、阈值、校准算法，不承诺精确通过概率或真实面试结果预测。

打磨模式暂停恢复需要保存的字段和引用仍为 UNKNOWN，见 §12。

### 5.6 进展树

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `ProgressTree` | 会话、整体进度、生成来源、状态、更新时间 | 打磨模式和压力面模式都应具备进展树 |
| `ProgressNode` | 进展树、父节点、节点类型、标题、状态、排序、完成度、来源证据 | 节点可表达技术点、项目经历、能力项、自我介绍、软技能、行为面、薄弱项、题目或训练主题 |
| `ProgressPosition` | 会话、当前节点、当前题目、当前位置更新时间、恢复状态 | 支撑当前位置展示和暂停恢复 |

进展树数据结构、节点状态全集和更新触发仍为 UNKNOWN，见 §12。

### 5.7 知识库、RAG 与证据引用

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `KnowledgeBase` | 所有者、名称、用途、状态、当前版本、创建 / 更新时间 | 后端逻辑检索边界，可被岗位、简历、面试会话、报告、复盘、薄弱项和训练建议引用 |
| `KnowledgeDocument` | 知识库、owner / 创建者、文档标题、来源类型、来源版本、状态、更新时间 | 表达用户维护或系统沉淀的知识文档；不承接文件导出能力 |
| `KnowledgeChunk` | 文档、文档版本、chunk 标识、片段摘要、位置范围、状态 | 只作为逻辑片段对象，不指定切分算法、向量索引或物理存储结构 |
| `KnowledgeEmbeddingRef` | chunk、外部 embedding 引用、生成批次、状态、更新时间 | 只保存外部引用边界，不指定向量数据库、embedding 模型或索引实现 |
| `RetrievalQuery` | 查询场景、发起对象、查询摘要、输入版本、创建时间 | 可来源于岗位匹配、出题、点评、报告、复盘、薄弱项训练或资产补充 |
| `RetrievalResult` | 查询、结果状态、命中数量、低置信度标记、命中摘要 | 进入 LLM 上下文前必须保留来源、版本、置信度或命中摘要 |
| `RetrievalEvidence` | 检索结果、知识文档、chunk、来源版本、置信度、命中摘要 | 支撑报告、复盘、评分解释和训练建议的来源追踪 |
| `Citation` / `EvidenceRef` | 目标对象、证据对象、证据版本、可展示摘要、引用位置 | 统一表达报告、复盘、评分解释、弱项和资产中的证据引用 |
| `RAGContextAssembly` | `RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、组装状态、失败或低置信度原因 | 只记录 RAG 上下文组装的数据边界；上下文裁剪和 Prompt 组织交给 `PROMPT_SPEC.md` |

`KnowledgeBase` 是后端逻辑检索边界，不代表新增一级导航、用户可见知识库页面、文件导入能力、文件导出能力或独立产品模块。知识库对象可以引用简历版本、岗位版本、面试会话、报告、复盘、薄弱项和资产来源，但不得反向静默改写这些业务对象。RAG 证据进入报告、复盘、评分解释或训练建议时，必须通过 `Citation` / `EvidenceRef` 或 `ScoreEvidenceLink` 追踪到来源文档、chunk、版本和命中摘要。

### 5.8 面试报告、复盘与可复制内容

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `InterviewReport` | 会话、报告状态、总体评分、低置信度标记、生成时间、可复制内容引用、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、`TraceRef` | 来源于打磨阶段性完成或压力面结束；生成后应引用生成时的 `ResumeVersion` 或简历快照、`JobVersion` 或岗位快照、`InterviewSession` 快照和 `ScoreRuleVersion` |
| `ReportSection` | 报告、分项类型、标题、正文、分项评分、排序 | 承载表现总结、主要失分点、具体建议、参考回答、考点解析、技术原理扩展、薄弱项和训练方向 |
| `CopyableContent` | 报告、可复制范围、内容片段、生成状态 | 只表示页面复制所需的结构化内容边界；不是导出物、不是下载文件、不是批量产物，也不代表 Markdown / PDF / docx 文件生成能力 |
| `InterviewRetrospective` | 复盘类型、关联会话或真实面试输入、岗位版本、简历版本、状态、低置信度标记 | 统一承载模拟面试复盘和真实面试复盘 |
| `MockInterviewReview` | 复盘、会话、报告、题目 / 回答 / 点评引用、评分引用、`VersionRef`、`SnapshotRef`、`TraceRef` | 来源于系统内模拟面试会话、题目、回答、点评、评分、报告和薄弱项；应引用生成时的系统内会话链路版本或快照 |
| `RealInterviewReview` | 复盘、真实面试输入版本、用户补充材料、面试官反馈或结果状态、岗位版本、简历版本、可信度摘要、完整度摘要 | 来源于用户手动录入的真实面试信息，不假设系统拥有完整真实面试过程；必须标注可信度和完整度 |
| `RealInterviewInput` | 所有者、面试时间、公司 / 岗位、问题回忆、回答回忆、面试官反馈、结果状态、补充材料 | 真实面试复盘的主要输入，字段可为空或部分可用 |
| `RealInterviewEvidence` | 真实面试输入、来源类型、内容摘要、可信度、完整度、用户确认状态 | 显式标注输入可信度、完整度和证据来源 |
| `ReviewItem` | 复盘、题目摘要、回答摘要、表现、失分点、建议、证据、来源引用、`TraceRef`、`LowConfidenceFlag` | 支撑题级复盘、薄弱项提炼和训练建议，并可回溯到 RAG / LLM / validation 链路 |
| `ReviewSourceRef` | 复盘或复盘项、来源对象、来源版本、来源类型、置信度 | 区分模拟复盘的系统内证据和真实复盘的用户录入证据 |

模拟复盘主要来源于系统内会话、题目、回答、点评、评分、报告和弱项；真实面试复盘主要来源于用户手动录入的真实面试问题、回答回忆、面试官反馈、结果状态和补充材料。两类复盘都可以沉淀薄弱项、训练建议和资产候选，但来源、完整度和置信度必须分别记录。

复盘材料切分规则、报告与复盘合并展示规则属于 F4 跨文档设计；本文只保留数据承载位置，不关闭 UNKNOWN。

### 5.9 薄弱项、资产、训练建议与回流

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Weakness` | 所有者、主题、严重程度、当前状态、关联岗位、关联简历、更新时间 | 来源于匹配分析、报告、复盘或打磨反馈 |
| `WeaknessEvidence` | 薄弱项、来源对象、来源版本、证据摘要、置信度提示、用户确认状态 | 来源必须可追溯到题答、评分、复盘、RAG 证据或用户确认 |
| `WeaknessStatusHistory` | 薄弱项、前后状态、变更原因、触发来源、变更时间 | 支撑生命周期审计 |
| `Asset` | 所有者、资产标题、资产类型、当前版本、状态、可用场景、更新时间 | 资产库独立于简历 |
| `AssetVersion` | 资产、版本号或版本序列、正文、摘要、质量提示、创建原因、来源、适用岗位 / 简历 / 场景 | 历史会话和报告引用资产版本 |
| `AssetCandidate` | 来源类型、候选内容、目标资产、候选状态、用户编辑内容、确认状态、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、`TraceRef`、`UserConfirmationRef`、适用岗位 / 简历 / 场景引用 | 内容沉淀确认前的候选态；训练建议不能直接等同于资产 |
| `AssetSource` | 资产或候选、来源类型、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、证据摘要 | 保存来源与回流关联 |
| `AssetPromotionRecord` | 候选资产、目标资产、确认方式、确认人或规则、结果、时间 | 资产候选必须经过用户确认或规则确认后才能进入正式资产 |
| `TrainingRecommendation` | 建议主题、原因、优先级、适用入口、来源证据、状态 | 可指向打磨模式、压力面模式、资产补充或后续复盘 |
| `TrainingTask` / `TrainingSession` | 训练建议、关联薄弱项、训练入口、状态、开始 / 完成时间 | 承载从建议到实际训练的执行过程 |
| `TrainingResult` | 训练任务、结果摘要、评分引用、弱项变化、资产候选引用、低置信度标记 | 训练完成后可产生弱项状态变化或资产候选，但不能直接生成正式资产 |
| `FeedbackLoop` | 来源对象、目标集合、总体状态、创建时间、完成时间 | 表达内容沉淀确认流程 |
| `UserConfirmation` | 回流记录、目标对象、确认动作、编辑后内容、目标级状态、失败原因 | 保存确认、编辑、取消、跳过、写入中、写入成功和写入失败 |

资产版本、合并、质量判断、薄弱项合并和自动消减规则仍为 UNKNOWN，见 §12。本文不设计复杂资产质量算法，只记录质量判断所需的逻辑字段和 UNKNOWN。

### 5.10 LLM request / response / usage / validation / retention

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `LlmRequestTrace` | 调用场景、关联业务对象、`RAGContextAssembly`、`SourceRef`、`VersionRef`、`SnapshotRef`、Prompt context 逻辑边界、请求时间、调用方、provider、model family、状态 | 只保存最小必要追踪信息，不保存 Prompt 模板、模型参数或上下文裁剪策略 |
| `LlmResponseTrace` | request trace、原始输出引用、结构化输出引用、`LlmValidationResult`、`TraceRef`、失败状态 | 区分原始输出引用、结构化输出、业务校验结果和失败状态 |
| `LlmUsageRecord` | request trace、token 统计、cost 统计、latency、provider、model family | 承载用量统计边界，不锁定具体供应商实现 |
| `LlmValidationResult` | response trace、校验类型、校验状态、问题摘要、低置信度标记 | 区分结构化校验、业务语义校验、低置信度、冲突、不完整和失败 |
| `LlmRetentionPolicyRef` | trace、策略引用、适用对象、状态 | 只记录保留策略引用边界，具体保留、删除策略交给 `SECURITY_PRIVACY.md` |
| `LlmRedactionRef` | trace、脱敏策略引用、字段范围、状态 | 只记录脱敏引用边界，具体脱敏细则交给 `SECURITY_PRIVACY.md` |
| `LlmFailureRecord` | request trace、失败阶段、错误分类、可重试性、影响对象、时间 | 记录生成失败、校验失败、冲突、不完整和不可用状态 |

前端不得直接消费 LLM 原始输出；业务对象只引用通过校验的结构化结果或人工确认后的结果。Prompt 模板、上下文裁剪、模型选择、调用参数和重试降级策略交给 `PROMPT_SPEC.md`。

## 6. 对象关系与引用规则

1. 所有用户业务数据必须通过 `UserAccount` / `OwnerRef` 或后续安全文档定义的所有权边界归属。
2. `JobMatchAnalysis`、`InterviewSession`、`InterviewReport`、`InterviewRetrospective`、`WeaknessEvidence` 和 `AssetSource` 应引用生成时的 `ResumeVersion`、`JobVersion` 或具体来源对象版本。
3. `JobResumeBinding` 保存绑定关系本身；解除绑定不得破坏历史报告、复盘、匹配分析或会话的可回看性。
4. `ResumeModule(type=project_experience)` 可以被题目、反馈、复盘、资产和证据引用，但不作为一级数据对象独立管理。
5. `InterviewSession` 是题目、回答、反馈、进展树和报告的聚合根；打磨模式和压力面模式只在模式详情上分化。
6. `KnowledgeDocument` / `KnowledgeChunk` 可以被题目、点评、报告、复盘、评分解释、薄弱项和训练建议引用，但只能通过 `RetrievalEvidence`、`Citation` / `EvidenceRef` 或 `ScoreEvidenceLink` 进入业务对象。
7. `RetrievalResult` 进入 LLM 上下文前应有来源、版本、置信度或命中摘要；`RAGContextAssembly` 只记录组装边界，不替代 `PROMPT_SPEC.md` 的上下文策略。
8. `ScoreResult` 必须引用 `ScoreRuleVersion`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`VersionRef`、`SnapshotRef` 和 `TraceRef`；题目点评、面试报告、弱项识别和训练建议应能追溯到评分规则版本、输入来源版本或快照、证据、解释、低置信度 / 冲突 / 不完整标记和相关 LLM validation 结果。
9. `InterviewReport` 可以进入 `InterviewRetrospective`、`Weakness`、`TrainingRecommendation` 和 `FeedbackLoop`，但不自动写入资产或薄弱项。
10. `MockInterviewReview` 的来源是系统内会话链路；`RealInterviewReview` 的来源是用户手动录入材料，两者都必须通过 `ReviewSourceRef` 表达来源和置信度。
11. `FeedbackLoop` 与 `UserConfirmation` 是回流写入边界；系统建议必须先成为候选或确认记录，再进入资产、薄弱项、训练建议或后续模拟面试输入。
12. `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord` 和 `LlmValidationResult` 只提供追踪、校验和审计引用，不替代业务结果对象。
13. `AuditEvent` 只记录关键动作的最小审计字段，不定义企业级多租户、复杂 ACL、日志保留或脱敏细则。

### 6.1 RAG / LLM / 业务结果审计链路

一次 RAG / LLM 生成业务结果的最小审计链路如下：

1. `RAGContextAssembly` 可以引用 `RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`SourceRef`、`EvidenceRef`、`VersionRef` 和 `SnapshotRef`，用于说明本次上下文由哪些查询、命中证据、来源版本和快照组成。
2. `LlmRequestTrace` 可以引用 `RAGContextAssembly`、`SourceRef`、`VersionRef`、`SnapshotRef` 和 Prompt context 的逻辑边界，但不记录 Prompt 模板、模型调用参数或 provider-specific request payload。
3. `LlmResponseTrace` 可以引用 `LlmRequestTrace`、原始输出引用、结构化输出引用、`LlmValidationResult` 和 `TraceRef`，用于区分原始响应、结构化结果、校验结果和失败状态。
4. 结构化业务结果可以通过 `TraceRef` / `EvidenceRef` / `VersionRef` / `SnapshotRef` 回溯到 RAG evidence、LLM request、LLM response、validation result，以及 low confidence / conflict / incomplete 标记。
5. `ScoreResult`、`InterviewReport`、`ReviewItem`、`WeaknessEvidence`、`TrainingRecommendation` 和 `AssetCandidate` 至少需要支持上述回溯链，避免业务结果只保存不可解释文案。

本文不展开 Prompt 模板、模型调用参数、retry / fallback 策略、provider-specific request / response payload、向量数据库实现或 embedding 模型选型；这些内容交给 `PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。

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
| 知识文档状态 | `draft`、`available`、`stale`、`archived`、`failed` | 草稿 -> 可用；可用 -> 过期 / 归档；处理失败时保留失败状态 |
| RAG 检索状态 | `not_started`、`retrieving`、`assembled`、`partial`、`low_confidence`、`failed` | 未开始 -> 检索中 -> 已组装 / 部分可用 / 低置信度 / 失败 |
| 报告状态 | `not_generated`、`generating`、`available`、`failed`、`low_confidence` | 未生成 -> 生成中 -> 可查看 / 失败 / 低置信度 |
| 复盘状态 | `not_generated`、`generating`、`needs_user_review`、`available`、`failed`、`low_confidence` | 未生成 -> 生成中 -> 待校对 / 可用 / 失败 |
| 薄弱项状态 | `weakness_detected`、`weakness_confirmed`、`low_priority`、`ignored`、`resolved_candidate`、`resolved`、`reopened` | 已发现 -> 已确认；已确认 -> 低优先级 / 忽略 / 解决候选 / 已解决；可再次暴露 |
| 训练状态 | `training_recommended`、`training_in_progress`、`training_completed`、`failed`、`skipped` | 已建议 -> 训练中 -> 已完成；可失败或跳过 |
| 资产状态 | `asset_candidate_generated`、`asset_confirmed`、`asset_archived`、`asset_rejected`、`superseded`、`disabled`、`failed` | 资产候选已生成 -> 已确认；已确认 -> 归档 / 被替代 / 禁用；候选可被拒绝 |
| 内容沉淀目标状态 | `not_confirmed`、`confirmed`、`cancelled`、`skipped`、`writing`、`written`、`failed`、`disabled` | 未确认 -> 已确认 / 取消 / 跳过；已确认 -> 写入中 -> 写入成功 / 失败 |
| 评分 / 解释状态 | `available`、`low_confidence`、`conflict`、`incomplete`、`failed` | 评分后进入可用、低置信度、冲突、不完整或失败 |
| LLM 校验状态 | `structured_validated`、`semantic_validated`、`validation_failed`、`low_confidence`、`conflict`、`incomplete`、`unusable` | 输出后区分结构化校验、业务语义校验、失败、低置信度、冲突、不完整或不可用 |
| 历史来源可用性状态 | `source_available`、`source_archived`、`source_deleted`、`source_disabled`、`source_unavailable` | 只表示历史结果所引用源对象的当前可用性，不表示历史结论失效 |

## 8. 版本策略与历史引用

### 8.1 当前可冻结原则

- 简历、岗位和资产都需要版本对象，避免历史分析结果引用被当前编辑覆盖。
- 匹配分析、会话、报告、复盘、薄弱项证据和资产来源都应保存生成时引用的版本。
- 版本引用应保留到足以支持历史报告和复盘回看。
- 用户编辑当前简历或岗位，不应隐式重算历史匹配分析、报告或复盘。
- 内容沉淀写入资产时，默认先形成 `AssetCandidate` 或 `FeedbackLoop` 记录，再由用户确认产生或更新 `AssetVersion`。
- 评分结果、评分解释、报告分项和复盘项应引用生成时的 `ScoreRuleVersion`，避免后续规则调整改写历史解释。
- 知识库检索、RAG 证据和引用应保存 `KnowledgeDocument` / `KnowledgeChunk` 的来源版本或外部引用，避免检索证据失去来源。

### 8.2 生成时版本 / 快照引用规则

- `InterviewReport` 生成后，应引用生成时的 `ResumeVersion` 或简历快照、`JobVersion` 或岗位快照、`InterviewSession` 快照、`ScoreRuleVersion`，以及相关 `SourceRef` / `EvidenceRef` / `VersionRef` / `SnapshotRef` / `TraceRef`。
- `MockInterviewReview` 应引用系统内会话、题目、回答、点评、评分和报告在生成时的版本或快照。
- `RealInterviewReview` 应引用用户录入的真实面试输入版本、用户补充材料、面试官反馈或结果状态，并标注可信度和完整度；系统不得假设拥有完整真实面试过程。
- `ScoreResult` 应引用评分时的输入版本或快照、评分规则版本、证据链、解释链路和相关 LLM validation 结果，不随后续简历、岗位、会话、知识文档或评分规则变化而自动重算。
- `AssetCandidate` 应记录来源类型、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、`TraceRef`、`UserConfirmationRef`、用户确认状态，以及适用岗位 / 简历 / 场景引用。
- 用户修改简历、岗位、复盘或资产后，不得导致历史报告、历史复盘、历史评分结果或历史资产候选自动变化；如需重新生成或重新评分，应形成新的结果或新版本结果。
- 历史报告、复盘、评分结果和资产候选保留生成时引用；当前源对象不可用时，不改写历史结论，只通过 `source_available`、`source_archived`、`source_deleted`、`source_disabled` 或 `source_unavailable` 展示来源当前可用性。
- 来源可用性状态不表示历史结论失效；是否允许用户重新生成、恢复引用或修复来源，留给后续 `API_SPEC.md` / F5 实现细化。

### 8.3 仍未冻结的版本决策

- 简历版本创建触发、命名、保留和回滚策略仍为 UNKNOWN。
- 岗位版本创建触发、投递状态是否进入版本正文仍为 UNKNOWN。
- 项目经历表达打磨结果是否形成独立表达版本、如何回指简历模块仍为 UNKNOWN。
- 资产版本、合并、替代、质量判断和回滚策略仍为 UNKNOWN。
- 评分规则版本治理、启停、回滚和历史规则保留策略仍为 UNKNOWN。
- 知识文档版本、chunk 重建、embedding 外部引用刷新和失效策略仍为 UNKNOWN。

## 9. 回流、资产、薄弱项生命周期

### 9.1 回流生命周期

1. 系统从报告、复盘、薄弱项或打磨反馈中生成可沉淀内容。
2. 可沉淀内容进入 `AssetCandidate`、`Weakness` 候选或 `TrainingRecommendation` 候选。
3. 系统创建 `FeedbackLoop`，并为每个目标创建 `UserConfirmation`。
4. 用户确认、编辑、取消、跳过或重试。
5. 只有目标级状态为已确认且写入成功时，才更新资产、薄弱项、训练建议或后续模拟面试输入。
6. 写入失败必须保留来源、候选内容、失败原因和重试状态。

### 9.2 资产生命周期

- `asset_candidate_generated`：系统建议沉淀，但用户或规则尚未确认。
- `asset_confirmed`：用户确认或规则确认后进入资产库，可作为后续模拟面试增强输入。
- `asset_rejected`：用户或规则拒绝候选，不进入正式资产。
- `asset_archived`：用户不再使用，但历史引用可回看。
- `superseded`：被新版本或合并结果替代。
- `disabled`：因来源不可用、质量不足或安全边界不可用。

资产合并、质量判断、重复检测和版本替代规则仍为 UNKNOWN。

### 9.3 薄弱项生命周期

- `weakness_detected`：系统从匹配分析、报告、复盘、反馈、RAG 证据或用户录入中识别出的候选。
- `weakness_confirmed`：用户或规则确认后进入薄弱项列表，可用于训练和出题。
- `low_priority`：仍存在但优先级降低。
- `ignored`：用户明确忽略。
- `resolved_candidate`：系统建议已改善，但尚未最终关闭。
- `resolved`：确认已解决。
- `reopened`：后续证据再次暴露。

薄弱项合并、状态流转、生命周期和是否自动消减仍为 UNKNOWN。

### 9.4 Weakness -> Training -> Asset 状态流

最小状态流为：

`weakness_detected` -> `weakness_confirmed` -> `training_recommended` -> `training_in_progress` -> `training_completed` -> `asset_candidate_generated` -> `asset_confirmed` -> `asset_archived` / `asset_rejected`

规则：

- 薄弱项来源必须可追溯到题答、评分、复盘、RAG 证据或用户确认。
- `TrainingRecommendation` 只能表达训练建议，不能直接等同于 `Asset`。
- `TrainingTask` / `TrainingSession` 记录训练执行过程，`TrainingResult` 记录训练完成后的结果、评分引用、弱项变化和资产候选。
- `AssetCandidate` 必须经过 `UserConfirmation` 或 `AssetPromotionRecord` 的规则确认后，才能生成或更新正式 `Asset` / `AssetVersion`。
- `AssetVersion` 需要记录来源、确认状态、适用岗位、适用简历和适用场景。
- 本文不设计复杂资产质量算法，只记录质量判断所需的逻辑字段和仍为 UNKNOWN 的决策点。

## 10. 评分、低置信度与可解释结果的数据承载边界

- `ScoreResult` 统一保存 0-100 展示分值、分数类型、关联对象、`ScoreRuleVersion`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`VersionRef`、`SnapshotRef`、`TraceRef` 和生成状态。
- `ScoreResult` 必须能追溯到评分规则版本、输入来源版本或快照、证据链、解释链路、低置信度 / 冲突 / 不完整标记，以及相关 `LlmValidationResult`。
- `ScoreResult` 不随后续简历、岗位、会话、知识文档或评分规则变化而自动重算；如需重新评分，应产生新的 `ScoreResult` 或新版本结果。
- `ScoreRuleSet` / `ScoreRuleVersion` 只表达规则版本边界，评分公式、权重、阈值、校准算法和规则发布流程不在本文冻结。
- `ScoreDimension` / `ScoreRubric` 只保存可追溯维度与 rubric 描述，不承诺精确通过概率或真实面试结果预测。
- `ScoreExplanation` 应连接面试报告、题目点评、弱项识别和训练建议需要展示的解释摘要。
- `ScoreEvidenceLink` 应连接题答、评分、报告、复盘、RAG 证据或用户确认记录。
- 本文不定义评分公式、权重、阈值、校准方法或通过概率。
- `LowConfidenceFlag` 或结果对象状态应保存低置信度、冲突、不完整和失败标记，并关联触发原因、影响范围和可校对入口。
- `EvidenceSummary`、`RetrievalEvidence`、`Citation` / `EvidenceRef` 和 `ScoreEvidenceLink` 保存可展示证据摘要；原始输入片段、隐私字段和日志脱敏边界交给 `SECURITY_PRIVACY.md`。
- 匹配分析、面试报告、复盘和反馈卡片可以引用证据摘要、评分结果和低置信度标记。
- 用户校对低置信度结果时，应产生 `UserConfirmation` 或后续 API 定义的校对记录，不能只覆盖原始结果。
- LLM 原始输出和结构化输出保存边界仍为 UNKNOWN；前端只接收通过校验的可展示结果或低置信度 / 部分可用状态。

## 11. 持久化边界与逻辑 schema 草案

### 11.1 持久化边界

- 前端不保存业务真相，不直接读取数据库，不直接调用 LLM。
- 后端持久化层负责保存用户数据、版本、知识库逻辑对象、RAG 证据引用、会话、报告、复盘、资产、薄弱项、训练建议、回流确认、最小 LLM trace 和关键审计事件。
- `SECURITY_PRIVACY.md` 负责定义隐私字段、日志脱敏、密钥、权限、保留和删除策略。
- `API_SPEC.md` 负责定义具体资源路径、请求响应结构、错误语义和异步任务查询。
- `PROMPT_SPEC.md` 负责定义 Prompt 输入输出、模型调用、结构化校验和低置信度判定。

### 11.2 逻辑 schema 草案

以下是逻辑对象分组，不是物理表 DDL。

| 分组 | 逻辑对象 |
|---|---|
| 身份、归属与审计 | `UserAccount`、`OwnerRef`、`RoleAssignment`、`RoleScope`、`PermissionBoundary`、`AuditActor`、`AuditTarget`、`AuditEvent` |
| 统一引用模型 | `SourceRef`、`EvidenceRef`、`VersionRef`、`TraceRef`、`SnapshotRef`、`UserConfirmationRef`、`OwnerRef` |
| 简历 | `Resume`、`ResumeVersion`、`ResumeModule` |
| 岗位 | `Job`、`JobVersion`、`JobStatus`、`JobResumeBinding` |
| 匹配分析 | `JobMatchAnalysis`、`MatchScore`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`EvidenceSummary` |
| 知识库与 RAG | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`KnowledgeEmbeddingRef`、`RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`Citation` / `EvidenceRef`、`RAGContextAssembly` |
| 模拟面试 | `InterviewSession`、`PolishSessionDetail`、`PressureSessionDetail`、`Question`、`Answer`、`Feedback` |
| 评分规则与解释 | `ScoreRuleSet`、`ScoreRuleVersion`、`ScoreDimension`、`ScoreRubric`、`ScoreResult`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag` |
| 题级解释材料 | `LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation` |
| 进展 | `ProgressTree`、`ProgressNode`、`ProgressPosition` |
| 报告 | `InterviewReport`、`ReportSection`、`CopyableContent` |
| 复盘 | `InterviewRetrospective`、`MockInterviewReview`、`RealInterviewReview`、`RealInterviewInput`、`RealInterviewEvidence`、`ReviewItem`、`ReviewSourceRef` |
| 薄弱项 | `Weakness`、`WeaknessEvidence`、`WeaknessStatusHistory` |
| 资产 | `Asset`、`AssetVersion`、`AssetCandidate`、`AssetSource`、`AssetPromotionRecord` |
| 训练与回流 | `TrainingRecommendation`、`TrainingTask`、`TrainingSession`、`TrainingResult`、`FeedbackLoop`、`UserConfirmation` |
| LLM 追踪 | `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord`、`LlmValidationResult`、`LlmRetentionPolicyRef`、`LlmRedactionRef`、`LlmFailureRecord` |

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
| DM-UNK-010 | LLM 原始输出、结构化输出、trace 与审计记录保存边界 | TECH_DESIGN §14、§16 | 已确认最小 `LlmRequestTrace` / `LlmResponseTrace` / `LlmUsageRecord` / `LlmValidationResult` 边界，未冻结原始输出保存范围、保留周期、脱敏和审计策略 |
| DM-UNK-011 | RAG 知识文档版本、chunk 和外部 embedding 引用策略 | `TECH_DESIGN.md` §14 / §16、`BACKLOG.md` AIFI-DATA-001 / AIFI-ARCH-002 | 已确认 `KnowledgeDocument`、`KnowledgeChunk`、`KnowledgeEmbeddingRef` 和 RAG 证据引用，不冻结向量库、embedding 模型、索引或 chunk 算法 |
| DM-UNK-012 | 评分规则版本治理和解释链路细则 | `PRD.md` §10、`DELIVERY_PLAN.md` F4、`BACKLOG.md` AIFI-DATA-001 / AIFI-ARCH-002 | 已确认 `ScoreRuleVersion`、`ScoreDimension`、`ScoreRubric`、`ScoreExplanation` 和 `ScoreEvidenceLink`，不冻结公式、权重、阈值、校准算法或发布流程 |
| DM-UNK-013 | 真实面试复盘输入可信度、完整度和证据等级 | `PRD.md` §10、`BACKLOG.md` AIFI-DATA-001 / AIFI-ARCH-002 | 已确认 `RealInterviewInput` / `RealInterviewEvidence` / `ReviewSourceRef`，不假设系统拥有完整真实面试过程 |
| DM-UNK-014 | MVP 权限、角色范围和审计事件细则 | `TECH_DESIGN.md` §16、`BACKLOG.md` AIFI-ARCH-002 / AIFI-SEC-001 | 已确认个人工作台 owner、最小 role scope 和关键动作审计字段，不设计企业级多租户、复杂 ACL 或资源继承 |

## 13. 与 API / Prompt / Security 子文档的交接边界

| 子文档 | 本文交接内容 | 本文不展开内容 |
|---|---|---|
| `API_SPEC.md` | 逻辑对象、状态域、引用关系、生成任务状态、历史引用原则、MVP role scope 和审计对象边界 | endpoint、request / response schema、错误码、分页过滤参数、异步任务协议、具体鉴权 API |
| `PROMPT_SPEC.md` | LLM 输出应落到哪些结构化对象、RAG 上下文组装结果如何被引用、低置信度和部分可用状态应被持久化 | Prompt 模板、模型选择、模型调用参数、上下文裁剪、重试降级策略、评分公式、权重、阈值、校准算法 |
| `SECURITY_PRIVACY.md` | 哪些对象包含用户资料、简历、岗位、回答、报告、复盘、资产、知识库文档、RAG 证据和 LLM trace | 密钥管理、权限矩阵、复杂 ACL、企业多租户、数据可见性、日志脱敏、保留 / 删除细则、隐私字段分级 |
| `TECH_DESIGN.md` | 本文回填数据模型子文档状态和待协同关闭的 UNKNOWN | 顶层架构重写、F4 UNKNOWN 关闭、`AIFI-ARCH-002` 完成判定 |

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-15 | 初始化 F4 数据模型工作草案 | 建立 `AIFI-DATA-001` 的对象、关系、状态、版本、回流、评分和 trace 承载边界；不关闭 `F4_TECH_DESIGN` UNKNOWN |
| 2026-05-15 | 补齐数据模型收敛缺口 | 补充 RAG / Knowledge Base、评分规则版本、LLM trace、真实 / 模拟复盘差异、Weakness -> Training -> Asset 状态流和 MVP 权限 / 审计边界；不关闭 `F4_TECH_DESIGN` UNKNOWN |
