# AI 模拟面试一期工作台 MVP 范围冻结草案

> 唯一事实源定位：本文档是“一期 MVP 范围”的唯一事实源。IA / 用户旅程、对象模型 / RAG / 多轮 / 后端边界、评分 / 复盘 / 导出 / DoD 分别以对应 W13 文档为准，本文档不重复维护那些细节。

## 1. 文档定位

- 本文档记录 `W13-A` 用户确认后的“一期工作台 MVP”范围冻结草案。
- 本文档只冻结产品范围层，不冻结具体实现方案，不作为代码实施入口。
- 本文档优先级高于 W10 首切片原型边界；W10 原型只作为探索证据保留。
- `W13-B` 已新增 [`2026-04-25-workbench-mvp-ia-user-journey.md`](2026-04-25-workbench-mvp-ia-user-journey.md)，用于补齐一期工作台信息架构、页面集合、用户旅程与页面对象映射。
- `W13-C` 已新增并更新 [`2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`](2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md)，用于补齐一期工作台对象模型、服务端保存、权限、RAG / 知识库、多轮高阶面试、打磨模式、压力面模式、复盘、薄弱项、训练机制、资产归档、真实 LLM、API / 后端与运维边界确认卡。
- `W13-D` 已新增 [`2026-04-25-workbench-mvp-scoring-review-export-dod.md`](2026-04-25-workbench-mvp-scoring-review-export-dod.md)，用于补齐一期工作台评分、复盘、导出、错误态 / 空状态与 MVP DoD 草案。

## 2. 用户确认结论

用户已确认组合：`1B2C3C4C5C6C7B8A9B10B11B12B`。

已确认范围如下：

- `1B`：最小项目范围必须是工作台级。
- `2C`：一期 MVP 必须包含服务端历史记录 / 复盘记录。
- `3C`：一期 MVP 必须接真实 LLM。
- `4C`：一期 MVP 必须有完整登录 / 权限。
- `5C`：简历和面试记录都需要服务端保存。
- `6C`：一期 MVP 需要完整 `0-100` 多维评分。
- `7B`：导出采用复制 / Markdown 下载，不做完整 PDF。
- `8A`：当前 `apps/web/**` 原型保留为参考证据，不直接扩展。
- `9B`：暂停代码开发，回到设计文档补齐。
- `10B`：一期 MVP 必须包含 RAG / 知识库能力。
- `11B`：一期 MVP 必须包含多轮高阶面试能力。
- `12B`：模拟面试模块默认入口必须是当前用户权限范围内可见的历史所有模拟记录列表，用户从列表发起模拟面试，再进入面试台，完成后回写历史记录 / 复盘记录。

## 3. 一期 MVP 初步范围

一期 MVP 初步冻结为“AI 模拟面试工作台”的可用闭环，而不是单页原型或 W10 首切片。

当前范围至少包含：

- 工作台入口：能组织岗位、简历、模拟面试、复盘和待处理事项。
- 简历能力：简历内容需要服务端保存，并能作为面试与复盘的长期输入。
- 模拟面试能力：接真实 LLM，生成和推进文本面试，不再依赖纯 mock 结果作为正式 MVP 行为。
- 模拟记录入口：模拟面试模块默认进入历史所有模拟记录 / 复盘记录列表，而不是直接开始新面试。
- 历史记录能力：面试过程、回答、轮次、RAG 引用、评分、复盘结果和关键状态需要服务端保存。
- 复盘能力：支持从历史记录进入复盘，沉淀可回看的诊断结果。
- RAG / 知识库能力：一期主链需要支持知识库入口、发起面试时选择知识库上下文、面试台展示 RAG 证据 / 引用、复盘详情回看引用来源。
- 多轮高阶面试能力：一期主链需要支持打磨模式和压力面模式两条多轮路径；打磨模式按进展树持续出题并由用户决定继续 / 结束，压力面模式按题组完成后结束；每轮或整场结果按模式进入评分和复盘。
- 登录 / 权限能力：一期必须具备完整登录与权限边界。
- 评分能力：输出完整 `0-100` 多维评分，并保留评分解释和证据依据。
- 导出能力：一期只做复制 / Markdown 下载，不做完整 PDF。

## 4. 仍未确定的实现方案

以下内容仍未确认，不得在本轮写成已确认实现：

