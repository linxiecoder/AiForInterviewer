# AI 模拟面试一期工作台 MVP 对象模型、RAG、多轮与后端边界草案

> 唯一事实源定位：本文档是“对象模型 / RAG / 多轮 / 后端边界”的唯一事实源。范围、IA / 用户旅程、评分 / 复盘 / 导出 / DoD 分别以对应 W13 文档为准，本文档不重复维护那些细节。

## 1. 背景

本文档是 `W13-C` 的设计前置草案，用于承接 `W13-A` 的一期工作台 MVP 范围冻结与 `W13-B` 的信息架构 / 用户旅程。本文档只做对象模型、生命周期、服务端保存边界、权限、RAG / 知识库、多轮高阶面试、面试模式、复盘、薄弱项、训练机制、资产归档、真实 LLM、API / 后端、部署 / 运维 / 配置边界梳理。

本文档不写代码，不创建 `apps/**` 或 `infra/**`，不修改 `tools/**`、`tests/**` 或 `docs/governance/DOC_STATE.yaml`，不生成 implementation packet，不放行实现窗口。W13-Cleanup 后，原确认卡只作为历史来源；当前 confirmed 范围以本文档正文、`OPEN_QUESTIONS.md` 和 `DESIGN_DECISIONS.md` 为准。

## 2. 已确认范围

以下内容是用户已确认范围，本文档不得再降级为历史推荐或待确认：

1. 一期 MVP 必须是工作台级。
2. 一期 MVP 必须包含服务端历史 / 复盘记录。
3. 一期 MVP 必须接真实 LLM。
4. 一期 MVP 必须有完整登录 / 权限。
5. 简历与面试记录必须服务端保存。
6. 一期 MVP 必须有完整 `0-100` 多维评分。
7. 导出采用复制 / Markdown 下载。
8. 当前 `apps/web/**` 原型仅作为参考证据。
9. 暂停代码开发，回到设计文档补齐。
10. 一期 MVP 必须包含 RAG / 知识库。
11. 一期 MVP 必须包含多轮高阶面试。
12. 模拟面试模块默认入口是历史模拟记录列表。
13. 发起模拟面试从记录列表进入。
14. 面试台是执行页。
15. 面试完成后回写历史记录 / 复盘。
16. 模拟面试可从岗位详情或模拟面试模块发起。
17. 发起模拟面试时选择岗位、简历、模式。
18. 系统整理参考材料包。
19. 系统生成面试策略与首题。
20. 一期至少包含打磨模式和模拟模式。
21. 打磨模式支持基于薄弱项、自定义主题、岗位 / 简历自动推荐开启。
22. 打磨模式中薄弱项不是必填输入。
23. 打磨模式每轮回答后输出本题得分、失分点、失分证据、参考回答、为什么这样回答更好、参考回答与失分点对应关系、相关技术原理。
24. 打磨模式同步更新能力树、当前进展、薄弱点、建议下一题方向。
25. 模拟模式更贴近真实面试节奏，面试过程中弱化中途打断。
26. 模拟模式结束后输出最终掌握情况、岗位匹配度、薄弱点、通过概率、建议打磨主题。
27. 复盘来源包括真实面试材料和模拟面试结果。
28. 真实面试复盘要求逐题严格拆解。
29. 模拟面试复盘重点展示整场判断、多维评分、岗位匹配度、通过概率、逐题点评、改进建议。
30. 支持整份归档到资产库。
31. 支持单题归档到资产库。
32. 归档时选择资产类型。
33. 若资产类型带 schema，则动态渲染字段表单。
34. 薄弱项 `WeaknessItem` 是可训练、可累计、可消减、可停练的中粒度训练主题。
35. 薄弱项来源包括岗位-简历匹配分析、模拟面试详情 / 报告、复盘报告。
36. 薄弱项按岗位聚合、按主题归并、保留所有证据。
37. 用户管理的是聚合后的 `WeaknessItem`。
38. 薄弱项状态包括 `active`、`low_priority`、`dismissed`、`resolved`。
39. 薄弱项有消减规则和用户停练规则。
40. 待打磨是执行层，不等于薄弱项中心。
41. 训练抽屉是统一训练入口。
42. 训练抽屉入口包括岗位详情、模拟面试详情 / 报告、复盘详情。
43. 训练抽屉支持归并到薄弱项、加入待打磨、立即发起打磨、暂不处理。
44. 训练抽屉展示来源摘要、严重度、关联岗位、证据摘要、推荐归并主题、操作影响预览。

### 2.1 用户补充确认：多轮面试按模式拆分

用户已补充确认：一期 MVP 中“多轮面试”不再按此前推荐的“固定 3 轮”作为总规则处理。此前“多轮范围 = A：固定 3 轮”不得写成 `confirmed`，也不再作为 `historical` 总规则。

当前 confirmed 口径为：

- 打磨模式是训练型模式：根据 `ProgressTree / 进展树` 持续出题；系统根据用户每轮回答更新能力树、当前进展、薄弱点和建议下一题方向；用户决定是否继续或结束；不固定轮次数。
- 压力面模式是模拟真实面试节奏的模式：系统生成模拟面试题组；用户按题完成面试；题目完成后面试结束；过程中不强调每题即时打断；结束后输出最终掌握情况、岗位匹配度、薄弱点、通过概率、建议打磨主题、多维评分和复盘报告。
- 题目数量、难度、题型组合仍可后续确认。
- 固定 3 轮最多只能作为压力面模式的一种候选题组策略，不是一期多轮面试总规则。

## 3. 一期 MVP 对象模型草案

本节只定义对象职责与关系，不定义完整数据库 schema。字段族中的实现细节仍需用户确认或由 `W13-D` 承接。

