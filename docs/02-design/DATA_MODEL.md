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
- 本文件不是终版数据库 schema，不提供物理表 DDL，不替代 `TECH_DESIGN.md`、`API_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 或 `PERSISTENCE_MODEL.md`。
- F5 persistence handoff 的 canonical 位置为 `PERSISTENCE_MODEL.md`；F5 不得只从本文逻辑对象自行推导物理表、join table、引用表、唯一约束或 API schema 映射。
- 本轮按 `AR-F4-FULL-001` 处置数据模型侧 F4 待决策项：M4 阻断项已冻结为逻辑对象、状态、版本、trace / evidence、candidate / formal 和 deferred_non_blocking 边界；不标记 `AIFI-ARCH-002` 或 `AIFI-DATA-001` 完成。
- 本文件不新增 roadmap、plan-v2、codex-plan、临时任务文档或并行设计入口。
- 本文件不得把 `archive/` 内容作为当前执行依据；历史内容只有进入 active docs 后才能影响本数据模型。

## 2. 输入来源与非目标

### 2.1 输入来源

| 来源 | 本文使用方式 |
|---|---|
| `docs/01-product/PRD.md` | 业务对象、核心数据流、非目标、状态异常、验收标准和 PRD §10 UNKNOWN |
| `docs/02-design/UX_SPEC.md` | 已冻结的用户可见页面、绑定关系入口、内容沉淀确认、低置信度校对、状态与异常 |
| `docs/02-design/TECH_DESIGN.md` | 模块划分、系统分层、LLM 边界、状态域和子文档交接边界 |
| `docs/02-design/PROMPT_SPEC.md` | AI Task Contract 的输出对象、validation、low confidence、trace / evidence 和用户确认交接边界 |
| `docs/02-design/SCORING_SPEC.md` | 评分 score type、rubric dimensions、权重、公式、低置信度降级和 `ScoreResult` 正式落库边界 |
| `docs/02-design/SEMANTICS_GLOSSARY.md` | `confidence_level`、`validation_status`、`source_availability`、candidate / suggestion / formal object 统一语义 |
| `docs/02-design/PERSISTENCE_MODEL.md` | F5 建议物理模型、字段组、关系、join / reference table、API schema 映射和 persistence fixture |
| `docs/02-design/PRESSURE_MODE_SPEC.md` | Pressure Mode lifecycle、turn model、pace/end/report handoff、candidate handoff 和 PR2 graph hold 的 mode-level 数据承接 |
| `docs/03-delivery/DELIVERY_PLAN.md` | F4 / M4 阶段边界和不得遗留的技术设计 UNKNOWN 类型 |
| `docs/03-delivery/BACKLOG.md` | `AIFI-DATA-001` 范围和与 `AIFI-ARCH-002`、`AIFI-PROMPT-001`、`AIFI-SEC-001` 的依赖 |

### 2.2 非目标

本文不展开以下内容：

- API endpoint、request / response schema、错误码。
- Prompt 模板、模型选择、LLM 调用参数、上下文裁剪策略。
- 隐藏评分公式、完整内部权重表、复杂阈值、真实结果校准算法、精确通过概率或面试结果预测。
- 密钥管理、日志脱敏细则、数据保留 / 删除细则。
- UI 布局、组件规范、Figma 设计。
- 文件导出实现。
- 外部材料解析自动生成岗位 / JD。
- 将“项目”升级为独立一级业务对象或一级数据对象。

如某项内容更适合 `API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`，本文只记录交接边界，不在数据模型中展开。

## 3. 数据模型设计原则

1. 采用逻辑数据模型表达，先冻结对象、引用、状态和生命周期；F5 物理关系、建议表和 join / reference table 交接由 `PERSISTENCE_MODEL.md` 承接。
2. 用户、简历、岗位、会话、报告、复盘、资产、薄弱项和训练建议都必须有明确归属，避免跨用户数据串联。
3. 历史结果引用应指向生成时使用的版本或快照，不依赖会被后续编辑覆盖的当前对象。
4. 项目经历只作为 Markdown 简历正文片段、派生 outline 节点、打磨主题、复盘分析对象或资产来源，不成为一级或二级 CRUD 业务对象。
5. 反馈回流和内容沉淀必须以用户确认记录为边界，不允许系统静默覆盖资产、薄弱项或后续训练输入。
6. 评分、低置信度和解释结果应以结构化结果对象承载；`AR-F4-FULL-003` 范围内的 `ScoreResult`、`ScoreRuleVersion`、rubric 维度、最小权重策略、证据、置信度和校准承载已冻结，隐藏评分公式、复杂阈值和真实结果校准算法不在本文展开。
7. LLM 原始输出、结构化输出和 trace 只作为后端可追踪对象，不成为前端或业务文案的直接事实源。
8. RAG / Knowledge Base 只作为 MVP 逻辑对象和外部引用边界，不在本文绑定向量数据库、embedding 模型、索引或物理实现。
9. 真实面试复盘必须显式记录用户输入来源、完整度和可信度，不能假设系统拥有完整真实面试过程。
10. 状态枚举要能支撑前端展示、API 查询、重试、暂停恢复、历史回看和 F7 验收。
11. AI Task Contract 输出必须区分正式业务对象、候选对象、建议对象、用户确认记录、validation result、low confidence flag、trace / evidence 和 audit event；候选结果不得直接等同于正式对象。

## 4. 业务对象到数据对象映射

| 业务对象 | 逻辑数据对象 | 说明 |
|---|---|---|
| 用户 / 账号 / 角色 / 审计 | `UserAccount`、`OwnerRef`、`RoleAssignment`、`RoleScope`、`PermissionBoundary`、`AuditEvent` | 保存账号归属、最小角色范围、关键动作审计和可见性边界；完整鉴权策略交给 `SECURITY_PRIVACY.md` |
| 简历 | `Resume`、`ResumeVersion`、`ResumeMarkdownOutline` | MVP 简历正文来自 Markdown 粘贴 / 手动编辑；`ResumeMarkdownOutline` 只能作为 derived / non-persistent 解析视图用于定位、分析和引用；不要求保存文件原文、MIME、文件名或文件大小 |
| 项目经历片段 | Markdown 正文片段 / `ResumeMarkdownOutline` 节点 | 项目经历不是一级或二级持久化业务对象，不建立独立 owner、version 或 CRUD；被匹配分析、会话、复盘和资产引用时必须回到 `ResumeVersion` 与 Markdown 位置范围 |
| 岗位 / JD | `Job`、`JobVersion`、`JobStatus` | 岗位来源为用户手动录入；不承接外部材料解析生成岗位 |
| 岗位-简历绑定 | `JobResumeBinding`、`JobBindingSummary` | 保存岗位、简历、版本、绑定 / 解绑状态、解绑 actor 和历史结果保留摘要；`JobBindingSummary` 是 API / F6 读取摘要，不新增物理实现细节 |
| 岗位匹配分析 | `JobMatchAnalysis`、`JobMatchSummary`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`MatchScore`、`EvidenceSummary` | 承载 0-100 匹配分数、解释、证据和薄弱项建议；`JobMatchSummary` 只暴露最新分析状态和产品匹配分，不表达精确通过概率 |
| 知识库 / RAG | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`KnowledgeEmbeddingRef`、`RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`Citation` / `EvidenceRef`、`RAGContextAssembly` | 只定义检索、证据和上下文组装的逻辑对象，不绑定向量库、embedding 模型或索引实现 |
| 模拟面试 | `InterviewSession`、`SessionSummary` | `InterviewSession` 统一承载打磨模式和压力面模式的公共会话信息；`SessionSummary` 承载可回溯的会话摘要逻辑对象 |
| 打磨模式会话 | `PolishSessionDetail`、`PolishTopicRef`、`PolishSubtopicRef` | 承载同题多轮打磨、主题 / 次主题上下文、暂停恢复、下一步建议和内容沉淀入口；主题 / 次主题是受控选项引用，不是正式业务对象 |
| 压力面模式会话 | `PressureSessionDetail`、`PressureTurn`（逻辑引用模型）、`PressureReportInputPackage`（逻辑 handoff） | 承载连续追问、节奏状态、中断、结束条件、报告输入包和复盘 handoff；mode-level 边界见 `PRESSURE_MODE_SPEC.md` |
| 题目 / 回答 / 点评 | `Question`、`Answer`、`Feedback` | 承载题级问答、点评、参考回答、考点解析和失分点 |
| 评分规则 / 解释 / 低置信度 | `ScoreRuleSet`、`ScoreRuleVersion`、`ScoreDimension`、`ScoreRubric`、`ScoreResult`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag` | 保存评分规则版本、rubric 维度、最小权重策略、证据和解释链路；不暴露隐藏评分公式、完整内部权重表或复杂阈值 |
| 失分点 / 参考回答 / 考点解析 | `LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation` | 只保存结果与解释，不冻结 Prompt 模板或评分算法 |
| 进展树 | `ProgressTree`、`ProgressNode`、`ProgressPosition` | 支撑多维进展、节点状态、当前位置和暂停恢复 |
| 面试报告 | `InterviewReport`、`ReportSection`、`CopyableContent` | 承载报告分项、可复制内容和低置信度提示 |
| 面试复盘 | `InterviewRetrospective`、`ReviewSummary`、`MockInterviewReview`、`RealInterviewReview`、`RealInterviewInput`、`RealInterviewEvidence`、`ReviewItem`、`ReviewSourceRef`、`CopyableReviewContent`、`ReviewCopyEvent` | 区分系统内模拟复盘和用户手动录入的真实面试复盘来源，承接列表投影、复盘复制内容边界和复制审计 |
| 薄弱项 | `Weakness`、`WeaknessCandidate`、`WeaknessEvidence`、`WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion`、`WeaknessStatusHistory` | 保存正式薄弱项、待确认候选、来源证据、合并建议、严重度提示、状态更新建议和训练建议关联 |
| 资产 | `Asset`、`AssetVersion`、`AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`AssetSource`、`AssetPromotionRecord` | 保存可复用材料、候选沉淀、质量提示、版本建议、来源、确认状态和版本引用 |
| 训练建议 / 训练过程 | `TrainingRecommendation`、`TrainingPriorityRanking`、`TrainingTask`、`TrainingSession`、`TrainingResult`、`TrainingResultReview` | 保存训练建议、排序提示、执行状态、结果复盘和回流候选 |
| 反馈回流 / 用户确认 | `FeedbackLoop`、`UserConfirmation`、`CandidateCorrection`、`UserCorrectionRef`、`DepositTarget` | 保存用户确认、编辑、取消、跳过、低置信校对、目标选择、写入成功或失败 |
| AI Task Contract 输出交接 | `AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`LlmValidationResult`、`LowConfidenceFlag`、`TraceRef`、`EvidenceRef`、`AuditEvent` | 保存 contract 输出结果引用、候选态、建议态、校验、低置信度、证据、追踪和审计边界；不等同于 provider response |
| API 幂等、任务与请求追踪 | `IdempotencyRecord`、`AiTask`、`AiTaskResult`、`ApiRequestTrace`、`ApiEndpointRef` | 承接 `API_SPEC.md` 的幂等重试、异步任务状态、接口请求 trace、owner boundary、字段级 schema 和 F7 contract tests；不定义物理队列、表结构或运行时平台 |
| LLM request / response / usage / validation | `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord`、`LlmValidationResult`、`LlmRetentionPolicyRef`、`LlmRedactionRef`、`LlmFailureRecord` | 保存最小可追踪信息、结构化输出状态、用量统计边界、校验和保留 / 脱敏引用 |

### 4.1 统一引用模型

统一引用模型只定义逻辑引用形态，不定义 API 字段命名规范，不定义 request / response schema，也不展开字段全集、类型、长度、DDL、外键或索引。后续 `API_SPEC.md` 可以基于这些逻辑引用对象定义接口字段，但不得改变其语义。

这些引用对象可被 `InterviewReport`、`MockInterviewReview`、`RealInterviewReview`、`ReviewItem`、`ScoreResult`、`WeaknessEvidence`、`TrainingRecommendation`、`TrainingPriorityRanking`、`TrainingResultReview`、`AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`AssetVersion`、`RetrievalEvidence`、`RAGContextAssembly`、`LlmRequestTrace`、`LlmResponseTrace`、`LlmValidationResult` 和 `AuditEvent` 复用。