- 具体 LLM provider、模型选择、模型路由、超时、重试、成本控制。
- 登录方案，例如固定 token、JWT、session cookie、托管身份服务或其他方式。
- 权限模型细节，例如角色集合、资源粒度、管理员能力边界、审计要求。
- 服务端保存方式，例如数据库类型、对象存储、文件版本、备份与迁移。
- API / 后端框架，例如 FastAPI、Next.js Route Handlers、BFF 或其他组合。
- 评分维度、权重、通过线、证据绑定、版本化与解释模板。
- RAG / 知识库细节，例如是否支持用户上传、知识库可见范围、检索失败降级策略、引用摘要规则、证据回溯和权限过滤。
- 多轮高阶面试细节：模式级结束条件已确认拆分为打磨模式进展树驱动、压力面模式题组驱动；压力面题目数量、难度、题型组合、暂停 / 继续、上下文保存、每轮评分和追问规则仍需确认。
- 模拟记录列表细节，例如默认筛选范围、管理员团队 / 组织视图、归档 / 删除是否进入一期、列表快捷导出范围。
- Markdown 下载的文件结构、命名规则、导出入口、复制范围。
- 运维 / 部署边界，例如本地部署、云部署、CI/CD、密钥管理与日志保留。

## 5. 不进入开发的原因

当前暂停代码开发的原因是：

- W10 首切片只验证了一个 mock 原型路径，不能代表用户认可的一期 MVP。
- 用户已经确认一期 MVP 必须是工作台级，范围显著大于 W10 原型。
- 真实 LLM、登录 / 权限、服务端保存、评分系统、复盘记录、RAG / 知识库、多轮高阶面试和模拟记录列表入口都进入一期范围，但实现方案尚未完成设计确认。
- 若此时继续扩 `apps/web/**`、创建 `apps/api/**` 或接真实 LLM，会把未冻结设计提前写成代码事实。

因此，在 W13-B/C/D 完成并经用户再次确认前，不允许进入实现。

## 6. 与 W10 `apps/web/**` 原型的关系

- W10 `apps/web/**` 原型是探索成果，不是当前一期 MVP 的正式起点。
- 原型可作为交互、文案和流程证据参考，但不能直接扩展为正式工作台。
- 原型中的 mock LLM、无登录、会话内临时数据、无数值评分、不导出、无 RAG / 知识库、无多轮高阶面试和非记录列表优先入口的边界已被 W13-A 及用户后续 confirmed 结论取代。
- 后续若复用原型中的页面结构或组件，必须先在 W13-B/C/D 的设计文档中重新裁剪、确认和登记。

## 7. W13 后续任务

### 7.1 W13-B：工作台 IA 与用户旅程

预期产出：

- 工作台一级导航与页面信息架构。
- 核心用户旅程：登录后进入工作台、查看模拟记录列表、从记录列表发起面试、选择岗位 / 简历 / 知识库 / 多轮策略、进入面试台、完成多轮问答、生成评分复盘、导出 Markdown、回到记录列表继续训练。
- 页面对象关系：工作台、岗位、简历、知识库、检索查询、引用证据、面试会话、面试轮次、问答 turn、复盘、评分、导出。
- W10 原型可参考和不可继承的界面清单。

当前 W13-B 已补充：

- 一期工作台 IA：登录 / 权限、工作台首页、岗位、简历、模拟记录列表、发起模拟面试、面试台、RAG / 知识库、多轮高阶面试、反馈评分、历史复盘、复制 / Markdown 下载、用户 / 权限入口。
- 页面集合：区分一期必须页面、一期可合并页面和后续占位页面。
- 模拟面试模块 IA：固定为“模拟记录列表 -> 发起模拟面试 -> 面试台 -> 评分 / 复盘详情 -> 回到模拟记录列表”，不得设计为直接开始新面试。
- 核心用户旅程：覆盖登录、查看模拟记录列表、从列表发起面试、创建 / 选择岗位、创建 / 上传 / 粘贴简历、选择知识库、选择多轮模式、真实 LLM 出题、多轮问答、评分反馈、历史复盘、Markdown 导出和回到模拟记录列表继续训练。
- 页面到对象映射：为 `W13-C` 的对象模型设计提供输入，新增覆盖 `KnowledgeBase`、`KnowledgeDocument`、`RetrievalQuery`、`RetrievalResult`、`Citation / Evidence`、`InterviewRound`、`InterviewTurn`、`RoundEvaluation`、`ProgressTree`、`PressureInterviewSession`、`InterviewQuestionSet` 等对象。
- 历史确认卡已由 `OPEN_QUESTIONS.md` 的 FC 归并索引和对应 W13 事实源文档吸收，不再作为当前待确认入口。

### 7.2 W13-C：对象模型与技术方案事实源

预期产出：

- 岗位、简历、知识库、检索、面试、多轮、打磨、压力面、复盘、薄弱项、训练、资产、评分、用户、权限、LLM 与审计的对象模型草案。
- 对象生命周期草案。
- 服务端保存方式确认卡。
- 具体 LLM provider / 模型策略确认卡。
- 登录 / 权限实现方案确认卡。
- RAG / 知识库确认卡。
- 多轮高阶面试确认卡。
- 面试模式、薄弱项、能力树、资产归档、训练抽屉与真实复盘确认卡。
- API / 后端框架确认卡。