| 对象 | 对象职责 | 是否已由 confirmed 范围要求 | 是否服务端保存 | 是否涉及敏感信息 | 与其他对象关系 | 待确认字段族 | 是否阻断一期开发 | 输入给 W13-D 的验收点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `User` | 表示真实使用者、资源创建者和访问者 | 是，完整登录 / 权限要求 | 是 | 是，身份与个人资料 | 关联 `Account`、`Role`、`Workspace / Organization` 和业务资源 | 用户资料、状态、停用、归属 | 是 | 评分、复盘、导出必须按用户权限读取 |
| `Account` | 表示登录账号、认证凭据与会话边界 | 是 | 是 | 是，登录凭据、会话、账号状态 | 属于 `User`，受 `Role` 和登录机制约束 | 账号来源、登录机制、凭据策略、会话过期 | 是 | 复盘和导出入口必须处理未登录 / 权限不足 |
| `Role` | 表示角色层级和默认能力集合 | 是 | 是 | 中，权限信息 | 绑定用户或 workspace membership，关联 `Permission` | 两级 / 三级 / owner-member-admin | 是 | 列表、复盘、归档、导出动作必须按角色可见 |
| `Permission` | 表示资源可见范围和动作授权 | 是 | 是 | 中，授权策略 | 被 `Role` 使用，作用于 `Job`、`Resume`、`KnowledgeBase`、`InterviewSession`、`Asset` | 读写、导出、归档、管理、审计粒度 | 是 | 权限不足状态和审计动作可验收 |
| `Workspace / Organization` | 表示团队或工作台资源隔离范围 | 是，权限和服务端保存隐含要求 | 是 | 中，组织关系 | 包含用户、岗位、简历、知识库、面试、资产 | 单组织 / 多组织、邀请、成员关系 | 是 | 团队范围记录和知识库可见性可验收 |
| `Job` | 保存岗位输入、岗位目标、能力要求和发起面试约束 | 是 | 是 | 中，可能含公司或业务信息 | 被面试、复盘、薄弱项、训练、资产引用 | 必填字段、版本、归档、可见范围 | 是 | 评分和复盘必须能引用岗位要求作为证据 |
| `Resume` | 保存用户简历内容、版本和面试输入 | 是 | 是 | 是，个人经历和联系方式 | 被面试、复盘、薄弱项、训练引用 | 上传 / 粘贴、版本、解析、脱敏、归档 | 是 | 评分、复盘、导出必须能引用简历事实 |
| `KnowledgeBase` | 表示可选择的知识库集合 | 是，RAG / 知识库要求 | 是 | 视材料而定 | 包含 `KnowledgeDocument`，被 `InterviewSession` 选择 | 个人 / 团队 / 公共范围、创建者、状态 | 是 | 复盘需说明是否使用知识库证据 |
| `KnowledgeDocument` | 表示知识库中的原始材料 | 是 | 是 | 可能高，含业务或个人资料 | 属于 `KnowledgeBase`，产生 `KnowledgeChunk` | 上传范围、文件类型、解析状态、删除策略 | 是 | 引用来源必须可回溯到文档 |
| `KnowledgeChunk` | 表示可检索知识片段 | 是 | 是 | 可能高 | 来自 `KnowledgeDocument`，进入 `RetrievalResult` | 切片粒度、embedding、权限过滤、重建 | 是 | 引用摘要和证据可信度可展示 |
| `RetrievalQuery` | 记录一次 RAG 查询意图和上下文 | 是 | 是，保存粒度待确认 | 可能高，含岗位 / 简历 / 回答摘要 | 由面试、打磨、评分、复盘触发 | query 原文、脱敏、topK、失败原因 | 是 | 复盘需说明检索是否命中与降级路径 |
| `RetrievalResult` | 记录检索命中结果、排序和得分 | 是 | 是，保存粒度待确认 | 可能高 | 引用 `KnowledgeChunk`，生成 `Citation / Evidence` | topK 保存范围、score、rerank、过期处理 | 是 | 每条 RAG 引用需能解释来源 |
| `Citation / Evidence` | 将 LLM 输出、评分、复盘、失分点与证据绑定 | 是 | 是 | 中到高 | 指向岗位、简历、回答、知识库片段、检索结果、真实面试材料 | 证据类型、显示摘要、引用粒度 | 是 | `0-100` 评分和复盘结论必须有证据依据 |
| `IndexingJob` | 表示文档解析、切片、索引任务 | 是 | 是 | 中 | 作用于 `KnowledgeDocument` 和 `KnowledgeChunk` | 同步 / 异步、重试、失败恢复、日志 | 是 | 知识库不可用和索引失败态可验收 |
| `EmbeddingProvider` | 表示向量化 provider 或检索向量边界 | 是，若采用向量或混合检索 | 是，配置保存待确认 | 是，可能含密钥或模型配置 | 被 `IndexingJob` 和检索链使用 | provider、模型、维度、成本、fallback | 取决于检索路线 | RAG 失败 / 降级需可解释 |
| `InterviewSession` | 表示一次模拟面试会话主对象 | 是 | 是 | 是，含面试与评价数据 | 关联用户、岗位、简历、知识库、模式、轮次、评分、复盘 | 状态、暂停 / 继续、归档、可见范围 | 是 | 完整记录、评分、复盘和导出以它为主线 |
| `InterviewLaunchContext` | 表示发起面试时选择的岗位、简历、模式、来源入口和约束 | 是 | 是 | 中到高 | 生成 `InterviewReferencePack`、`InterviewStrategy`、首题 | 岗位 / 简历缺失是否允许、默认值、入口来源 | 是 | 发起流程和缺失输入错误态可验收 |
| `InterviewReferencePack` | 表示系统整理出的参考材料包 | 是 | 是 | 高，含岗位、简历、知识库摘要 | 由发起上下文、RAG、简历、岗位生成，被策略和首题使用 | 包含范围、摘要策略、证据引用 | 是 | 首题、评分、复盘需能回看参考材料来源 |
| `InterviewMode` | 表示打磨模式、压力面模式及后续模式枚举 | 是 | 是 | 低 | 约束 `InterviewSession`、`PolishModeSession`、`PressureInterviewSession` | 模式枚举、默认模式、模式切换 | 是 | 模式差异必须影响反馈时机、结束条件和报告内容 |
| `InterviewStrategy` | 表示面试策略、轮次规则、难度和高阶定义 | 是 | 是 | 低到中 | 由 `InterviewLaunchContext` 生成，约束轮次和问题 | 固定轮次、岗位驱动、弱项驱动、结束条件 | 是 | 策略如何影响评分和复盘由 W13-D 验收 |
| `FirstQuestionGeneration` | 表示首题生成过程和结果 | 是 | 是 | 中到高 | 依赖 `InterviewReferencePack`、RAG、LLM 请求 | 失败重试、候选数量、引用显示 | 是 | 首题必须可追溯 LLM / RAG 证据 |
| `InterviewRound` | 表示多轮高阶面试中的一轮 | 是 | 是 | 中 | 属于 `InterviewSession`，包含多个 `InterviewTurn` | 轮次策略、跳过规则、结束条件 | 是 | 每轮评价如何进入总分由 W13-D 验收 |
| `InterviewTurn` | 表示一次问答 turn | 是 | 是 | 是，含用户回答 | 属于 `InterviewRound`，关联问题、回答、检索、证据 | turn 类型、重试、修订、上下文摘要 | 是 | 逐题复盘和导出需要完整 turn |
| `InterviewQuestion` | 表示 LLM 生成的面试问题 | 是 | 是 | 中 | 属于 turn 或 round，可引用 RAG 证据 | 生成来源、版本、追问关系、失败状态 | 是 | 问题需能绑定评分和证据 |
| `InterviewAnswer` | 表示用户回答 | 是 | 是 | 是，含个人经历和面试表现 | 回答问题，进入评分、复盘、薄弱项、训练 | 草稿、提交、修改、空回答处理 | 是 | 回答需进入评分、复盘、导出 |
| `FollowUpQuestion` | 表示追问或深挖问题 | 是，多轮高阶要求 | 是 | 中 | 关联父问题、回答和轮次策略 | 追问深度、生成条件、最大次数 | 是 | 高阶面试需能验收追问链 |
| `InterviewContext` | 表示当前面试上下文摘要与可恢复状态 | 是，暂停 / 继续和多轮需要 | 是，保存方式待确认 | 是，含摘要和证据 | 汇总岗位、简历、RAG、历史 turns、策略 | 完整上下文 / 摘要 / token 裁剪 | 是 | 暂停 / 继续与复盘可信度依赖该对象 |
| `RoundEvaluation` | 表示单轮评价结果 | 是，多轮和评分要求 | 是 | 中 | 属于 `InterviewRound`，汇总到 `ScoreReport` | 维度、权重、证据、是否可修订 | 是 | 每轮评价如何进入总分是 W13-D 输入 |
| `PolishModeSession` | 表示一次打磨模式训练会话 | 是 | 是 | 高，含弱项、回答、反馈 | 是 `InterviewSession` 的模式化子对象，关联 `WeaknessItem`、`TrainingTask`、`ProgressTree`、`UserEndDecision` | 开启来源、保存粒度、用户结束决策 | 是 | 每题即时反馈、进展更新、用户决定继续 / 结束和下一题建议可验收 |
| `ProgressTree` | 表示打磨模式中的进展树 | 是，用户已确认打磨模式按进展树持续出题 | 是 | 中 | 关联 `PolishModeSession`、`AbilityTree`、`TrainingProgress`、`NextQuestionRecommendation` | 节点粒度、进展计算、展示层级 | 是 | W13-D 需区分进展树驱动的持续训练与压力面题组完成 |
| `WeaknessItem` | 表示中粒度、可训练、可累计、可消减、可停练的薄弱主题 | 是 | 待确认，推荐服务端保存 | 中到高 | 聚合 `WeaknessEvidence`，关联岗位、训练、复盘 | 聚合 key、状态、消减、归并、停练 | 是，需确认实现深度 | 弱项如何影响打磨建议和复盘输出 |
| `WeaknessEvidence` | 表示薄弱项的所有来源证据 | 是 | 是 | 高，可能含回答与复盘片段 | 来自岗位-简历匹配、模拟报告、复盘报告 | 证据类型、置信度、引用摘要、权限 | 是 | 弱项结论必须可回看证据 |
| `WeaknessStatus` | 表示 `active`、`low_priority`、`dismissed`、`resolved` 状态 | 是 | 是 | 低 | 属于 `WeaknessItem` | 状态变更条件、恢复 active 条件 | 是 | 训练建议需尊重状态 |
| `WeaknessAggregationRule` | 表示按岗位聚合、按主题归并的规则 | 是 | 是，规则版本待确认 | 中 | 用于归并 `WeaknessEvidence` 到 `WeaknessItem` | 聚合 key、相似度、人工确认 | 是 | 训练抽屉的推荐归并主题需可解释 |
| `WeaknessDecayRule` | 表示薄弱项消减规则 | 是 | 待确认 | 中 | 根据训练结果、评分、复盘更新弱项状态 | 自动执行 / 推荐执行、阈值、窗口期 | 是，需确认 | 打磨完成后弱项如何降级或 resolved |
| `WeaknessDismissal` | 表示用户停练 / 暂不处理记录 | 是 | 是 | 中 | 作用于 `WeaknessItem` 或来源建议 | 停练原因、持续时间、恢复条件 | 是 | dismissed 后再次暴露需有规则 |
| `AbilityTree` | 表示能力树总结构 | 是，打磨同步更新能力树 | 待确认 | 中 | 包含 `AbilityNode`、`AbilityLevel`、训练进展 | 完整树 / 轻量树、岗位差异 | 是，需确认深度 | 能力树是否进入一期由确认卡决定 |
| `AbilityNode` | 表示能力树中的能力节点 | 是 | 待确认 | 中 | 被弱项、评分、训练进展引用 | 节点粒度、层级、标签 | 取决于能力树深度 | 评分和训练建议是否能映射节点 |
| `AbilityLevel` | 表示能力节点等级或掌握度 | 是 | 待确认 | 中 | 属于 `AbilityNode`，由评分和训练更新 | 等级范围、计算规则、显示方式 | 取决于能力树深度 | 掌握度展示和变化趋势可验收 |
| `TrainingProgress` | 表示打磨会话和弱项训练进展 | 是 | 是 | 中 | 关联 `PolishModeSession`、`TrainingTask`、`ProgressTree`、能力树 | 当前进展、连续训练、完成条件 | 是 | 打磨后当前进展必须可回写 |
| `LossPoint` | 表示单题失分点 | 是 | 是，保存粒度待确认 | 中 | 属于打磨反馈或题目复盘 | 失分类别、严重度、证据引用 | 是 | 每题反馈必须列出失分点 |
| `LossEvidence` | 表示支持失分点的证据 | 是 | 是 | 高 | 指向回答、岗位、简历、RAG、复盘材料 | 引用摘要、证据强度、显示范围 | 是 | 失分点不得无证据 |
| `ReferenceAnswer` | 表示参考回答 | 是 | 是，保存粒度待确认 | 中 | 关联问题、失分点、技术原理 | 完整回答、框架、版本、引用 | 是 | 每题反馈必须展示参考回答 |
| `AnswerImprovementRationale` | 说明为什么参考回答更好 | 是 | 是 | 中 | 关联参考回答和失分点 | 对应关系、解释深度、技术原理 | 是 | 打磨反馈必须解释“为什么更好” |
| `NextQuestionRecommendation` | 表示下一题方向建议 | 是 | 是 | 中 | 由打磨反馈、弱项、训练进展和 `ProgressTree` 生成 | 推荐方向、依据、难度 | 是 | 每轮打磨后必须能生成下一题方向 |
| `UserEndDecision` | 表示用户在打磨模式中继续或结束的显式决策 | 是，用户已确认打磨模式由用户决定是否继续 / 结束 | 是 | 中 | 关联 `PolishModeSession`、`InterviewTurn`、`TrainingProgress` | 继续 / 结束动作、结束原因、是否生成总结 | 是 | 打磨模式不得被固定轮次自动结束 |
| `SimulationModeSession` | 表示原“模拟模式”会话的历史命名，当前设计中应按压力面模式收敛 | 是 | 是 | 高 | 与 `PressureInterviewSession` 对齐 | 是否保留别名、迁移命名 | 否，命名可由后续实现统一 | 不得继续用该对象表达固定 3 轮总规则 |
| `PressureInterviewSession` | 表示一次压力面模式会话 | 是，用户已确认压力面模式模拟真实面试节奏 | 是 | 高 | 是 `InterviewSession` 的模式化子对象，包含 `InterviewQuestionSet`、`InterviewCompletion` | 题目数量、难度、题型组合 | 是 | 题组完成后结束，结束后集中生成评分和复盘 |
| `InterviewQuestionSet` | 表示压力面模式题组 | 是 | 是 | 中 | 包含多个 `InterviewQuestion`，由 `PressureInterviewSession` 使用 | 题目数量、题型、难度、生成策略 | 是 | 题组完成是压力面结束条件 |
| `FinalMasteryAssessment / FinalAssessment` | 表示最终掌握情况和整场最终评估 | 是 | 是 | 中 | 属于压力面模式报告和复盘 | 维度、证据、等级 | 是 | 压力面结束必须输出最终掌握情况 |
| `JobMatchAssessment` | 表示岗位匹配度判断 | 是 | 是 | 中 | 关联岗位、简历、回答、评分 | 匹配维度、权重、证据 | 是 | 模拟报告必须展示岗位匹配度 |
| `PassProbability` | 表示通过概率 | 是 | 是 | 中 | 由评分、岗位匹配、风险点生成 | 概率模型、区间、解释 | 是，W13-D 细化 | 通过概率需有证据与说明 |
| `SuggestedPolishTopic` | 表示建议打磨主题 | 是 | 是 | 中 | 可转入 `WeaknessItem` 或 `TrainingTask` | 生成条件、去重、优先级 | 是 | 模拟结束后必须可生成建议主题 |
| `WeaknessSummary` | 表示压力面模式结束后的薄弱点汇总 | 是 | 是 | 中 | 汇总 `WeaknessItem`、`RoundEvaluation`、`ScoreReport` | 汇总粒度、证据映射、去重 | 是 | W13-D 需将薄弱点汇总纳入复盘报告 |
| `InterviewCompletion` | 表示压力面模式题组完成后的结束事件 | 是 | 是 | 中 | 连接 `PressureInterviewSession`、`InterviewQuestionSet`、`ScoreReport`、`MockInterviewReview` | 完成条件、失败态、是否允许补答 | 是 | 压力面模式以题组完成结束，而非固定轮次结束 |
| `ReviewSource` | 表示复盘来源，真实面试材料或模拟面试结果 | 是 | 是 | 高 | 指向 `RealInterviewReview` 或 `MockInterviewReview` | 来源录入、权限、原始材料类型 | 是 | 复盘必须区分真实 / 模拟来源 |
| `RealInterviewReview` | 表示真实面试复盘 | 是 | 待确认实现深度 | 高 | 包含多个 `QuestionReviewItem` | 录入方式、逐题完整度、导出 | 是，需确认深度 | 真实复盘是否进入一期需用户确认 |
| `MockInterviewReview` | 表示模拟面试复盘 | 是 | 是 | 高 | 来自 `InterviewSession` 和 `ScoreReport` | 报告范围、逐题点评、建议 | 是 | 模拟复盘必须覆盖整场和逐题 |
| `QuestionReviewItem` | 表示复盘中的单题拆解项 | 是 | 是 | 高 | 包含原始问题、回答、问题意图和改进项 | 字段完整度、排序、引用 | 是 | 真实面试复盘逐题严格拆解 |
| `AnswerIssue` | 表示回答问题的总类 | 是 | 是 | 中 | 聚合遗漏、错误、表达问题 | 分类、严重度、证据 | 是 | 复盘逐题问题可结构化 |
| `MissingPoint` | 表示遗漏点 | 是 | 是 | 中 | 属于 `QuestionReviewItem` | 缺失内容、证据、影响 | 是 | 真实复盘必须列遗漏点 |
| `ErrorPoint` | 表示错误点 | 是 | 是 | 中 | 属于 `QuestionReviewItem` | 错误事实、纠正说明 | 是 | 真实复盘必须列错误点 |
| `ExpressionIssue` | 表示表达问题 | 是 | 是 | 中 | 属于 `QuestionReviewItem` | 表达类型、示例、建议 | 是 | 真实复盘必须列表达问题 |
| `BetterAnswerFramework` | 表示更优回答框架 | 是 | 是 | 中 | 属于真实 / 模拟复盘逐题项 | 框架步骤、示例、证据 | 是 | 逐题复盘必须给出更优框架 |
| `FollowUpRisk` | 表示继续追问风险 | 是 | 是 | 中 | 来自回答问题和岗位要求 | 风险类型、触发点、建议 | 是 | 真实复盘必须展示追问风险 |
| `OverallAssessment` | 表示整场复盘总体判断 | 是 | 是 | 中 | 汇总评分、匹配度、概率、弱项 | 结论结构、证据、风险 | 是 | 模拟复盘必须展示整场判断 |
| `TrainingQueue` | 表示待打磨执行层清单 | 是 | 待确认页面化深度 | 中 | 包含 `TrainingTask`，不等于薄弱项中心 | 独立页面 / 嵌入式、排序、清理 | 是，需确认 | 待打磨和弱项中心必须区分 |
| `TrainingTask` | 表示一次待打磨任务 | 是 | 是 | 中 | 来自弱项、训练抽屉、建议主题 | 状态、来源、执行入口、优先级 | 是 | 可立即发起打磨或加入待打磨 |
| `TrainingDrawerContext` | 表示训练抽屉打开时的上下文 | 是 | 是或临时保存待确认 | 中到高 | 来源于岗位、模拟详情 / 报告、复盘详情 | 来源摘要、推荐归并、操作预览 | 是 | 训练抽屉是统一训练入口 |
| `TrainingSource` | 表示训练来源 | 是 | 是 | 中 | 指向岗位、模拟报告、复盘报告、题目 | 来源类型、原始引用、权限 | 是 | 训练建议必须可追溯来源 |
| `TrainingAction` | 表示训练抽屉操作 | 是 | 是 | 中 | 作用于弱项、待打磨、打磨会话 | 归并、加入待打磨、立即打磨、暂不处理 | 是 | 四类操作都需可验收 |
| `TrainingImpactPreview` | 表示操作影响预览 | 是 | 可临时或保存待确认 | 中 | 基于 `TrainingAction` 生成 | 影响对象、状态变化、风险提示 | 是 | 操作前必须说明影响 |
| `RecommendedMergeTopic` | 表示推荐归并主题 | 是 | 是 | 中 | 由弱项聚合规则生成 | 相似度、目标弱项、解释 | 是 | 推荐归并必须可解释 |
| `Severity` | 表示严重度 | 是 | 是 | 低到中 | 用于弱项、训练来源、失分点、问题 | 分级、计算规则、显示文案 | 是 | 训练抽屉展示严重度 |
| `Asset` | 表示资产库中的归档对象 | 是 | 是 | 中到高 | 由归档请求创建，关联类型和来源 | 资产状态、权限、搜索、归档范围 | 是 | 整份 / 单题归档需落到资产 |
| `AssetType` | 表示资产类型 | 是 | 是 | 中 | 约束 `Asset` 和 `AssetSchema` | 类型来源、管理员管理、启停 | 是 | 归档时必须选择资产类型 |
| `AssetSchema` | 表示资产类型字段 schema | 是，动态字段表单要求 | 是 | 中 | 绑定 `AssetType`，渲染字段表单 | schema 表达、字段类型、校验 | 是，需确认边界 | 动态字段是否一期支持需确认 |
| `AssetArchiveRequest` | 表示一次归档请求 | 是 | 是 | 中到高 | 从复盘、题目、回答、报告发起 | 整份 / 单题、失败重试、权限 | 是 | 归档失败、成功、字段校验可验收 |
| `AssetFieldValue` | 表示动态字段填写值 | 是 | 是 | 视字段而定 | 属于 `Asset`，由 `AssetSchema` 约束 | 类型、校验、脱敏、展示 | 是 | schema 字段保存和展示可验收 |
| `ArchivedQuestion` | 表示单题归档结果 | 是 | 是 | 高 | 指向原题、回答、复盘项、资产 | 原始来源、引用快照、题目版本 | 是 | 单题归档必须保留来源 |
| `ArchivedReview` | 表示整份复盘归档结果 | 是 | 是 | 高 | 指向真实 / 模拟复盘、资产 | 报告快照、引用、权限 | 是 | 整份归档必须可回看来源 |
| `FeedbackSummary` | 表示复盘摘要、建议和诊断文字 | 是 | 是 | 中 | 关联 `ScoreReport`、`SessionRecord`、证据 | 摘要结构、建议数量、引用展示 | 是 | 复盘详情和 Markdown 导出必须覆盖 |
| `ScoreReport` | 表示 `0-100` 多维评分报告 | 是 | 是 | 中 | 关联会话、轮次评价、评分维度和证据 | 维度、权重、通过线、版本、修订 | 是，W13-D 细化 | W13-D 需冻结评分 DoD |
| `ScoreDimension` | 表示评分维度和权重 | 是 | 是 | 低 | 被 `ScoreReport` 和 `RoundEvaluation` 使用 | 维度集合、权重、岗位类型差异 | 是，W13-D 细化 | W13-D 需确认维度与权重 |
| `SessionRecord` | 表示历史模拟记录列表中的展示记录 | 是 | 是 | 中 | 聚合会话、评分、复盘、导出、归档状态 | 列表字段、筛选、权限、删除 | 是 | 默认入口和回写行为可验收 |
| `ExportSnapshot / ExportRecord` | 表示复制 / Markdown 下载的内容快照与导出动作 | 是 | 是，保存程度待确认 | 中到高 | 读取复盘、评分、证据、会话记录 | 是否记录复制、快照保留、文件名、内容范围 | 是，W13-D 细化 | Markdown 复制 / 下载 DoD 依赖该对象 |
| `LLMGenerationRequest` | 表示一次 LLM 调用请求 | 是，真实 LLM 要求 | 是，保存程度待确认 | 高，可能含 prompt / 上下文 | 关联会话、轮次、问题、评分、provider | prompt 保存、脱敏、超时、重试、成本 | 是 | 失败态和评分生成需可追溯 |
| `LLMGenerationResult` | 表示 LLM 调用结果或失败状态 | 是 | 是，保存程度待确认 | 高，可能含生成内容 | 对应请求，生成问题、反馈、评分、复盘 | response 保存、错误码、重试、token / 成本 | 是 | 失败后重试和复盘生成状态可验收 |
| `PromptTemplateVersion` | 表示 prompt 模板版本 | 是，真实 LLM 可追溯需要 | 是 | 低到中 | 被 LLM request 引用 | 模板版本、变量、场景、变更记录 | 是 | 评分和复盘输出需有版本依据 |
| `LLMProviderConfig` | 表示真实 LLM provider 配置边界 | 是 | 是，密钥应安全保存或外置 | 是，含密钥和模型配置 | 被 LLM adapter 使用，关联审计和成本 | provider、模型、key 管理、限额、fallback | 是 | 真实 LLM 接入与失败处理依赖该对象 |
| `AuditEvent / OperationLog` | 表示关键操作、权限、LLM、RAG、导出、归档的审计记录 | 是，权限和服务端保存隐含要求 | 是 | 中到高 | 关联用户、资源、LLM / RAG / 导出动作 | 日志范围、保留周期、脱敏、成本记录 | 是，至少需最小边界 | 导出 / 复盘 / 归档操作可追踪 |