| 引用对象 | 职责 | 适用对象 | 引用规则 | 后续交接文档 |
|---|---|---|---|---|
| `SourceRef` | 记录业务来源，例如简历、岗位、会话、报告、复盘、知识文档、用户录入或真实面试输入 | 报告、复盘、评分、资产候选、训练建议、RAG / LLM trace 和审计事件 | 按来源类型、来源对象、生成场景和可展示摘要建立逻辑引用；不得只保留当前最新对象名称 | `API_SPEC.md` 定义接口字段，`SECURITY_PRIVACY.md` 定义可见性和脱敏边界 |
| `EvidenceRef` | 记录证据来源，例如题目、回答、点评、评分解释、RAG 检索证据、用户确认或面试官反馈 | `ReviewItem`、`ScoreResult`、`WeaknessEvidence`、`TrainingRecommendation`、`TrainingPriorityRanking`、`TrainingResultReview`、`AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`RetrievalEvidence` | 证据引用应能回溯到证据对象、证据版本或快照、摘要和置信度 / 完整度标记 | `API_SPEC.md` 定义查询和展示字段，`SECURITY_PRIVACY.md` 定义证据片段可展示范围 |
| `VersionRef` | 记录源对象版本，例如 `ResumeVersion`、`JobVersion`、`KnowledgeDocument` version、`AssetVersion`、`ScoreRuleVersion` | 历史报告、复盘、评分、资产候选、RAG evidence、LLM trace | 指向生成时使用的版本；源对象后续编辑不得改写已生成结果 | `API_SPEC.md` 定义版本引用表达，F5 实现冻结具体持久化方式 |
| `SnapshotRef` | 记录生成时快照引用，用于历史报告、复盘、评分和资产候选的稳定回看 | `InterviewReport`、`MockInterviewReview`、`RealInterviewReview`、`ScoreResult`、`AssetCandidate`、`AuditEvent` | 当版本对象不足以稳定回看时，引用生成时的内容快照或快照摘要；不得退化为当前最新对象引用 | `API_SPEC.md` 定义快照读取语义，`SECURITY_PRIVACY.md` 定义快照保留和删除边界 |
| `TraceRef` | 记录 API request、LLM、RAG、校验、审计和持久化交接等过程引用 | `ApiRequestTrace`、`AiTask`、`ScoreResult`、`InterviewReport`、`ReviewItem`、`WeaknessEvidence`、`TrainingRecommendation`、`TrainingPriorityRanking`、`TrainingResultReview`、`AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`AuditEvent` | 只表达过程追踪链路，不保存或暴露 provider payload、system prompt、completion 原文、隐藏评分规则、request / response body 或未脱敏正文 | `API_SPEC.md` 定义 request / response trace 字段，`PROMPT_SPEC.md` 定义模型过程边界，`SECURITY_PRIVACY.md` 定义日志和保留边界 |
| `UserConfirmationRef` | 记录用户确认、拒绝、修正、回流确认或资产入库确认 | `AssetCandidate`、`AssetVersionSuggestion`、`AssetVersion`、`WeaknessEvidence`、`TrainingRecommendation` candidate、`TrainingResultReview`、`FeedbackLoop`、`AuditEvent` | 系统建议进入正式资产、薄弱项或训练输入前，应保留确认动作、确认状态和编辑结果引用 | `API_SPEC.md` 定义确认流程字段，`SECURITY_PRIVACY.md` 定义确认记录可见性 |
| `CandidateRef` | 记录 AI 生成的待确认候选对象引用 | `WeaknessCandidate`、`AssetCandidate`、`TrainingRecommendation` candidate、`SessionSummary`、`AiTaskResultRef` | 候选引用必须保留 owner、来源、证据、trace、候选状态和用户确认要求；用户确认前不得升级为正式对象 | `API_SPEC.md` 定义候选查询、确认和状态展示语义 |
| `SuggestionRef` | 记录合并建议、严重度提示、状态更新建议、质量提示、版本建议、排序提示或结果复盘建议引用 | `WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion`、`AssetQualityHint`、`AssetVersionSuggestion`、`TrainingPriorityRanking`、`TrainingResultReview` | 建议对象不等于正式业务动作，必须可被确认、编辑、跳过、拒绝或人工校对 | `API_SPEC.md` 定义建议列表、确认动作和过期状态语义 |
| `AiTaskResultRef` | 记录一个 AI Task Contract 或 API AI task 的输出结果引用 | `AiTaskResult`、Report / Review / Weakness / Asset / Training 相关结果、候选、建议、validation 和 audit event | 必须关联 `ai_task_id`、`contract_id`、owner、status、validation result、low confidence、source availability、trace 和 evidence；不保存 provider response 原文 | `PROMPT_SPEC.md` 定义 contract 输出，`API_SPEC.md` 定义响应 envelope、task status 和 result 语义 |
| `OwnerRef` | 记录对象归属、创建者和 MVP 最小 role scope | 用户业务对象、知识文档、资产、报告、复盘、trace、审计事件 | MVP 默认以个人工作台 owner 为主要边界；只表达最小可见性和维护角色范围，不设计复杂权限继承 | `API_SPEC.md` 定义资源 owner 表达，`SECURITY_PRIVACY.md` 定义鉴权和审计边界 |

历史报告、复盘、评分结果和资产候选不能只引用“当前最新简历 / 岗位 / 知识文档 / 评分规则”，必须引用生成时的 `VersionRef` 或 `SnapshotRef`。如果源对象被后续编辑、归档、禁用或删除，历史结果仍保留生成时引用，只额外展示来源当前可用性状态。

### 4.2 逻辑对象分层

本节按职责和实现重量标注逻辑对象，避免后续把所有对象都建成同等重量的持久化表。该分层是逻辑设计分层，不等同于数据库表拆分，也不要求 F5 逐一建表。

#### 4.2.1 按职责分层