当前 W13-C 已补充：

- 对象模型草案：覆盖 `User`、`Account`、`Role`、`Permission`、`Workspace / Organization`、`Job`、`Resume`、`KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`RetrievalQuery`、`RetrievalResult`、`Citation / Evidence`、`IndexingJob`、`EmbeddingProvider`、`InterviewSession`、`InterviewLaunchContext`、`InterviewReferencePack`、`InterviewMode`、`InterviewStrategy`、`FirstQuestionGeneration`、`InterviewRound`、`InterviewTurn`、`InterviewQuestion`、`InterviewAnswer`、`FollowUpQuestion`、`InterviewContext`、`RoundEvaluation`、`PolishModeSession`、`ProgressTree`、`UserEndDecision`、`WeaknessItem`、`WeaknessEvidence`、`AbilityTree`、`TrainingProgress`、`LossPoint`、`ReferenceAnswer`、`NextQuestionRecommendation`、`SimulationModeSession`、`PressureInterviewSession`、`InterviewQuestionSet`、`InterviewCompletion`、`FinalMasteryAssessment / FinalAssessment`、`JobMatchAssessment`、`PassProbability`、`WeaknessSummary`、`SuggestedPolishTopic`、`RealInterviewReview`、`MockInterviewReview`、`QuestionReviewItem`、`TrainingQueue`、`TrainingTask`、`TrainingDrawerContext`、`TrainingAction`、`TrainingImpactPreview`、`Asset`、`AssetType`、`AssetSchema`、`AssetArchiveRequest`、`ArchivedQuestion`、`ArchivedReview`、`FeedbackSummary`、`ScoreReport`、`SessionRecord`、`ExportSnapshot / ExportRecord`、`LLMGenerationRequest`、`LLMGenerationResult`、`PromptTemplateVersion`、`LLMProviderConfig`、`AuditEvent / OperationLog` 等对象。
- 对象生命周期草案：覆盖 `Job`、`Resume`、`KnowledgeDocument`、`IndexingJob`、`InterviewSession`、`InterviewRound`、`InterviewTurn`、`PolishModeSession`、`PressureInterviewSession`、`InterviewQuestionSet`、`InterviewCompletion`、`SimulationModeSession`、`WeaknessItem`、`TrainingTask`、`AssetArchiveRequest`、`ScoreReport`、`ExportSnapshot`。
- 账号、权限、RAG、LLM、对象模型、多轮、复盘、薄弱项、训练与资产等历史确认卡已压缩为对象模型文档第 17 节的吸收索引。
- 用户已确认多轮面试按模式拆分：打磨模式进展树驱动、用户决定结束；压力面模式题组驱动、题目完成后结束；固定 3 轮不再作为多轮总规则。

### 7.3 W13-D：评分、复盘、导出与 MVP DoD

已完成产出：

- 已补齐 `0-100` 多维评分维度、权重、证据绑定、评分版本、重算 / 修订和低置信度提示草案。
- 已分别覆盖打磨模式与压力面模式的评分、复盘、导出与 DoD：打磨模式验收进展树、能力树、薄弱点、下一题建议和用户结束决策；压力面模式验收题组完成、最终评估、多维评分、复盘报告和建议打磨主题。
- 已补齐真实面试复盘和模拟面试复盘结构、RAG 引用展示与评分证据、Markdown 复制 / 下载范围、薄弱项 / 训练机制 DoD、错误态 / 空状态和一期 MVP 五层 DoD。
- 历史确认卡已压缩为评分 / 复盘 / 导出 / DoD 文档第 13 节的吸收索引；当前事实以该文档正文为准。

## 8. 历史确认卡吸收状态

本节原先包含具体 LLM provider、登录 / 权限、服务端保存、数据库、评分维度、API / 后端、导出形态、运维 / 部署等确认卡。W13-Cleanup 后不再在范围文档重复维护这些卡片正文：

- 已被用户 confirmed 的产品范围、IA、对象模型、多轮、复盘、资产、薄弱项与训练事实，分别回收到四份 W13 唯一事实源文档和 `DESIGN_DECISIONS.md`。
- provider、数据库、部署、日志等实现级选型不在本轮范围文档中拍板；进入实现计划前由 W13-E/F 压缩成可执行验收清单。
- 原确认卡正文只保留在 git 历史中，不再作为当前待确认任务池。

## 9. 当前禁止项

在 W13-B/C/D 完成并经用户再次确认前，禁止：

- 继续扩展 `apps/web/**`。
- 创建 `apps/api/**`。
- 创建 `infra/**`。
- 接真实 LLM。
- 实现数据库或服务端保存。
- 实现登录 / 权限。
- 实现评分系统。
- 实现后端 API。
- 把 W10 首切片写成一期 MVP。
