# Workbench MVP Object Model, RAG, Multi-round and Backend Boundary

## 1. 设计边界

本文定义一期工作台 MVP 的对象、关系、状态字段和后端边界。它不定义具体数据库 schema、API route、prompt 模板、provider SDK 代码或部署脚本。

## 2. 核心对象族

| 对象族 | 代表对象 | 一期职责 |
| --- | --- | --- |
| 账号与权限 | `User`、`Account`、`Role`、`Permission`、`Workspace` | 登录身份、权限边界、资源可见性和基础审计。 |
| 岗位与简历 | `Job`、`Resume`、`Document` | 发起模拟、匹配分析、复盘和训练建议的业务输入。 |
| 知识库与检索 | `KnowledgeBase`、`KnowledgeDocument`、`Chunk`、`RetrievalQuery`、`RetrievalResult`、`Citation`、`Evidence` | 资料上传、解析、索引、检索、引用和证据展示。 |
| 模拟面试 | `InterviewSession`、`LaunchContext`、`ReferencePack`、`InterviewMode`、`InterviewStrategy`、`InterviewRound`、`InterviewTurn`、`Question`、`Answer`、`FollowUp` | 发起、执行、追问、多轮状态和上下文组织。 |
| 打磨模式 | `PolishModeSession`、`ProgressTree`、`UserEndDecision` | 围绕薄弱项和进度树进行多轮打磨，结束由用户决定。 |
| 压力面模式 | `PressureInterviewSession`、`InterviewQuestionSet`、`InterviewCompletion`、`FinalAssessment` | 围绕题组执行，题目完成后结束并生成整场评估。 |
| 评分与复盘 | `ScoreReport`、`ScoreDimension`、`QuestionReviewItem`、`MockInterviewReview`、`RealInterviewReview` | 总分、维度分、题级反馈、证据、岗位匹配和通过概率。 |
| 薄弱项与训练 | `WeaknessItem`、`WeaknessEvidence`、`AbilityTree`、`TrainingTask`、`TrainingQueue`、`TrainingDrawerContext` | 聚合薄弱项、训练入列、状态消减、停练和归档。 |
| 资产与导出 | `Asset`、`AssetType`、`AssetSchema`、`ArchiveRequest`、`ExportSnapshot` | 整份或单题归档、动态字段、Markdown 下载 / 复制。 |
| LLM 与审计 | `LLMGenerationRequest`、`LLMGenerationResult`、`PromptTemplateVersion`、`LLMProviderConfig`、`AuditEvent` | 生成请求、provider 配置、模板版本、低置信度和审计。 |

## 3. 数据关系

- `User` 通过权限访问 `Job`、`Resume`、`KnowledgeBase`、`InterviewSession`、`ScoreReport` 和 `Asset`。
- `Job` 与 `Resume` 组成发起模拟的业务上下文。
- `LaunchContext` 汇总岗位、简历、知识库、模式、策略和缺失输入。
- `ReferencePack` 聚合 RAG 检索结果、引用、证据缺口和面试可用资料。
- `InterviewSession` 包含多个 `InterviewRound` 和 `InterviewTurn`。
- `InterviewTurn` 关联问题、回答、追问、评分证据和修订记录。
- `ScoreReport` 关联整场、维度、题级反馈、证据、弱项和导出快照。
- `WeaknessItem` 可来自模拟面试、真实面试、打磨模式和训练反馈。
- `Asset` 可由复盘、单题、薄弱项、训练结果或用户主动归档产生。

## 4. RAG / 知识库边界

一期 RAG 支持：

- 用户私有文档上传与解析。
- 管理员公共知识库的低干扰入口。
- 文档切块、索引任务、检索查询、检索结果和引用证据。
- 面试台展示可解释的参考材料与证据缺口。
- 评分和复盘可以使用 RAG 证据，但 RAG 不直接决定分数。
- 检索失败时允许面试继续，并显式标注证据缺口。

一期不强制支持：

- 团队共享知识库。
- 多租户复杂可见性策略。
- 完整搜索爬取系统。
- 高级检索质量评估平台。

## 5. 多轮模式边界

| 模式 | 驱动对象 | 结束条件 | 关键约束 |
| --- | --- | --- | --- |
| 打磨模式 | `ProgressTree` | 用户主动结束或达到用户确认的阶段目标 | 面向能力修补和持续训练，不使用固定轮数作为总规则。 |
| 压力面模式 | `InterviewQuestionSet` | 题组完成后结束 | 固定 3 轮只能作为题组策略候选，不是所有多轮的总规则。 |
| 真实面试复盘 | `RealInterviewReview` | 材料解析和复盘生成完成 | 支持逐字稿原文，由 LLM 识别问答边界，低置信度时提示用户校对。 |

## 6. 后端服务边界

一期后端边界应覆盖：

- 账号、权限和资源可见性。
- 岗位、简历、知识库、模拟记录、复盘、导出和资产的服务端保存。
- RAG 上传、解析、索引、查询和引用证据链。
- LLM 调用、prompt 版本、生成结果和审计记录。
- 多轮状态机、暂停 / 继续 / 完成和异常恢复。
- 分数、维度、题级点评、弱项、训练建议和导出快照的可追溯保存。

本文不指定具体框架、数据库、队列、缓存、provider SDK 或 API 路由命名。

## 7. 状态字段约束

状态字段应满足：

- 可追溯：关键结果必须保留生成输入、引用证据、低置信度和版本上下文。
- 可恢复：面试、索引、评分、导出等长链路需要明确 `pending`、`running`、`failed`、`completed` 类状态。
- 可解释：评分和复盘必须能展示维度、证据和建议来源。
- 可回看：历史模拟记录、复盘详情和导出快照必须能在后续会话中重现。
- 可降级：RAG、LLM 或解析失败时，应保留可继续路径和明确提示。

## 8. 仍需后续确认的实现问题

- 具体数据库表、索引和迁移策略。
- API 路由、请求响应 schema 和分页策略。
- LLM provider 选择、fallback、超时和成本策略。
- RAG chunk 策略、embedding provider、检索排序和质量评估。
- 权限矩阵、审计日志保留周期和管理员操作边界。