## 4. 对象生命周期草案

| 对象 | 生命周期草案 | 状态说明 | 是否需要确认卡 |
| --- | --- | --- | --- |
| `Job` | `draft -> active -> archived` | `draft` 可编辑未用于正式面试；`active` 可被发起面试选择；`archived` 不再默认显示但保留历史引用 | 否，当前可作为草案；归档 / 删除细节后续确认 |
| `Resume` | `draft -> ready -> archived` | `draft` 保存编辑中内容；`ready` 可用于发起面试；`archived` 保留历史引用 | 否；上传 / 版本细节后续确认 |
| `KnowledgeDocument` | `uploaded -> parsing -> indexed -> failed -> archived` | 上传后解析；成功后可检索；失败需展示原因；归档后不再参与新检索 | 是，上传范围、失败重试和删除策略待确认 |
| `IndexingJob` | `queued -> running -> succeeded -> failed` | 控制知识库索引任务可观测性 | 是，异步任务、重试和日志边界待确认 |
| `InterviewSession` | `draft -> ready -> in_progress -> paused -> completed -> reviewed -> archived` | 草稿发起、准备就绪、执行中、暂停、完成、已复盘、归档 | 是，暂停 / 继续、归档 / 删除和恢复策略待确认 |
| `InterviewRound` | `pending -> active -> completed -> skipped` | 多轮流程中的单轮状态 | 是，跳过是否允许、轮次策略待确认 |
| `InterviewTurn` | `asked -> answered -> evaluated -> revised` | 问题提出、用户回答、被评价、可选修订 | 是，是否允许修订和题中暂停待确认 |
| `PolishModeSession` | `draft -> active -> paused -> completed -> archived` | 打磨准备、训练中、暂停、完成、归档 | 是，暂停 / 保存粒度 / 结束条件待确认 |
| `SimulationModeSession` | `draft -> active -> completed -> reviewed -> archived` | 模拟准备、执行中、完成、已复盘、归档 | 是，即时评分和结束后总结范围待确认 |
| `PressureInterviewSession` | `draft -> active -> completed -> reviewed -> archived` | 压力面准备、题组作答中、题组完成、已复盘、归档 | 是，题目数量、难度和题型组合仍待确认 |
| `InterviewQuestionSet` | `draft -> generated -> active -> completed -> archived` | 题组草稿、已生成、作答中、全部完成、归档 | 是，固定 3 轮只能作为题组策略候选，不是总规则 |
| `InterviewCompletion` | `pending -> completed -> reviewed -> archived` | 等待题组完成、已完成、已进入复盘、归档 | 是，失败态和补答策略仍待确认 |
| `WeaknessItem` | `active -> low_priority -> dismissed -> resolved` | 活跃、低优先级、用户停练、已解决 | 是，消减自动化和恢复 active 规则待确认 |
| `TrainingTask` | `queued -> active -> completed -> dismissed` | 待打磨、执行中、完成、暂不处理 | 是，独立页面化和排序规则待确认 |
| `AssetArchiveRequest` | `draft -> submitted -> archived -> failed` | 草稿、提交、归档成功、归档失败 | 是，字段校验、重试和失败展示待确认 |
| `ScoreReport` | `pending -> generated -> revised -> archived` | 评分等待、生成、修订、归档 | 由 `W13-D` 确认 |
| `ExportSnapshot` | `generated -> copied -> downloaded` | 内容生成后可复制或下载，是否记录复制动作待确认 | 由 `W13-D` 确认 |