| 分层 | 对象 | 说明 |
|---|---|---|
| 一级领域对象 / Domain Entity | `User` / `Account`、`Resume`、`ResumeVersion`、`Job` / `JD`、`JobVersion`、`ResumeJobBinding`、`MatchAnalysis`、`InterviewSession`、`SessionSummary`、`PolishingSession`、`PressureInterviewSession`、`ProgressTree`、`InterviewReport`、`MockInterviewReview`、`RealInterviewReview`、`Weakness`、`TrainingRecommendation`、`TrainingTask` / `TrainingSession`、`Asset`、`AssetVersion`、`AssetCandidate`、`KnowledgeBase`、`KnowledgeDocument`、`LlmRequestTrace` / `LlmResponseTrace`、`AuditEvent` | 具有独立生命周期、状态或跨模块引用价值；其中 `KnowledgeBase` 只是后端逻辑检索边界，不代表产品一级模块 |
| 明细或值对象 / Value Object or Detail Object | `ResumeMarkdownOutline`、Markdown 位置范围、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`JobBindingSummary`、`JobMatchSummary`、`PolishTopicRef`、`PolishSubtopicRef`、`InterviewQuestion`、`InterviewAnswer`、`Feedback`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`ReviewItem`、`WeaknessEvidence`、`RetrievalEvidence`、`Citation` / `CitationRef`、`TrainingResult`、`AssetPromotionRecord` | 依附于主对象，通常不独立管理生命周期；其中 `ResumeMarkdownOutline`、`JobBindingSummary`、`JobMatchSummary` 为 derived / read-model 语义，不要求物理持久化 |
| 候选 / 建议 / AI 结果交接对象 | `CandidateRef`、`WeaknessCandidate`、`AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`TrainingRecommendation` candidate、`TrainingPriorityRanking`、`TrainingResultReview`、`SuggestionRef`、`WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion`、`AiTaskResultRef`、`LowConfidenceFlag`、`LlmValidationResult` | 承接 AI Task Contract 输出和用户确认流；不等同于正式业务对象或实际业务动作 |
| API 协议承接对象 / API Handoff Object | `IdempotencyRecord`、`AiTask`、`AiTaskResult`、`ApiRequestTrace`、`ApiEndpointRef` | 承接 API 字段级 contract、异步任务协议、幂等持久化、trace / audit 和 F7 contract test 的逻辑落点；不等同于物理表或队列实现 |
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
| `SessionSummary` | `derived context` / `snapshot-backed summary` | 从会话题答、点评、评分、追问和候选回流状态派生，服务后续 Context Assembly，不替代原始问答记录 |
| `InterviewReport` | `entity` / `snapshot-backed result` | 生成后引用生成时版本和快照，不随后续输入变化自动改写 |
| `MockInterviewReview` | `entity` / `snapshot-backed result` | 来源于系统内会话链路和生成时快照 |
| `RealInterviewReview` | `entity` / `user-input-backed result` | 来源于用户录入和补充材料，需要可信度和完整度标记 |
| `Weakness` | `entity` | 可被训练、报告、复盘和资产候选引用 |
| `WeaknessCandidate` | `candidate` | AI 或用户请求产生的薄弱项候选，默认需要用户确认后才可成为正式 `Weakness` |
| `WeaknessMergeSuggestion` | `suggestion` | 候选与既有 `Weakness` 的合并建议，不自动合并或覆盖正式对象 |
| `WeaknessSeverityAssessment` | `suggestion` / `assessment` | 严重度提示和训练优先级 hint，不冻结严重度算法或正式训练优先级 |
| `WeaknessStatusUpdateSuggestion` | `suggestion` | 状态更新建议，不自动改变正式 `Weakness` 状态 |
| `TrainingRecommendation` | `candidate` / `derived view` / `entity` | 从薄弱项、评分、复盘和证据派生；可先以候选态存在，用户确认前不得成为正式训练建议 |
| `TrainingPriorityRanking` | `suggestion` / `ranking` | 训练建议排序提示，不冻结训练优先级算法，不自动创建训练任务 |
| `TrainingTask` / `TrainingSession` | `entity` | 承载训练执行状态；不得由 AI suggestion 自动创建，必须经过确认或显式用户动作 |
| `TrainingResultReview` | `review` / `suggestion` | 训练结果复盘对象，只产生 Weakness / Asset / Training 的候选或建议态回流输入 |
| `Asset` | `aggregate root` | 资产库材料的主要一致性边界 |
| `AssetVersion` | `entity` / `snapshot` | 支撑历史会话、报告和复盘引用 |
| `AssetCandidate` | `candidate` | 候选沉淀对象，需要确认后才能变为正式资产或正式结果 |
| `AssetQualityHint` | `suggestion` / `hint` | 资产候选或 AssetVersion 的质量提示，不冻结质量算法，不等于自动归档规则 |
| `AssetVersionSuggestion` | `suggestion` | 资产版本更新建议，不自动替换、覆盖或发布 AssetVersion |
| `KnowledgeBase` | `logical boundary` / `aggregate-like backend boundary` | 后端检索边界，不升级为产品一级模块 |
| `KnowledgeDocument` | `entity` | 可被 RAG、评分解释、报告、复盘和训练建议引用 |
| `KnowledgeChunk` | `value object` / `reference` | 依附于知识文档版本，用作检索和证据引用 |
| `RetrievalEvidence` | `reference` | 连接检索结果、知识文档、chunk、版本和命中摘要 |
| `RAGContextAssembly` | `trace` / `derived context` | 记录一次上下文组装过程和来源集合 |
| `IdempotencyRecord` | `api protocol state` / `handoff record` | 承接 mutation 幂等、request body hash、first response snapshot、AI task 绑定、TTL、owner 和 audit |
| `AiTask` | `api task entity` | API 可查询、可重试、可取消的异步任务逻辑对象；不等同于 provider task 或物理队列任务 |
| `AiTaskResult` | `task result` / `handoff result` | 承接 result、candidate、suggestion、validation、low confidence、source availability、evidence 和 trace |
| `ApiRequestTrace` | `trace` | 记录 API request id、trace id、actor、endpoint、resource refs、validation、audit 和日志脱敏边界 |
| `LlmRequestTrace` | `trace` | 记录 LLM 请求过程边界 |
| `LlmResponseTrace` | `trace` | 记录 LLM 响应和结构化输出边界 |
| `LlmValidationResult` | `trace` / `validation result` | 记录结构化校验和业务语义校验结果 |
| `AuditEvent` | `trace` | 记录关键动作的审计链路 |
| `CandidateRef` / `SuggestionRef` / `AiTaskResultRef` | `handoff reference` | AI 输出、候选、建议和 validation 结果的跨文档交接引用 |
| `SourceRef` / `EvidenceRef` / `VersionRef` / `SnapshotRef` / `TraceRef` / `UserConfirmationRef` / `OwnerRef` | `reference` | 跨对象引用、证据、版本、归属和确认记录 |

### 4.3 候选 / 确认 / AI 输出交接（Candidate / Confirmation / AI Output Handoff）

本节只定义 AI 输出从 Prompt contract 进入数据模型和 API 契约的逻辑承载边界，不定义物理表、DDL、ORM、索引、migration、API endpoint 或完整 request / response schema。`PROMPT_SPEC.md` 负责 AI Task Contract 的输入输出和校验规则，`API_SPEC.md` 负责具体接口状态、response envelope、确认动作和资源展示语义。

AI Task Contract 的输出必须先落入以下一种或多种逻辑对象，不得把候选或建议直接写成正式业务对象：

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `CandidateRef` | `candidate_id`、`candidate_type`、`owner_ref`、`source_refs`、`evidence_refs`、`trace_refs`、`low_confidence_flags`、`candidate_status`、`user_confirmation_required`、`created_at`、`updated_at` | 表示 AI 生成的待确认候选对象引用，可用于 `WeaknessCandidate`、`AssetCandidate` 和后续 Training candidate；用户确认前不得升级为正式对象 |
| `UserConfirmationRef` | `confirmation_id`、`owner_ref`、`actor_ref`、`target_ref`、`target_type`、`action_type`、`action_result`、`before_summary`、`after_summary`、`confirmed_at`、`trace_ref`、`audit_event_ref` | 表示用户对候选、合并建议、状态更新建议、资产归档、训练建议等回流动作的确认记录，不是单纯 boolean |
| `UserCorrectionRef` | `correction_id`、`owner_ref`、`actor_ref`、`candidate_ref`、`base_candidate_version_ref`、`validation_result_ref`、`audit_event_ref`、`corrected_at` | 表示用户对低置信 candidate / suggestion 的校对保存记录；校对后仍需 validation 和 confirmation，不直接覆盖正式对象或 Prompt source |
| `AiTaskResultRef` | `ai_task_result_id`、`ai_task_id`、`contract_id`、`owner_ref`、`status`、`source_refs`、`source_availability`、`evidence_refs`、`validation_result_ref`、`low_confidence_flags`、`trace_refs`、`created_at`、`updated_at` | 表示一个 AI Task Contract 或 API AI task 的输出结果引用，用于追踪具体 contract 生成结果；不等于 LLM provider response |
| `SuggestionRef` | `suggestion_id`、`suggestion_type`、`target_ref`、`source_refs`、`evidence_refs`、`confidence`、`low_confidence_flags`、`user_confirmation_required`、`status`、`trace_refs` | 表示建议对象，例如 merge suggestion、severity assessment、status update suggestion 或 next recommended action；不等于正式业务动作 |

公共规则：

- 正式业务对象包括 `Weakness`、`Asset`、`AssetVersion`、确认后的 `TrainingRecommendation`、`TrainingTask` 等具有正式生命周期的对象。
- 候选对象包括 `WeaknessCandidate`、`AssetCandidate` 和 `TrainingRecommendation` candidate；候选对象必须绑定 `CandidateRef` 或等价字段。
- 建议对象包括 `WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion`、`AssetQualityHint`、`AssetVersionSuggestion`、`TrainingPriorityRanking` 和 `TrainingResultReview`；建议对象必须绑定 `SuggestionRef` 或等价字段。
- 用户确认记录必须能区分确认主体、确认动作、目标对象、目标类型、确认时间、确认前后摘要和失败状态。
- 用户校对记录必须保留被校对 candidate / suggestion、基础版本、validation result 和 audit 引用；它只能成为后续 confirmation 或 task input，不反向污染 Prompt source。
- validation result、low confidence flag、trace、evidence 和 audit event 是 AI 输出交接的独立引用，不得被折叠成一段不可追溯文案。
- `TrainingRecommendation` 可先以候选态存在；用户确认前不得自动成为正式训练建议。
- `TrainingTask`、`TrainingSession`、`Asset`、`AssetVersion` 或正式 `Weakness` 不得从 AI 输出直接写入。
- 所有候选 / 建议对象都要能绑定 `UserConfirmationRef` 或明确 `user_confirmation_required`。

### 4.4 API 幂等、AI Task、Trace 与持久化承接

本节补齐 `AR-F4-F8-001` 中 `API_SPEC.md` 字段级 contract 所依赖的逻辑承接。这里仍是逻辑数据模型，不是物理表、队列、DDL、索引或 migration；F5 可以按实现需要拆分存储，但不得删除以下语义字段或绕过 owner / trace / audit 边界。

#### 4.4.1 IdempotencyRecord

`IdempotencyRecord` 承接所有创建、确认、复制审计、AI task create / retry / cancel 和其它可能重复提交的 mutation。固定幂等范围为 `scope = actor_id + method + path + idempotency_key + request_body_hash`。

| 字段 | 必要性 | 规则 |
|---|---|---|
| `idempotency_record_id` | 必须 | 逻辑记录 ID；不得暴露为业务对象 ID |
| `scope` | 必须 | 固定为 `actor_id + method + path + idempotency_key + request_body_hash` |
| `actor_ref` / `owner_ref` | 必须 | 当前登录 actor 和 owner 边界；不得由请求体 owner_id 决定 |
| `method` | 必须 | HTTP method |
| `path_template` | 必须 | 例如 `/api/v1/reports/{report_id}/copy-events`，不保存 query 中的敏感正文 |
| `idempotency_key` | 必须 | `Idempotency-Key` header 值；日志只可记录 hash 或摘要 |
| `request_body_hash` | 必须 | 标准化 request body 的 hash；不得保存原始敏感正文 |
| `first_response_ref` / `response_snapshot` | 必须二选一 | 重复请求返回第一次 response 等价结果或当前 task status；snapshot 不得包含 provider payload、Prompt、completion 或敏感正文 |
| `linked_ai_task_id` | 条件必需 | 异步任务创建、retry 或 cancel 时绑定对应 `AiTask.ai_task_id` |
| `target_ref` | 建议 | 被创建、确认、复制审计或重试的目标引用 |
| `created_at` | 必须 | 首次接收时间 |
| `expires_at` | 必须 | TTL 过期时间；MVP 默认不少于 24 小时，具体实现由 F5 冻结 |
| `conflict_behavior` | 必须 | same key + same body 返回第一次 response；same key + different body 返回 `idempotency_conflict` |
| `audit_event_ref` | 必须 | 记录创建、复用、冲突或异常过期审计事件 |

幂等规则：

- idempotent retry 不得重复创建 `Resume`、`Job`、`InterviewReport`、`Review`、`Asset`、`Weakness`、`TrainingRecommendation`、`TrainingTask`、candidate、suggestion 或 `AiTask`。
- 异步 task 的重复创建返回同一个 `ai_task_id` 或等价当前状态；不得重新排队导致重复 candidate / suggestion / formal object。
- 同一 `idempotency_key` 携带不同 `request_body_hash` 时必须拒绝，不能把后一次请求覆盖为“修正”。
- 幂等记录自身不保存 request / response body 明文、简历正文、岗位正文、报告正文、复盘正文、Prompt、completion、provider payload、token、cookie、secret 或隐藏评分规则。

#### 4.4.2 AiTask 与 AiTaskResult

`AiTask` 是 API 层可查询、可重试、可取消的异步任务逻辑对象；`AiTaskResult` 是任务结果和候选 / 建议 / validation / trace 的逻辑承接。两者都不等同于 provider task、物理队列任务或 Prompt contract ID。

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `AiTask` | `ai_task_id`、`owner_ref`、`actor_ref`、`task_type`、`status`、`contract_ids`、`target_ref`、`input_refs`、`idempotency_record_ref`、`created_at`、`updated_at`、`timeout_at`、`cancelled_at`、`retry_count`、`retryable`、`user_visible_status` | 对外暴露为 API task status；`contract_ids` 必须来自 `PROMPT_SPEC.md` canonical registry；`target_ref` 和 `input_refs` 必须通过 owner / source availability 校验 |
| `AiTaskResult` | `ai_task_result_id`、`ai_task_id`、`owner_ref`、`task_type`、`status`、`result_ref`、`candidate_refs`、`suggestion_refs`、`validation_result_ref`、`low_confidence_flags`、`source_availability`、`evidence_refs`、`trace_refs`、`created_at`、`updated_at` | 保存结构化结果引用、候选、建议、校验、低置信度、来源可用性、证据和 trace；不保存 provider response 原文 |
| `AiTaskResultRef` | `ai_task_result_id`、`ai_task_id`、`contract_id`、`owner_ref`、`status`、`result_ref`、`validation_result_ref`、`low_confidence_flags`、`evidence_refs`、`trace_refs` | 跨 API / Prompt / Data 的轻量引用；可进入 response envelope、candidate、suggestion、report、review、weakness、asset、training 等结果 |

状态和写入规则：

- `status` 至少包含 `queued`、`running`、`succeeded`、`partial`、`low_confidence`、`validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled`。
- `retry_count`、`retryable`、`timeout_at`、`cancelled_at` 必须能支撑 `API-AITASK-004` retry 与 `API-AITASK-005` cancel。
- `cancelled`、`timed_out`、`generation_failed`、`validation_failed` 和 `source_unavailable` 不得产生 late formal write。
- `candidate_refs` / `suggestion_refs` 只表示候选或建议；成为正式 `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation` 或 `TrainingTask` 必须走 `UserConfirmationRef` 或显式业务动作。
- `result_ref` 指向结构化业务结果或可展示结果引用，不是 raw completion、provider response、system prompt、Prompt 模板或隐藏评分规则。

#### 4.4.3 ApiRequestTrace 与 TraceRef

`ApiRequestTrace` 记录一次 API 请求的最小追踪事实，服务于 F7 contract tests、权限审计、幂等复核、source unavailable 和失败排障。

| 字段 | 必要性 | 规则 |
|---|---|---|
| `api_request_trace_id` | 必须 | API request trace 逻辑 ID |
| `request_id` | 必须 | 来自 `X-Request-Id` 或服务端生成 |
| `trace_id` | 必须 | 服务端链路追踪 ID |
| `actor_ref` | 必须 | 当前登录 actor；匿名业务 API 不应进入业务处理 |
| `endpoint_ref` | 必须 | `ApiEndpointRef`，包含 API ID、method、path_template 和 domain |
| `method` | 必须 | HTTP method |
| `path_template` | 必须 | route template；不得保存敏感 path 变体正文 |
| `resource_refs` | 条件必需 | 目标资源、复合输入资源、candidate、suggestion、report、review 或 task refs |
| `ai_task_id` | 条件必需 | 创建、查询、重试、取消 AI task 时记录 |
| `validation_result_ref` | 条件必需 | request validation、output validation 或 business validation 结果 |
| `audit_event_ref` | 条件必需 | owner mismatch、permission denied、copy event、confirmation、source unavailable、validation failed 等关键事件 |
| `created_at` | 必须 | 请求追踪创建时间 |
| `log_redaction_boundary` | 必须 | 明确不保存 request / response body、provider payload、system prompt、completion 原文、隐藏评分规则、token、cookie、secret、简历正文、岗位正文、回答正文、报告正文或复盘正文 |

`TraceRef` 可以引用 `ApiRequestTrace`、`RAGContextAssembly`、`LlmRequestTrace`、`LlmValidationResult`、`AuditEvent` 或 persistence handoff；但 trace 可追踪不等于原文可见。前端只接收必要 `trace_id` / `trace_refs` 和安全摘要。

#### 4.4.4 AuditEvent 覆盖范围

`AuditEvent` 至少覆盖以下 API / persistence 事件：

| 事件 | 必须记录 | 不得记录 |
|---|---|---|
| copy event / report copy boundary | actor、report_ref、copy_content_ref、copy_surface、result、request_id、trace_id | 复制正文、报告全文、Prompt、provider payload、隐藏评分规则 |
| owner mismatch | actor、target_ref、endpoint_ref、result、risk flag | 目标资源正文或可泄露存在性的详细信息 |
| permission denied | actor、role_scope、endpoint_ref、target summary、result | token、cookie、secret、敏感正文 |
| candidate confirmation | actor、candidate_ref / suggestion_ref、action、before_summary_ref、after_summary_ref、result | 大段原文、Prompt、completion |
| AI task create / retry / cancel | actor、ai_task_id、task_type、contract_ids、result、idempotency_record_ref | provider task payload、模型参数、Prompt 文案 |
| source unavailable | actor、source_ref、source_status、target_ref、result | 已删除或禁用来源正文 |
| validation failed | actor、endpoint_ref、validation_result_ref、failure_signals、result | request body、response body、原始模型输出 |
| export_not_supported | actor、endpoint_ref、attempted_semantic、result | 任何导出物、filename、download URL 或文件快照 |

#### 4.4.5 持久化交接（Persistence handoff）

- candidate / draft / suggestion 不能静默写正式对象；正式对象必须经过用户确认、用户编辑、合并确认、显式业务动作或明确状态转换。
- `WeaknessCandidate`、`AssetCandidate`、`AssetVersionSuggestion`、`TrainingRecommendation` candidate、`WeaknessMergeSuggestion`、`WeaknessStatusUpdateSuggestion` 和 `TrainingPriorityRanking` 默认不是正式事实。
- formal object 写入必须记录 `UserConfirmationRef`、`AuditEvent`、`TraceRef`、owner、source / evidence 和版本引用。
- idempotent retry 不得重复创建 formal object；如果第一次请求已创建 task 或结果，重复请求返回同一 task / result / response snapshot。
- async task result 与 formal object 的边界必须显式：`AiTaskResult` 可产生 candidate / suggestion / validation result；只有确认流或显式业务动作才能创建或更新 `Weakness`、`Asset`、`AssetVersion`、正式 `TrainingRecommendation` 或 `TrainingTask`。
- validation failed、low confidence、source unavailable、generation failed、provider unavailable、task timeout 和 cancel 后的结果不得被报告读取、copy content 或前端视为高置信正式事实。
- 持久化实现不得为了排障保存 provider payload、system prompt、completion 原文、隐藏评分规则或未脱敏正文；排障只使用 `ApiRequestTrace`、`TraceRef`、`LlmValidationResult`、`LlmFailureRecord`、`AuditEvent` 和安全摘要。

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

### 5.2 简历、版本与 Markdown 派生结构

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Resume` | 所有者、简历名称、目标方向、当前版本、资料状态、创建 / 更新时间 | 简历是岗位匹配、模拟面试和复盘的基础输入，不承载资产库材料、复盘结论、打磨记录或薄弱项 |
| `ResumeVersion` | 简历标识、版本号或版本序列、Markdown 正文、摘要、来源（`markdown_paste` / `manual_input`）、创建时间、创建原因 | 匹配分析、会话、报告和复盘应引用版本，而不是只引用可变的 `Resume` |
| `ResumeMarkdownOutline` | 简历版本、派生节点类型、标题、Markdown 位置范围、可展示摘要、识别状态、证据摘要 | derived / non-persistent；用于定位、预览、上下文装配和引用，不建立独立 owner、version 或 CRUD；`project_experience` 只是节点类型或正文片段 |