## 5. 模拟面试启动边界

一期必须支持两个入口：

- 从岗位详情发起新面试。
- 从模拟面试模块的历史记录列表发起新面试。

启动流程草案：

```text
入口动作
-> InterviewLaunchContext
-> 选择 Job / Resume / InterviewMode
-> 整理 InterviewReferencePack
-> 根据 InterviewMode 生成 InterviewStrategy
-> RAG 检索可用材料
-> LLM 生成 FirstQuestionGeneration
-> InterviewSession ready / in_progress
```

边界说明：

- `InterviewLaunchContext` 必须记录入口来源、用户、workspace、岗位、简历、模式、知识库选择和缺失输入状态。
- `InterviewReferencePack` 至少包含岗位要求摘要、简历事实摘要、知识库引用摘要、历史弱项摘要、模式要求和证据清单。
- `InterviewMode` 影响 `InterviewStrategy`：打磨模式允许每题即时反馈和下一题建议，模拟模式弱化中途打断并在结束后输出整场判断。
- `FirstQuestionGeneration` 必须关联真实 LLM 调用和 RAG 证据；RAG 失败时不得伪装成有证据生成。
- 岗位或简历缺失是否允许发起仍需用户确认，见确认卡“岗位 / 简历是否是发起模拟面试的必选输入”。

## 6. 打磨模式边界

打磨模式确认进入一期，且必须支持以下开启方式：

- 基于薄弱项开启。
- 基于自定义主题开启。
- 基于岗位 / 简历自动推荐开启。
- 薄弱项不是必填输入。
- 根据 `ProgressTree / 进展树` 持续出题。
- 每轮回答后更新能力树、当前进展、薄弱点和建议下一题方向。
- 用户通过 `UserEndDecision` 决定继续或结束。
- 不固定轮次数，不得把“固定 3 轮”写成打磨模式规则。

每轮回答后必须输出：

- 本题得分。
- 失分点。
- 失分证据。
- 参考回答。
- 为什么这样回答更好。
- 参考回答与失分点对应关系。
- 相关技术原理。
- 能力树更新。
- 当前进展更新。
- 薄弱点更新。
- 下一题方向建议。

对象关系草案：

```text
PolishModeSession
-> InterviewTurn / InterviewAnswer
-> LossPoint + LossEvidence
-> ReferenceAnswer + AnswerImprovementRationale
-> ProgressTree
-> AbilityTree / AbilityNode / AbilityLevel
-> TrainingProgress
-> WeaknessItem / TrainingTask
-> NextQuestionRecommendation
-> UserEndDecision
```

边界说明：

- 打磨模式可以从 `WeaknessItem` 来，也可以只从自定义主题或岗位 / 简历推荐来；没有 `WeaknessItem` 时不得阻止启动。
- 打磨模式可以生成或更新 `WeaknessItem`，但 `WeaknessItem` 是否作为一期核心对象独立服务端保存仍需确认。
- 打磨模式可以消耗或生成 `TrainingTask`，但待打磨清单只是执行层，不等于薄弱项中心。
- 打磨模式每题反馈是否完整保存仍需确认。推荐保存结构化反馈和证据，而不是只保存在当前会话 UI。
- 打磨模式是否进入 `ScoreReport` 由 `W13-D` 细化；当前草案建议打磨模式有题级得分，但整场 `ScoreReport` 与模拟模式区分展示。
- 打磨模式结束条件已确认由用户决定是否继续或结束，不再按固定轮次自动结束。