MVP 不要求保存 `original_file`、`parsed_file`、MIME、文件名或文件大小；`file_upload` / PDF 类来源如未来需要，只能作为 Deferred enum 扩展，不能成为 MVP required path。项目经历只是 Markdown 正文片段，普通 API 不单独识别、查询、修改或新增项目经历模块。简历版本创建触发、版本保留策略和历史引用细节按 §8 / §12 的 F4 处置表承接：保存 Markdown 正文时创建新 `ResumeVersion`，历史结果引用生成时版本或快照，回滚以新版本写入而不改写历史。

### 5.3 岗位 / JD、版本与状态

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Job` | 所有者、岗位名称、公司、部门、投递状态、当前版本、资料状态、创建 / 更新时间 | 岗位仅来自用户手动录入，不保存外部材料解析来源 |
| `JobVersion` | 岗位标识、版本号或版本序列、岗位职责、岗位要求、其他、创建时间、创建原因 | 匹配分析和历史报告应引用生成时的岗位版本 |
| `JobStatus` | 岗位标识、状态类型、状态值、状态更新时间 | 区分资料状态与投递状态；用户可见枚举以 UX / API 后续契约为准，不重开 F2 UX UNKNOWN |
| `JobResumeBinding` | 岗位、岗位版本、简历、简历版本、绑定状态、绑定 / 解绑时间、`unbound_by`、是否当前有效、`preserved_history_refs`、`affected_default_entry_summary` | 支撑岗位详情绑定 / 解绑简历模块、匹配分析生成和历史记录回看；解除绑定只改变当前默认关系，不删除历史报告、复盘、匹配分析或会话引用 |
| `JobBindingSummary` | `not_bound` / `bound` 状态、当前绑定 ID、绑定简历标题、绑定版本、绑定时间、解绑后默认入口摘要 | 由 `JobResumeBinding` 派生，服务 F6 Job list/detail，不定义物理表或新生命周期 |
| `JobMatchSummary` | `match_not_generated`、`match_queued`、`match_running`、`match_succeeded`、`match_low_confidence`、`match_failed`、`match_stale`、最新分析 ID、产品匹配分、`score_scale`、`score_version`、`rubric_version`、摘要、置信度、生成时间、stale 原因 | 由 `JobMatchAnalysis` 和相关 task 状态派生；不返回精确通过概率，不重算历史匹配 |

岗位版本策略按 §8 / §12 的 F4 处置表承接：岗位正文保存时创建新 `JobVersion`，投递状态保存在 `JobStatus`，历史匹配分析和报告引用生成时岗位版本；岗位编辑不静默重算历史结果。

### 5.4 岗位匹配分析

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `JobMatchAnalysis` | 岗位版本、简历版本、绑定关系、分析状态、生成时间、低置信度标记、解释摘要 | 一次分析结果引用固定版本，不能随简历或岗位编辑自动变形 |
| `MatchScore` | `ScoreResult` 引用、分数类型、`score_value`、`score_scale=0_100_product_scale`、`score_version`、`rubric_version`、`confidence_level`、解释、生成来源 | 岗位匹配视图包装，只引用 canonical `ScoreResult`；0-100 是产品评分刻度，不是精确通过概率 |
| `MatchPoint` | 分析标识、标题、说明、证据引用、排序 | 表达匹配点 |
| `MismatchPoint` | 分析标识、标题、说明、证据引用、影响范围、排序 | 表达不匹配点 |
| `ImprovementPoint` | 分析标识、标题、建议动作、关联薄弱项、证据引用 | 表达加强点 |
| `EvidenceSummary` | 来源对象类型、来源版本、片段摘要、置信度提示、可展示性 | 关联解释、证据和低置信度提示 |

匹配分析可以提炼薄弱项，但薄弱项写入应通过 `Weakness` / `FeedbackLoop` 记录，不能隐式覆盖既有薄弱项。

### 5.5 模拟面试会话、题目、回答与反馈

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `InterviewSession` | 所有者、会话名称、模式、岗位版本、简历版本、状态、启动来源、创建 / 更新时间 | 统一承载打磨模式和压力面模式；模式值至少区分 `polish` 与 `pressure` |
| `PolishSessionDetail` | 会话、当前题目、当前节点、同题轮次、`PolishTopicRef`、`PolishSubtopicRef`、`custom_topic_text` 安全摘要、暂停恢复快照引用、下一步建议 | 支撑同题多轮回答、主题 / 次主题上下文装配、题目生成、暂停恢复和内容沉淀；主题 / 次主题不是正式业务对象 |
| `PressureSessionDetail` | 会话、当前题目、追问链、`PressureTurn` refs、节奏状态、中断状态、end condition ref、session score ref、report input package ref、review handoff refs | 支撑连续追问、中断、暂停恢复、结束后报告输入和模拟面试复盘 handoff；具体 mode-level 语义见 `PRESSURE_MODE_SPEC.md` |
| `Question` | 会话、进展节点、题目正文、题目类型、来源上下文、生成状态、生成时间 | 可来源于岗位、简历、薄弱项、资产或进展树节点 |
| `Answer` | 题目、用户、回答正文、回答轮次、提交时间、保存状态 | 支撑打磨模式同题多轮回答和压力面连续问答 |
| `Feedback` | 回答、点评摘要、下一步建议、生成状态、低置信度标记 | 聚合评分、失分点、参考回答和考点解析 |
| `SessionSummary` | `id`、`owner_id`、`session_id`、`session_type` / `mode`、`summary_status`、`summary_version`、`covered_turn_refs`、`source_session_snapshot_ref`、`current_topic`、`asked_question_refs`、`forbidden_repeat_refs`、`open_threads`、`closed_threads`、`weakness_candidate_refs`、`asset_candidate_refs`、`risk_flags`、`low_confidence_flags`、`trace_ref`、`created_at`、`updated_at` | 会话摘要逻辑对象；通过模式区分打磨、压力面、复盘等场景，供后续 Context Assembly 使用 |
| `LossPoint` | 关联反馈或报告、失分说明、证据、建议动作 | 可转化为薄弱项候选 |
| `ReferenceAnswer` | 关联题目或反馈、参考回答正文、适用场景、与失分点对应关系 | 仅保存结果，不定义 Prompt 模板 |
| `KnowledgePointExplanation` | 关联题目或反馈、考点、解析、技术原理扩展 | 支撑打磨反馈和报告展示 |

#### 5.5.1 SessionSummary 逻辑对象约束

`SessionSummary` 是逻辑对象，不是物理表设计，不绑定具体数据库、ORM、DDL、索引或 migration。它用于表达会话摘要的最小可追踪承载位置，具体 API 字段和持久化实现由后续 `API_SPEC.md` / F5 承接。

约束如下：

- `SessionSummary` 不替代原始问答记录、题目、回答、点评、评分或追问链。
- `SessionSummary` 不是唯一事实源；事实性结论仍应通过 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef` 或业务对象引用追踪。
- `covered_turn_refs` 必须能回溯到被摘要覆盖的题目、回答、点评、评分或追问记录。
- `source_session_snapshot_ref` 用于暂停 / 恢复、报告前、复盘前或会话结束时引用对应会话快照或等价快照。
- `summary_version` 必须递增或形成可追溯版本链；历史版本不得被当前 summary 覆盖到不可回溯。
- `asked_question_refs` 与 `forbidden_repeat_refs` 用于后续 Context Assembly 避免重复追问。
- `open_threads` 与 `closed_threads` 表达仍需继续追问、已完成或已关闭的话题，不替代进展树状态。
- `weakness_candidate_refs` 与 `asset_candidate_refs` 只引用候选，不因摘要更新静默转为正式薄弱项或正式资产。
- `risk_flags` 与 `low_confidence_flags` 必须继承摘要覆盖范围内的低置信度、冲突、不完整、来源不可用或 summary 生成失败状态。
- 低置信度内容进入 summary 时必须携带风险标记，并影响后续 Context Assembly 的置信度表达。

#### 5.5.2 评分规则版本与解释链路

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `ScoreRuleSet` | 规则集标识、适用场景、状态、当前版本、创建 / 更新时间 | 归集匹配分析、回答点评、报告和复盘可引用的评分规则族 |
| `ScoreRuleVersion` | 规则集、版本号、`rubric_version`、适用阶段、启用状态、维度权重元数据、创建原因、生效时间、停用时间 | `ScoreResult` 必须引用生成时使用的评分规则版本；同一版本内权重总和为 100 |
| `ScoreDimension` | 规则版本、维度名称、维度说明、适用对象、权重、排序 | 表达评分维度和权重策略；权重来自 rule version 元数据，不由 LLM 单次输出临时发明 |
| `ScoreRubric` | 规则版本、维度、等级或区间说明、解释模板引用、校准样例集引用 | 保存评分解释需要的 rubric 边界和最小校准样例引用；不承诺精确通过概率 |
| `ScoreResult` | 关联对象、`ScoreRuleVersion`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`VersionRef`、`SnapshotRef`、`TraceRef`、`generated_by_task_id`、`score_version`、`rubric_version`、`score_type`、`score_value`、`score_scale`、`confidence_level`、`validation_status`、`generated_at`、`created_at`、`updated_at` | 可关联匹配分析、回答反馈、报告、复盘或训练结果；`score_value` 是 0-100 产品展示分，不是通过概率；必须能追溯评分规则版本、输入来源版本或快照、证据链、解释链路和相关 LLM validation 结果 |
| `ScoreExplanation` | 评分结果、解释摘要、命中维度、维度权重引用、低置信度标记、冲突或不完整标记、非决策性免责声明引用 | 面试报告、题目点评、弱项识别和训练建议应引用解释对象而不是复制散落文案 |
| `ScoreEvidenceLink` | 评分结果、证据对象、证据版本、片段摘要、证据作用、可展示性、source availability | 连接题答、报告、复盘、RAG 证据或用户确认记录；source unavailable 时只保留 ref / snapshot / summary status |
| `LowConfidenceFlag` | 关联对象、触发原因、影响范围、建议校对入口、状态 | 低置信度、冲突、不完整和失败都应作为状态或风险标记进入数据模型 |

本文冻结 `AR-F4-FULL-003` 的最小评分承载边界：正式评分只保留 `score_value` / `display_score` 作为 0-100 产品刻度，不同时持久化 `raw_score`、`normalized_score` 和 `display_score` 三套正式分数。若 LLM 生成 scoring candidate / draft，候选原始值只能进入 `LlmValidationResult`、trace 或 repair 路径；通过结构化校验、业务语义校验、evidence binding、低置信度分类和版本记录后，才允许形成正式 `ScoreResult`。

Rubric / rule version 的最小维度如下：

| score type | MVP rubric dimensions | 默认权重策略 |
|---|---|---|
| `job_match` | `requirement_alignment`、`experience_evidence`、`skill_coverage`、`gap_risk`、`readiness_actions` | `30/25/20/15/10`，写入 `ScoreRuleVersion` |
| `polish_round` / `pressure_session` / `report_section` | `answer_relevance`、`technical_depth`、`communication_structure`、`evidence_specificity`、`risk_control` | `25/25/20/15/15`，写入 `ScoreRuleVersion` |

权重是 rule version 元数据，不在前端暴露隐藏评分规则；API 可以返回 score、维度解释、版本和证据摘要，但不得返回可反向复制内部评分细则的隐藏规则。

版本变更规则：

- 历史 `ScoreResult`、`InterviewReport` 和 `ReviewItem` 保留生成时的 `score_version`、`rubric_version`、`ScoreRuleVersion`、`VersionRef` / `SnapshotRef`、`EvidenceRef` 和 `TraceRef`。
- 不同 `ScoreRuleVersion` 的分数不可直接强比较，除非后续引入明确校准映射。
- 重新评分必须生成新的 `ScoreResult` 或新版本结果，不改写历史评分。
- MVP 校准不依赖真实招聘结果；最小校准由 rule version、人工验收样例集和 F7 回归 fixture 组成。真实结果校准为 `LATER` / `SHOULD`，且校准数据不得包含未脱敏第三方隐私。

通过倾向和风险提示的承载边界：

- `pass_tendency_level` 只允许 `low` / `medium` / `high` / `caution` / `insufficient_evidence`，对应用户可见文案为“偏低 / 中等 / 偏高 / 需谨慎 / 证据不足，无法判断倾向”。
- 禁止保存或展示精确通过概率、录取概率、offer 概率、通过率百分比或等价字段。
- `RiskSignal` / 报告风险项至少包含 `risk_level`、`risk_reason`、`confidence_level`、`evidence_refs`、`score_version`、`rubric_version`、`rule_version_ref`、`validation_status` 和 `low_confidence_flags`；如不新增独立一级对象，可由 `ReportSection`、`ReviewItem` 或等价风险字段承载。
- 低置信度、证据不足、source unavailable 或 validation failed 时，不得给出确定性通过倾向，只能进入 `insufficient_evidence` 或 `manual_review_required`。

打磨模式和压力面模式暂停恢复的最小快照边界已冻结：`InterviewSession` / mode detail 保存 owner、mode、current question、current answer draft 或 submitted answer ref、`ProgressPosition`、`SessionSummary`、last stable `TraceRef`、low confidence / failure flags、updated_at 和 resume attempt status；恢复必须校验 `source_session_snapshot_ref`、`covered_turn_refs`、`ProgressPosition` 和 source availability，失败时进入 `pause_snapshot_unavailable`、`resume_failed`、`source_unavailable` 或 `partial`，不得重复生成题目、丢弃进展或隐藏低置信度继承。