## 7. 压力面模式边界

压力面模式确认进入一期，目标是更接近真实面试节奏。它承接原 W13-C “模拟模式”的真实面试节奏语义，但不继承“固定 3 轮”作为总规则：

- 系统生成模拟面试题组。
- 用户按题完成面试。
- 题目完成后面试结束。
- 面试过程中弱化中途打断。
- 仍保留必要的错误状态、暂停状态和保存状态。
- 结束后输出最终掌握情况、岗位匹配度、薄弱点、通过概率、建议打磨主题、多维评分和复盘报告。

对象关系草案：

```text
PressureInterviewSession
-> InterviewQuestionSet
-> InterviewQuestion / InterviewAnswer
-> InterviewCompletion
-> FinalAssessment / FinalMasteryAssessment
-> JobMatchAssessment
-> PassProbability
-> ScoreReport
-> WeaknessSummary
-> SuggestedPolishTopic
-> MockInterviewReview
-> WeaknessItem / TrainingDrawerContext
```

边界说明：

- 压力面模式是多轮高阶面试的主要承载形态之一；题目数量、难度、题型组合仍需确认。
- 固定 3 轮最多只能作为压力面模式的一种候选题组策略，不是一期多轮面试总规则。
- 压力面模式过程中不强调每题即时打断；必要评价证据可后台保留，结束后集中展示。
- `SuggestedPolishTopic` 由整场表现、岗位匹配、失分点和弱项证据生成，可进入训练抽屉。
- 压力面模式如何回写 `WeaknessItem` 取决于薄弱项是否作为一期核心服务端对象和消减规则是否自动执行。