### 5.6 进展树

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `ProgressTree` | 会话、整体进度、生成来源、状态、更新时间 | 打磨模式和压力面模式都应具备进展树 |
| `ProgressNode` | 进展树、父节点、节点类型、标题、状态、排序、完成度、来源证据 | 节点可表达技术点、项目经历、能力项、自我介绍、软技能、行为面、薄弱项、题目或训练主题 |
| `ProgressPosition` | 会话、当前节点、当前题目、当前位置更新时间、恢复状态 | 支撑当前位置展示和暂停恢复 |

进展树数据结构和最小状态域已冻结：`ProgressTree` / `ProgressNode` / `ProgressPosition` 支撑能力项、题目、薄弱项、训练主题和会话位置；节点状态至少使用 §7 的 `not_started`、`in_progress`、`completed`、`suggested`、`paused`、`blocked`。更细的推荐排序和 UI 展示策略由 UX / F7 fixture 承接，不阻断 M4。

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
| `InterviewReport` | 会话、报告状态、总体评分、通过倾向分档、风险摘要、低置信度标记、生成时间、可复制内容引用、`score_version`、`rubric_version`、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、`TraceRef` | 来源于打磨阶段性完成或压力面结束；生成后应引用生成时的 `ResumeVersion` 或简历快照、`JobVersion` 或岗位快照、`InterviewSession` 快照和 `ScoreRuleVersion`；通过倾向不是通过概率 |
| `ReportSection` | 报告、分项类型、标题、正文、分项评分、`risk_level`、`risk_reason`、`confidence_level`、`evidence_refs`、排序 | 承载表现总结、主要失分点、具体建议、参考回答、考点解析、技术原理扩展、薄弱项和训练方向；风险提示必须绑定证据和版本 |
| `CopyableContent` | 报告、可复制范围、内容片段、生成状态 | 只表示页面复制所需的结构化内容边界；不是导出物、不是下载文件、不是批量产物，也不代表 Markdown / PDF / docx 文件生成能力 |
| `InterviewRetrospective` | 复盘类型、关联会话或真实面试输入、岗位版本、简历版本、状态、低置信度标记 | 统一承载模拟面试复盘和真实面试复盘 |
| `ReviewSummary` | 复盘 ID、复盘类型、展示标题、来源摘要、创建 / 更新时间、状态、置信度、`source_availability`、关联报告 / 会话引用、下一步动作 | 统一承接 `GET /api/v1/reviews` 列表投影；同时覆盖模拟面试复盘和真实面试复盘，不新增物理表要求 |
| `MockInterviewReview` | 复盘、会话、报告、题目 / 回答 / 点评引用、评分引用、`VersionRef`、`SnapshotRef`、`TraceRef` | 来源于系统内模拟面试会话、题目、回答、点评、评分、报告和薄弱项；应引用生成时的系统内会话链路版本或快照 |
| `RealInterviewReview` | 复盘、真实面试输入版本、用户补充材料、面试官反馈或结果状态、岗位版本、简历版本、可信度摘要、完整度摘要 | 来源于用户手动录入的真实面试信息，不假设系统拥有完整真实面试过程；必须标注可信度和完整度 |
| `RealInterviewInput` | 所有者、面试时间、公司 / 岗位、问题回忆、回答回忆、面试官反馈、结果状态、补充材料 | 真实面试复盘的主要输入，字段可为空或部分可用 |
| `RealInterviewEvidence` | 真实面试输入、来源类型、内容摘要、可信度、完整度、用户确认状态 | 显式标注输入可信度、完整度和证据来源 |
| `ReviewItem` | 复盘、题目摘要、回答摘要、表现、失分点、建议、证据、来源引用、`TraceRef`、`LowConfidenceFlag` | 支撑题级复盘、薄弱项提炼和训练建议，并可回溯到 RAG / LLM / validation 链路 |
| `ReviewSourceRef` | 复盘或复盘项、来源对象、来源版本、来源类型、置信度 | 区分模拟复盘的系统内证据和真实复盘的用户录入证据 |
| `CopyableReviewContent` | 复盘、可复制范围、内容片段、脱敏状态、第三方隐私脱敏摘要、生成状态 | 只表示复盘详情页面复制所需的结构化内容边界；不得包含 system prompt、provider payload、隐藏评分规则或未脱敏第三方 / 公司 / 面试官 / 他人隐私 |
| `ReviewCopyEvent` | 复盘、复制内容 ID、actor、复制范围摘要、结果、时间、`AuditEvent` | 记录复盘复制审计；不得记录复制正文、provider payload 或敏感原文 |

模拟复盘主要来源于系统内会话、题目、回答、点评、评分、报告和弱项；真实面试复盘主要来源于用户手动录入的真实面试问题、回答回忆、面试官反馈、结果状态和补充材料。两类复盘都可以沉淀薄弱项、训练建议和资产候选，但来源、完整度和置信度必须分别记录。

复盘材料最小切分边界已冻结：模拟复盘按 session / report / question-answer / feedback / score refs 切分为 `MockInterviewReview` 和 `ReviewItem`；真实复盘按用户手动录入的 `RealInterviewInput`、可信度、完整度和 `RealInterviewEvidence` 切分为 `RealInterviewReview` 和 `ReviewItem`。跨复盘聚合、题级合并算法和最终 UX 展示细节为 deferred_non_blocking，不阻断 M4。

### 5.9 薄弱项、资产、训练建议与回流

| 对象 | 必要字段组 | 关系与说明 |
|---|---|---|
| `Weakness` | 所有者、主题、严重程度、当前状态、关联岗位、关联简历、更新时间 | 来源于匹配分析、报告、复盘或打磨反馈 |
| `WeaknessCandidate` | `candidate_id`、`owner_ref`、标题、描述、`source_type`、`source_refs`、`evidence_refs`、`weakness_evidence_refs`、`related_review_item_refs`、关联岗位要求、关联简历模块、严重度提示、置信度、`merge_candidate_refs`、建议训练方向、`candidate_status`、`user_confirmation_required`、`user_confirmation_ref`、`low_confidence_flags`、`trace_refs` | 表示薄弱项候选，可由 Job Match、Polish、Pressure、Report、Review 或用户显式请求产生；不等于正式 `Weakness`，默认需要用户确认；单次轻微失误不得直接高置信升级为正式 Weakness |
| `WeaknessEvidence` | 薄弱项或候选薄弱项、`source_refs`、source artifact、source version / snapshot、`EvidenceRef`、`TraceRef`、证据摘要、置信度、`LowConfidenceFlag`、用户确认状态 | 可来源于 Job Match、Polish、Pressure、Report、Review、用户确认或训练结果；source unavailable 时不得重新读取正文，只保留 ref / snapshot / summary status |
| `WeaknessMergeSuggestion` | `suggestion_id`、`owner_ref`、`candidate_ref`、`target_weakness_ref`、`merge_recommendation`、`merge_reason`、`similarity_signals`、`conflict_signals`、`evidence_refs`、`confidence`、`manual_review_required`、`user_confirmation_required`、`user_confirmation_ref`、`trace_refs` | 表示候选 Weakness 与既有 Weakness 的合并建议；不自动合并、不覆盖既有 Weakness，用户确认前不得改正式对象 |
| `WeaknessSeverityAssessment` | `assessment_id`、`weakness_ref` 或 `weakness_candidate_ref`、`severity_hint`、`severity_reason`、`evidence_refs`、`recency_signals`、`frequency_signals`、`impact_signals`、`training_priority_hint`、`confidence`、`severity_unknown_flags`、`manual_review_required`、`trace_refs` | 表示严重度提示，不冻结严重度算法，不等于正式训练优先级 |
| `WeaknessStatusUpdateSuggestion` | `suggestion_id`、`weakness_ref`、`current_status`、`suggested_status`、`status_update_reason`、`supporting_evidence_refs`、`conflicting_evidence_refs`、`confidence`、`manual_review_required`、`user_confirmation_required`、`user_confirmation_ref`、`trace_refs` | 表示状态更新建议，不自动变更正式 Weakness 状态，用户确认前不得更新正式状态 |
| `WeaknessStatusHistory` | 薄弱项、前后状态、变更原因、触发来源、变更时间 | 支撑生命周期审计 |
| `Asset` | 所有者、资产标题、资产类型、当前版本、状态、可用场景、更新时间 | 资产库独立于简历 |
| `AssetVersion` | 资产、版本号或版本序列、正文、摘要、质量提示、创建原因、来源、适用岗位 / 简历 / 场景 | 历史会话和报告引用资产版本；新版本发布必须来自用户确认或显式业务动作 |
| `AssetCandidate` | `candidate_id`、`owner_ref`、来源类型、候选内容、目标资产、候选状态、用户编辑内容、确认状态、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、`TraceRef`、`UserConfirmationRef`、适用岗位 / 简历 / 场景引用 | 内容沉淀确认前的候选态；不等于正式 `Asset`，确认前不得写入正式 `Asset` / `AssetVersion`；训练建议不能直接等同于资产 |
| `AssetQualityHint` | `quality_hint_id`、`owner_ref`、`target_asset_ref`、`target_candidate_ref`、`target_asset_version_ref`、`quality_level_hint`、`quality_reason`、`reuse_readiness_hint`、`fact_boundary_risks`、`phrasing_risks`、`technical_accuracy_risks`、`missing_context`、`evidence_refs`、`confidence`、`low_confidence_flags`、`manual_review_required`、`trace_refs`、`suggestion_ref` | 表示资产候选或 `AssetVersion` 的质量提示；不冻结资产质量算法，不等于归档规则，不自动创建 / 发布 `AssetVersion`，可作为 `SuggestionRef` 的具体语义承接对象 |
| `AssetVersionSuggestion` | `suggestion_id`、`owner_ref`、`target_asset_ref`、`base_asset_version_ref`、`candidate_ref`、`suggested_action`、`suggested_content_delta`、`version_update_reason`、`evidence_refs`、`conflict_signals`、`confidence`、`user_confirmation_required`、`user_confirmation_ref`、`manual_review_required`、`trace_refs` | 表示资产版本更新建议；不自动替换、覆盖或发布 `AssetVersion`，用户确认前不得写入正式 `AssetVersion`，可作为 `SuggestionRef` 的具体语义承接对象 |
| `AssetSource` | 资产或候选、来源类型、`SourceRef`、`EvidenceRef`、`VersionRef`、`SnapshotRef`、证据摘要 | 保存来源与回流关联 |
| `AssetPromotionRecord` | 候选资产、目标资产、确认方式、确认人或规则、结果、时间 | 资产候选必须经过用户确认或规则确认后才能进入正式资产 |
| `TrainingRecommendation` | `recommendation_id`、`owner_ref`、建议主题、原因、优先级提示、适用入口、目标 Weakness / Asset、来源证据、`candidate_ref`、`user_confirmation_required`、`user_confirmation_ref`、状态 | 可先作为训练建议候选存在；用户确认前不得自动成为正式 `TrainingRecommendation`，不得自动创建 `TrainingTask` |
| `TrainingPriorityRanking` | `ranking_id`、`owner_ref`、`ranked_recommendations`、`recommendation_refs`、`priority_rank`、`priority_hint`、`priority_reason`、`evidence_refs`、`impact_signals`、`effort_signals`、`confidence`、`ranking_unknown_flags`、`manual_review_required`、`trace_refs`、`suggestion_ref` | 表示训练建议排序；不冻结训练优先级算法，不等于自动创建训练任务，可作为 `SuggestionRef` 的具体语义承接对象 |
| `TrainingTask` / `TrainingSession` | 训练建议、关联薄弱项、训练入口、状态、开始 / 完成时间、显式启动动作或确认引用 | 承载从建议到实际训练的执行过程；不得由 AI suggestion 自动创建，必须经过用户确认或显式用户动作 |
| `TrainingResult` | 训练任务、结果摘要、评分引用、弱项变化候选、资产候选引用、低置信度标记 | 训练完成后可产生回流候选，但不得直接更新正式 Weakness、正式 Asset 或正式 `TrainingRecommendation` |
| `TrainingResultReview` | `training_result_review_id`、`owner_ref`、`training_result_ref`、`training_task_refs`、`training_recommendation_refs`、`training_result_summary`、`target_weakness_refs`、`related_asset_refs`、`improvement_signals`、`remaining_gap_signals`、`weakness_status_update_candidate_refs`、`asset_candidate_refs`、`next_training_recommendation_candidate_refs`、`evidence_refs`、`low_confidence_flags`、`manual_review_required`、`trace_refs`、`candidate_refs`、`suggestion_refs` | 表示训练结果复盘；不自动更新正式 Weakness，不自动归档 Asset，不自动创建下一轮 `TrainingRecommendation`，只产生候选 / 建议态回流输入 |
| `FeedbackLoop` | 来源对象、目标集合、总体状态、创建时间、完成时间 | 表达内容沉淀确认流程 |
| `DepositTarget` | `target_type`、`target_ref`、目标可用状态、禁用原因、确认动作、`created_formal_ref` | 表示用户选择的沉淀目标；允许 `asset`、`weakness`、`training_suggestion`、`polish_input`、`pressure_input`、`next_interview_input`、`review_note`、`none` / `skip` |
| `UserConfirmation` | 回流记录、目标对象、`target_type`、确认动作、编辑后内容、目标级状态、失败原因、`created_formal_ref` | 保存确认、编辑、取消、跳过、写入中、写入成功和写入失败 |
| `CandidateCorrection` | candidate / suggestion、校对内容摘要、校对原因、`base_candidate_version_ref`、`confidence_override_reason`、`validation_result_ref`、`audit_event_ref` | 保存低置信校对结果；校对内容不能直接覆盖原始候选、正式对象或 Prompt source，只能进入后续 confirmation / task input |

资产自动沉淀、资产版本、合并、质量判断、训练优先级、训练结果评估、薄弱项合并和自动消减均以候选 / 建议 / 用户确认边界冻结：AI 只能生成 `AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`WeaknessMergeSuggestion`、`TrainingPriorityRanking` 或 `TrainingResultReview`；正式对象写入必须经过 `UserConfirmationRef`、显式用户动作或可审计规则确认。复杂质量算法、排序算法和自动消减规则为 deferred_non_blocking。

### 5.10 LLM 请求 / 响应 / 用量 / 校验 / 保留边界

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
2. `JobMatchAnalysis`、`InterviewSession`、`InterviewReport`、`InterviewRetrospective`、`WeaknessCandidate`、`WeaknessEvidence` 和 `AssetSource` 应引用生成时的 `ResumeVersion`、`JobVersion` 或具体来源对象版本。
3. `JobResumeBinding` 保存绑定关系本身；解除绑定必须写入 `unbound_at` / `unbound_by` / `preserved_history_refs` / `affected_default_entry_summary`，不得破坏历史报告、复盘、匹配分析或会话的可回看性。
4. 项目经历片段可以被题目、反馈、复盘、资产和证据引用，但必须通过 `ResumeVersion`、Markdown 位置范围或 derived `ResumeMarkdownOutline` 节点回溯；不得作为独立 version / owner / CRUD 对象管理。
5. `InterviewSession` 是题目、回答、反馈、进展树和报告的聚合根；打磨模式和压力面模式只在模式详情上分化。
6. `SessionSummary` 依附于 `InterviewSession`，通过 `covered_turn_refs`、`source_session_snapshot_ref`、`trace_ref` 和候选对象引用形成可回溯摘要；它可以被后续 Context Assembly 使用，但不能替代原始问答记录或证据引用。
7. `KnowledgeDocument` / `KnowledgeChunk` 可以被题目、点评、报告、复盘、评分解释、薄弱项和训练建议引用，但只能通过 `RetrievalEvidence`、`Citation` / `EvidenceRef` 或 `ScoreEvidenceLink` 进入业务对象。
8. `RetrievalResult` 进入 LLM 上下文前应有来源、版本、置信度或命中摘要；`RAGContextAssembly` 只记录组装边界，不替代 `PROMPT_SPEC.md` 的上下文策略。
9. `ScoreResult` 必须引用 `ScoreRuleVersion`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`VersionRef`、`SnapshotRef` 和 `TraceRef`；题目点评、面试报告、弱项识别和训练建议应能追溯到评分规则版本、输入来源版本或快照、证据、解释、低置信度 / 冲突 / 不完整标记和相关 LLM validation 结果。
10. `InterviewReport` 可以进入 `InterviewRetrospective`、`Weakness`、`TrainingRecommendation` 和 `FeedbackLoop`，但不自动写入资产或薄弱项。
11. `MockInterviewReview` 的来源是系统内会话链路；`RealInterviewReview` 的来源是用户手动录入材料，两者都必须通过 `ReviewSourceRef` 表达来源和置信度。
12. `FeedbackLoop`、`DepositTarget`、`UserConfirmation` 与 `CandidateCorrection` 是回流写入边界；系统建议必须先成为候选、校对记录、沉淀目标或确认记录，再进入资产、薄弱项、训练建议、打磨输入、压力输入、下一次模拟输入或复盘备注。
13. `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord` 和 `LlmValidationResult` 只提供追踪、校验和审计引用，不替代业务结果对象。
14. `AuditEvent` 只记录关键动作的最小审计字段，不定义企业级多租户、复杂 ACL、日志保留或脱敏细则。
15. `WeaknessCandidate` 只表达待确认候选，不得被前端、API 或后续训练链路当作正式 `Weakness`。
16. `WeaknessMergeSuggestion` 只表达合并建议，不等于实际合并动作；用户确认前不得覆盖既有 Weakness。
17. `WeaknessSeverityAssessment` 只表达严重度提示，不等于固定算法结果或正式训练优先级。
18. `WeaknessStatusUpdateSuggestion` 只表达状态更新建议，不等于实际状态变更。
19. `AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`UserCorrectionRef`、`UserConfirmationRef`、`LlmValidationResult`、`LowConfidenceFlag`、`TraceRef`、`EvidenceRef` 和 `AuditEvent` 应共同构成 AI 输出的最小可追踪交接链。
20. `AssetQualityHint` 应引用 `AssetCandidate` 或 `AssetVersion`、`EvidenceRef`、`TraceRef`、`LowConfidenceFlag` 和 `SuggestionRef`；它只表达质量提示，不等于自动归档规则。
21. `AssetVersionSuggestion` 应引用 `AssetCandidate`、目标 `Asset`、基础 `AssetVersion`、`EvidenceRef`、`TraceRef`、`LowConfidenceFlag`、`SuggestionRef` 和 `UserConfirmationRef`；确认前不得发布、覆盖或替换正式版本。
22. `TrainingPriorityRanking` 应引用 `TrainingRecommendation` candidate 或正式建议、`SuggestionRef`、`EvidenceRef`、`TraceRef` 和低置信度标记；排序是 hint，不自动创建 `TrainingTask` / `TrainingSession`。
23. `TrainingResultReview` 应引用 `TrainingRecommendation`、`TrainingTask` / `TrainingSession`、`TrainingResult`、`Weakness`、`Asset`、`CandidateRef`、`SuggestionRef`、`EvidenceRef` 和 `TraceRef`；回流到 Weakness / Asset / Training 必须保持候选态或建议态。
24. 不得从 AI 输出直接写正式 Weakness、正式 Asset、正式 AssetVersion、正式 TrainingRecommendation 或 TrainingTask。

### 6.1 RAG / LLM / 业务结果审计链路

一次 RAG / LLM 生成业务结果的最小审计链路如下：

1. `RAGContextAssembly` 可以引用 `RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`SourceRef`、`EvidenceRef`、`VersionRef` 和 `SnapshotRef`，用于说明本次上下文由哪些查询、命中证据、来源版本和快照组成。
2. `LlmRequestTrace` 可以引用 `RAGContextAssembly`、`SourceRef`、`VersionRef`、`SnapshotRef` 和 Prompt context 的逻辑边界，但不记录 Prompt 模板、模型调用参数或 provider-specific request payload。
3. `LlmResponseTrace` 可以引用 `LlmRequestTrace`、原始输出引用、结构化输出引用、`LlmValidationResult` 和 `TraceRef`，用于区分原始响应、结构化结果、校验结果和失败状态。
4. 结构化业务结果可以通过 `TraceRef` / `EvidenceRef` / `VersionRef` / `SnapshotRef` 回溯到 RAG evidence、LLM request、LLM response、validation result，以及 low confidence / conflict / incomplete 标记。
5. `ScoreResult`、`InterviewReport`、`ReviewItem`、`WeaknessEvidence`、`TrainingRecommendation` 和 `AssetCandidate` 至少需要支持上述回溯链，避免业务结果只保存不可解释文案。

本文不展开 Prompt 模板、模型调用参数、retry / fallback 策略、provider-specific request / response payload、向量数据库实现或 embedding 模型选型；这些内容交给 `PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。

## 7. 状态枚举与状态流

本节给出 F4 逻辑状态域，具体 API 返回值、错误码、response enum 和前端文案由 `API_SPEC.md` 承接。这些枚举是 F4 数据模型的最小冻结状态域；更细的实现状态机、UI 文案和回归 fixture 可由 F5 / F7 细化，但不得改变 candidate / suggestion / confirmation / formal object 边界。

| 对象域 | 建议状态域 | 基本状态流 |
|---|---|---|
| 简历资料状态 | `draft`、`available`、`needs_supplement`、`archived`、`deleted` | 草稿 -> 可用；可用 -> 需补充；可用 / 需补充 -> 废弃或删除候选 |
| Markdown outline 派生识别状态 | `pending`、`recognized`、`failed`、`partial` | 待识别 -> 已识别 / 失败 / 部分可用；只描述 derived outline，不建立模块 CRUD |
| 岗位资料状态 | `draft`、`available`、`needs_binding`、`needs_supplement`、`archived` | 草稿 -> 可用；可用 -> 待绑定 / 需补充；可用 -> 废弃 |
| 岗位投递状态 | `user_defined` 或后续枚举 | F2 已冻结用户可见投递状态入口；具体落库枚举由 API 契约固化 |
| 绑定关系状态 | `active`、`unbinding`、`unbound`、`failed` | 绑定中 -> 已绑定；解绑中 -> 已解除；失败后保留原关系 |
| 生成任务状态 | `not_generated`、`generating`、`generated`、`failed`、`low_confidence`、`partial` | 未生成 -> 生成中 -> 已生成 / 失败 / 低置信度 / 部分可用 |
| 会话状态 | `not_started`、`in_progress`、`paused`、`completed`、`interrupted`、`failed` | 未开始 -> 进行中 -> 暂停 / 完成 / 中断 / 失败 |
| 会话摘要状态 | `empty_initial`、`not_available`、`summary_updated`、`summary_partial`、`summary_failed`、`low_confidence_inherited` | 初始轮次可为空；无可用摘要时不阻断原始问答保存；失败或低置信度状态只影响后续上下文置信度 |
| 题目状态 | `draft`、`generated`、`answered`、`skipped`、`failed` | 草稿或生成中 -> 已生成 -> 已回答 / 跳过 |
| 回答状态 | `draft`、`submitted`、`saved`、`invalid` | 草稿 -> 已提交 -> 已保存；异常时标记无效 |
| 反馈状态 | `generating`、`available`、`failed`、`low_confidence`、`partial` | 生成中 -> 可用 / 失败 / 低置信度 / 部分可用 |
| 进展节点状态 | `not_started`、`in_progress`、`completed`、`suggested`、`paused`、`blocked` | 未开始 -> 进行中 -> 已完成；可被建议、暂停或阻塞 |
| 知识文档状态 | `draft`、`available`、`stale`、`archived`、`failed` | 草稿 -> 可用；可用 -> 过期 / 归档；处理失败时保留失败状态 |
| RAG 检索状态 | `not_started`、`retrieving`、`assembled`、`partial`、`low_confidence`、`failed` | 未开始 -> 检索中 -> 已组装 / 部分可用 / 低置信度 / 失败 |
| 报告状态 | `not_generated`、`generating`、`available`、`failed`、`low_confidence` | 未生成 -> 生成中 -> 可查看 / 失败 / 低置信度 |
| 复盘状态 | `not_generated`、`generating`、`needs_user_review`、`available`、`failed`、`low_confidence` | 未生成 -> 生成中 -> 待校对 / 可用 / 失败 |
| 薄弱项状态 | `weakness_detected`、`weakness_confirmed`、`low_priority`、`ignored`、`resolved_candidate`、`resolved`、`reopened` | 已发现 -> 已确认；已确认 -> 低优先级 / 忽略 / 解决候选 / 已解决；可再次暴露 |
| 候选对象状态 | `candidate_detected`、`awaiting_user_confirmation`、`user_confirmed`、`user_edited`、`user_skipped`、`merged`、`rejected`、`low_confidence`、`manual_review_required` | AI 发现候选 -> 等待确认 -> 用户确认 / 编辑 / 跳过 / 合并 / 拒绝；证据不足时进入低置信度或人工校对 |
| 建议对象状态 | `suggested`、`accepted`、`edited`、`skipped`、`rejected`、`manual_review_required`、`expired` | 建议生成 -> 接受 / 编辑 / 跳过 / 拒绝；无法安全自动应用时进入人工校对或过期 |
| 候选校对状态 | `correction_saved`、`validation_failed`、`manual_review_required`、`stale_version_conflict` | 低置信候选校对保存 -> 校验通过 / 失败 / 人工校对；版本过期时不得覆盖原候选 |
| 资产质量提示状态 | 复用建议对象状态或 `hint_available`、`hint_low_confidence`、`manual_review_required` | `AssetQualityHint` 只是提示，不冻结资产质量算法，不等于自动归档规则；具体 API enum 后续收敛 |
| 资产版本建议状态 | 复用建议对象状态或 `version_suggestion_available`、`version_suggestion_low_confidence`、`manual_review_required` | `AssetVersionSuggestion` 只是版本更新建议，不等于发布版本；确认前不得写正式 `AssetVersion` |
| 训练优先级排序状态 | 复用建议对象状态或 `ranking_available`、`ranking_low_confidence`、`priority_rule_unknown`、`manual_review_required` | `TrainingPriorityRanking` 只是排序 hint，不冻结训练优先级算法，不自动创建训练任务 |
| 训练结果复盘状态 | 复用复盘 / 训练结果状态或 `review_available`、`review_low_confidence`、`manual_review_required` | `TrainingResultReview` 只产生候选 / 建议态回流输入，不自动更新 Weakness、归档 Asset 或创建下一轮训练建议 |
| 用户确认动作类型 | `confirm`、`edit`、`skip`、`merge`、`reject`、`manual_review` | 用于 `UserConfirmationRef` 记录确认、编辑、跳过、合并、拒绝或人工校对动作，不压缩为 boolean |
| 薄弱项生命周期状态草案 | `candidate`、`active`、`improving`、`monitoring`、`resolved`、`archived`、`manual_review_required` | 作为正式 Weakness 与候选链路的后续 API / UX 收敛占位；不强行替换现有 `weakness_*` 状态，复杂状态流转算法为 deferred_non_blocking |
| 训练状态 | `training_recommended`、`training_in_progress`、`training_completed`、`failed`、`skipped` | 已建议 -> 训练中 -> 已完成；可失败或跳过 |
| 资产状态 | `asset_candidate_generated`、`asset_confirmed`、`asset_archived`、`asset_rejected`、`superseded`、`disabled`、`failed` | 资产候选已生成 -> 已确认；已确认 -> 归档 / 被替代 / 禁用；候选可被拒绝 |
| 内容沉淀目标状态 | `not_confirmed`、`confirmed`、`cancelled`、`skipped`、`writing`、`written`、`failed`、`disabled` | 未确认 -> 已确认 / 取消 / 跳过；已确认 -> 写入中 -> 写入成功 / 失败 |
| 内容沉淀目标类型 | `asset`、`weakness`、`training_suggestion`、`polish_input`、`pressure_input`、`next_interview_input`、`review_note`、`none`、`skip` | 用户选择沉淀目标；`none` / `skip` 不写正式对象，其他目标必须 owner scoped 并经过确认 |
| 评分 / 解释状态 | `available`、`low_confidence`、`conflict`、`incomplete`、`failed` | 评分后进入可用、低置信度、冲突、不完整或失败 |
| 通过倾向状态 | `available`、`insufficient_evidence`、`low_confidence`、`validation_failed`、`not_applicable` | 只能表达分档倾向或证据不足，不表示精确通过概率或自动决策 |
| 风险提示状态 | `available`、`low_confidence`、`evidence_missing`、`source_unavailable`、`validation_failed`、`manual_review_required` | 风险提示必须绑定证据、评分版本、规则版本和低置信度状态 |
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