## 8. 复盘模型

复盘来源确认包括：

- 真实面试材料。
- 模拟面试结果。

真实面试复盘必须覆盖：

- 原始问题。
- 原始回答。
- 问题意图。
- 回答问题。
- 遗漏点。
- 错误点。
- 表达问题。
- 更优回答框架。
- 继续追问风险。

模拟面试复盘必须覆盖：

- 整场判断。
- 多维评分。
- 岗位匹配度。
- 通过概率。
- 逐题点评。
- 改进建议。

边界说明：

- `RealInterviewReview` 与 `MockInterviewReview` 建议共享 `ReviewSource`、`QuestionReviewItem`、`OverallAssessment`、`Citation / Evidence` 等底层对象，但页面和报告重点不同。
- 真实面试材料如何录入、是否完整进入一期实现深度仍需确认。
- 复盘可以生成 `WeaknessEvidence` 和 `SuggestedPolishTopic`，再通过训练抽屉让用户决定归并、加入待打磨、立即打磨或暂不处理。
- 复盘整份和单题都可以进入资产归档流程。

## 9. 薄弱项体系

薄弱项 confirmed 口径：

- `WeaknessItem` 是中粒度训练主题，不是小知识点。
- 来源包括岗位-简历匹配分析、模拟面试详情 / 报告、复盘报告。
- 按岗位聚合、按主题归并、保留所有证据。
- 用户管理的是聚合后的 `WeaknessItem`。
- 状态包括 `active`、`low_priority`、`dismissed`、`resolved`。
- 有消减规则和用户停练规则。

对象关系草案：

```text
WeaknessEvidence
-> WeaknessAggregationRule
-> WeaknessItem
-> WeaknessStatus
-> WeaknessDecayRule / WeaknessDismissal
-> TrainingTask / PolishModeSession
-> AbilityTree / AbilityNode / AbilityLevel
```

边界说明：

- `WeaknessItem` 是否作为一期核心服务端对象独立保存仍需确认。
- 能力树是否完整进入一期仍需确认。推荐一期采用轻量能力树，先支持能力节点、掌握度和训练进展，不做完整职业能力 ontology。
- 消减规则是否自动执行仍需确认。推荐一期先输出消减建议，由用户或明确动作确认。
- `dismissed` 后再次暴露如何恢复 `active` 仍需确认。推荐保留证据并在新高严重度证据出现时提示用户恢复。

## 10. 训练机制

训练机制 confirmed 口径：

- 待打磨是执行层，不等于薄弱项中心。
- 一个主题可以归并到薄弱项、加入待打磨、两者都做、只临时加入待打磨。
- 训练抽屉是统一入口。
- 入口包括岗位详情、模拟面试详情 / 报告、复盘详情。
- 支持归并到薄弱项、加入待打磨、立即发起打磨、暂不处理。
- 展示来源摘要、严重度、关联岗位、证据摘要、推荐归并主题、操作影响预览。

对象关系草案：

```text
TrainingDrawerContext
-> TrainingSource
-> Severity
-> RecommendedMergeTopic
-> TrainingImpactPreview
-> TrainingAction
-> WeaknessItem / TrainingQueue / TrainingTask / PolishModeSession
```

边界说明：

- `TrainingQueue` 承载待打磨执行层清单，不反向替代 `WeaknessItem`。
- 训练抽屉是否作为一期通用交互仍需确认。推荐作为通用入口进入一期，否则薄弱项、打磨和复盘会割裂。
- 待打磨清单是否独立页面化仍需确认。推荐一期先做工作台 / 详情页内的最小清单，不单独扩展完整训练中心。

## 11. 资产归档

资产归档 confirmed 口径：

- 支持整份归档到资产库。
- 支持单题归档到资产库。
- 归档时选择资产类型。
- 若资产类型带 schema，则动态渲染字段表单。

对象关系草案：

```text
AssetArchiveRequest
-> AssetType
-> AssetSchema
-> AssetFieldValue
-> Asset
-> ArchivedQuestion / ArchivedReview
```

边界说明：

- `AssetType` 表示归档类型，来源和管理权限仍需确认。
- `AssetSchema` 建议只支持一期所需的字段子集，如文本、枚举、标签、日期、引用对象，完整复杂 schema 后置。
- `ArchivedQuestion` 和 `ArchivedReview` 必须保留原始来源引用和归档时快照。
- 资产库页面是否进入一期仍需确认。推荐一期具备最小资产列表 / 详情查看，复杂检索和管理后置。

## 12. RAG / 知识库对象与流程草案

```text
KnowledgeBase
-> KnowledgeDocument uploaded
-> IndexingJob queued/running
-> KnowledgeChunk indexed
-> InterviewSession / PolishModeSession / Review 使用知识库上下文
-> RetrievalQuery
-> RetrievalResult
-> Citation / Evidence
-> InterviewQuestion / FollowUpQuestion / Feedback / ScoreReport / Review 引用证据
```

边界说明：

- 一期知识库范围、上传范围、个人 / 团队 / 公共可见性仍需确认。
- 检索技术路线仍需确认。推荐混合检索作为 `historical`，但不得写成 confirmed。
- RAG 失败降级仍需确认。推荐无命中时使用岗位 / 简历上下文继续，并显式标注证据缺口。
- 复盘详情必须回看引用来源，不得把无 RAG 证据的 LLM 解释伪装为有证据支持。

## 13. 多轮高阶面试对象与状态机草案

```text
SessionRecord 列表或 Job 详情发起
-> InterviewLaunchContext
-> InterviewReferencePack
-> InterviewStrategy
-> InterviewSession draft/ready/in_progress
-> 按模式分支
   -> PolishModeSession active
      -> ProgressTree
      -> InterviewTurn asked/answered/evaluated/revised
      -> RoundEvaluation
      -> AbilityTree / TrainingProgress / WeaknessItem
      -> NextQuestionRecommendation
      -> UserEndDecision continue/end
   -> PressureInterviewSession active
      -> InterviewQuestionSet generated/active/completed
      -> InterviewQuestion / InterviewAnswer
      -> InterviewCompletion
      -> FinalAssessment / ScoreReport / MockInterviewReview
-> SessionRecord 回写
```

边界说明：