### 8.3 版本决策处置状态

- 简历版本：保存 Markdown 正文或用户确认编辑时创建新 `ResumeVersion`；命名可使用时间戳 / 序号；历史结果引用生成时版本或快照；回滚通过创建新版本完成，不改写历史。
- 岗位版本：岗位职责、要求或其他正文保存时创建新 `JobVersion`；投递状态留在 `JobStatus`，不进入历史正文；重新匹配产生新的 `JobMatchAnalysis`。
- 项目经历表达版本：项目经历仍是 Markdown 正文片段；打磨结果先进入 `AssetCandidate` 或 `AssetVersionSuggestion`，用户确认后只能通过创建新的 `ResumeVersion` 更新 Markdown 正文，或更新资产版本，并保留 `ResumeVersion`、Markdown 位置范围和来源引用；不得为项目经历模块建立独立 version / owner / CRUD。
- 资产版本：`AssetCandidate` 经用户确认后创建或更新 `AssetVersion`；合并、替代和质量提示通过 `AssetQualityHint` / `AssetVersionSuggestion` 表达，复杂自动合并算法后置。
- 评分规则版本：历史评分引用生成时 rule version；不同版本不可直接强比较，除非存在校准映射。更细的启停审批、回滚流程和运营发布流程为后续治理细节，不阻断 M4。
- 知识文档版本：`KnowledgeDocument` / `KnowledgeChunk` / `KnowledgeEmbeddingRef` 保存来源版本和索引状态；chunk 重建、embedding 外部引用刷新和失效实现由 F5 / F7 承接，不改变 F4 逻辑对象。

## 9. 回流、资产、薄弱项生命周期

### 9.1 回流生命周期

1. 系统从报告、复盘、薄弱项或打磨反馈中生成可沉淀内容。
2. 可沉淀内容进入 `AssetCandidate`、`WeaknessCandidate` / `CandidateRef` 或 `TrainingRecommendation` candidate。
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

资产合并、质量判断、重复检测和版本替代在 MVP 中只输出建议或质量提示；正式合并、替代或发布版本必须由用户确认或显式业务动作完成。

### 9.3 薄弱项生命周期

- `weakness_detected`：系统从匹配分析、报告、复盘、反馈、RAG 证据或用户录入中识别出的候选。
- `weakness_confirmed`：用户或规则确认后进入薄弱项列表，可用于训练和出题。
- `low_priority`：仍存在但优先级降低。
- `ignored`：用户明确忽略。
- `resolved_candidate`：系统建议已改善，但尚未最终关闭。
- `resolved`：确认已解决。
- `reopened`：后续证据再次暴露。

薄弱项合并、状态流转和生命周期的最小边界已冻结：候选 -> 用户确认 -> 正式 Weakness；合并、状态更新和严重度变化先形成 suggestion / assessment，用户确认前不得自动改正式 Weakness。自动消减算法为 deferred_non_blocking。

`WeaknessCandidate`、`WeaknessMergeSuggestion`、`WeaknessSeverityAssessment` 和 `WeaknessStatusUpdateSuggestion` 均属于候选 / 建议链路：它们可以进入用户确认、编辑、跳过、合并、拒绝或人工校对流程，但不得在用户确认前创建、合并、关闭、删除或更新正式 `Weakness`。

### 9.4 Weakness -> Training -> Asset 状态流

最小状态流为：

`weakness_detected` -> `weakness_confirmed` -> `training_recommended` -> `training_in_progress` -> `training_completed` -> `asset_candidate_generated` -> `asset_confirmed` -> `asset_archived` / `asset_rejected`

规则：

- 薄弱项来源必须可追溯到题答、评分、复盘、RAG 证据或用户确认。
- `TrainingRecommendation` 只能表达训练建议，不能直接等同于 `Asset`。
- `TrainingRecommendation` 可存在候选态，用户确认前不得自动成为正式训练建议。
- `TrainingPriorityRanking` 只能表达训练排序 hint，不冻结训练优先级算法，也不等于自动创建训练任务。
- `TrainingTask` / `TrainingSession` 记录训练执行过程，不得由 AI suggestion 自动创建，必须经过确认或显式用户动作。
- `TrainingResult` 记录训练完成后的结果和评分引用；`TrainingResultReview` 可以产生弱项状态更新候选、资产候选和下一轮训练建议候选，但不得直接更新正式 Weakness、正式 Asset 或正式 `TrainingRecommendation`。
- `AssetQualityHint` 只能表达质量提示，不等于自动归档规则。
- `AssetVersionSuggestion` 只能表达版本更新建议，不等于发布版本，用户确认前不得写入正式 `AssetVersion`。
- `AssetCandidate` 必须经过 `UserConfirmation` 或 `AssetPromotionRecord` 的规则确认后，才能生成或更新正式 `Asset` / `AssetVersion`。
- `AssetVersion` 需要记录来源、确认状态、适用岗位、适用简历和适用场景。
- 本文不设计复杂资产质量算法、训练优先级算法、训练结果评估规则或弱项自动消减规则；这些为 deferred_non_blocking，F5 只能按候选 / 建议 / 用户确认边界实现。

## 10. 评分、低置信度与可解释结果的数据承载边界

- `ScoreResult` 统一保存 0-100 产品展示分、分数类型、关联对象、`score_version`、`rubric_version`、`ScoreRuleVersion`、`ScoreDimension`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`VersionRef`、`SnapshotRef`、`TraceRef`、`generated_by_task_id`、`generated_at`、`created_at`、`updated_at` 和生成状态。
- `ScoreResult.score_value` / `display_score` 是唯一正式展示分；MVP 不持久化 `raw_score`、`normalized_score`、`display_score` 三套并行正式分数。若后续引入 raw / normalized，只能通过新 `score_version` 和校准映射扩展。
- `ScoreResult` 必须能追溯到评分规则版本、输入来源版本或快照、证据链、解释链路、低置信度 / 冲突 / 不完整标记，以及相关 `LlmValidationResult`。
- `ScoreResult` 不随后续简历、岗位、会话、知识文档或评分规则变化而自动重算；如需重新评分，应产生新的 `ScoreResult` 或新版本结果。
- `ScoreRuleSet` / `ScoreRuleVersion` 表达规则版本、rubric version、维度权重、启用状态和校准样例引用；不暴露隐藏评分规则给前端或 copy content。
- `ScoreDimension` / `ScoreRubric` 保存可追溯维度、权重和等级描述，不承诺精确通过概率或真实面试结果预测。
- `ScoreExplanation` 应连接面试报告、题目点评、弱项识别和训练建议需要展示的解释摘要，并包含可信度说明和非决策性免责声明引用。
- `ScoreEvidenceLink` 应连接题答、评分、报告、复盘、RAG 证据或用户确认记录。
- `LowConfidenceFlag` 或结果对象状态应保存低置信度、冲突、不完整和失败标记，并关联触发原因、影响范围和可校对入口。
- `EvidenceSummary`、`RetrievalEvidence`、`Citation` / `EvidenceRef` 和 `ScoreEvidenceLink` 保存可展示证据摘要；原始输入片段、隐私字段和日志脱敏边界交给 `SECURITY_PRIVACY.md`。
- 匹配分析、面试报告、复盘和反馈卡片可以引用证据摘要、评分结果、风险提示和低置信度标记。
- 用户校对低置信度结果时，应产生 `CandidateCorrection` / `UserCorrectionRef`，并绑定 `validation_result_ref` 与 `audit_event_ref`；校对通过后仍需作为后续 confirmation 或 task input，不能只覆盖原始结果、正式对象或 Prompt source。
- LLM 原始输出和结构化输出保存边界仍由 `SECURITY_PRIVACY.md` 与后续实现细化；前端只接收通过校验的可展示结果或低置信度 / 部分可用状态。

## 11. 持久化边界与逻辑 Schema 草案

### 11.1 持久化边界

- 前端不保存业务真相，不直接读取数据库，不直接调用 LLM。
- 后端持久化层负责保存用户数据、版本、知识库逻辑对象、RAG 证据引用、会话、报告、复盘、资产、薄弱项、训练建议、回流确认、最小 LLM trace 和关键审计事件。
- `PERSISTENCE_MODEL.md` 负责把本文逻辑对象映射为 F5 建议物理模型、primary key、owner / actor、version、status、created_at / updated_at、关键外键、唯一约束、1:N / M:N 关系和 API schema 映射。
- `SECURITY_PRIVACY.md` 负责定义隐私字段、日志脱敏、密钥、权限、保留和删除策略。
- `API_SPEC.md` 负责定义具体资源路径、请求响应结构、错误语义和异步任务查询。
- `PROMPT_SPEC.md` 负责定义 Prompt 输入输出、模型调用、结构化校验和低置信度判定。

### 11.2 逻辑 Schema 草案

以下是逻辑对象分组，不是物理表 DDL。