- 多轮范围已由用户补充确认拆分为两类：打磨模式按 `ProgressTree / 进展树` 持续出题并由用户决定结束；压力面模式按 `InterviewQuestionSet / 题组` 完成后结束。
- “固定 3 轮”不再作为多轮面试总规则，也不再作为 W13-C 推荐总方案；它最多只能作为压力面模式题组策略的一种后续候选。
- 压力面模式的题目数量、难度、题型组合仍需确认，不得由 Codex 自行决定。
- 高阶面试定义、多轮上下文保存方式、压力面模式暂停 / 继续策略仍需确认；打磨模式中“用户决定继续 / 结束”已 confirmed。
- `InterviewContext` 必须让暂停 / 继续、复盘和评分证据链可恢复，但完整 prompt / response 或完整上下文保存仍需确认。

## 14. LLM provider / adapter 边界草案

草案边界：

- 一期必须接真实 LLM，但具体 provider 未确认。
- `LLMProviderConfig` 保存或引用 provider 配置，密钥不应写入普通业务文档或明文日志。
- `LLMGenerationRequest` / `LLMGenerationResult` 记录请求、结果、失败、成本与版本的保存边界，但完整 prompt / response 是否保存必须由用户确认。
- `PromptTemplateVersion` 用于将问题生成、追问、打磨反馈、评分、复盘输出与模板版本绑定。
- 推荐保留 provider adapter 抽象并先接一个默认 provider；该推荐仍是 `historical`。

## 15. API / 后端服务边界草案

后端服务边界草案：

- Auth / Permission：登录、会话、角色、资源授权、权限不足。
- Workspace：组织、成员归属、资源范围。
- Job / Resume：岗位与简历保存、列表、归档、版本。
- Knowledge：知识库、文档、切片、索引、检索、引用。
- Interview：发起、策略、首题、轮次、turn、暂停 / 继续、完成。
- Polish / Simulation：模式化会话、反馈、报告、训练建议。
- Review：真实复盘、模拟复盘、逐题拆解、整场判断。
- Weakness / Training：薄弱项、证据、训练队列、训练抽屉操作。
- Asset：整份 / 单题归档、资产类型、schema、动态字段。
- Score / Export：评分报告、导出快照、Markdown 下载。
- LLM / Audit：LLM adapter、调用日志、RAG 日志、操作审计。

未确认内容：

- 后端框架。
- API 优先还是实现优先。
- 前后端目录结构。
- 数据库类型。
- 部署 / 运维边界。

## 16. 部署 / 运维 / 配置边界草案

一期至少需要确认：

- 部署目标：本地 / 演示、单机服务器、云平台轻部署或其他。
- 配置边界：LLM provider、embedding provider、数据库连接、知识库存储、密钥来源。
- 日志边界：应用日志、LLM 调用日志、RAG 检索日志、权限审计、导出 / 归档操作。
- 成本记录：LLM token、embedding、索引任务、失败重试是否记录。
- 数据安全：简历、面试回答、知识库材料、prompt / response、复盘报告、资产字段都需要脱敏和保留周期策略。

## 17. 历史确认卡吸收状态

本节原先包含账号、权限、服务端保存、RAG、LLM、API / 后端、多轮、复盘、薄弱项、训练、资产等确认卡。W13-Cleanup 后，这些卡不再作为当前待确认入口；产品范围与对象边界已由用户 confirmed 事实、`OPEN_QUESTIONS.md` 和 `DESIGN_DECISIONS.md` 吸收。

| 原确认卡范围 | 当前状态 | 当前事实源 |
| --- | --- | --- |
| 登录 / 权限、服务端保存、真实 LLM、RAG / 知识库 | confirmed | 本文档第 2、3、12、14、15 节；`FC-01`、`FC-05`、`FC-15` |
| 多轮高阶面试、打磨模式、压力面模式 | confirmed | 本文档第 6、7、13 节；`FC-06`、`FC-10`、`FC-11` |
| 真实 / 模拟复盘、薄弱项、训练抽屉、待打磨 | confirmed | 本文档第 8、9、10 节；`FC-12`、`FC-14`、`FC-17`、`FC-18`、`FC-19` |
| 资产归档与资产类型 schema | confirmed | 本文档第 11 节；`FC-13`、`FC-16` |
| 数据库、provider、部署、日志等实现级选型 | implementation detail | 不在本轮产品范围清理中拍板；进入实现计划前由后续实现计划或 W13-E/F 压缩确认 |

## 18. 当前推荐汇总状态

原推荐汇总已被压缩为上表。当前有效事实以本文档的对象模型正文、`OPEN_QUESTIONS.md` 的 FC 归并索引和 `DESIGN_DECISIONS.md` 的 DD 索引为准；旧确认卡正文只保留在 git 历史中，不能再被后续窗口当作待确认任务池。

## 19. W13-D 输入

`W13-D` 应承接以下输入：

- `ScoreReport`、`ScoreDimension`、`RoundEvaluation` 的维度、权重、总分汇总、修订和证据绑定。
- `FeedbackSummary` 的复盘摘要、逐轮反馈、逐题反馈、岗位 / 简历 / RAG 证据说明。
- `SessionRecord` 列表中的评分、复盘、导出状态、权限不足、归档 / 删除、训练入口和弱项入口。
- `ExportSnapshot / ExportRecord` 的复制 / Markdown 下载范围、快照保存、文件命名、失败态和敏感信息处理。
- 打磨模式需要单独验收：`ProgressTree` 驱动出题、每题反馈、能力树 / 当前进展 / 薄弱点更新、`NextQuestionRecommendation` 和 `UserEndDecision` 是否进入评分、复盘、导出与 DoD。
- 压力面模式需要单独验收：`InterviewQuestionSet` 题组完成、`InterviewCompletion` 结束、`FinalAssessment`、`ScoreReport`、`WeaknessSummary`、`SuggestedPolishTopic` 和 `MockInterviewReview` 是否完整进入评分、复盘、导出与 DoD。
- 打磨模式题级反馈是否进入导出、压力面模式结束报告是否完整导出、真实面试复盘是否导出。
- RAG 无命中、多轮暂停 / 继续、LLM 失败、评分失败、复盘生成失败、归档失败的 MVP DoD。
- 训练抽屉、弱项消减建议、资产归档和动态 schema 字段在复盘 / 报告 / 导出中的展示边界。
- `W13-D` 应承接本文档清理后的唯一事实源，不再读取旧确认卡作为待确认入口。

## 20. 当前不进入实现的说明

当前仍不进入实现窗口，原因不是产品范围缺失，而是实现层任务尚未正式开窗：

- provider、数据库、部署、日志等实现级选型仍需在 W13-E/F 或后续实现计划中压缩成可执行验收清单。
- `apps/**`、`infra/**`、`tools/**`、`tests/**` 和 `DOC_STATE.yaml` 均不是本窗口修改对象。
- 本文档只作为对象模型 / RAG / 多轮 / 后端边界事实源，不生成 implementation packet。