| 分组 | 逻辑对象 |
|---|---|
| 身份、归属与审计 | `UserAccount`、`OwnerRef`、`RoleAssignment`、`RoleScope`、`PermissionBoundary`、`AuditActor`、`AuditTarget`、`AuditEvent` |
| 统一引用模型 | `SourceRef`、`EvidenceRef`、`VersionRef`、`TraceRef`、`SnapshotRef`、`UserConfirmationRef`、`OwnerRef` |
| AI 输出交接 | `AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`LlmValidationResult`、`LowConfidenceFlag`、`AuditEvent` |
| API 幂等、任务与请求追踪 | `IdempotencyRecord`、`AiTask`、`AiTaskResult`、`ApiRequestTrace`、`ApiEndpointRef` |
| 简历 | `Resume`、`ResumeVersion`、`ResumeMarkdownOutline (derived_non_persistent)` |
| 岗位 | `Job`、`JobVersion`、`JobStatus`、`JobResumeBinding`、`JobBindingSummary (derived_read_model)` |
| 匹配分析 | `JobMatchAnalysis`、`JobMatchSummary (derived_read_model)`、`MatchScore`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`EvidenceSummary` |
| 知识库与 RAG | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`KnowledgeEmbeddingRef`、`RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`Citation` / `EvidenceRef`、`RAGContextAssembly` |
| 模拟面试 | `InterviewSession`、`PolishSessionDetail`、`PolishTopicRef`、`PolishSubtopicRef`、`PressureSessionDetail`、`Question`、`Answer`、`Feedback`、`SessionSummary` |
| Skill / Capability Model | `SkillTaxonomyVersion`、`SkillArea`、`Skill`、`SkillLevel`、`SkillEvidence`、`SkillAssessment`、`SkillGap`、`SkillProgress`、`SkillToQuestionPattern`、`SkillToScoreDimension`、`SkillToTrainingAction`；逻辑语义以 `SKILL_MODEL_SPEC.md` 为 canonical，不在本文定义物理表 |
| 评分规则与解释 | `ScoreRuleSet`、`ScoreRuleVersion`、`ScoreDimension`、`ScoreRubric`、`ScoreResult`、`ScoreExplanation`、`ScoreEvidenceLink`、`LowConfidenceFlag` |
| 题级解释材料 | `LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation` |
| 进展 | `ProgressTree`、`ProgressNode`、`ProgressPosition` |
| 报告 | `InterviewReport`、`ReportSection`、`CopyableContent` |
| 复盘 | `InterviewRetrospective`、`ReviewSummary`、`MockInterviewReview`、`RealInterviewReview`、`RealInterviewInput`、`RealInterviewEvidence`、`ReviewItem`、`ReviewSourceRef`、`CopyableReviewContent`、`ReviewCopyEvent` |
| 薄弱项 | `Weakness`、`WeaknessCandidate`、`WeaknessEvidence`、`WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion`、`WeaknessStatusHistory` |
| 资产 | `Asset`、`AssetVersion`、`AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`AssetSource`、`AssetPromotionRecord` |
| 训练与回流 | `TrainingRecommendation`、`TrainingPriorityRanking`、`TrainingTask`、`TrainingSession`、`TrainingResult`、`TrainingResultReview`、`FeedbackLoop`、`DepositTarget`、`UserConfirmation`、`CandidateCorrection`、`UserCorrectionRef` |
| LLM 追踪 | `LlmRequestTrace`、`LlmResponseTrace`、`LlmUsageRecord`、`LlmValidationResult`、`LlmRetentionPolicyRef`、`LlmRedactionRef`、`LlmFailureRecord` |

## 12. F4 待决策项处置表

本节保留原 `DM-UNK-*` 编号作为审计追踪 ID，但不再表示 M4 阻断。所有条目均归类为 `must_close_in_F4` 已关闭、`already_closed_by_recent_remediation` 或 `deferred_non_blocking`。

| 编号 | 待决策项 | 分类 | F4 处置结论 | 后续承接 |
|---|---|---|---|---|
| DM-UNK-001 | 简历版本策略 | must_close_in_F4 | Markdown 保存或确认编辑创建新 `ResumeVersion`；历史结果引用生成时版本 / 快照；回滚创建新版本。 | F5 落库字段和 UI 命名细节 |
| DM-UNK-002 | 岗位版本策略 | must_close_in_F4 | 岗位正文保存创建新 `JobVersion`；投递状态留在 `JobStatus`；编辑不静默重算历史分析。 | F5 migration / API 字段 |
| DM-UNK-003 | 项目经历表达版本策略 | must_close_in_F4 | 本轮按人工审计决策执行：Resume API Markdown-only。项目经历是 Markdown 正文片段或 derived outline 节点；打磨结果先进入候选 / 建议，确认后通过新 `ResumeVersion` 更新 Markdown，或更新资产版本。 | F5 confirmation flow；不得建立 project-experience module CRUD |
| DM-UNK-004 | 资产版本、合并、质量判断与自动沉淀 | deferred_non_blocking | `AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`AssetSource`、`UserConfirmationRef` 已冻结；自动合并、质量评分和去重算法不作为 MVP 阻断。 | Asset / F7 fixture |
| DM-UNK-005 | 打磨模式 / 压力面模式暂停恢复字段与引用 | must_close_in_F4 | 最小恢复快照字段已冻结：session、mode、question / answer ref、progress position、session summary、trace、risk / low confidence、resume attempt status；恢复失败、快照不可用、来源不可用和 partial 状态必须用户可见。 | F7 pause/resume fixture |
| DM-UNK-006 | 进展树数据结构、节点状态和更新触发 | must_close_in_F4 | `ProgressTree` / `ProgressNode` / `ProgressPosition` 和最小状态域已冻结；暂停 / 恢复必须绑定 `ProgressPosition`；排序和推荐算法后置。 | F7 progress-tree fixture |
| DM-UNK-007 | 薄弱项合并、状态流转、生命周期和自动消减 | deferred_non_blocking | 候选、合并建议、严重度提示、状态更新建议和正式 Weakness 边界已冻结；自动消减和复杂合并算法后置。 | Weakness / Training 后续优化 |
| DM-UNK-008 | 匹配分析和报告评分结果如何存储 | already_closed_by_recent_remediation | `ScoreResult` 承载 0-100 产品展示分、版本、规则、置信度、validation、task、证据和解释。 | F7 scoring fixture |
| DM-UNK-009 | 解释、证据和低置信度如何关联 | already_closed_by_recent_remediation | `EvidenceSummary`、`ScoreEvidenceLink`、`LowConfidenceFlag`、免责声明、风险提示和通过倾向降级边界已冻结。 | F7 low confidence / evidence fixture |
| DM-UNK-010 | LLM 原始输出、结构化输出、trace 与审计记录保存边界 | must_close_in_F4 | MVP 默认不保存原始 Prompt / completion / provider payload；只保存结构化结果、validation、usage、failure、trace / evidence 引用和最小审计。 | `SECURITY_PRIVACY.md` §11；F5 配置化 retention |
| DM-UNK-011 | RAG 知识文档版本、chunk 和外部 embedding 引用策略 | deferred_non_blocking | `KnowledgeDocument`、`KnowledgeChunk`、`KnowledgeEmbeddingRef` 和 RAG 证据引用已冻结；向量库、embedding 模型、索引和 chunk 算法后置。 | F5 技术实现 / F7 source unavailable |
| DM-UNK-012 | 评分规则版本治理和解释链路细则 | already_closed_by_recent_remediation | `ScoreRuleVersion`、`ScoreDimension`、`ScoreRubric`、解释链、最小权重策略和 MVP fixture 校准策略已冻结；真实结果校准后置。 | F7 score regression |
| DM-UNK-013 | 真实面试复盘输入可信度、完整度和证据等级 | must_close_in_F4 | `RealInterviewInput` / `RealInterviewEvidence` / `ReviewSourceRef` 已冻结；系统不假设拥有完整真实面试过程。 | Review / Security fixture |
| DM-UNK-014 | MVP 权限、角色范围和审计事件细则 | must_close_in_F4 | 个人工作台 owner、最小 role scope、PermissionBoundary 和关键动作审计字段已冻结；企业多租户和复杂 ACL 后置。 | `SECURITY_PRIVACY.md` / API auth tests |
| DM-UNK-015 | 训练优先级与训练结果评估规则 | deferred_non_blocking | `TrainingPriorityRanking` 和 `TrainingResultReview` 已冻结为建议 / 复盘对象；训练优先级算法、结果评估算法、弱项自动消减和自动训练任务后置。 | Training 后续优化 / F7 candidate-only fixture |

## 13. 与 API / Prompt / Security 子文档的交接边界

| 子文档 | 本文交接内容 | 本文不展开内容 |
|---|---|---|
| `API_SPEC.md` | 逻辑对象、状态域、引用关系、生成任务状态、历史引用原则、MVP role scope、候选 / 建议 / 确认对象和审计对象边界 | endpoint、request / response schema、错误码、分页过滤参数、异步任务协议、具体鉴权 API |
| `SCORING_SPEC.md` | `ScoreResult`、`ScoreRuleVersion`、score type、维度、权重、公式、低置信度和正式落库规则 | 复杂算法、真实招聘结果校准、隐藏规则实现细节 |
| `SKILL_MODEL_SPEC.md` | Skill taxonomy、SkillArea、Skill、SkillLevel、SkillEvidence、SkillAssessment、SkillGap、SkillProgress 及与 Score / Progress / Weakness / Asset / Training 的非替代映射 | ORM、DDL、migration、endpoint、前端实现和生产 Prompt 文案 |
| `SEMANTICS_GLOSSARY.md` | Low Confidence、validation、source availability、candidate / suggestion / formal object 的 canonical 语义 | API endpoint、物理表和 UI 文案最终稿 |
| `PERSISTENCE_MODEL.md` | 将本文逻辑对象映射为 F5 建议物理模型、关系、join / reference table、唯一约束、derived / read model 和 API schema 映射 | SQL DDL、ORM model、migration、数据库供应商特性 |
| `PRESSURE_MODE_SPEC.md` | `PressureSessionDetail`、`PressureTurn` refs、pace/end/report input package、review handoff 和 candidate-only 边界的 mode-level 组合规则 | ORM、DDL、migration、endpoint 实现、前端实现、graph 代码或 Prompt builder |
| `PROMPT_SPEC.md` | LLM 输出应落到哪些结构化对象、RAG 上下文组装结果如何被引用、低置信度、候选态 / 建议态和部分可用状态应被持久化；scoring candidate 进入正式 `ScoreResult` 前必须完成 schema validation、rule version、evidence、confidence 和 trace 校验 | Prompt 模板、模型选择、模型调用参数、上下文裁剪、重试降级策略、隐藏评分规则实现细节 |
| `SECURITY_PRIVACY.md` | 哪些对象包含用户资料、简历、岗位、回答、报告、复盘、资产、知识库文档、RAG 证据和 LLM trace | 密钥管理、权限矩阵、复杂 ACL、企业多租户、数据可见性、日志脱敏、保留 / 删除细则、隐私字段分级 |
| `TECH_DESIGN.md` | 本文回填数据模型子文档状态、F4 待决策项处置表和 deferred_non_blocking 边界 | 顶层架构重写、M4 整体验收、`AIFI-ARCH-002` 完成判定 |

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-24 | 增加 Pressure Mode mode-level 数据承接 | 将 `PressureSessionDetail` 扩展为引用 `PressureTurn`、pace、end condition、session score、report input package 和 review handoff 的逻辑承接；不新增物理 schema，不进入 implementation |
| 2026-05-17 | 增加 F5 persistence handoff 交接 | 明确本文仍是逻辑模型，物理模型、join / reference table、关系和 API schema 映射以 `PERSISTENCE_MODEL.md` 为 canonical；避免 F5 从逻辑对象自行推导物理关系 |
| 2026-05-24 | 增加 Skill / Capability Model 交叉引用 | 将 Skill taxonomy、SkillEvidence、SkillAssessment、SkillGap、SkillProgress 作为逻辑对象登记，并明确 canonical 语义以 `SKILL_MODEL_SPEC.md` 为准；不进入物理 schema 或 implementation |
| 2026-05-17 | 修复 `AR-DOCS02-SEM-001` 数据模型断链 | 补齐岗位解绑历史保留字段、复盘列表投影、复盘复制内容 / 审计、低置信候选校对记录和内容沉淀目标类型；不定义物理 schema，不处理 `AR-DOCS02-SEM-002/003` |
| 2026-05-17 | 修复 `AR-F4-F8-004` / `AR-F4-F8-005` / `AR-F4-F8-006` 人工审计数据语义偏差 | 将 Resume 收敛为 Markdown-only，项目经历降级为 Markdown 片段 / derived non-persistent outline；补 `JobBindingSummary` / `JobMatchSummary` 作为 F6 read model；补 `PolishTopicRef` / `PolishSubtopicRef` 与 `custom_topic_text` 安全输入边界；不进入物理 schema 或 implementation |
| 2026-05-17 | 修复 `AR-F4-F8-001` 数据承接缺口 | 新增 `IdempotencyRecord`、`AiTask` / `AiTaskResult`、`ApiRequestTrace` / `TraceRef`、`AuditEvent` 覆盖范围和 persistence handoff 规则；承接 API 字段级 contract、幂等重试、AI task result、source availability、candidate / suggestion / formal object 边界；不进入物理 schema 或 implementation |
| 2026-05-16 | 修复 `AR-F4-FULL-001` 数据模型侧阻断项 | 将 `DM-UNK-*` 改为 F4 待决策项处置表；冻结简历 / 岗位版本、项目经历表达版本、暂停恢复最小快照、进展树最小状态、复盘切分、候选 / 正式对象、trace / evidence 和训练 / 资产 / 弱项 deferred_non_blocking 边界；等待 verification |
| 2026-05-16 | 修复 `AR-F4-FULL-005` 暂停恢复与进展树状态机缺口 | 将暂停恢复最小快照扩展到打磨和压力面两种模式，明确 `source_session_snapshot_ref`、`covered_turn_refs`、`ProgressPosition`、恢复失败、来源不可用、partial 和低置信度继承；不进入 implementation |
| 2026-05-16 | 修复 `AR-F4-FULL-003` 评分数据承载缺口 | 冻结 `ScoreResult` 正式字段、0-100 产品刻度、`score_version` / `rubric_version` / `ScoreRuleVersion`、rubric 维度与权重策略、通过倾向分档、风险提示字段、低置信度降级和 MVP 校准承载；不新增独立一级业务对象，不进入物理 schema |
| 2026-05-16 | 同步 Asset / Training handoff 逻辑对象 | 补充 `AssetQualityHint`、`AssetVersionSuggestion`、`TrainingPriorityRanking`、`TrainingResultReview` 及其候选 / 建议 / 用户确认边界；不定义物理 schema |
| 2026-05-15 | 初始化 F4 数据模型工作草案 | 建立 `AIFI-DATA-001` 的对象、关系、状态、版本、回流、评分和 trace 承载边界 |
| 2026-05-15 | 补齐数据模型收敛缺口 | 补充 RAG / Knowledge Base、评分规则版本、LLM trace、真实 / 模拟复盘差异、Weakness -> Training -> Asset 状态流和 MVP 权限 / 审计边界 |
| 2026-05-15 | 补充 SessionSummary 逻辑对象 | 增加会话摘要的逻辑字段、状态、回溯约束和 Context Assembly 交接边界；不定义物理 schema |
| 2026-05-16 | 同步 Weakness 后候选态、正式态与确认流 | 补充 `CandidateRef`、`UserConfirmationRef`、`AiTaskResultRef`、`SuggestionRef`、`WeaknessCandidate`、Weakness 建议对象和候选 / 建议状态边界；不定义物理 schema |
